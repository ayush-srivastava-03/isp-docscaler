# ******************************************************************************
#
#                                --- WARNING ---
#
#   This work contains trade secrets of DataDirect Networks, Inc.  Any
#   unauthorized use or disclosure of the work, or any part thereof, is
#   strictly prohibited.  Copyright in this work is the property of DataDirect.
#   Networks, Inc. All Rights Reserved. In the event of publication, the.
#   following notice shall apply: (C) 2017, DataDirect Networks, Inc.
#
# ******************************************************************************

""" REST API section of EXAScaler configuration file.
"""

from modules.lustreConfig.section import EsConfigSection


class RestSection(EsConfigSection):
    """ SFA section of EXAScaler configuration file.
    """

    def __init__(self, config, shadow_config=None):
        """ Basic initialization.
        """

        self.master_nodes = None
        self.ext_vip = None
        self.ext_mask = None
        self.int_vip = None
        self.int_mask = None
        self.ka_vr_id = None
        self.ext_vip_fqdn = None
        self.auth_ou = None

        super(RestSection, self).__init__(config, 'rest', shadow_config)

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._space_separated_list_fields = ['master_nodes', ]
        self._str_fields = ['ext_vip', 'ext_mask', 'int_vip', 'int_mask', 'ka_vr_id', 'ext_vip_fqdn', 'auth_ou', ]
        self._mandatory_fields = ['master_nodes', 'ext_vip', 'ext_mask', 'int_vip', 'int_mask', 'ka_vr_id', ]

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = ('master_nodes', 'ext_vip', 'ext_mask', 'int_vip', 'int_mask', 'ka_vr_id',
                    'ext_vip_fqdn', 'auth_ou', )

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

    def to_dict(self):
        """ Convert to dictionary.
        """

        return dict(master_nodes=self.master_nodes,
                    ext_vip=self.ext_vip,
                    ext_mask=self.ext_mask,
                    int_vip=self.int_vip,
                    int_mask=self.int_mask,
                    ka_vr_id=self.ka_vr_id,
                    ext_vip_fqdn=self.ext_vip_fqdn,
                    auth_ou=self.auth_ou)
