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


"""
[zpool mgt]
dataset: mgt
vdevs: raidz2 enc440c-port0000 enc440c-port0001 enc440c-port0002 enc440c-port0003 cache enc440c-port0004 enc440c-port0005
opts: -o cachefile=none -O canmount=off -o multihost=on
vdev_base_path: /dev/disk/by-vdev/
"""


class ZpoolSection(EsConfigSection):
    """ Pool section of EXAScaler configuration file.
    """

    def __init__(self, config, zpool_name, shadow_config=None):
        """ Basic initialization.
        """

        self.name = zpool_name
        self.vdevs = None
        self.opts = '-o cachefile=none -O canmount=off -o multihost=on'
        self.vdev_base_path = '/dev/disk/by-vdev/'
        self.dataset = None
        self.idx = None
        self.type = None

        super(ZpoolSection, self).__init__(config, 'zpool {0}'.format(zpool_name), shadow_config)

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._mandatory_fields = ['vdevs', ]
        self._str_fields = ['opts', 'vdev_base_path', ]
        self._list_of_nodes_fields = ['vdevs', ]

    def _check_settings(self):
        """ Verify obtained settings.
        """

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = ('vdevs', 'opts', 'vdev_base_path')

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

    def to_dict(self):
        """ Convert to dictionary.
        """

        return dict(name=self.name, vdevs=self.vdevs, opts=self.opts, vdev_base_path=self.vdev_base_path)
