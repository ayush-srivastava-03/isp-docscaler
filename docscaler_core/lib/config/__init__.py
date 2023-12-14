'''
Created on 2 Jun 2018

@author: mwolf
'''
import os
import io
import json
import copy
import tarfile
import shutil
import functools

from jsoncfg.text_encoding import load_utf_text_file
from collections import OrderedDict
from copy import deepcopy
from modules.tools import istext
from pathlib import Path

class ConfigDict(OrderedDict):
    __getattr__= OrderedDict.__getitem__
    __setattr__= OrderedDict.__setitem__
    __delattr__= OrderedDict.__delitem__
    
    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.items():
            setattr(result, k, deepcopy(v, memo))
        return result

class ConfigData():
    
    def __init__(self, configFile, generateConfigData=False):
        self.__configFile = configFile
        self.__orig_config = self.__loadJson__()
        
        if generateConfigData:
            self.generateConfigData(True)
    
    def getConfigPath(self, addTrailingChar=""):
        if os.path.isabs(self.__configFile):
            return os.path.dirname(self.__configFile) + addTrailingChar
        else:
            return os.path.dirname(os.getcwd() + "/" + self.__configFile) + addTrailingChar
    
    def getConfigName(self):
        return os.path.basename(self.__configFile)
    
    def getConfig(self):
        return self.__config
    
    def getDocumentFilename(self):
        return self.__config.general.document_name
    
    @staticmethod
    def __load__(listData):
        if type(listData) is OrderedDict:
            return ConfigData.__load_dict__(listData)
        elif type(listData) is list:
            return ConfigData.__load_list__(listData)  
        else:
            return listData  
        
    @staticmethod
    def __load_dict__(listData: dict):
        result = ConfigDict()
        for key, value in listData.items():
            result[key] = ConfigData.__load__(value)
        
        return result
        
    @staticmethod
    def __load_list__(listData: list):
        result = [ConfigData.__load__(item) for item in listData]
        return result
    
    def __loadJson__(self):
        #TODO: Json Schema implementation to check for correct values.
        return ConfigData.__load__(json.loads(load_utf_text_file(self.__configFile), object_pairs_hook=OrderedDict))
        
    @staticmethod
    def saveJson(filepath:str, config:ConfigDict):
        with open(filepath, 'w') as outfile:
            json.dump(config, outfile, indent=3) 
    
    @staticmethod
    def copyTemplates(self, filepath:str):
        overview = "overview.template"
        summary = "summary.template"
        
        basePath = os.path.dirname(filepath) + "/"
        
        if not os.path.exists(basePath + overview):
            shutil.copyfile("templates/overview.template", basePath + overview)
            
        if not os.path.exists(basePath + summary):
            shutil.copyfile("templates/summary.template", basePath + summary)
    
    
    def generateConfigData(self, ignore):
        from modules import sfa, gpfs, lustre
        
        config = copy.deepcopy(self.__orig_config)
        
        print ("Generating '{}'".format(config.general.document_name))
        
        '''Project'''
        if "project" in config: 
            for proj in config.project:
                print ("  Collecting data for project '{}'".format(proj))
                
                '''SFA'''
                if "sfa" in config.project[proj]:
                    sfa_data = ConfigDict()
                    sfa_config = config.project[proj].sfa
                        
                    # Single log file which could be a TXT or a TGZ file
                    # Get the subsystem name from the log file
                    if isinstance(sfa_config, list):
                        
                        for conf in sfa_config:
                            # Combined log file. Get the subsystem names from the config file
                            if isinstance(conf, ConfigDict):
                                for subsystemName in conf:
                                    print ("    Parsing 'show sub sum'")
                                    print("      - {}".format(conf[subsystemName]))
                                    with open("{0}/{1}".format(self.getConfigPath(), conf[subsystemName]), "rb") as f:
                                        sss = sfa.parse_sss(f.read().decode("utf-8")).getData()
                                        sfa_data.update({subsystemName: sss})   
                            
                            # a TXT or TGZ file
                            if isinstance(conf, str):
                                file = "{}/{}".format(self.getConfigPath(), conf)
                                
                                # Is a TXT file
                                if istext(file):
                                    print ("    Parsing 'show sub sum'")
                                    print("      - {}".format(conf))
                                    with open(file, "rb") as f:
                                        sss = sfa.parse_sss(f.read().decode("utf-8")).getData()
                                        sfa_data.update({sss.getSubsystemName(): sss})
                                        
                                # Is a TGZ file
                                elif tarfile.is_tarfile(file):
                                    with tarfile.open(file, "r") as tar:
                                        print ("    Parsing 'show sub sum' in {}".format(conf))
                                        for member in tar.getmembers():
                                            print("      - {}".format(member.name))
                                            f = tar.extractfile(member)
                                            read = f.read().decode("utf-8")
                                            sss = sfa.parse_sss(read).getData()
                                            sfa_data.update({sss.getSubsystemName(): sss})
                                     
                            
                config.project[proj].sfa = sfa_data
                
                '''GPFS'''
                #if "gpfs" in config.project[proj]:
                #    for filesystem in config.project[proj].gpfs:
                #        print(filesystem)
                    
                '''LUSTRE'''
                if "lustre" in config.project[proj]:
                        lustre_config = config.project[proj].lustre
                        
                        if isinstance(lustre_config, str) or isinstance(lustre_config, list):
                        
                            if isinstance(lustre_config, str):
                                lustre_config = [lustre_config]
                        
                            for idx, conf in enumerate(lustre_config):
                                print ("    Parsing es_showall: {}'".format(conf))
                                file = "{}/{}".format(self.getConfigPath(), conf)
                            
                                lustre_config[idx] = lustre.parse_esctl(file).getData()
                                
                                if len(lustre_config) == 1:
                                    config.project[proj].lustre = lustre_config[0]
                                else:
                                    config.project[proj].lustre = lustre_config
                            
                        # Combined log file. Get the names from the config file
                        # If the number of nodes inside the tar is larger then the combined setting,
                        # then all none combined nodes will be treated as single ones.
                        elif isinstance(lustre_config, ConfigDict):
                            for nodes in lustre_config:
                                print ("    Parsing es_showall: {}'".format(lustre_config[nodes]))
                                file = "{}/{}".format(self.getConfigPath(), lustre_config[nodes])
                                
                                config.project[proj].lustre = lustre.parse_esctl(file, nodes).getData()

                print("\n")
                      
        self.__config = config 
        return config
    
class ConfigWriter:

    #general
    def setDate(self, date:str):
        self.date = "now"
        
    def setDocumentName(self, document_name:str):
        if not document_name.strip().endswith(".pdf"):
            document_name = document_name.strip() + ".pdf"
        
        self.document_name = document_name.strip()
        
    def setTitle(self, title1:str = "", title2:str = "", title3:str = ""):
        self.title1 = title1.strip()
        self.title2 = title2.strip()
        self.title3 = title3.strip()

    #customer
    def setCustomerCompany(self, company:str):
        self.customer_company = company.strip()
        
    def setCustomerLogo(self, logo:str):
        self.customer_logo = logo.strip()
        
    def setCustomerName(self, name:str):
        self.customer_name = name.strip()
        
    def setCustomerPhone(self, phone:str):
        self.customer_phone = phone.strip()
    
    def setCustomerEmail(self, email:str):
        self.customer_email = email.strip()
        
    def setCustomerAddress(self, address1:str = "",
                                 address2:str = "",
                                 address3:str = "",
                                 address4:str = ""):
        
        self.address1 = address1.strip()
        self.address2 = address2.strip()
        self.address3 = address3.strip()
        self.address4 = address4.strip()
    
    #team
    def setDDNTeam(self, team:list):
        self.ddnTeam = team
    
    #network
    def setRackLayout(self, rack:str):
        self.rackDiagram = rack.strip()
        
    def setNetworkDiagram(self, network:str):
        self.networkDiagram = network.strip()
        
    def setProjects(self, projects:list):
        self.projects = projects
        
    def setTemplates(self, templates:list):
        self.templates = templates
    
    def writeConfig(self, reportPath:str, configFile:str):
        
        config = ConfigDict([('general',
                    ConfigDict([('date', self.date),
                                ('document_name', self.document_name),
                                ('title', ConfigDict([('1', self.title1),
                                                      ('2', self.title2),
                                                      ('3', self.title3)]
                                          )
                                )]
                    )),
                    ('customer',
                     ConfigDict([('company', self.customer_company),
                                 ('logo', self.customer_logo),
                                 ('name', self.customer_name),
                                 ('phone', self.customer_phone),
                                 ('email', self.customer_email),
                                 ('address',ConfigDict([('1', self.address1),
                                                        ('2', self.address2),
                                                        ('3', self.address3),
                                                        ('4', self.address4)]
                                            ))
                                 ])),
                    ('ddn',
                     ConfigDict([('team', self._generateTeamList())])),
                    ('network',
                     ConfigDict([('rack_diagram', self.rackDiagram + '::'),
                                 ('network_diagram', self.networkDiagram + '::')])),
                    ('project', self._generateProjectList()),
                    ('templates', self.templates)])
        
        
        
        if self.rackDiagram == "" and self.networkDiagram == "":
            config.pop("network")
            if "rack_network" in self.templates:
                self.templates.remove("rack_network")
        
        if len(config["project"]) == 0:
            config.pop('project')
            if "project" in self.templates:
                self.templates.remove("project")
    
        ConfigData.copyTemplates(self, filepath = reportPath.strip())
        ConfigData.saveJson(filepath = reportPath.strip() + configFile.strip(), config = config)
        
        return True
        
    def _generateTeamList(self):
        teamList = []
        
        for team in self.ddnTeam:
            teamList.append(ConfigDict([('name', team[0]),
                                        ('role', team[1]),
                                        ('phone', team[2]),
                                        ('email', team[3]),
                                        ('doc_creator', team[4])]))
        return teamList
    
    def _generateProjectList(self):
        projectList = ConfigDict()
        
        for project in self.projects:
            projectList.update(ConfigDict(project))
            
        return projectList
    