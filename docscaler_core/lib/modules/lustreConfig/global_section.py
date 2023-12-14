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

""" Global section of EXAScaler configuration file.
"""

from modules.lustreConfig.section import EsConfigSection


class GlobalSection(EsConfigSection):
    """ Global section of EXAScaler configuration file.
    """

    def __init__(self, config, shadow_config=None):
        """ Basic initialization.
        """

        self.s2a_user = 'admin'
        self.s2a_pass = 'password'
        self.email_domain = None
        self.email_relay = None
        self.log_dir = '/scratch/log'
        self.mdt_backup = 'none'
        self.mdt_backup_dir = '/scratch'
        self.kdump_path = '/scratch/crash'

        self.fs_list = list()
        self.used_backfs_types = set()
        self.extra_hosts_start = list()
        self.extra_hosts_end = list()
        self.s2a_list = list()
        self.sfa_list = list()
        self.vg_activation_list = ['auto', ]
        self.clients_list = list()
        self.email_list = list()
        self.ntp_list = list()
        self.timezone = None

        # Undocumented option which allows to change pacemaker behavior in case of multiple lnets.
        # Special for DDN-659.
        # Should be reworked and improved in ES 5.0 to support all Multi-Rail cases.
        self.lnet_mr_fault_sensitive = False
        self.pingd = True
        self.hsm_active = False
        self.shadow_conf = False

        self.host_list = list()
        self.set_param_tunings = None
        self.conf_param_tunings = None
        self.mgs_fs = None

        self.cluster_name = None

        # For DDN-1370, adding password policy
        self.password_policy = 'plain-text'

        super(GlobalSection, self).__init__(config, 'global', shadow_config)

    def to_dict(self):
        """ Convert to dictionary.
        """

        fields = ('s2a_user', 's2a_pass', 'email_domain', 'email_relay', 'log_dir', 'mdt_backup', 'kdump_path',
                  'fs_list', 'extra_hosts_start', 'extra_hosts_end', 's2a_list', 'sfa_list',
                  'vg_activation_list', 'clients_list', 'email_list', 'pingd', 'hsm_active', 'shadow_conf',
                  'host_list', 'mgs_fs', 'ntp_list', 'cluster_name', 'mdt_backup_dir', 'timezone',
                  'lnet_mr_fault_sensitive', 'password_policy', )
        result = {field: getattr(self, field) for field in fields}
        result['set_param_tunings'] = None if self.set_param_tunings is None else self.set_param_tunings.to_dict()
        result['conf_param_tunings'] = None if self.conf_param_tunings is None else self.conf_param_tunings.to_dict()
        return result

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._mandatory_fields = ['fs_list', ]

        self._str_fields = ['s2a_user', 's2a_pass', 'email_domain', 'email_relay', 'log_dir',
                            'mdt_backup', 'mdt_backup_dir', 'kdump_path', 'cluster_name', 'timezone', 'password_policy', ]

        self._space_separated_list_fields = ['fs_list', 's2a_list', 'sfa_list', 'vg_activation_list', 'ntp_list', ]

        self._bool_fields = ['pingd', 'hsm_active', 'shadow_conf', 'lnet_mr_fault_sensitive']

        self._list_of_nodes_fields = ['extra_hosts_start', 'extra_hosts_end', 'clients_list', ]

        self._comma_separated_list_fields = ['email_list', ]

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = ('fs_list', 's2a_user', 's2a_pass', 'email_domain', 'email_relay', 'email_list', 'log_dir',
                    'mdt_backup', 'mdt_backup_dir', 'kdump_path', 's2a_list', 'sfa_list', 'vg_activation_list',
                    'clients_list', 'pingd', 'hsm_active', 'shadow_conf', 'extra_hosts_start', 'extra_hosts_end',
                    'ntp_list', 'cluster_name', 'timezone', 'lnet_mr_fault_sensitive', 'password_policy')

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

        self.host_list.extend(self.extra_hosts_start)

    def finalize_host_list(self):
        """ Add any extra hosts to the end of the host list
        run this after the host list has been populated, adds extras to the end.
        """

        for element in self.extra_hosts_end:
            if element not in self.host_list:
                self.host_list.append(element)

    def add_hosts_to_host_list(self, host_list):
        """ Add hosts to host_list.
        :param host_list: list of  hosts
        """

        for element in host_list:
            if element not in self.host_list:
                self.host_list.append(element)
