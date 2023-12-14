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

""" Extra section of EXAScaler configuration file.
"""

import configparser
from collections import OrderedDict

from modules.lustreConfig.section import EsConfigSection


class ExtraSection(EsConfigSection):
    """ Extra section of EXAScaler configuration file.
    """

    def __init__(self, config_file, section_name, default_settings=None, shadow_config=None):
        """ Basic initialization.
        """

        self._default_settings = default_settings

        self.settings = OrderedDict()

        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str
        config.read(config_file)

        super(ExtraSection, self).__init__(config, section_name, shadow_config)

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        pass

    def _check_settings(self):
        """ Verify obtained settings.
        """

        pass

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        if self._default_settings is not None:
            self.settings.update(self._default_settings)
        self.settings.update(self.unknown_settings)

    def to_dict(self):
        """ Convert to dictionary.
        """

        return self.settings
