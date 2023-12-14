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

""" Pool section of EXAScaler configuration file.
"""

from modules.lustreConfig.section import EsConfigSection


class PoolSection(EsConfigSection):
    """ Pool section of EXAScaler configuration file.
    """

    def __init__(self, config, pool_name, shadow_config=None):
        """ Basic initialization.
        """

        self.ost_list = list()
        self.name = pool_name

        super(PoolSection, self).__init__(config, 'pool {0}'.format(pool_name), shadow_config)

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._list_of_nodes_fields = ['ost_list', ]
        self._mandatory_fields = ['ost_list', ]

    def _check_settings(self):
        """ Verify obtained settings.
        """

        pass

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        self.ost_list = self._untuned_settings['ost_list']

    def to_dict(self):
        """ Convert to dictionary.
        """

        return dict(name=self.name, ost_list=self.ost_list)
