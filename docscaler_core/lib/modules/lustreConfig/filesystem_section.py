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

""" Filesystem section of EXAScaler configuration file.
"""

import os
import re
from itertools import chain

from modules.lustreConfig.section import EsConfigSection
from .utils import cast_to_bytes


class FilesystemSection(EsConfigSection):
    """ Filesystem section of EXAScaler configuration file.
    """

    def __init__(self, config, fs_name, log_dir_base, shadow_config=None):
        """ Basic initialization.
        """

        self.name = fs_name

        self.mkfs_opts = None
        self.ost_opts = None
        self.mdt_opts = None
        self.mgt_mount_opts = 'max_sectors_kb=0'
        self.mdt_mount_opts = 'max_sectors_kb=0'
        self.ost_mount_opts = 'max_sectors_kb=0'
        self.mdt_size = '80%'
        self.mgs_size = None
        self.fake_nid = None
        self.mgs_fs = None
        self.ost_device_path = '/dev/mapper'
        self.mdt_base_device_path = None
        self._default_mdt_base_device_path = '/dev/mapper'
        self.mgs_device_path = None

        self.mgs_list = list()
        self.mds_list = list()
        self.oss_list = list()
        self.mdt_mke2fs_opts = list()
        self.ost_mke2fs_opts = list()
        self.tune_ost_mke2fs_opts = list()
        self.pools = list()

        self.backfs = 'ldiskfs'
        self.mgs_zpools = list()
        self.mdt_zpools = list()
        self.ost_zpools = list()

        self.default_ost_count = None
        self.default_mdt_count = 0
        self.mmp_update_interval = 5
        self.mdt_parts = None

        self.mgs_internal = False
        self.mdt_failback = None
        self.mgs_failback = None
        self.ost_failback = None
        self.hsm_active = False

        self.host_list = list()
        self.log_dir = os.path.join(log_dir_base, fs_name)

        self.ost_list = dict()
        self.mdt_list = dict()
        self.ost_lnet_list = dict()

        self.cur_ost_index = 0
        self.cur_mdt_index = 0

        self.total_ost_count = None
        self.total_mdt_count = None

        self.dom_enabled = False
        self.dom_max_file_size = '64K'

        self.client_allow_intr = 1

        super(FilesystemSection, self).__init__(config, 'fs {0}'.format(fs_name), shadow_config)

    def to_dict(self):
        """ Convert to dictionary.
        """

        fields = ['name', 'mdt_opts', 'ost_opts', 'mgs_size', 'mdt_size', 'mgs_list', 'mds_list', 'oss_list', 'pools',
                  'default_mdt_count', 'default_ost_count', 'mmp_update_interval', 'mdt_parts', 'mgs_internal',
                  'mgs_failback', 'mdt_failback', 'ost_failback', 'hsm_active', 'host_list', 'log_dir',
                  'mdt_list', 'ost_list', 'ost_lnet_list', 'cur_mdt_index', 'cur_ost_index', 'total_mdt_count',
                  'total_ost_count', 'mdt_mount_opts', 'ost_mount_opts', 'mgt_mount_opts', 'backfs',
                  'dom_enabled', 'dom_max_file_size', 'client_allow_intr', ]

        if self.backfs == 'ldiskfs':
            fields.extend(('mdt_mke2fs_opts', 'ost_mke2fs_opts', 'tune_ost_mke2fs_opts', 'mgs_device_path', 'mdt_base_device_path',
                           'ost_device_path', ))
        elif self.backfs == 'zfs':
            fields.extend(('mgs_zpools', 'mdt_zpools', 'ost_zpools', ))

        result = {field: getattr(self, field) for field in fields}

        return result

    def _configure_section(self):
        """ List all possible settings.
        """

        self._mandatory_fields = ['mds_list', 'oss_list', 'mgs_internal', ]

        self._str_fields = ['ost_opts', 'mdt_opts', 'mdt_size', 'mgs_size', 'fake_nid', 'mgs_fs',
                            'mdt_mount_opts', 'ost_mount_opts', 'mgt_mount_opts', 'backfs', 'ost_device_path',
                            'mdt_base_device_path', 'mgs_device_path', 'dom_max_file_size', ]

        self._space_separated_list_fields = ['pools', 'mdt_mke2fs_opts', 'ost_mke2fs_opts', ]

        self._int_fields = ['default_ost_count', 'default_mdt_count', 'mmp_update_interval', 'mdt_parts',
                            'client_allow_intr', ]

        self._bool_fields = ['mgs_internal', 'mgs_failback', 'mdt_failback', 'ost_failback', 'hsm_active', 'dom_enabled', ]

        self._list_of_nodes_fields = ['mgs_list', 'mds_list', 'oss_list', 'mgs_zpools', 'mdt_zpools', 'ost_zpools', ]

        self._regex_separated_list_fields = ['tune_ost_mke2fs_opts', ]

    def _check_settings(self):
        """ Verify obtained settings.
        """
        if self.backfs == 'ldiskfs':
            # ToDo: Deprecate mds_base_device_path option in favour of mdt_base_device_path
            self.mdt_base_device_path = self.mdt_base_device_path or self._default_mdt_base_device_path

        valid_allow_intr_values = (0, 1)

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """
        settings = chain(self._str_fields, self._space_separated_list_fields, self._int_fields, self._bool_fields,
                         self._list_of_nodes_fields, self._regex_separated_list_fields, )
        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

        if self.mdt_size is not None:
            self.mdt_size = self.mdt_size.replace('%%', '%')
        if self.mgs_size is not None:
            self.mgs_size = self.mgs_size.replace('%%', '%')

        if self.mgs_internal:
            if self.mgs_size is None:
                self.mgs_size = '500m'
            if not self.mgs_list:
                self.mgs_list = self.mds_list[:2]

        for element in chain(self.mgs_list, self.mds_list, self.oss_list):
            if element not in self.host_list:
                self.host_list.append(element)

        if self.tune_ost_mke2fs_opts:
            tune_ost_mke2fs_opts_tmp = list()
            for option in self.tune_ost_mke2fs_opts:
                pattern = re.compile(
                    r"for\s+(?P<arg1>(\d+(B|KB|MB|GB|TB|PB)\s?(<|>|<=|>=|==))?\s?size\s?((<|>|<=|>=|==)\s?\d+(B|KB|MB|GB|TB|PB))?)\s+apply\s+(\'(?P<arg2>((?:''|[^'])*))\')\s?$")
                size_pattern = re.compile(r'([\d+]+B|[\d+]+KB|[\d+]+MB|[\d+]+GB|[\d+]+TB|[\d+]+PB)')
                tune_ost_mke2fs_opts_tmp.append(size_pattern.sub(lambda x: str(cast_to_bytes(x.group())), option))
            self.tune_ost_mke2fs_opts = tune_ost_mke2fs_opts_tmp

        keys_to_proceed = [key for key in self.unknown_settings.keys() if key.endswith('_ost')]
        for key in keys_to_proceed:
            lnet = key.split('_ost')[0]
            osts = [int(ost) for ost in self.unknown_settings[key].split()]
            self.ost_lnet_list[lnet] = osts
            del self.unknown_settings[key]

        try:
            self.dom_max_file_size = cast_to_bytes(self.dom_max_file_size)
        except ValueError as e:
            raise ValueError(e)

    def fsck_log_dir(self):
        """ Get directory for fsck logs.
        """

        return os.path.join(self.log_dir, 'fsck')

    def client_mount_point(self):
        """ Get client mount point.
        """
        return os.path.join('/lustre', self.name, 'client')

    def get_next_odx(self):
        """ Returns the next free OST index
        """

        ret = self.cur_ost_index
        self.cur_ost_index += 1
        return ret

    def get_next_mdx(self):
        """ Returns the next free MDT index.
        """

        ret = self.cur_mdt_index
        self.cur_mdt_index += 1
        return ret

    def associate_hosts(self, hosts):
        """ Go through host list and get references to Host objects that serve us.
        :param hosts: list of hosts
        """

        for host in self.host_list:
            host_obj = hosts[host]
            host_obj.register_fs(self)

        for host in self.oss_list:
            host_obj = hosts[host]
            host_obj.register_fs_osts(self)
            self.ost_list[host] = host_obj.ost_list[self.name]

        ost_count = 0
        for host in self.oss_list:
            ost_count += len(self.ost_list[host])
        self.total_ost_count = ost_count

        for host in self.mds_list:
            host_obj = hosts[host]
            self.mdt_list[host] = host_obj.register_fs_mdts(self)

        mdt_count = 0
        for host in self.mds_list:
            mdt_count += len(self.mdt_list[host])
        self.total_mdt_count = mdt_count

    def check_ost_lnet_list(self, hosts):
        """ Check that LNET with OST restrictions were configured correctly.
        :param hosts: list of hosts
        """

        ost_list = list()

        for osts in self.ost_list.values():
            ost_list.extend(osts)


    def get_ost_list(self, host):
        """ Returns the list of OSTs that run on a host.
        :param host: host name
        """

        if host not in self.ost_list:
            return list()
        return self.ost_list[host]

    def get_mdt_list(self, host):
        """ Returns the list of MDTs that run on a host.
        :param host: host name
        """

        if host not in self.mdt_list:
            return list()
        return self.mdt_list[host]
