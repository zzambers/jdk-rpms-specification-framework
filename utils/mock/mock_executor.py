import ntpath
import os
import re

import outputControl.logging_access
import utils.mock.rpm_uncpio_cache
import utils.process_utils as exxec
import utils.rpmbuild_utils as rpmuts
import utils.test_utils as tu
from utils.rpmbuild_utils import unpackFilesFromRpm


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
        self.inited = False;
        self.alternatives = False;
        outputControl.logging_access.LoggingAccess().log("Providing new instance of " + self.getMockName())
        self._scrubLvmCommand()


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
        if self.inited:
            self.reinit()
        else:
            self._init()

    def _init(self):
        o, e = exxec.processToStrings(self.mainCommand() + ["--init"])
        outputControl.logging_access.LoggingAccess().log(e)
        self.inited = True;

    def reinit(self):
        self._rollbackCommand("postinit")

    def listSnapshots(self):
        o =  exxec.processAsStrings(self.mainCommand() + ["--list-snapshots"])
        current = None
        items = []
        for item in o[1:len(o)]:
            i = re.sub("^.\s+","", item)
            if (item.startswith("*")):
                current = i
            items.append(i)
        return current, items

    def _snapsotCommand(self, name):
        o, e = exxec.processToStrings(self.mainCommand() + ["--snapshot", name])
        outputControl.logging_access.LoggingAccess().log(e)
        outputControl.logging_access.LoggingAccess().log(o)
        outputControl.logging_access.LoggingAccess().log(str(self.listSnapshots()));

    def _rollbackCommand(self, name):
        o, e = exxec.processToStrings(self.mainCommand() + ["--rollback-to", name])
        outputControl.logging_access.LoggingAccess().log(e)
        outputControl.logging_access.LoggingAccess().log(o)
        outputControl.logging_access.LoggingAccess().log(str(self.listSnapshots()));

    def _scrubLvmCommand(self):
        o, e = exxec.processToStrings(self.mainCommand() + ["--scrub", "lvm"])
        outputControl.logging_access.LoggingAccess().log(e)
        outputControl.logging_access.LoggingAccess().log(o)
        outputControl.logging_access.LoggingAccess().log(str(self.listSnapshots()));

    def installAlternatives(self):
        if self.alternatives:
            self.getSnapshot("alternatives")
        else:
            self._installAlternatives();


    def _installAlternatives(self):
        o, e = exxec.processToStrings(self.mainCommand() + ["--install", "chkconfig"])
        outputControl.logging_access.LoggingAccess().log(e)
        self.createSnapshot("alternatives")
        self.alternatives=True

    def mktemp(self, suffix="me"):
        o, e = exxec.processToStrings(self.mainCommand() + ["--chroot", "mktemp --suffix " + suffix])
        outputControl.logging_access.LoggingAccess().log(e)
        return o

    def importFileContnet(self, suffix, content):
        src = tu.saveStringsAsTmpFile(content, suffix)
        dest = self.mktemp(suffix)
        self.copyIn([src], dest)
        return dest

    def copyIn(self, src, dest):
        o, e, r = exxec.processToStringsWithResult(self.mainCommand() + ["--copyin"] + src + [dest])
        outputControl.logging_access.LoggingAccess().log(e)
        return o, e, r

    def copyIns(self, cwd, srcs, dest):
        #unlike copyIn, this copppy list of files TO destination. Because of necessary relativitu of srcs, CWD is included
        o, e, r = exxec.processToStringsWithResult(self.mainCommand() + ["--copyin"] + srcs + [dest], True, cwd)
        outputControl.logging_access.LoggingAccess().log(e)
        return o, e, r

    def importUnpackedRpm(self, rpmPath):
        uncipioed = utils.mock.rpm_uncpio_cache.UcipioCached().uncipio(rpmPath)
        dirs = tu.get_dirs(uncipioed, "", False)
        nwDirs = [];
        for dir in dirs:
            nwDir = dir[len(uncipioed):]
            nwDirs.append(nwDir);
        # mock is to dummy to to live, copy like this do not preserve directories tree
        #files = tu.get_files(uncipioed, "", False)
        #nwFiles = [];
        #for file in files:
        #    nwFile = file[len(uncipioed)+1:]
        #    nwFiles.append(nwFile)

        files = tu.get_top_dirs_and_files(uncipioed)
        o = ""
        e = ""
        r = 0

        dod, drd = self.mkdirsP(nwDirs)
        o += dod
        r += drd

        oo, ee, rr = self.copyIns(uncipioed, files, "/")
        o += oo
        e += ee
        r += rr

        return o, e, r

    def mkdirP(self, dirName):
        return self.executeCommand(["mkdir -p " + dirName])

    def mkdirsP(self, dirNames):
        all="";
        for  dir in dirNames:
            all=all+" "+dir;
        return self.executeCommand(["mkdir -p " + all])

    def executeCommand(self, cmds):
        o, e, r = exxec.processToStringsWithResult(self.mainCommand() + ["--chroot"] + cmds)
        outputControl.logging_access.LoggingAccess().log(e)
        return o, r

    def executeShell(self, scriptFilePath):
        o, e, r = exxec.processToStringsWithResult(self.mainCommand() + ["--chroot", "sh", scriptFilePath])
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
        if (self.alternatives):
            self.installAlternatives()
        else:
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
        self._snapsotCommand(name)

    def getSnapshot(self, name):
        self._rollbackCommand(name)


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
