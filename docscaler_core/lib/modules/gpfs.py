'''
Created on 13 Dec 2017

@author: mwolf

This module is for parsing the output of gsctl showall.
It currently excepts the tar file created by gsctl.

TODO: mmlsconfig, host files, 
'''

import tarfile
from io import StringIO

class parse_gsctl():
    
    FOI = ["mmlscluster", "mmlsconfig", "mmlsnsd_m", "mmlsnsd_l", "mmlsfs", "gpfs_any_mmlsdisk", "mmremotecluster"]
    
    MMLSFS = [["-f", None,"Minimum fragment size in bytes"],
              ["-i", "4096", "Inode size in bytes"],
              ["-I", None, "Indirect block size in bytes"],
              ["-m", "1", "Default number of metadata replicas"],
              ["-M", "2", "Maximum number of metadata replicas"],
              ["-r", "1", "Default number of data replicas"],
              ["-R", "2", "Maximum number of data replicas"],
              ["-j", "0", "Block allocation type"],
              ["-D", "nfs4", "File locking semantics in effect"],
              ["-k", "all", "ACL semantics in effect"],
              ["-n", "0", "Estimated number of nodes that will mount file system"],
              ["-B", "0", "Block size"],
              ["-Q", "none", "Quotas accounting enabled"],
              ["--perfileset-quota", "no", "Per-fileset quota enforcement"],
              ["--filesetdf", "no", "Fileset df enabled?"],
              ["-V", None, "File system version"],
              ["--create-time", None, "File system creation time"],
              ["-z", "no", "Is DMAPI enabled?"],
              ["-L", "4M", "Logfile size"],
              ["-E", "yes", "Exact mtime mount option"],
              ["-S", "no", "Suppress atime mount option"],
              ["-K", "whenpossible", "Strict replica allocation option"],
              ["--fastea", None, "Fast external attributes enabled?"],
              ["--encryption", None, "Encryption enabled?"],
              ["--inode-limit", None, "Maximum number of inodes"],
              ["--log-replicas", "0", "Number of log replicas"],
              ["--is4KAligned", None, "is4KAligned?"],
              ["--rapid-repair", None, "rapidRepair enabled?"],
              ["--write-cache-threshold", None, "HAWC Threshold (max 65536)"],
              ["--subblocks-per-full-block", None, "Number of subblocks per full block"],
              ["-P", None, "Disk storage pools in file system"],
              ["-d", None, "Disks in file system"],
              ["-A", "yes", "Automatic mount option"],
              ["-o", None, "Additional mount options"],
              ["-T", "/gpfs", "Default mount point"],
              ["--mount-priority", "0", "Mount priority"]]

    MMCRCLUSTER = [["--ccr-enable", "", "Repository type"],
                   ["-r", "/usr/bin/ssh", "Remote shell"],
                   ["-R", "/usr/bin/scp", "Remote file copy"],
                   ["-C", "", "Cluster name"],
                   ["-A", "", "Autostart"],
                   ["-c", "", "Config file"]]

    gsctl_data = {}
    
    def __init__(self, gsctl):
        try:
            for filename in gsctl:
                print("- {0}".format(filename))
                self.tar = tarfile.open(filename, "r")
                m = filter(self.findFOI,self.tar.getmembers())
                
                self.gsctl_data[len(self.gsctl_data)] = {}
                index = len(self.gsctl_data)-1
                
                for member in m:
                    foi = [x for a, x in enumerate(self.FOI) if x in member.name][0]
                    
                    if foi == "gpfs_any" and not member.name.endswith("mmlsdisk.txt"):
                        if member.name.endswith("gpfs_any.txt"):
                            pass
                        #else: 
                        #    continue
                    
                    f = self.tar.extractfile(member)
                    
                    if f:
                        content = f.read().decode("utf-8")
                        start = content.find("STDOUT") + 7
                        stop = content.find("STDERR")
                        content = content[start:stop].strip()
                        self.gsctl_data[index][foi] = content
                    #print "%s has content:\n%s\n" %(foi, content)
                
                print(" \- reading information for: ")
                print("   -> Initial config")    
                self.gsctl_data[index]["initial_config"] = self.initialConfig(index)
                print("   -> mmlsconfig") 
                self.gsctl_data[index]["config"] = self.mmlsconfig(index)
                print("   -> tiebreakerDisks") 
                self.gsctl_data[index]["tiebreakerdisks"] = self.tiebreakerDisks(index)
                print("   -> Cluster name")
                self.gsctl_data[index]["cluster_name"] = self.getClusterName(index)  
                print("   -> mmlscluster")
                self.gsctl_data[index]["cluster"] = self.mmcrcluster(index)
                print("   -> Server list")
                self.gsctl_data[index]["serverlist"] = self.getNodeList(index)
                print("   -> Node list") 
                self.gsctl_data[index]["nodelist"] = self.getNodeList(index, nodesOnly=True)
                print("   -> Client list")
                self.gsctl_data[index]["clientlist"] = self.getNodeList(index, server=False)
                print("   -> Filesystems")
                self.gsctl_data[index]["filesystems"] = self.getFilesystems(index)
                self.gsctl_data[index]["stanza"] = ""
                for filesystem in self.getFilesystems(index):
                        print("      \- {0}".format(filesystem))
                        print("        -> Creating stanza")
                        self.gsctl_data[index]["stanza_{0}".format(filesystem)] = self.getStanza(filesystem, index)
                        self.gsctl_data[index]["stanza"] += self.getStanza(filesystem, index) + "\n"
                        print("        -> Creating mmcrfs command")
                        self.gsctl_data[index]["filesystem_{0}".format(filesystem)] = self.mmcrfs(filesystem, index)
                
                self.gsctl_data[index]["stanza"] = self.gsctl_data[index]["stanza"][:len(self.gsctl_data[index]["stanza"]) - 1]
                
        except Exception as e:
            print(e)
            exit()

    def getData(self):
        """Get the discovered data from the gsctl"""
        return self.gsctl_data

    def getFilesystems(self, index):
        """Get all available filesystems"""
        
        filesystems=[]
        mmlsconfig = StringIO(self.gsctl_data[index]["mmlsconfig"])
        
        for line in mmlsconfig:
            if line.find("/dev") != -1:
                filesystems.append(line[5:].strip())
                
        return filesystems


    def getStanza(self, fs, index):
        """Reverse creation of the stanza file from the given filesystem"""
        
        found = False
        stanza = ""
        mmlsdisk = StringIO(self.gsctl_data[index]["gpfs_any_mmlsdisk"])
        mmlsnsd_m = StringIO(self.gsctl_data[index]["mmlsnsd_m"])
        mmlsnsd_l = StringIO(self.gsctl_data[index]["mmlsnsd_l"])
        
        for line in mmlsdisk:
            if line.find("mmlsdisk") != -1 and line.find(fs) != -1:
                found = True
            elif line.find("Number") != -1:
                if found == True:
                    return stanza.strip()
            
            if found:
                disk = line.split()
                if len(line.split()) > 2 and line.split()[1] == "nsd":
                    
                    for nsd in mmlsnsd_m:
                        if nsd.find(disk[0]) != -1:
                            device = nsd.split()[2]
                            break
                        
                    for nsd in mmlsnsd_l:
                        if nsd.find(disk[0]) != -1:
                            server = nsd.split()[3]
                            break
                    
                    if disk[4] == "Yes" and disk[5] == "Yes":
                        usage = "dataAndMetadata"
                    elif disk[4] == "Yes" and disk[5] == "No":
                        usage = "metadataOnly"
                    elif disk[4] == "No" and disk[5] == "Yes":
                        usage = "dataOnly" 
                    
                    for s in server.split(","):
                        d = s.split(".")
                        if not d[0].isdigit():
                            server = server.replace(s,d[0])
                    
                    stanza = "{0}%nsd: device={1} nsd={2} servers={3} usage={4} failureGroup={5} pool={6}\n".format(stanza, device, disk[0].split(".")[0], server, usage, disk[3], disk[9])
 
        return stanza.strip()
        
    def mmcrfs(self, fs, index, full=False):
        """Reverse creation of the options for mmcrfs"""
        
        found = False
        mmcrfs = "mmcrfs {0} -F stanza".format(fs)
        mmlsfs = StringIO(self.gsctl_data[index]["mmlsfs"])
        
        for line in mmlsfs:
            if line.find("/dev/") != -1:
                if line.find(fs) != -1:
                    found = True 
                    continue
                else:
                    found = False
            if found:
                option = line.split()
                if len(line.split()) > 1:
                    default = self.getDefaultMMLSFSOption(option[0])
                    if default != None:
                        if full or default != option[1]:
                            if option[0] == "-Q" and option[1] != "none":
                                option[1] = "yes"
    
                            mmcrfs = "{0} {1} {2}".format(mmcrfs, option[0], option[1])   
                             
        return mmcrfs.strip()

    def getNodeList(self, index, server=True, nodesOnly=False):
        """Get nodes in the cluster"""
        
        nodelist = ""
        mmlscluster = StringIO(self.gsctl_data[index]["mmlscluster"])
        #print(self.gsctl_data[index]["mmlscluster"])
        for line in mmlscluster:
            option = line.split()
            if len(line.split()) > 1:
                if option[0].isdigit() and len(option) == 5 and server:
                    if nodesOnly:
                        nodelist = "{0}{1}\n".format(nodelist, option[1])
                        continue
                    
                    nodelist = "{0}{1}:{2}".format(nodelist, option[1], option[4])
                    if option[1] != option[3]:
                        nodelist = "{0}:{1}".format(nodelist, option[3])
                    nodelist = "{0}\n".format(nodelist)
                elif option[0].isdigit() and len(option) == 4 and not server:
                    nodelist = "{0}{1}\n".format(nodelist, option[1])
        
        return nodelist.strip()
    
    def initialConfig(self, index):
        """Reverse creation of the config for mmcrcluster"""
        
        config = ""
        section = ""
        mmlsconfig = StringIO(self.gsctl_data[index]["mmlsconfig"])
        
        for line in mmlsconfig:
            option = line.split()
            
            if line[:1] == "[":
                section = line[1:len(line)-2].lower()
            
            if len(line.split()) > 1 and (section == "common" or section == ""):
                if option[0].lower() == "pagepool":
                    config = '''{0}{1} {2}\n'''.format(config, option[0], option[1])
                if option[0].lower() == "maxmbps":
                    config = '''{0}{1} {2}\n'''.format(config, option[0], option[1])
                if option[0].lower() == "maxblocksize":
                    config = '''{0}{1} {2}\n'''.format(config, option[0], option[1])
                    
        
        return config.strip()
                    
    def tiebreakerDisks(self, index): 
         
        config = ""
        section = ""
        mmlsconfig = StringIO(self.gsctl_data[index]["mmlsconfig"])
        
        for line in mmlsconfig:
            option = line.split()
            
            if line[:1] == "[":
                section = line[1:len(line)-2].lower()
            
            if len(line.split()) > 1 and (section == "common" or section == ""):
                if option[0].lower() == "tiebreakerdisks":
                    config = '''{0}{1}\n'''.format(config, option[1])
            
        return config.strip()              
                    
    def mmlsconfig(self, index):
        return self.gsctl_data[index]["mmlsconfig"]
    
    def getClusterName(self, index):
        mmlscluster = StringIO(self.gsctl_data[index]["mmlscluster"])
        
        for line in mmlscluster:
            option = line.split()
            if line.find("GPFS cluster name:") != -1:
                return option[3]
    
        return ""
        
    def mmcrcluster(self, index):
        """Reverse creation of the options for mmcrcluster"""
        
        mmcrcluster = "mmcrcluster -N serverList "
        mmlscluster = StringIO(self.gsctl_data[index]["mmlscluster"])
        mmlsconfig = StringIO(self.gsctl_data[index]["mmlsconfig"])
        
        for line in mmlscluster:
            option = line.split()
            if len(line.split()) > 1:
                if line.find("GPFS cluster name:") != -1:
                    cluster_name = option[3]
                if line.find("Remote shell command:") != -1:
                    cluster_rsh = option[3]
                if line.find("Remote file copy command:") != -1:
                    cluster_rcp = option[4]
                if line.find("Repository type:") != -1:
                    cluster_repository = option[2]
                if line.find("Primary Server:") != -1:
                    cluster_primary = option[1]
                if line.find("Secondary Server:") != -1:
                    cluster_secondary = option[1]
        
        for line in mmlsconfig:
            option = line.split()
            if len(line.split()) > 1:
                if option[0] == "autoload":
                    cluster_autostart = True
        
        if "cluster_repository" not in locals():
            mmcrcluster = mmcrcluster + "--ccr-disable -p {0} ".format(cluster_primary)
            if cluster_secondary and cluster_secondary != None:
                mmcrcluster = mmcrcluster + "-s {0} ".format(cluster_secondary)
        
        if cluster_rsh != self.getDefaultMMCRCLUSTEROption("-r"):
            mmcrcluster = mmcrcluster + "-r {0} ".format(cluster_rsh)
        
        if cluster_rcp != self.getDefaultMMCRCLUSTEROption("-R"):
            mmcrcluster = mmcrcluster + "-R {0} ".format(cluster_rcp)
            
        mmcrcluster = mmcrcluster + "-C {0} ".format(cluster_name)
        
        if "cluster_autostart" in locals():
            mmcrcluster = mmcrcluster + "-A "
        
        mmcrcluster = mmcrcluster + "-c configFile "
        
        return mmcrcluster.strip()
    
    def exportServices(self, index):
        return
    
    # Helper classes
    def findFOI(self, foi):
        if [i for i, x in enumerate(self.FOI) if x in foi.name]:
            return True
        else:
            return False
        
    def getDefaultMMLSFSOption(self, option):  
        for opt in self.MMLSFS:
            if opt[0] == option:
                if opt[1] == None:
                    return None
                return opt[1]

    def getDefaultMMCRCLUSTEROption(self, option):  
        for opt in self.MMCRCLUSTER:
            if opt[0] == option:
                if opt[1] == None:
                    return None
                return opt[1]