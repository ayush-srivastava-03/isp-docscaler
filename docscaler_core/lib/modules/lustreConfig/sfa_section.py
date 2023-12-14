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

""" SFA section of EXAScaler configuration file.
"""

from modules.lustreConfig.section import EsConfigSection


class SFASection(EsConfigSection):
    """ SFA section of EXAScaler configuration file.
    """

    def __init__(self, config, sfa_name, shadow_config=None):
        """ Basic initialization.
        """

        self.name = sfa_name
        self.controllers = list()
        self.user = 'user'
        self.password = 'user'

        super(SFASection, self).__init__(config, 'sfa {0}'.format(sfa_name), shadow_config)

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._str_fields = ['user', 'password', ]
        self._space_separated_list_fields = ['controllers', ]
        self._mandatory_fields = ['controllers', ]

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = ('controllers', 'user', 'password', )

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

        password_policy = 'plain-text'
        if self._config.has_option('global', 'password_policy'):
            password_policy = self._config.get('global', 'password_policy')

        if password_policy == 'encryption':
            self.password = 'xxxx'


    def to_dict(self):
        """ Convert to dictionary.
        """

        return dict(name=self.name, user=self.user, password=self.password, controllers=self.controllers)
