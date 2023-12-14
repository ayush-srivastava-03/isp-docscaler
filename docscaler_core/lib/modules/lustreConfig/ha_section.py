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

""" HA section of EXAScaler configuration file.
"""

from itertools import chain

from modules.lustreConfig.section import EsConfigSection
from modules.lustreConfig.utils import parse_nodespec, split_list_settings

class HASection(EsConfigSection):
    """ HA section of EXAScaler configuration file.
    """

    def __init__(self, config, shadow_config=None):
        """ Basic initialization.
        """

        self.corosync_nics = list()

        self.no_quorum_policy = 'freeze'
        self.type = 'corosync'
        self.transport = 'multicast'
        self.failover_policy = 'standard'
        self.rrp_mode = 'passive'
        self.crypto_hash = 'sha1'
        self.crypto_cipher = 'aes256'
        self.secauth = 'on'
        self.netmtu = 1500
        self.window_size = 50
        self.max_messages = 17

        self.mcastport = 5405
        self.ha_group_count = None

        self.dampen_ping = 20
        self.dampen_ifspeed = 20

        self.stonith_timeout = 300
        self.stonith_action_sfa_vm = 'reboot'
        
        self.zpool_monitor_timeout = 60
        self.lustre_start_timeout = 450

        self.start_on_boot = True

        # Calculated
        self.ha_groups = list()

        super(HASection, self).__init__(config, 'HA', shadow_config)

    def to_dict(self):
        """ Convert to dictionary.
        """

        fields = ('corosync_nics', 'no_quorum_policy', 'type', 'transport', 'failover_policy', 'rrp_mode',
                  'mcastport', 'ha_group_count', 'start_on_boot', 'ha_groups', 'dampen_ping', 'dampen_ifspeed',
                  'crypto_hash', 'crypto_cipher', 'secauth', 'netmtu', 'window_size', 'max_messages', 'stonith_timeout',
                  'zpool_monitor_timeout', 'lustre_start_timeout', 'stonith_action_sfa_vm')

        result = {field: getattr(self, field) for field in fields}

        return result

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._str_fields = ['no_quorum_policy', 'type', 'transport', 'failover_policy', 'rrp_mode', 'crypto_hash',
                            'crypto_cipher', 'secauth', 'stonith_action_sfa_vm', ]
        self._space_separated_list_fields = ['corosync_nics', ]
        self._int_fields = ['mcastport', 'ha_group_count', 'dampen_ping', 'dampen_ifspeed', 'netmtu', 'window_size',
                            'max_messages', 'stonith_timeout', 'zpool_monitor_timeout', 'lustre_start_timeout']
        self._bool_fields = ['start_on_boot', ]

    def _parse_ha_groups(self):
        """ Parse mentioned ha groups with appropriate indexes.
        """

        if self.ha_group_count is not None:
            for ha_group_idx in range(self.ha_group_count):
                ha_group_param = 'ha_group{0}'.format(ha_group_idx)
                if ha_group_param in self.unknown_settings:
                    value = self.unknown_settings[ha_group_param]
                    del self.unknown_settings[ha_group_param]
                    parsed_value = parse_nodespec(split_list_settings(value, ' '))
                    self.ha_groups.append(parsed_value)

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = chain(self._str_fields, self._space_separated_list_fields, self._int_fields, self._bool_fields,
                         self._list_of_nodes_fields, )
        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

        self._parse_ha_groups()
