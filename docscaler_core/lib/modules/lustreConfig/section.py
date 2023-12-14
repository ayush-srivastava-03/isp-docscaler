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

""" Section representation in EXAScaler configuration file.
"""

import abc
from collections import OrderedDict

from modules.lustreConfig.utils import split_list_settings, parse_nodespec, split_list_settings_regex

class EsConfigSection(object):
    """ Section representation in EXAScaler configuration file.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, config, section_name, shadow_config=None):
        """ Basic initialization.
        """

        self._config = config
        self._section_name = section_name
        self._shadow_config = shadow_config

        self._mandatory_fields = list()
        self._comma_separated_list_fields = list()
        self._regex_separated_list_fields = list()
        self._space_separated_list_fields = list()
        self._str_fields = list()
        self._bool_fields = list()
        self._int_fields = list()
        self._list_of_nodes_fields = list()

        self._untuned_settings = OrderedDict()
        self.unknown_settings = OrderedDict()

        self._configure_section()
        self._load_from_config()

    @abc.abstractmethod
    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory, comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

    def _load_from_config(self):
        """ Load section from EXAScaler configuration file.
        """

        self._load_settings_from_config()

        self._load_unknown_settings_from_config()

        self._perform_custom_tunings()

        #self._check_mandatory_fields_present()

        #self._check_settings()

    def _load_settings_from_config(self):
        """ Load settings from configuration file.
        """
        for int_setting in self._int_fields:
            if self._config.has_option(self._section_name, int_setting):
                self._untuned_settings[int_setting] = self._config.getint(self._section_name, int_setting)
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, int_setting):
                    self._untuned_settings[int_setting] = self._shadow_config.getint(
                        self._section_name, int_setting)

        for bool_setting in self._bool_fields:
            if self._config.has_option(self._section_name, bool_setting):
                self._untuned_settings[bool_setting] = self._config.getboolean(self._section_name, bool_setting)
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, bool_setting):
                    self._untuned_settings[bool_setting] = self._shadow_config.getboolean(
                        self._section_name, bool_setting)

        for str_setting in self._str_fields:
            if self._config.has_option(self._section_name, str_setting):
                self._untuned_settings[str_setting] = self._config.get(self._section_name, str_setting)
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, str_setting):
                    self._untuned_settings[str_setting] = self._shadow_config.get(self._section_name, str_setting)

        for comma_separated_list_setting in self._comma_separated_list_fields:
            if self._config.has_option(self._section_name, comma_separated_list_setting):
                self._untuned_settings[comma_separated_list_setting] = split_list_settings(
                    self._config.get(self._section_name, comma_separated_list_setting), ',')
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, comma_separated_list_setting):
                    self._untuned_settings[comma_separated_list_setting] = split_list_settings(
                        self._shadow_config.get(self._section_name, comma_separated_list_setting), ',')

        for regex_separated_list_setting in self._regex_separated_list_fields:
            if regex_separated_list_setting == 'tune_ost_mke2fs_opts':
                pattern = "(?:,)(?=\s*for)"
            if self._config.has_option(self._section_name, regex_separated_list_setting):
                self._untuned_settings[regex_separated_list_setting] = split_list_settings_regex(
                    self._config.get(self._section_name, regex_separated_list_setting), pattern)
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, regex_separated_list_setting):
                    self._untuned_settings[regex_separated_list_setting] = split_list_settings_regex(
                        self._shadow_config.get(self._section_name, regex_separated_list_setting), pattern)

        for space_separated_list_setting in self._space_separated_list_fields:
            if self._config.has_option(self._section_name, space_separated_list_setting):
                self._untuned_settings[space_separated_list_setting] = split_list_settings(
                    self._config.get(self._section_name, space_separated_list_setting), ' ')
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, space_separated_list_setting):
                    self._untuned_settings[space_separated_list_setting] = split_list_settings(
                        self._shadow_config.get(self._section_name, space_separated_list_setting), ' ')

        for nodes_list_setting in self._list_of_nodes_fields:
            if self._config.has_option(self._section_name, nodes_list_setting):
                self._untuned_settings[nodes_list_setting] = parse_nodespec(split_list_settings(
                    self._config.get(self._section_name, nodes_list_setting), ' '))
            if self._shadow_config is not None:
                if self._shadow_config.has_option(self._section_name, nodes_list_setting):
                    self._untuned_settings[nodes_list_setting] = parse_nodespec(split_list_settings(
                        self._shadow_config.get(self._section_name, nodes_list_setting), ' '))

    def _load_unknown_settings_from_config(self):
        """ Load unknown settings from configuration file.
        """

        known_settings = self._int_fields + self._str_fields + self._bool_fields + self._comma_separated_list_fields + \
                         self._space_separated_list_fields + self._list_of_nodes_fields + self._regex_separated_list_fields

        self.unknown_settings = OrderedDict((s, self._config.get(self._section_name, s)) for s in self._config.options(
            self._section_name) if s not in known_settings)

        if self._shadow_config is not None and self._shadow_config.has_section(self._section_name):
            settings = OrderedDict((s, self._shadow_config.get(self._section_name, s)) for s in \
                                   self._shadow_config.options(self._section_name) if s not in known_settings)
            self.unknown_settings.update(settings)

    @abc.abstractmethod
    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

    @abc.abstractmethod
    def _check_settings(self):
        """ Check if obtained settings meet all necessary conditions.
        """
