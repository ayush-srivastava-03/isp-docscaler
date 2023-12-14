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

""" HSM section of EXAScaler configuration file.
"""

from modules.lustreConfig.section import EsConfigSection

DB_HOST_NAMES = 'db_host_names'
REDIS_VIP = 'redis_vip'
DB_VIP = 'db_vip'
REPLICATION_USER_NAME = 'replication_user'
REPLICATION_USER_PASSWD = 'replication_passwd'
LUSTRE_MOUNT_DEVICE = 'lustre_mount_device'
LUSTRE_MOUNT_DIR = 'lustre_mount_directory'
WOS_ADDRESS = 'wos_address'
WOS_LISTEN_ADRESS = 'wos_listen_address'
BROKER_COUNT = 'broker_count'


class HSMSection(EsConfigSection):
    """ HSM section of EXAScaler configuration file.
    """

    def __init__(self, config, shadow_config=None):
        """ Basic initialization.
        """

        self.db_host_names = list()
        self.redis_vip = None
        self.db_vip = None
        self.lustre_mount_device = None
        self.lustre_mount_directory = None
        self.wos_address = None
        self.wos_listen_address = None
        self.broker_count = None
        self.replication_user = None
        self.replication_user_passwd = None

        super(HSMSection, self).__init__(config, 'HSM', shadow_config)

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._int_fields = [BROKER_COUNT]
        self._str_fields = [REDIS_VIP, DB_VIP, LUSTRE_MOUNT_DEVICE, LUSTRE_MOUNT_DIR, WOS_ADDRESS, WOS_LISTEN_ADRESS,
                            REPLICATION_USER_NAME, REPLICATION_USER_PASSWD]

        self._space_separated_list_fields = [DB_HOST_NAMES]

        self._mandatory_fields = [REDIS_VIP, DB_VIP, LUSTRE_MOUNT_DEVICE, LUSTRE_MOUNT_DIR, WOS_ADDRESS,
                                  WOS_LISTEN_ADRESS, DB_HOST_NAMES, BROKER_COUNT,
                                  REPLICATION_USER_NAME, REPLICATION_USER_PASSWD]

    def _check_settings(self):
        """ Verify obtained settings.
        """

        pass

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        self.db_host_names = self._untuned_settings[DB_HOST_NAMES]
        self.redis_vip = self._untuned_settings[REDIS_VIP]
        self.db_vip = self._untuned_settings[DB_VIP]
        self.lustre_mount_device = self._untuned_settings[LUSTRE_MOUNT_DEVICE]
        self.lustre_mount_directory = self._untuned_settings[LUSTRE_MOUNT_DIR]
        self.wos_address = self._untuned_settings[WOS_ADDRESS]
        self.wos_listen_address = self._untuned_settings[WOS_LISTEN_ADRESS]
        self.broker_count = self._untuned_settings[BROKER_COUNT]
        self.replication_user = self._untuned_settings[REPLICATION_USER_NAME]
        self.replication_passwd = self._untuned_settings[REPLICATION_USER_PASSWD]

    def to_dict(self):
        """ Convert to dictionary.
        """

        return dict(db_hosts=self.db_host_names, redis_vip=self.redis_vip, db_vip=self.db_vip,
                    lustre_mount_device=self.lustre_mount_device, lustre_mount_directory=self.lustre_mount_directory,
                    wos_address=self.wos_address, wos_listen_addres=self.wos_listen_address,
                    replication_user=self.replication_user_name, replication_passwd=self.replication_user_passwd)