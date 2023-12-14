# ******************************************************************************
#
#                                --- WARNING ---
#
#   This work contains trade secrets of DataDirect Networks, Inc.  Any
#   unauthorized use or disclosure of the work, or any part thereof, is
#   strictly prohibited.  Copyright in this work is the property of DataDirect.
#   Networks, Inc. All Rights Reserved. In the event of publication, the.
#   following notice shall apply: (C) 2020, DataDirect Networks, Inc.
#
# ******************************************************************************

""" EMF section of EXAScaler configuration file.
"""

from itertools import chain

from modules.lustreConfig.section import EsConfigSection

MGS_MIN_FREE_SIZE_GB = 80.0


class EmfSection(EsConfigSection):
    """User Inteface section of EXAScaler configuration file."""

    def __init__(self, config, shadow_config=None):
        """Basic initialization."""

        self.enabled = False
        self.ip = None
        self.nic = None
        self.cidr = None
        self.size = "80G"

        super(EmfSection, self).__init__(config, "EMF", shadow_config)

    def to_dict(self):
        """Convert to dictionary."""

        fields = ("enabled", "ip", "nic", "cidr", "size")

        result = {field: getattr(self, field) for field in fields}

        return result

    def _configure_section(self):
        """Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._str_fields = ["ip", "nic", "size"]
        self._int_fields = ["cidr"]
        self._bool_fields = ["enabled"]
        self._mandatory_fields = ["enabled"]

    def _perform_custom_tunings(self):
        """Perform custom tunings for obtained settings."""
        settings = chain(
            self._str_fields,
            self._int_fields,
            self._bool_fields,
        )

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])
