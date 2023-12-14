'''
Created on 13 Dec 2017

@author: mwolf

This module is for parsing the output of show sub sum.
It currently excepts a tar or text file.

'''

import re
from config import ConfigDict

class parse_sss():
    def __init__(self, content):
        try:        
            headerRegEx = r"(?:(?<=\* ).+(?= \*\n))"
            dataRegEx = r"(?s)(?<=\*\n\n)[^*]+(?=\n\n\*)"
            
            unwanted = ["Jobs", "Event Log Information"]
           
            header = list()
            listData = list()
            
            self.__sss_data = ConfigDict()
            
            content = content.replace("\r", "")
            
            #Find all headers
            headerMatch = list(re.finditer(headerRegEx, content, re.MULTILINE))
            dataMatch = list(re.finditer(dataRegEx, content, re.MULTILINE))
            for headerIndex, h in enumerate(headerMatch, start=0):
                #Ommit the "Subsystem Summary" header as there is no listData
                if "Subsystem Summary" in h.group().strip():
                    continue
                
                #Find the listData for each header
                for dataIndex, d in enumerate(dataMatch, start=1):
                    if d.start() > h.end():
                        if [uw for uw in unwanted if uw in h.group().strip()]:
                            dataMatch.pop(dataIndex - 1)
                            break
                    
                        if len(dataMatch) != dataIndex:
                            #Match found for the header
                            if d.end() < headerMatch[headerIndex + 1].start():
                                header.append(h.group().strip())
                                listData.append(d.group().rstrip())
                                break

            self.__sss_data = ConfigDict(zip(header,listData))
            self.__sss_data["Content"] = content   
            
            self.__subsystemName = self.getSubsystemName      
                    
        except Exception as e:
            print(repr(e))
            exit()        

    def getData(self):
        """Return the SFA sss object"""
        return self
    
    def getRawSectionData(self, sectionHeader):
        if sectionHeader in self.__sss_data:
            return self.__sss_data[sectionHeader]
        else:
            return None
    
    def getSubsytemModel(self):
        model = re.search("SFA.*", self.getRawSectionData("Subsystem"), re.MULTILINE)
        
        if model:
            return model.group().strip();
        else:
            return None
        
    def getSubsystemName(self):
        name = re.search("(?:\S+) +(?=\d)", self.getRawSectionData("Subsystem"), re.MULTILINE)
        
        if name:
            return name.group().strip()
        else:
            return None
    
    def getFirmware(self):
        firmware = re.findall(r"\d{1,2}[.]\d{1,2}[.]\d{1,2}[.]{0,1}\d{0,2}", self.getRawSectionData("Controller(s)"), re.MULTILINE)
        
        if firmware:
            return firmware
        else:
            return None

    def getTimezone(self):
        timezone = re.findall(r"(?:REOPENING PAGE TZ SET: )(.*)",  self.getRawSectionData("Content"), re.MULTILINE)
        
        if timezone:
            return timezone[len(timezone) - 1].strip()
        else:
            return None

    def getDiskSummary(self):
        pds = re.findall(r"(Found:)( *\d+)( \w+)( +\S+)( +\S+)( +\S+)( \w+)( +\S+)( +\S+)( +\S+)", self.getRawSectionData("Physical Disk(s)"), re.MULTILINE)
        
        if pds:    
            header = """<tr><td>Count</td>
                            <td>Manufactor</td>
                            <td>Model</td>
                            <td>Type</td>
                            <td>Size</td>
                            <td>Firmware</td></tr>"""
            listData = ""           
            for pdType in pds:   
                listData = listData + """<tr><td>{}</td>
                                     <td>{}</td>
                                     <td>{}</td>
                                     <td>{}</td>
                                     <td>{}</td>
                                     <td>{}</td></tr>""".format(pdType[1].strip(), 
                                                                pdType[2].strip(), 
                                                                pdType[3].strip(), 
                                                                pdType[4].strip(),
                                                                pdType[5].strip() + pdType[6],
                                                                pdType[8].strip())
            
            summary = "<table>" + header + listData + "</table>"
        
            return summary
        
