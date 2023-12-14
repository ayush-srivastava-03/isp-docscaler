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
import re
import socket
import struct
from collections import OrderedDict

from modules.lustreConfig.section import EsConfigSection
from modules.lustreConfig.utils import parse_index_list, split_list_settings


class HostSection(EsConfigSection):
    """ Host section of EXAScaler configuration file.
    """

    _nic_names = {
        'ib0': 'o2ib',
        'ib1': 'o2ib1',
        'ib2': 'o2ib2',
        'ib3': 'o2ib3',
        'eth0': 'tcp',
        'eth1': 'tcp1',
        'eth2': 'tcp2',
        'eth3': 'tcp3',
    }

    class Nic(object):
        """ Nic settings.
        """

        def __init__(self, name, default_settings=None):
            """ Basic initialization
            """

            self.name = name

            self.cfg = None if default_settings is None else default_settings.cfg
            self.device = None if default_settings is None else default_settings.device
            self.slaves = None if default_settings is None else default_settings.slaves
            self.netmask = None if default_settings is None else default_settings.netmask
            self.gateway = None if default_settings is None else default_settings.gateway
            self.master = None
            self.slave = None
            self.netaddr = None
            self.is_bonded = None
            self.ip = None
            self.network = None
            self.mac = None

        def get_from_config_settings(self, settings):
            """ Obtain settings from configuration file.
            :param settings: Dictionary with settings from configuration file.
            """

            if self.name == 'ipmi':
                keys = ('netmask', 'gateway',)
            else:
                self.device = self.name
                keys = ('cfg', 'device', 'slaves', 'netmask', 'gateway', 'network', 'mac')

            for key in keys:
                setting = '{0}_{1}'.format(self.name, key)
                if setting in settings:
                    setattr(self, key, settings[setting])
                    del settings[setting]

            if self.cfg is not None:

                valid_keys = ('NETMASK', 'GATEWAY', 'MASTER', 'SLAVE')
                unknown_settings = list()

                for line in self.cfg.splitlines():

                    if len(line) == 0:
                        continue

                    settings = line.split('=')
                    if len(settings) != 2 or settings[0] not in valid_keys:
                        unknown_settings.append(line)
                        continue

                    name, value = settings[0].lower(), settings[1]

                    setattr(self, name, value)

                self.cfg = None if len(unknown_settings) == 0 else '\n'.join(unknown_settings)

        def to_dict(self):
            """ Convert to dictionary.
            """

            keys = ('cfg', 'device', 'slaves', 'netmask', 'gateway', 'network', 'mac',
                    'master', 'slave', 'netaddr', 'is_bonded', 'ip',)

            return {key: getattr(self, key) for key in keys if getattr(self, key) is not None}

    def __init__(self, config, name, host_defaults, shadow_config=None):
        """ Basic initialization.
        """

        self.name = name

        self._host_defaults = host_defaults

        self.nic_list = self._host_defaults.nic_list if self._host_defaults is not None else list()
        self.lnets = self._host_defaults.lnets if self._host_defaults is not None else list()
        self.host_sfa_list = self._host_defaults.host_sfa_list if self._host_defaults is not None else list()
        self.stonith_pass = self._host_defaults.stonith_pass if self._host_defaults is not None else None
        self.stonith_user = self._host_defaults.stonith_user if self._host_defaults is not None else None
        self.stonith_type = self._host_defaults.stonith_type if self._host_defaults is not None else None
        self.ipmi_delay = self._host_defaults.ipmi_delay if self._host_defaults is not None else None
        self.ipmi_method = self._host_defaults.ipmi_method if self._host_defaults is not None else None
        self.ipmi_monitor = self._host_defaults.ipmi_monitor if self._host_defaults is not None else None
        self.ipmi_power_wait = self._host_defaults.ipmi_power_wait if self._host_defaults is not None else 5

        self.bonding_mode = self._host_defaults.bonding_mode if self._host_defaults is not None else None
        self.modprobe_cfg = self._host_defaults.modprobe_cfg if self._host_defaults is not None else None
        self.serial_speed = self._host_defaults.serial_speed if self._host_defaults is not None else '115200'
        self.serial_port = self._host_defaults.serial_port if self._host_defaults is not None else 'ttyS0'
        self.ring0 = self._host_defaults.ring0 if self._host_defaults is not None else None
        self.ring1 = self._host_defaults.ring1 if self._host_defaults is not None else None
        self.grub_args = self._host_defaults.grub_args if self._host_defaults is not None else list()

        self.rest_ext_nic = self._host_defaults.rest_ext_nic if self._host_defaults is not None else None
        self.rest_int_nic = self._host_defaults.rest_int_nic if self._host_defaults is not None else None
        self.rest_primary_nic = self._host_defaults.rest_primary_nic if self._host_defaults is not None else None
        self.rest_keepalived_nic = self._host_defaults.rest_keepalived_nic if self._host_defaults is not None else None

        self.rest_cert_ca = self._host_defaults.rest_cert_ca if self._host_defaults is not None else None
        self.rest_cert_crl = self._host_defaults.rest_cert_crl if self._host_defaults is not None else None
        self.rest_cert_server = self._host_defaults.rest_cert_server if self._host_defaults is not None else None
        self.rest_cert_server_key = self._host_defaults.rest_cert_server_key \
            if self._host_defaults is not None else None

        self.nics = dict()

        self.peers = list()
        self.stonith_primary_peers = list()
        self.stonith_secondary_peers = list()
        self.oid = None

        self.sysctl = None
        self.fs_list = list()
        self.ost_list = dict()
        self.ost_device_paths = dict()
        self.mdt_list = dict()
        self.mdt_base_device_paths = dict()
        self.ha_group_idx = None
        self.ha_group = None

        self.lnet_nics = list()
        self.lnet_members = dict()

        super(HostSection, self).__init__(config, 'host {0}'.format(self.name), shadow_config)

    def to_dict(self):
        """ Convert to dictionary.
        """

        fields = ('name', 'nic_list', 'lnets', 'stonith_pass', 'stonith_user', 'stonith_type', 'bonding_mode',
                  'modprobe_cfg', 'serial_speed', 'serial_port', 'peers', 'stonith_primary_peers', 'grub_args',
                  'stonith_secondary_peers', 'host_sfa_list', 'oid', 'fs_list', 'ost_list', 'mdt_list', 'ha_group_idx',
                  'ha_group', 'ring0', 'ring1', 'lnet_nics', 'lnet_members', 'ipmi_delay', 'ipmi_monitor', 'ipmi_method',
                  'ipmi_power_wait', 'rest_ext_nic', 'rest_int_nic', 'rest_primary_nic', 'rest_keepalived_nic',
                  'rest_cert_ca', 'rest_cert_crl', 'rest_cert_server', 'rest_cert_server_key', 'ost_device_paths',
                  'mdt_base_device_paths', )

        result = {field: getattr(self, field) for field in fields}
        result['nics'] = {key: value.to_dict() for key, value in self.nics.items()}
        result['sysctl'] = None if self.sysctl is None else self.sysctl.to_dict()
        return result

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._str_fields = ['stonith_pass', 'stonith_user', 'stonith_type', 'bonding_mode', 'modprobe_cfg',
                            'serial_speed', 'serial_port', 'oid', 'ring0', 'ring1', 'ipmi_method', 'grub_args',
                            'rest_ext_nic', 'rest_int_nic', 'rest_primary_nic', 'rest_keepalived_nic',
                            'rest_cert_ca', 'rest_cert_crl', 'rest_cert_server', 'rest_cert_server_key', ]

        self._space_separated_list_fields = ['nic_list', 'lnets', 'stonith_primary_peers',
                                             'stonith_secondary_peers', 'host_sfa_list', ]

        self._mandatory_fields = ['lnets', 'stonith_type', 'nic_list', ]

        self._list_of_nodes_fields = ['peers', ]

        self._int_fields = ['ipmi_delay', 'ipmi_monitor', 'ipmi_power_wait', ]

    def is_ipmi_required(self):
        """ If the stonith settings require IPMI.
        """

        return self.stonith_type in ('ipmi', 'ipmi-slow',)

    def _tune_bonding(self, nic_list):
        """ Perform tunings for bonding.
        """

        for nic in nic_list:

            if self.nics[nic].slave is not None:
                self.nics[nic].slave = None

            if self.nics[nic].master is not None:
                master = self.nics[nic].master
                self.nics[master].is_bonded = True

        for nic in nic_list:
            if self.nics[nic].slaves is None:
                if self.nics[nic].is_bonded is None:
                    self.nics[nic].is_bonded = False
                continue
            self.nics[nic].is_bonded = True

            slave_list = self.nics[nic].slaves.split(' ')

            for slave in slave_list:
                self.nics[slave].master = nic

    def _tune_ip(self, nic_list):
        """ Perform tunings for ip addresses.
        """

        for nic in nic_list:

            if self.nics[nic].master is not None:
                continue

            ip_setting = '{0}_ip'.format(nic)

            if ip_setting in self.unknown_settings:
                self.nics[nic].ip = self.unknown_settings[ip_setting]
                del self.unknown_settings[ip_setting]
            elif (self._host_defaults is not None) and (nic in self._host_defaults.base_ip):
                self.nics[nic].ip = self._host_defaults.get_next_ip(nic)

    def _tune_netaddr(self, nic_list):
        """ Perform tunings for net addresses.
        """

        for nic in nic_list:

            if (nic == 'ipmi') or (self.nics[nic].ip is None):
                continue
            try:
                unpacked_ip = struct.unpack('!L', socket.inet_aton(self.nics[nic].ip))[0]
                unpacked_netmask = struct.unpack('!L', socket.inet_aton(self.nics[nic].netmask))[0]
                self.nics[nic].netaddr = socket.inet_ntoa(struct.pack('!L', unpacked_ip & unpacked_netmask))
            except socket.error:
                raise Exception("Incorrect IP format '{0}' for interface '{1}' of host '{2}' "
                                       "in EXAScaler configuration file.".format(self.nics[nic].ip, nic, self.name))

    def parse_lnets(self):
        """ Parse lnets.
        """

        result = list()
        for network in self.lnets:
            if network in self._nic_names:
                lnet, nic = self._nic_names[network], network
            else:
                lnet, nic = network.replace(')', '').split('(')
            for nic in  nic.split(','):
                result.append((lnet, nic,))
        return result

    def lnet_networks(self):
        """ Format the lnets into modprobe format.
        """

        host_lnets = self.parse_lnets()
        all_lnets_ordered = OrderedDict()

        for (lnet, nic) in host_lnets:
            if lnet not in all_lnets_ordered:
                all_lnets_ordered[lnet] = list()
            all_lnets_ordered[lnet].append(nic)

        return ', '.join([lnet + '(' + ','.join(self.nics[nic].device for nic in nics) + ')' for (lnet, nics) in all_lnets_ordered.items()])

    def _tune_nics(self, nic_list):
        """ Perform tunings for network settings.
        """

        self._tune_bonding(nic_list)
        self._tune_ip(nic_list)
        self._tune_netaddr(nic_list)

        have_gateway = False
        for nic in nic_list:

            if (nic == 'ipmi') or (self.nics[nic].gateway is None):
                continue

            have_gateway = True

        #self._validate_lnet_configuration()

    def _parse_nics(self):
        """ Parse network settings.
        """

        nic_list = list()
        if self.nic_list is not None:
            nic_list = self.nic_list[:]
        if self.is_ipmi_required():
            nic_list.append('ipmi')

        for name in nic_list:
            default_settings = None if ((self._host_defaults is None) or (name not in self._host_defaults.nics)) \
                else self._host_defaults.nics[name]
            nic = self.Nic(name, default_settings)
            nic.get_from_config_settings(self.unknown_settings)
            self.nics[name] = nic

        self._tune_nics(nic_list)

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = ('stonith_pass', 'stonith_user', 'stonith_type', 'bonding_mode', 'modprobe_cfg',
                    'serial_speed', 'serial_port', 'nic_list', 'lnets', 'stonith_primary_peers',
                    'stonith_secondary_peers', 'host_sfa_list', 'oid', 'peers', 'ring0', 'ring1',
                    'ipmi_delay', 'ipmi_method', 'ipmi_monitor', 'ipmi_power_wait', 'grub_args',
                    'rest_ext_nic', 'rest_int_nic', 'rest_primary_nic', 'rest_keepalived_nic',
                    'rest_cert_ca', 'rest_cert_crl', 'rest_cert_server', 'rest_cert_server_key', )

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

        if self.serial_speed[:2].lower() == 'no':
            self.serial_port = None

        self._parse_nics()
        self._set_stonith_defaults()

        self.lnet_nics = [element[1] for element in self.parse_lnets()]

        #self._check_lnets()

    def register_fs(self, fs):
        """ Notify this host that it is serving given fs, loads configuration.
        :param fs: filesystem
        """

        self.fs_list.append(fs.name)
        self.ost_list[fs.name] = list()
        self.mdt_list[fs.name] = list()

        if fs.backfs == 'ldiskfs':
            host_defined_ost_device_path = self.unknown_settings.get('%s_ost_device_path' % fs.name)
            self.ost_device_paths[fs.name] = host_defined_ost_device_path or fs.ost_device_path
            host_defined_mdt_base_device_path = self.unknown_settings.get('%s_mdt_base_device_path' % fs.name)
            self.mdt_base_device_paths[fs.name] = host_defined_mdt_base_device_path or fs.mdt_base_device_path

    def register_fs_osts(self, fs):

        if self.name in fs.oss_list:
            list_key = '{0}_osts'.format(fs.name)
            count_key = '{0}_ost_count'.format(fs.name)

            if list_key in self.unknown_settings:

                self.ost_list[fs.name] = sorted(parse_index_list(split_list_settings(
                    self.unknown_settings[list_key], ' ')))
                del self.unknown_settings[list_key]

            else:

                if count_key in self.unknown_settings:
                    ost_count = int(self.unknown_settings[count_key])
                else:
                    ost_count = fs.default_ost_count

                self.ost_list[fs.name] = [fs.get_next_odx() for _ in range(ost_count)]

    def register_fs_mdts(self, fs):

        if self.name in fs.mds_list:

            list_key = '{0}_mdts'.format(fs.name)
            count_key = '{0}_mdt_count'.format(fs.name)

            if list_key in self.unknown_settings:
                self.mdt_list[fs.name] = sorted(parse_index_list(split_list_settings(
                    self.unknown_settings[list_key], ' ')))
                del self.unknown_settings[list_key]
                return self.mdt_list[fs.name]

            else:

                if count_key in self.unknown_settings:
                    mdt_count = int(self.unknown_settings[count_key])
                else:
                    mdt_count = fs.default_mdt_count

                    if mdt_count == 0 and self.name == fs.mds_list[0]:
                        mdt_count = 1

                self.mdt_list[fs.name] = [fs.get_next_mdx() for _ in range(mdt_count)]
                return self.mdt_list[fs.name]

    def has_stonith_peers(self):
        """ Is stonith peers presented.
        """

        return (len(self.stonith_primary_peers) > 0) and (len(self.stonith_secondary_peers) > 0)

    def _set_stonith_defaults(self):
        """ Set stonith default settings if it is necessary.
        """

        password_policy = 'plain-text'
        if self._config.has_option('global', 'password_policy'):
            password_policy = self._config.get('global', 'password_policy')
        if self.is_ipmi_required():
            if self.stonith_user is None:
                self.stonith_user = 'root'
            if self.stonith_pass is None:
                if password_policy == 'plain-text':
                    self.stonith_pass = 'calvin'
                else:
                    self.stonith_pass = 'xxxx'
            if self.ipmi_delay is None:
                self.ipmi_delay = 15
            if self.ipmi_monitor is None:
                self.ipmi_monitor = 60
            if self.ipmi_method is None:
                self.ipmi_method = "onoff"

        elif self.stonith_type == 'ilo':
            if self.stonith_user is None:
                self.stonith_user = 'Administrator'
            if self.stonith_pass is None:
                if password_policy == 'plain-text':
                    self.stonith_pass = 'datadirect'
                else:
                    self.stonith_pass = 'xxxx'

        elif self.stonith_type == 'sfa_vm':
            if self.stonith_user is None:
                self.stonith_user = 'user'
            if self.stonith_pass is None:
                if password_policy == 'plain-text':
                    self.stonith_pass = 'user'
                else:
                    self.stonith_pass = 'xxxx'

    def host_nids(self):
        """Return a list of nids (ip@net) for this host"""

        nid_list = list()

        for (lnet, nic) in self.parse_lnets():
            ip = self.nics[nic].ip
            nid = ip + '@' + lnet
            nid_list.append(nid)

        return nid_list

    def host_lnets(self):
        """Return a list of lnets (nic@lnet) for this host"""

        nid_list = list()

        for (lnet, nic) in self.parse_lnets():
            device = self.nics[nic].device
            nid_list.append((device, lnet, ))

        return nid_list

    def host_nids_dict(self):
        """ Return a dict of nids (net: ip) or (net: [ip, ip]) for this host.
        """

        results = {}
        for lnet, nic in self.parse_lnets():
            results.setdefault(lnet, []).append(self.nics[nic].ip)

        return results

    def host_lnet_nic_mapping(self):
        """ Return a dict (lnet: nic) for this host.
        """

        results = {}
        for lnet, nic in self.parse_lnets():
            results.setdefault(lnet, []).append(nic)

        return results