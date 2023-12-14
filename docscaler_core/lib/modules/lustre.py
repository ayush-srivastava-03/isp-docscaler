'''
Created on 09 May 2019

@author: mwolf

This module is for parsing the output of esctl showall.
It currently excepts the tar file created by esctl.

'''
import os
import tarfile
import re
from tqdm import tqdm

from io import StringIO
from ClusterShell.NodeSet import NodeSet

from os.path import isfile
from pathlib import Path
import json

from config import ConfigDict
from modules.exascaler import es_config_loader

def sortNodes(s):
    subbed = re.sub('[\[\]]', '', s).lower()
    return any(c in '!@#$%^&*' for c in s), subbed

class parse_esctl():     
    #Files of interest
    __FOI = ["sysconfig_network.network", "lustre_log.txt", "etc.modprobe.d.lustre.conf", 
             "etc.ddn.exascaler.conf", "EXAScaler_release.es_install_version", "rpm_qa.txt",
             "hastatus.txt",
           #ES5.2
           "exascaler_conf.exascaler.conf"
           ]
    
    #ES6.2
    __FOI62 = ["lustre.conf", "es_install_version", "emf_ha", "exascaler.toml", "sh_-c_rpm_--nodigest_-qa"]
    
    __excludedNodes = []
    
    def __init__(self, es_showall, combine = None, ignore = True):
        try:
            if isfile(es_showall):
                __esctl_data = ConfigDict()
                self.__combine = combine
                
                if os.path.getsize(es_showall) > 500000000:
                    print("      NOTE: The filesize is > 500MB. Be patient!\n            A list of all files in the TAR will be generated now")
                
                if self.__combine:
                    nodes = re.findall(r"(.+?)(?:,|$)(?!\d)", self.__combine, re.MULTILINE)
                    self.__excludedNodes = [n for nodeSet in nodes for n in NodeSet(nodeSet)[1:]]
                
                with tarfile.open(es_showall, "r:*") as self.tar:
                    
                    #Check if showall or sos
                    sos = None

                    try:
                        sos = self.tar.extractfile(Path(Path(es_showall).stem).stem + "/sos_reports/manifest.json")
                    except Exception as e:
                        pass
                    
                    if sos:
                        manifest = json.loads(sos.read())
                        
                        for node in manifest["components"]["collect"]["nodes"]:
                            print("\n      {}:".format(manifest["components"]["collect"]["nodes"][node]["hostname"]))
                            print("            Extracting {} to scan the files".format(manifest["components"]["collect"]["nodes"][node]["collected_archive"]))
                            node_sos = self.tar.extractfile(Path(Path(es_showall).stem).stem + "/" + manifest["components"]["collect"]["nodes"][node]["collected_archive"])
                            
                            hostname = manifest["components"]["collect"]["nodes"][node]["hostname"]
                            if hostname not in __esctl_data:
                                __esctl_data[hostname] = {}
                                  
                            with tarfile.open(fileobj=node_sos, mode="r:*") as gz:
                                m = filter(self.__findFOI62, tqdm(gz.getmembers(), smoothing=0.5, desc="            Scanning files", unit=" files", ncols=110, delay=1)) #colour="#A71930"))    
                                for member in m:
                                    f = gz.extractfile(member)
                                    
                                    if f:
                                        content = f.read().decode("utf-8", "replace")
                                        foi = os.path.basename(member.name)
                                
                                    if foi == "exascaler.toml":
                                        foi = "exascaler.conf.raw"
                                        
                                    if "sh_-c_rpm_--nodigest_-qa" in foi:
                                        foi = "rpm_qa.txt"
                                
                                    __esctl_data[hostname][foi] = content.strip()
                    else:
                        #get all members in the tar file that match the FOIs
                        m = filter(self.__findFOI, tqdm(self.tar.getmembers(), smoothing=0.5, desc="      Scanning files", unit=" files", ncols=110, delay=3)) #colour="#A71930"))                 
                        
                        for member in m:
                            host = member.name.split("/")[2]
                            
                            if self.__combine:
                                nodes = re.findall(r"(.+?)(?:,|$)(?!\d)", self.__combine, re.MULTILINE)
                                for nodeSet in nodes:
                                    for n in NodeSet(nodeSet):
                                        if n == host:
                                            host = nodeSet
                                            break                
                            
                            if host not in __esctl_data:
                                __esctl_data[host] = {}
                                                        
                            f = self.tar.extractfile(member)
                            
                            if f:
                                content = f.read().decode("utf-8", "replace")
                                
                                listData = re.search(r"(?s)(?<=STDOUT:\n).*?(?=STDERR:)", content, re.MULTILINE)
                                foi = os.path.basename(member.name)
                                
                                if foi == "etc.ddn.exascaler.conf" or foi == "exascaler_conf.exascaler.conf":
                                    foi = "exascaler.conf.raw"
                                
                                if listData:
                                    __esctl_data[host][foi] = listData.group().strip()
                                else:
                                    __esctl_data[host][foi] = content.strip()
                    
                self._exaconfig = es_config_loader(__esctl_data)  
                self._exaconfig.getExaScalerVersionNum()
            else:
                print("\n{} can't be found.\nExit".format(es_showall))
                exit()
                
        except Exception as e:
            print("Can't read 'exascaler.conf' because of an issue. Message received: {}\n".format(e))
            exit()
                
    def getData(self):
        """Get the discovered listData from the esctl"""
        return self  
    
    def getNodes(self):
        return self._exaconfig.getNodes()
    

    def getRawExaScalerConf(self):
        return self._exaconfig.getRawExaScalerConf()

    def getFilesystemNames(self):
        return self._exaconfig.getFilesystemNames()
    
    def getExaScalerType(self):
        return self._exaconfig.getExaScalerType()
    
    #FIX: Get the version digits only for comparison
    def getExaScalerVersion(self):
        return self._exaconfig.getExaScalerVersion()
    
    def getExaScalerVersionNum(self):
        return self._exaconfig.getExaScalerVersionNum()
    
    def getLustreVersion(self):
        return self._exaconfig.getLustreVersion()
        
    def getLustreSettings(self):
        return self._exaconfig.getLustreSettings()
    
    def getModuleSettings(self):
        return self._exaconfig.getModuleSettings()
            
    def getModuleSetting(self, node):
        return self._exaconfig.getModuleSetting(node)
    
    def getTimezone(self):
        return self._exaconfig.getTimezone()
    
    def getNTPServers(self):
        return self._exaconfig.getNTPServers()
    
    def getMDSServerList(self, filesystem, folded = False):
        return self._exaconfig.getMDSServerList(filesystem, folded)
    
    def getOSSServerList(self, filesystem, folded = False): 
        return self._exaconfig.getOSSServerList(filesystem, folded)

    def getMDTCount(self, filesystem):
        return self._exaconfig.getMDTCount(filesystem)

    def getOSTCount(self, filesystem):
        return self._exaconfig.getOSTCount(filesystem) 
    
    def getLustreNodes(self):
        return self._exaconfig.getLustreNodes()
    
    def getInterfaceList(self):
        return self._exaconfig.getInterfaceList()
    
    def getHAConfig(self, host):
        if "[" in host and "]" in host:
            nodes = NodeSet(host)
            hastatus = ""
            
            for node in nodes:
                m = re.search(r"(?s)(?:Node {}: )[^N]+(?=\n)".format(node), self.__esctl_data[node]["hastatus.txt"], re.MULTILINE)
                hastatus = hastatus + m.group()
            return hastatus
        else:
            m = re.search(r"(?s)(?:Node {}: )[^N]+(?=\n)".format(host), self.__esctl_data[host]["hastatus.txt"], re.MULTILINE)
            return m.group()
            
    
    def getInterfaceConfig(self, host):
        return self._exaconfig.getInterfaceConfig(host)
        
    def snapshotKernelInstalled(self):
        if "ddns" in self.getLustreVersion():
            return True
        else:
            return False  
        
    def targetDetails(self, index, filesystem, nodeType):
        dftype = "size"
        targetDetails = {}
            
        for node in self.mdsList(index, filesystem):
            if (node not in self.__esctl_data[index].keys()):
                continue
            
            lustre_conf = StringIO(self.__esctl_data[index][node]["lustre_log.txt"])
            
            inSection = False
            for line in lustre_conf:
                if "lfs df" in line.strip():
                    inSection = True
                    if "-h" in line:
                        dftype = "size"
                    if "-i" in line:
                        dftype = "inode"
                        
                    continue
                elif not inSection:
                    continue
                
                #if "dumpe2fs" in line.strip():
                #        inSection = True
                #        continue                             
                    
                #if inSection and line.strip().startswith("Filesystem volume name:"):
                #    name = line.strip()[len("Filesystem volume name:")+1:].strip()
                if inSection and line.strip().startswith(filesystem):
                    name = line.strip().split("-")[1].split("_")[0]
                    
                    if "MDT" not in name and nodeType == "mds":
                    #    inSection = False
                        continue
                    
                    if "OST" not in name and nodeType == "oss":
                    #    inSection = False
                        continue
                    
                    if name not in targetDetails:
                        targetDetails[name] = {}
        
                    if inSection and dftype == "size":
                        targetDetails[name]["size"] = line.strip().split()[1]
                    
                    if inSection and dftype == "inode":
                        targetDetails[name]["inodes"] = line.strip().split()[1]
                
                #if inSection and line.strip().startswith("Inode count:"):
                #    targetDetails[name]["inodes"] = line.strip()[len("Inode count:")+1:].strip()
       
                #if inSection and line.strip().startswith("Block count:"):
                #    targetDetails[name]["blocks"] = line.strip()[len("Block count:")+1:].strip()
                    
                #if inSection and line.strip().startswith("Block size:"):
                #    targetDetails[name]["blockSize"] = line.strip()[len("Block size:")+1:].strip()
                    
                #    targetDetails[name]["size"] = round((int(targetDetails[name]["blocks"]) * int(targetDetails[name]["blockSize"])) / 1024 / 1024 / 1024 / 1024, 3) 
                    
                #    inSection = False 
        
                if inSection and line.startswith("filesystem_summary"):
                    inSection = False
        
        return targetDetails                           
    
    # Helper classes        
    def convertNetmask(self, netmask):
        return sum(bin(int(x)).count('1') for x in netmask.split('.'))
        

    def __findFOI(self, foi):
        if [i for i, x in enumerate(self.__FOI) if x in foi.name]:
            if len(self.__excludedNodes) == 0:
                return True
            else:
                if [i for i, n in enumerate(self.__excludedNodes) if n in foi.name]:
                    return False
                else:
                    return True
        else:
            return False  
        
    def __findFOI62(self, foi):
        if [i for i, x in enumerate(self.__FOI62) if x in foi.name]:
            if len(self.__excludedNodes) == 0:
                return True
            else:
                if [i for i, n in enumerate(self.__excludedNodes) if n in foi.name]:
                    return False
                else:
                    return True
        else:
            return False  
        
    # def __findInterface(self, foi):
    #     if [i for i, x in enumerate(self.getInterfaceList()) if x in foi.name]:
    #         return True
    #     else:
    #         return False 
        
