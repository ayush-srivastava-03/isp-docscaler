# ******************************************************************************
#
#                                --- WARNING ---
#
#   This work contains trade secrets of DataDirect Networks, Inc.  Any
#   unauthorized use or disclosure of the work, or any part thereof, is
#   strictly prohibited.  Copyright in this work is the property of DataDirect.
#   Networks, Inc. All Rights Reserved. In the event of publication, the.
#   following notice shall apply: (C) 2016, DataDirect Networks, Inc.
#
# ******************************************************************************

import os
import configparser
import re
import stat
from itertools import chain

from modules.lustreConfig.section import EsConfigSection
from modules.lustreConfig.global_section import GlobalSection
from modules.lustreConfig.ha_section import HASection
from modules.lustreConfig.host_defaults_section import HostDefaultsSection
from modules.lustreConfig.hsm_section import HSMSection
from modules.lustreConfig.emf_section import EmfSection
from modules.lustreConfig.filesystem_section import FilesystemSection
from modules.lustreConfig.pool_section import PoolSection
from modules.lustreConfig.zpool_section import ZpoolSection
from modules.lustreConfig.host_section import HostSection
from modules.lustreConfig.extra_section import ExtraSection
from modules.lustreConfig.sfa_section import SFASection
from modules.lustreConfig.rest_section import RestSection
#from es.utils import get_file_content
#from scalers.errors import ScalersException
#from scalers.utils.command import StringCommand
#from scalers.utils.cmd import CmdExecutor


class EXAScalerConfig(object):
    """ EXAScaler configuration.
    """

    class EXAScalerConfigParser(configparser.ConfigParser):
        """ Custom ConfigParser implementation which overrides standard optionxform method.
        """

        def _tune_aliased_nic_names(self):
            """ Replace all occurrences of strings like 'ib0-alias0' with sth like 'ib0:0' in all keys and values of
                'host_defaults' and 'host' sections of exascaler.conf.
            """
        
            aliased_nic_regex = r'(?P<nic>\w+)-alias(?P<alias>\d+)(?P<param>\w*)'
            for section_data in (v for k, v in self._sections.items() if k.startswith('host')):
                for key, value in list(section_data.items()):
                    match = re.search(aliased_nic_regex, key)
                    if match:                 
                        section_data['{nic}:{alias}{param}'.format(**match.groupdict())] = section_data.pop(key)
                        
                for key in ('nic_list', 'lnets', 'ring0', 'ring1'):
                    if key in section_data:
                        section_data[key] = re.sub(aliased_nic_regex, '\g<nic>:\g<alias>\g<param>', section_data[key])

        def read(self, filenames):
            configparser.ConfigParser.read(self, filenames)
            self._tune_aliased_nic_names()

        def optionxform(self, optionstr):
            """ Custom optionxform implementation which doesn't cast optionstr to lowercase.
            """

            return optionstr

    def ha_group_list(self, hostname):
        """ Return the list of host names in the same group as hostname

        This is a solution method rather than a host method as the host does not have
        visibility of the ha_groups data currently.  A better long term solution might be
        to create a "ha group" object and have the hosts reference that.
        """
        if hostname in self.global_settings.clients_list:
            return list()
        return self.ha_settings.ha_groups[self.hosts_settings[hostname].ha_group_idx]

    def _tune_global(self):
        """ Tune global settings.
        """
        self.global_settings = GlobalSection(self.config)

        if self.config.has_section('set_param_tunings'):
            self.global_settings.set_param_tunings = ExtraSection(
                self.config_file, 'set_param_tunings', shadow_config=self.shadow_config)
        if self.config.has_section('conf_param_tunings'):
            self.global_settings.conf_param_tunings = ExtraSection(
                self.config_file, 'conf_param_tunings', shadow_config=self.shadow_config)

    def _tune_ha(self):
        """ Tune HA settings.
        """

        if not self.config.has_section('HA'):
            self.ha_settings = None
            return

        self.ha_settings = HASection(self.config, shadow_config=self.shadow_config)

        if self.ha_settings.ha_group_count is None:
            self.ha_settings.ha_groups = [self.global_settings.host_list[:], ]
            self.ha_settings.ha_group_count = 1

        cur_ha_group = 0
        for host_list in self.ha_settings.ha_groups:
            for host in host_list:
                self.hosts_settings[host].ha_group_idx = cur_ha_group
                self.hosts_settings[host].ha_group = self.ha_settings.ha_groups[cur_ha_group][:]
            cur_ha_group += 1

        for host_name in self.global_settings.host_list:
            ha_group_idx = self.hosts_settings[host_name].ha_group_idx
            for lnet, _ in self.hosts_settings[host_name].parse_lnets():
                if lnet not in self.hosts_settings[host_name].lnet_members:
                    self.hosts_settings[host_name].lnet_members[lnet] = list()
                for host in self.ha_settings.ha_groups[ha_group_idx]:
                    if lnet in self.hosts_settings[host].host_nids_dict():
                        self.hosts_settings[host_name].lnet_members[lnet].append(
                            self.hosts_settings[host].host_nids_dict()[lnet]
                        )


    def _tune_emf(self):
        """ Tune emf settings.
        """
        if not self.config.has_section('EMF'):
            self.emf_settings = None
        else:
            self.emf_settings = EmfSection(self.config, shadow_config=self.shadow_config)


    def _tune_fs(self):
        """ Tune fs settings.
        """

        self.fs_settings = dict()
        self.pool_settings = dict()
        mgs_count = 0
        mgs_fs = None

        for fs in self.global_settings.fs_list:
            self.fs_settings[fs] = FilesystemSection(
                self.config, fs, self.global_settings.log_dir, shadow_config=self.shadow_config)
            self.global_settings.add_hosts_to_host_list(self.fs_settings[fs].host_list)

            if self.fs_settings[fs].mgs_internal:
                mgs_count += 1
                self.global_settings.mgs_fs = mgs_fs = fs

            if self.fs_settings[fs].mdt_failback is None:
                self.fs_settings[fs].mdt_failback = True

            if self.fs_settings[fs].mgs_failback is None:
                self.fs_settings[fs].mgs_failback = True

            if self.fs_settings[fs].ost_failback is None:
                self.fs_settings[fs].ost_failback = True

            for pool in self.fs_settings[fs].pools:
                self.pool_settings[pool] = PoolSection(self.config, pool, shadow_config=self.shadow_config)

        # Ensure that the fs with the mgs is at the start of the list
        self.global_settings.fs_list.remove(mgs_fs)
        self.global_settings.fs_list.insert(0, mgs_fs)

        self.global_settings.used_backfs_types = set(fs.backfs for fs in self.fs_settings.values())

    def _tune_zpools(self):
        """ Tune zpools settings.
        """

        self.zpool_settings = dict()
        for fs in self.global_settings.fs_list:
            fs_settings = self.fs_settings[fs]
            if fs_settings.backfs == 'zfs':
                for zpool in chain(fs_settings.mgs_zpools, fs_settings.mdt_zpools, fs_settings.ost_zpools):
                    self.zpool_settings[zpool] = ZpoolSection(self.config, zpool, shadow_config=self.shadow_config)

    def _tune_hsm(self):
        """ Tune HSM settings.
        """

        if self.global_settings.hsm_active:
            self.hsm_settings = HSMSection(self.config, shadow_config=self.shadow_config)
        else:
            self.hsm_settings = None if not self.config.has_section('HSM') else HSMSection(
                self.config, shadow_config=self.shadow_config)

    def _tune_hosts(self):
        """ Tune hosts settings.
        """

        self.hosts_settings = dict()

        for host in self.global_settings.host_list:
            self.hosts_settings[host] = HostSection(
                self.config, host, self.host_defaults_settings, shadow_config=self.shadow_config)

        for host in self.global_settings.clients_list:
            self.hosts_settings[host] = HostSection(
                self.config, host, self.host_defaults_settings, shadow_config=self.shadow_config)

        sysctl_defaults = ExtraSection(self.config_file, 'sysctl_defaults', shadow_config=self.shadow_config)\
            if self.config.has_section('sysctl_defaults') else None

        for host in self.global_settings.host_list:

            if self.config.has_section('sysctl {0}'.format(host)):
                self.hosts_settings[host].sysctl = \
                    ExtraSection(
                        self.config_file,
                        'sysctl {0}'.format(host),
                        sysctl_defaults.settings if sysctl_defaults is not None else None,
                        shadow_config=self.shadow_config)
            else:
                self.hosts_settings[host].sysctl = sysctl_defaults
    #
    # def _parse_es_install_version_file(self):
    #     """ Get EXAScaler version and flavour from '/etc/es_install_version' file.
    #     """
    #
    #     if os.path.exists('/etc/es_install_version'):
    #
    #         content = get_file_content('/etc/es_install_version')
    #
    #         template = re.compile(r"^\s*EXAScaler\s(?P<flavour>\S+)\s(?P<distro>\S+)"
    #                               r"\s(?P<major>\d+)\.(?P<minor>\d+)\.(?P<revision>\d+)-(?P<release>\S+)\s*$")
    #
    #         match = template.match(content)
    #         if match is not None:
    #             self.flavour = match.group('flavour')
    #             self.distro = match.group('distro')
    #             major = int(match.group('major'))
    #             minor = int(match.group('minor'))
    #             rev = int(match.group('revision'))
    #             self.version = (major, minor, rev,)
    #
    # def _parse_es_drivers_type_file(self):
    #     """ Get EXAScaler drivers type from '/etc/es_drivers_type' file.
    #     """
    #
    #     if os.path.exists('/etc/es_drivers_type'):
    #         content = get_file_content('/etc/es_drivers_type')
    #         self.drivers_type = content.strip()

    def _tune_sfa(self):
        """ Tune SFA settings.
        """

        self.sfa_settings = dict()

        for sfa in self.global_settings.sfa_list:
            self.sfa_settings[sfa] = SFASection(self.config, sfa, shadow_config=self.shadow_config)

    def _tune_rest(self):
        """ Tune REST API settings.l
        """

        if not self.config.has_section('rest'):
            self.rest_settings = None
            return

        self.rest_settings = RestSection(self.config, shadow_config=self.shadow_config)

        for host in self.global_settings.host_list:
            if self.hosts_settings[host].rest_keepalived_nic is None:
                self.hosts_settings[host].rest_keepalived_nic = self.hosts_settings[host].rest_primary_nic

    def __init__(self, config_file):
        """ Basic initialization.
        :param config_file: absolute path to configuration file.
        """

        self.version = (None, None, None, )
        self.flavour = None
        self.distro = None
        self.drivers_type = None

        self.config_file = config_file
        self.config = self.EXAScalerConfigParser()
        self.config.read(config_file)
        self.shadow_config = None

        self._tune_global()

        self.host_defaults_settings = None if not self.config.has_section('host_defaults') \
            else HostDefaultsSection(self.config, shadow_config=self.shadow_config)

        self._tune_hsm()

        self._tune_fs()

        self._tune_zpools()

        # sort host_list by the order of host sections to fix automatic IP assignment
        ordered_sections_list = self.config.sections()
        ordered_hosts = [ i.split()[1] for i in ordered_sections_list if i.startswith('host ') ]
        self.global_settings.host_list = [ host for host in ordered_hosts if host in self.global_settings.host_list ]

        self.global_settings.finalize_host_list()
        if self.global_settings.hsm_active:
            self.global_settings.add_hosts_to_host_list(self.hsm_settings.rbh_host_name)

        self._tune_hosts()

        for fs in self.global_settings.fs_list:
            fs_settings = self.fs_settings[fs]
            fs_settings.associate_hosts(self.hosts_settings)
            fs_settings.check_ost_lnet_list(self.hosts_settings)

        self._tune_ha()

        self._tune_emf()

        self._tune_sfa()

        self._tune_rest()

    def to_dict(self):
        """ Convert to dictionary.
        """

        return dict(
            global_settings=self.global_settings.to_dict(),
            host_defaults_settings=None if self.host_defaults_settings is None else (
                self.host_defaults_settings.to_dict()),
            hsm_settings=None if self.hsm_settings is None else self.hsm_settings.to_dict(),
            fs_settings={key: value.to_dict() for key, value in self.fs_settings.items()},
            pool_settings={key: value.to_dict() for key, value in self.pool_settings.items()},
            zpool_settings=None if not self.zpool_settings else {
                key: value.to_dict() for key, value in self.zpool_settings.items()},
            emf_settings=None if self.emf_settings is None else self.emf_settings.to_dict(),
            ha_settings=None if self.ha_settings is None else self.ha_settings.to_dict(),
            hosts_settings={key: value.to_dict() for key, value in self.hosts_settings.items()},
            sfa_settings={key: value.to_dict() for key, value in self.sfa_settings.items()},
            rest_settings=None if self.rest_settings is None else self.rest_settings.to_dict(),
        )