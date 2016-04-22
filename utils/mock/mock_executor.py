import ntpath
import shutil
import sys

import config.runtime_config
import outputControl.logging_access
import utils.process_utils as exxec
import utils.rpmbuild_utils as rpmuts
import utils.test_utils as tu
from utils.mock import FsZipCache


class Mock:
    caredTopDirs = [
        "/bin",
        "/boot",
        "/builddir",
        "/dev",
        "/etc",
        "/home",
        "/lib",
        "/lib64",
        "/media",
        "/opt",
        "/root",
        "/run",
        "/sbin",
        "/tmp",
        "/usr"
        #            ,"/var"
    ]

    def __init__(self, os="fedora", version="rawhide", arch="x86_64", command="mock"):
        self.os = os
        self.version = version
        self.arch = arch
        self.command = command
        self.snapshots = dict()
        outputControl.logging_access.LoggingAccess().log("Providing new instance of " + self.getMockName())

    def getMockName(self):
        return self.os + "-" + self.version + "-" + self.arch

    def getConfigFile(self):
        return "/etc/mock/" + self.getMockName() + ".cfg"

    def getDir(self):
        return "/var/lib/mock/" + self.getMockName()

    def getRootDir(self):
        return self.getDir() + "/root"

    def getResultDir(self):
        return self.getDir() + "/result"

    def mainCommand(self):
        return [self.command, "-r", self.getMockName()]

    def init(self):
        o, e = exxec.processToStrings(self.mainCommand() + ["--init"])
        outputControl.logging_access.LoggingAccess().log(e)

    def installAlternatives(self):
        o, e = exxec.processToStrings(self.mainCommand() + ["--install", "chkconfig"])
        outputControl.logging_access.LoggingAccess().log(e)

    def mktemp(self, suffix="me"):
        o, e = exxec.processToStrings(self.mainCommand() + ["--chroot", "mktemp --suffix " + suffix])
        outputControl.logging_access.LoggingAccess().log(e)
        return o

    def importFileContnet(self, suffix, content):
        src = tu.saveStringsAsTmpFile(content, suffix)
        dest = self.mktemp(suffix)
        o, e = exxec.processToStrings(self.mainCommand() + ["--copyin", src, dest])
        outputControl.logging_access.LoggingAccess().log(e)
        return dest

    def executeShell(self, scriptFilePath):
        o, e, r= exxec.processToStringsWithResult(self.mainCommand() + ["--chroot", "sh", scriptFilePath])
        outputControl.logging_access.LoggingAccess().log(e)
        return o, r

    def listFiles(self):
        o = exxec.processAsStrings(self.mainCommand() + ["--chroot", "find"] + Mock.caredTopDirs, log=False)
        return o

    def createAndExecuteShell(self, scriptSuffix, lines):
        script = self.importFileContnet(scriptSuffix, lines)
        o, r = self.executeShell(script)
        return o, r

    def provideCleanUsefullRoot(self):
        self.init()
        self.installAlternatives()

    def executeScriptlet(self, rpmFile, scripletName):
        scriplet = rpmuts.getSrciplet(rpmFile, scripletName)
        if scriplet is None or len(scriplet) == 0:
            raise Exception("Scriptlet " + scripletName + " is not in " + rpmFile)
        return self.createAndExecuteShell("_" + scripletName + "_" + ntpath.basename(rpmFile), scriplet)

    def _getAbsFiles(self, files):
        absDirs = []
        for f in files:
            absDirs.append(self.getRootDir() + "/" + f)
        return absDirs

    def createSnapshot(self, name):
        raise Exception("Dont use, still nto implemented correctly")
        snapData = FsZipCache.createInMemoryArchive(self._getAbsFiles(self.caredTopDirs))
        self.snapshots[name] = snapData
        return snapData

    def getSnapshot(self, name):
        snapData = self.snapshots[name]
        return snapData

    def rewertToSnapshot(self, name):
        raise Exception("Dont use, still nto implemented correctly")
        snapData = self.getSnapshot(name)
        if snapData is None:
            return
        shutil.rmtree(self.getRootDir())
        snapData.unpack()


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
