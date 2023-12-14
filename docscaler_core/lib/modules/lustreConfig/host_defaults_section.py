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

""" Host defaults section of EXAScaler configuration file.
"""

import copy, struct, socket

from modules.lustreConfig.section import EsConfigSection


class HostDefaultsSection(EsConfigSection):
    """ Host defaults section of EXAScaler configuration file.
    """

    class Nic(object):
        """ Nic settings.
        """

        def __init__(self, name):
            """ Basic initialization
            """

            self.name = name

            self.cfg = None
            self.device = None
            self.slaves = None
            self.netmask = None
            self.gateway = None

        def get_from_config_settings(self, settings):
            """ Obtain settings from configuration file.
            :param settings: Dictionary with settings from configuration file.
            """

            if self.name == 'ipmi':
                keys = ('netmask', 'gateway',)
            else:
                self.device = self.name
                keys = ('cfg', 'device', 'slaves', 'netmask', 'gateway',)

            for key in keys:
                setting = '{0}_{1}'.format(self.name, key)
                if setting in settings:
                    setattr(self, key, settings[setting])
                    del settings[setting]

            if self.cfg is not None:
                self.cfg = self.cfg.strip()

        def to_dict(self):
            """ Convert to dictionary.
            """

            keys = ('cfg', 'device', 'slaves', 'netmask', 'gateway',)

            return {key: getattr(self, key) for key in keys if getattr(self, key) is not None}

    def __init__(self, config, shadow_config=None):
        """ Basic initialization.
        """

        self.nic_list = list()
        self.lnets = list()

        self.stonith_pass = None
        self.stonith_user = None
        self.stonith_type = None
        self.ipmi_delay = None
        self.ipmi_method = None
        self.ipmi_monitor = None
        self.ipmi_power_wait = 5

        self.bonding_mode = None
        self.modprobe_cfg = None
        self.serial_speed = '115200'
        self.serial_port = 'ttyS0'
        self.ring0 = None
        self.ring1 = None

        self.rest_ext_nic = None
        self.rest_int_nic = None
        self.rest_primary_nic = None
        self.rest_keepalived_nic = None

        self.rest_cert_ca = None
        self.rest_cert_crl = None
        self.rest_cert_server = None
        self.rest_cert_server_key = None

        self.nics = dict()
        self.base_ip = dict()

        self.host_sfa_list = list()
        self.grub_args = None

        super(HostDefaultsSection, self).__init__(config, 'host_defaults', shadow_config)

    def to_dict(self):
        """ Convert to dictionary.
        """

        fields = ('nic_list', 'lnets', 'stonith_pass', 'stonith_user', 'stonith_type', 'bonding_mode', 'modprobe_cfg',
                  'serial_speed', 'serial_port', 'base_ip', 'ring0', 'ring1', 'host_sfa_list', 'grub_args',
                  'ipmi_delay', 'ipmi_method', 'ipmi_monitor', 'ipmi_power_wait',
                  'rest_ext_nic', 'rest_int_nic', 'rest_primary_nic', 'rest_keepalived_nic',
                  'rest_cert_ca', 'rest_cert_crl', 'rest_cert_server', 'rest_cert_server_key', )

        result = {field: getattr(self, field) for field in fields}
        result['nics'] = {key: value.to_dict() for key, value in self.nics.items()}
        return result

    def _configure_section(self):
        """ Divide settings according their types.
        Set mandatory,comma separated list, space separated list, str, bool,
        int, list of nodes fields if it is necessary.
        """

        self._str_fields = ['stonith_pass', 'stonith_user', 'stonith_type', 'bonding_mode', 'modprobe_cfg',
                            'serial_speed', 'serial_port', 'ring0', 'ring1', 'ipmi_method', 'grub_args',
                            'rest_ext_nic', 'rest_int_nic', 'rest_primary_nic', 'rest_keepalived_nic',
                            'rest_cert_ca', 'rest_cert_crl', 'rest_cert_server', 'rest_cert_server_key',]
        self._space_separated_list_fields = ['nic_list', 'lnets', 'host_sfa_list', ]
        self._int_fields = ['ipmi_delay', 'ipmi_monitor', 'ipmi_power_wait', ]

    def is_ipmi_required(self):
        """ If stonith settings require IPMI.
        """

        return self.stonith_type in ('ipmi', 'ipmi-slow',)

    def _set_stonith_defaults(self):
        """ Set stonith default settings if it is necessary.
        """

        if self.is_ipmi_required():
            if self.stonith_user is None:
                self.stonith_user = 'root'
            if self.stonith_pass is None:
                self.stonith_pass = 'calvin'
            if self.ipmi_delay is None:
                self.ipmi_delay = 15
            if self.ipmi_monitor is None:
                self.ipmi_monitor = 60
            if self.ipmi_method is None:
                self.ipmi_method = "onoff"

        elif self.stonith_type == 'ilo':
            if self.stonith_user is None:
                self.stonith_user = 'Administrator'
            if self.stonith_pass is None:
                self.stonith_pass = 'datadirect'

        elif self.stonith_type == 'sfa_vm':
            if self.stonith_user is None:
                self.stonith_user = 'user'
            if self.stonith_pass is None:
                self.stonith_pass = 'user'

    def _parse_nics(self):
        """ Parse network settings.
        """

        nic_list = list()
        if self.nic_list is not None:
            nic_list = self.nic_list[:]
        if self.is_ipmi_required():
            nic_list.append('ipmi')

        for name in nic_list:

            nic = self.Nic(name)
            nic.get_from_config_settings(self.unknown_settings)
            self.nics[name] = nic

            base_ip_setting = '{0}_ip_base'.format(name)
            if base_ip_setting in self.unknown_settings:
                base_ip = self.unknown_settings[base_ip_setting]
                self.base_ip[name] = [int(part) for part in base_ip.split('.')]
                del self.unknown_settings[base_ip_setting]

    def _perform_custom_tunings(self):
        """ Perform custom tunings for obtained settings.
        """

        settings = ('stonith_pass', 'stonith_user', 'stonith_type', 'bonding_mode', 'modprobe_cfg',
                    'serial_speed', 'serial_port', 'nic_list', 'lnets', 'ring0', 'ring1', 'host_sfa_list',
                    'ipmi_delay', 'ipmi_method', 'ipmi_monitor', 'ipmi_power_wait', 'grub_args',
                    'rest_ext_nic', 'rest_int_nic', 'rest_primary_nic', 'rest_keepalived_nic',
                    'rest_cert_ca', 'rest_cert_crl', 'rest_cert_server', 'rest_cert_server_key',)

        for setting in settings:
            if setting in self._untuned_settings:
                setattr(self, setting, self._untuned_settings[setting])

        self._parse_nics()
        # self._set_stonith_defaults()
        # self._check_lnets()

    def get_next_ip(self, nic_name):
        """ Generate next ip address.
        """

        ip = self.base_ip[nic_name]
        netmask = self.nics[nic_name].netmask
        prefix = sum(bin(int(x)).count('1') for x in netmask.split('.'))
        ip_result = '.'.join([str(part) for part in ip])
        host_bits = 32 - prefix
        i = struct.unpack('>I', socket.inet_aton(ip_result))[0]
        start = ((i >> host_bits) << host_bits)
        end = start | (1 << host_bits)-1
        ip_list = range(start,end+1)
        get_index = ip_list.index(i)
        if  i < ip_list[-1]:
            get_index+=1
            self.base_ip[nic_name] = copy.deepcopy([int(n) for n in socket.inet_ntoa
            (struct.pack('>I',ip_list[get_index])).split('.')])
            return ip_result
