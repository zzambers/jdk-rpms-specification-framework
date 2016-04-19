import sys
import tempfile
from _snack import scale

import outputControl.logging_access
import testcases.utils.process_utils as exec
import testcases.utils.test_utils as tu


class Mock():
    def __init__(self, os="fedora", version="rawhide", arch="x86_64", command="mock"):
        self.os=os
        self.version = version
        self.arch = arch
        self.command = command
        outputControl.logging_access.LoggingAccess().log("Providing new instance of " +self.getMockName())

    def getMockName(self):
        return self.os + "-" + self.version + "-" + self.arch

    def getConfigFile(self):
        return "/etc/mock/" + self.getMockName()+ ".cfg"

    def getDir(self):
        return "/var/lib/mock/" + self.getMockName()

    def getRootDir(self):
        return self.getDir()+ "/root"

    def getResultDir(self):
        return self.getDir() + "/result"

    def mainCommand(self):
        return [self.command, "-r", self.getMockName()]


    def init(self):
        o, e = exec.processToStrings(self.mainCommand() + ["--init"])
        outputControl.logging_access.LoggingAccess().log(e)

    def installAlternatives(self):
         o, e = exec.processToStrings(self.mainCommand() + ["--install", "chkconfig"])
         outputControl.logging_access.LoggingAccess().log(e)

    def mktemp(self, suffix="me"):
        o, e = exec.processToStrings(self.mainCommand() + ["--chroot", "mktemp --suffix "+suffix])
        outputControl.logging_access.LoggingAccess().log(e)
        return o

    def importFileContnet(self, suffix, content):
        src = tu.saveStringsAsTmpFile(content, suffix)
        dest = self.mktemp(suffix)
        o, e = exec.processToStrings(self.mainCommand() + ["--copyin", src, dest])
        outputControl.logging_access.LoggingAccess().log(e)
        return dest

    def executeShell(self, scriptFilePath):
        o, e = exec.processToStrings(self.mainCommand() + ["--chroot", "sh", scriptFilePath])
        outputControl.logging_access.LoggingAccess().log(e)
        return o

    def createAndexecuteShell(self, scriptSuffix, lines):
        script = DefaultMock().importFileContnet(scriptSuffix,lines)
        o = DefaultMock().executeShell(script)
        return o

    def createSnapshot(self):
        """ To work with snapshots, you need mock-lvm installed and
        have it enabled in  /etc/mock/site-defaults.cfg
        see  cfg's nits and https://fedoraproject.org/wiki/Mock/Plugin/LvmRoot?rd=Subprojects/Mock/Plugin/LvmRoot"""
        pass #not yet implemented
        #but once done, it will be speedup

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# Try to avoid making unnecessary instances of Mock()
# if possible, try to work with the DefaultMock and its snapshots
class DefaultMock(Mock, metaclass=Singleton):
    pass

def main(argv):
    DefaultMock().init()
    DefaultMock().installAlternatives()
    o = DefaultMock().createAndexecuteShell("_terror", ["echo helloX", "echo helloY"])
    print(o)



if __name__ == "__main__":
    main(sys.argv[1:])
