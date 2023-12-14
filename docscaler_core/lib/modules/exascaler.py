'''
Created on 09 May 2023

@author: mwolf

This module is for parsing the exascaler config file.
".conf" if ES5.x and ".toml" if ES6.x

'''

import re
import json

from modules.lustreConfig import EXAScalerConfig
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE, STDOUT
from collections import defaultdict
from config import ConfigDict
from functools import reduce
from ClusterShell.NodeSet import NodeSet

def es_config_loader(config: ConfigDict):
    
    print("\n    Loading and checking exascaler config")
    
    try:
        return exascaler_toml_parser(config)
    except TOMLParseError as e:
            print("\n{}".format(e))
            print("\nPlease check your exascaler.toml file and the error message above. Aborting.")
            exit(0)
    except NoTOMLFileError:
        try:
            return exascaler_conf_parser(config)
        except:
            pass
    
    pass

class TOMLParseError(Exception):
    pass

class NoTOMLFileError(Exception):
    pass

class es_config_interface:
    _exaconfig = {}
    _config_data = {}
    
    _ES5X = 0
    _ES6X = 1
    
    def __init__(self, config: ConfigDict):
        self._config_data = config
        self._loadExaScalerConf()

          
    def _sortNodes(self, s):
        subbed = re.sub('[\[\]]', '', s).lower()
        return any(c in '!@#$%^&*' for c in s), subbed  
    
    def _compareConf(self, foi):  
        '''Compares all exascaler.conf files for a filesystem to be equal
        
           Returns
           -------
           list 
                the list contains tuples with [0] the exascaler.conf and [1] a list of nodes that have the same 
                config file
        '''
        compare = defaultdict(list)
        for node in self.getNodes():
            compare[self._config_data[node][foi]].append(node)
            
        return compare
            
    def _equalConf(self, foi):
        '''Checks if config file entries are equal
        
           Returns
           -------
           value
                the value of the config if all are equal
           list 
                the list contains tuples with [0] the config and [1] a list of nodes that have the same 
                config file
        '''
        compare = self._compareConf(foi)
        
        if len(compare) == 1:
            return list(compare.keys())[0]
        else:
            return compare

        return compare
    
    def getNodes(self):
        return sorted([node for node in self._config_data], key=self._sortNodes)
    
    def getRawExaScalerConf(self):
        esconf = self._equalConf("exascaler.conf.raw")
        if isinstance(esconf, str):
            return esconf
        else:
            print("The exascaler.conf file differs between the nodes! Check if they were synced properly.")
            return esconf
        
    def _loadExaScalerConf(self):
        esconf = self.getRawExaScalerConf()
        
        temp = NamedTemporaryFile()  
        temp.write(esconf.encode('ascii'))
        temp.flush()
        
        self._load_conf(temp.name)

        temp.close()

    def _load_conf(self, path: str):
        pass
    
    def getExaScalerType(self):
        pass
    
    def getExaScalerVersion(self):
        pass
    
    def getExaScalerVersionNum(self):
        return re.findall(r"(\d+\.?\d?\.?\d?-\w+)", self.getExaScalerVersion())[0]

    def getLustreVersion(self):
        compare = defaultdict(list)
        
        for node in self.getNodes():
            rpms = self._config_data[node]["rpm_qa.txt"]
            lustre_version = re.search(r"lustre-\d.+ddn.+(?=\.)", rpms, re.MULTILINE)
            compare[lustre_version.group().strip()].append(node)
            
        if len(compare) == 1:
            return list(compare.keys())[0]
        else:
            print("Various Lustre versions found! Check all nodes for the same version.")
            return list(compare.keys())[0]
    
    def getModuleSettings(self):
        pass
    
    def getModuleSetting(self, node):
        pass
    
    def getFilesystemNames(self):
        return self._exaconfig["global_settings"]["fs_list"]
    
    def getLustreSettings(self):
        settings = self._exaconfig["global_settings"]["set_param_tunings"]
        settings = reduce(lambda x,y: x + y, [i + ': ' + settings[i]+'\n' for i in settings])[:-1]
        return settings
    
    def getTimezone(self):
        return self._exaconfig["global_settings"]["timezone"]
    
    def getNTPServers(self):
        return ",".join(self._exaconfig["global_settings"]["ntp_list"])
    
    def getMDSServerList(self, filesystem, folded = False):
        if folded:
            return NodeSet(",".join(self._exaconfig["fs_settings"][filesystem]["mds_list"]))
        else:
            return self._exaconfig["fs_settings"][filesystem]["mds_list"]
    
    def getOSSServerList(self, filesystem, folded = False):
        if folded:
            return NodeSet(",".join(self._exaconfig["fs_settings"][filesystem]["oss_list"]))
        else:
            return self._exaconfig["fs_settings"][filesystem]["oss_list"]
    
    def getMDTCount(self, filesystem):
        mdtCount = self._exaconfig["fs_settings"][filesystem]["mdt_list"]
        mdtCount = sum([len(v) for v in mdtCount.values()])
        
        return mdtCount
    
    def getOSSCount(self, filesystem):
        ostCount = self._exaconfig["fs_settings"][filesystem]["ost_list"]
        ostCount = sum([len(v) for v in ostCount.values()])
        
        return ostCount 
    
    def getLustreNodes(self):
        return self._exaconfig["hosts_settings"]
    
    def getInterfaceList(self):
        return self._exaconfig["host_defaults_settings"]["nics"]
    
    def getInterfaceConfig(self, host):        
        pass
        
    def convertNetmask(self, netmask):
        return sum(bin(int(x)).count('1') for x in netmask.split('.'))
    
#Used for ES5.x
class exascaler_conf_parser(es_config_interface):
    # def __init__(self, config: ConfigDict):
    #     super().__init__(config)
    
    def _load_conf(self, path):        
        self._exaconfig = EXAScalerConfig(path).to_dict()
    
    def getExaScalerType(self):
        return self._ES5X
    
    def getExaScalerVersion(self):
        version = self._equalConf("EXAScaler_release.es_install_version")
        
        if isinstance(version, str):
            return version
        else:
            version_num = None
            for v in version:
                ver = v.split(" ")
                if version_num == None:
                    version_num = ver[len(ver)-1]
                else:
                    if version_num == ver[len(ver)-1]:
                        continue
                    else:
                        print("Various ExaScaler versions found! Check all nodes for the same version.")
                        return version
            
            return version_num

    def getModuleSettings(self):
        module = self._equalConf("etc.modprobe.d.lustre.conf")
        
        if isinstance(module, str):
            return module
        else:
            print("Various modprobe.d settings found! Check all nodes for the same settings.")
            return module
        
    def getModuleSetting(self, node):
        return self._config_data[node]["etc.modprobe.d.lustre.conf"]
    
    def getInterfaceConfig(self, host):        
        header = []
        listData = ""
        
        #for host in hosts:
        if "[" in host and "]" in host:
            nodes = NodeSet(host)
            
            header.append("Node")
            #create header
            for node in nodes:
                for nic in self._exaconfig["hosts_settings"][node]["nics"]:
                    nic = ConfigDict(self._exaconfig["hosts_settings"][node]["nics"][nic])
                    if nic.device not in header:
                        header.append(nic.device)
                    
                        if "gateway" in nic:
                            header.append("Gateway")
            
            temp = "<tr>"
            for h in header:
                temp = temp + "<td>{}</td>".format(h)
                
            header = temp + "</tr>"
              
            #create listData
            for node in nodes:                
                listData = listData + "<tr><td>{}</td>".format(node)
                
                for nic in self._exaconfig["hosts_settings"][node]["nics"]:
                    nic = ConfigDict(self._exaconfig["hosts_settings"][node]["nics"][nic])
                    
                    listData = listData + "<td>{}</td>".format(nic.ip + "/" + str(self.convertNetmask(nic.netmask)))
                    
                    if "gateway" in nic:
                        listData = listData + "<td>{}</td>".format(nic.gateway)
            
                listData = listData + "</tr>"
                
            
            summary = "<table>" + header + listData + "</table>"
            return summary
                               
        else:
            gateway = [nic for nic in self._exaconfig["hosts_settings"][host]["nics"] if "gateway" in self._exaconfig["hosts_settings"][host]["nics"][nic]]
            bonded = [nic for nic in self._exaconfig["hosts_settings"][host]["nics"] if self._exaconfig["hosts_settings"][host]["nics"][nic]["is_bonded"]]
            cfg = [nic for nic in self._exaconfig["hosts_settings"][host]["nics"] if "cfg" in self._exaconfig["hosts_settings"][host]["nics"][nic]]

            header = "<tr><td>Interface</td><td>IP</td><td>Netmask</td>"
            
            if gateway:
                header = header + "<td>Gateway</td>"
                
            if bonded:
                header = header + "<td>Bonded</td>"
                
            if cfg:
                header = header + "<td>Config</td>"
            
            header = header + "</tr>"
            

            for nic in self._exaconfig["hosts_settings"][host]["nics"]:
                nic_str = nic
                nic = ConfigDict(self._exaconfig["hosts_settings"][host]["nics"][nic_str])
                if "ip" not in nic:
                    continue
                
                if "ipmi" in nic_str:
                    nic.update({"device": nic_str})
                
                listData = listData + "<tr><td>{}</td><td>{}</td><td>{}</td>".format(nic.device,
                                                                             nic.ip,
                                                                             nic.netmask)
            
                if "gateway" in nic:
                    listData = listData + "<td>{}</td>".format(nic.gateway)
                elif "gateway" not in nic and gateway:
                    listData = listData + "<td>--</td>"   
                    
                if nic.is_bonded:
                    listData = listData + "<td>{}</td>".format(",".join(nic.slaves.split(" ")))
                elif not nic.is_bonded and bonded:
                    listData = listData + "<td>--</td>"    
                    
                if "cfg" in nic:
                    listData = listData + "<td>{}</td>".format(nic.cfg)
                elif "cfg" not in nic and cfg == None:
                    listData = listData + "<td>--</td>"    
                    
                listData = listData + "</tr>"
                   
            summary = "<table>" + header + listData + "</table>"
            
            return summary
    
#Used for ES6.x
class exascaler_toml_parser(es_config_interface):
    
    def _load_conf(self, path):
        exatoml = Popen(["lib/es-config-show", '-c', path], stdout=PIPE, stderr=STDOUT, text=True)
        
        result = exatoml.communicate()

        if "ERROR" in result[0]:
            if not "TOML" in result[0]:
                raise TOMLParseError(result[0])
            else:
                raise NoTOMLFileError
        
        self._exaconfig = json.loads(result[0])
        
    def getExaScalerType(self):
        return self._ES6X
        
    def getExaScalerVersion(self):
        version = self._equalConf("es_install_version")
        
        if isinstance(version, str):
            return version
        else:
            version_num = None
            for v in version:
                ver = v.split(" ")
                if version_num == None:
                    version_num = ver[len(ver)-1]
                else:
                    if version_num == ver[len(ver)-1]:
                        continue
                    else:
                        print("Various ExaScaler versions found! Check all nodes for the same version.")
                        return version
            
            return version_num
        
    def getModuleSettings(self):
        module = self._equalConf("lustre.conf")
        
        if isinstance(module, str):
            return module
        else:
            print("Various modprobe.d settings found! Check all nodes for the same settings.")
            return module
        
    def getModuleSetting(self, node):
        return self._config_data[node]["lustre.conf"]
    
    def getInterfaceConfig(self, host):        
        header = []
        listData = ""
        
        #for host in hosts:
        if "[" in host and "]" in host:
            nodes = NodeSet(host)
            
            header.append("Node")
            #create header
            for node in nodes:
                for nic in self._exaconfig["hosts_settings"][node]["nics"]:
                    nic = ConfigDict(self._exaconfig["hosts_settings"][node]["nics"][nic])
                    if nic.device not in header:
                        header.append(nic.device)
                    
                        if "gateway" in nic:
                            header.append("Gateway")
            
            temp = "<tr>"
            for h in header:
                temp = temp + "<td>{}</td>".format(h)
                
            header = temp + "</tr>"
              
            #create listData
            for node in nodes:                
                listData = listData + "<tr><td>{}</td>".format(node)
                
                for nic in self._exaconfig["hosts_settings"][node]["nics"]:
                    nic = ConfigDict(self._exaconfig["hosts_settings"][node]["nics"][nic])
                    
                    listData = listData + "<td>{}</td>".format(nic.ip + "/" + str(self.convertNetmask(nic.netmask)))
                    
                    if "gateway" in nic:
                        listData = listData + "<td>{}</td>".format(nic.gateway)
            
                listData = listData + "</tr>"
                
            
            summary = "<table>" + header + listData + "</table>"
            return summary
                               
        else:
            gateway = [nic for nic in self._exaconfig["hosts_settings"][host]["nics"] if "gateway" in self._exaconfig["hosts_settings"][host]["nics"][nic]]
            bonded = [nic for nic in self._exaconfig["hosts_settings"][host]["nics"] if self._exaconfig["hosts_settings"][host]["nics"][nic]["bonding_mode"] != None]
            cfg = [nic for nic in self._exaconfig["hosts_settings"][host]["nics"] if "cfg" in self._exaconfig["hosts_settings"][host]["nics"][nic]]

            header = "<tr><td>Interface</td><td>IP</td><td>Netmask</td>"
            
            if gateway:
                header = header + "<td>Gateway</td>"
                
            if bonded:
                header = header + "<td>Bonded</td>"
                
            if cfg:
                header = header + "<td>Config</td>"
            
            header = header + "</tr>"
            

            for nic in self._exaconfig["hosts_settings"][host]["nics"]:
                nic_str = nic
                nic = ConfigDict(self._exaconfig["hosts_settings"][host]["nics"][nic_str])
                if "ip" not in nic:
                    continue
                
                if "ipmi" in nic_str:
                    nic.update({"device": nic_str})
                
                listData = listData + "<tr><td>{}</td><td>{}</td><td>{}</td>".format(nic.device,
                                                                             nic.ip,
                                                                             nic.netmask)
            
                if "gateway" in nic:
                    listData = listData + "<td>{}</td>".format(nic.gateway)
                elif "gateway" not in nic and gateway:
                    listData = listData + "<td>--</td>"   
                    
                if nic.bonding_mode:
                    listData = listData + "<td>{}</td>".format(",".join(nic.slaves.split(" ")))
                elif not nic.bonding_mode and bonded:
                    listData = listData + "<td>--</td>"
                    
                if nic.cfg:
                    nic_cfg = ""
                    for k, v in nic.cfg.items():
                        if len(nic.cfg[k].items()) > 0:
                            for key, value in nic.cfg[k].items():
                                nic_cfg += "{}={}\n".format(key,value)
                        else:
                            nic_cfg += "{}={}\n".format(k,v)
                    
                    listData = listData + "<td>{}</td>".format(nic_cfg.strip())
                elif not nic.cfg and cfg:
                    listData = listData + "<td>--</td>"    
                    
                listData = listData + "</tr>"
                   
            summary = "<table>" + header + listData + "</table>"
            
            return summary
    
