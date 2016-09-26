import ntpath
import os
import re

import outputControl.logging_access
import utils.mock.rpm_uncpio_cache
import utils.process_utils as exxec
import utils.rpmbuild_utils as rpmuts
import utils.test_utils as tu
from utils.rpmbuild_utils import unpackFilesFromRpm
import utils.mock.mock_execution_exception
import utils.pkg_name_split

PRIORITY = "priority"
STATUS = "status"
FAMILY = "family"
TARGET = "target_link"
SLAVES = "slaves"
ALTERNATIVES_DIR = "/var/lib/alternatives"


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
        self.inited = False
        self.alternatives = False
        self.snapshots = dict()
        outputControl.logging_access.LoggingAccess().log("Providing new instance of " + self.getMockName())
        # comment this, set inited and alternatives to true if debug of some test needs to be done in hurry
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

    def mainCommandAsString(self):
        s = ""
        for x in self.mainCommand():
            s=s+" " + x
        return s

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
        o, e, r = exxec.processToStringsWithResult(self.mainCommand() + ["--rollback-to", name])
        outputControl.logging_access.LoggingAccess().log(e)
        outputControl.logging_access.LoggingAccess().log(o)
        outputControl.logging_access.LoggingAccess().log(str(self.listSnapshots()));
        return e, o, r

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
        o, e = exxec.processToStrings(self.mainCommand() + ["--install", "lua"])
        outputControl.logging_access.LoggingAccess().log(e)
        o, e = exxec.processToStrings(self.mainCommand() + ["--install", "lua-posix"])
        outputControl.logging_access.LoggingAccess().log(e)
        o, e = exxec.processToStrings(self.mainCommand() + ["--install", "copy-jdk-configs"])
        outputControl.logging_access.LoggingAccess().log(e)
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

    def importRpm(self, rpmPath, resetBuildRoot=True):
        # there is restriciton to chars and length in/of vg name
        key= re.sub('[^0-9a-zA-Z]+', '_', ntpath.basename(rpmPath))
        if key in self.snapshots:
            outputControl.logging_access.LoggingAccess().log(rpmPath + " already extracted in snapshot. Rolling to " + key)
            return self.getSnapshot(key)
        else:
            outputControl.logging_access.LoggingAccess().log(rpmPath + " not extracted in snapshot. Creatign " + key)
            out, serr, res = self.importRpmCommand(rpmPath, resetBuildRoot)
            self.createSnapshot(key)
            self.snapshots[key] = rpmPath
            return out, serr, res

    def importRpmCommand(self, rpmPath, resetBuildRoot=True):
        """ Using various copy-in  variants have perofroamnce or existence issues at all """
        if (resetBuildRoot):
            DefaultMock().provideCleanUsefullRoot()
        out, serr, res = utils.process_utils.executeShell("rpm2cpio " + rpmPath + " | " + self.mainCommandAsString() + " --shell \"cpio -idmv\"")
        return out, serr, res

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
        # ibm plugin packages expect mozilla installed in the filesystem, this gives us directories neccessary
        self.mkdirP("/usr/lib64/mozilla")
        self.mkdirP("/usr/lib64/mozilla/plugins")
        self.mkdirP("/usr/lib/mozilla")
        self.mkdirP("/usr/lib/mozilla/plugins")
        # oracle plugin package expect these directories
        self.mkdirP("/usr/lib/jvm/jce-1.7.0-oracle")
        self.mkdirP("/usr/lib/jvm/jce-1.8.0-oracle")

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
        return self._rollbackCommand(name)

    def install_postscript(self, pkg):
        return self._install_scriptlet(pkg, utils.rpmbuild_utils.POSTINSTALL)

    def _install_scriptlet(self, pkg, scriptlet):
        scriptlet_pkg = str(scriptlet + "_"
                            + utils.pkg_name_split.get_subpackage_only(os.path.basename(pkg))
                            + "_"
                            + utils.pkg_name_split.get_arch(os.path.basename(pkg)))
        current, items = self.listSnapshots()
        if scriptlet_pkg in items:
            self.getSnapshot(scriptlet_pkg)
            return

        self.importRpm(pkg)
        content = utils.rpmbuild_utils.getSrciplet(pkg, scriptlet)
        if len(content) == 0:
            raise utils.mock.mock_execution_exception.MockExecutionException(scriptlet + " scriptlet not found in given package.")

        else:
            o, r = self.executeScriptlet(pkg, scriptlet)
            outputControl.logging_access.LoggingAccess().log(scriptlet + "returned " +
                                                             str(r) + " of " + os.path.basename(pkg))
            self.createSnapshot(scriptlet_pkg)

    def execute_ls(self, dir):
        return self.executeCommand(["ls " + dir])

    def execute_ls_for_alternatives(self):
        return self.execute_ls(ALTERNATIVES_DIR)

    def get_masters(self):
        otp, r = self.execute_ls_for_alternatives()
        masters = otp.split("\n")
        return masters

    def display_alternatives(self, master):
        output, r = self.executeCommand(["alternatives --display " + master])
        return output

    def parse_alternatives_display(self, master):
        output = self.display_alternatives(master)
        if len(output.strip()) == 0:
            outputControl.logging_access.LoggingAccess().log("alternatives --display master output is empty")
            raise utils.mock.mock_execution_exception.MockExecutionException("alternatives --display master "
                                                                             "output is empty ")
        data = {}
        otp = output.splitlines()
        data[PRIORITY]= otp[2].split(" ")[-1]
        if not data[PRIORITY].isdigit():
            raise ValueError("Priority must be digit-only.")
        data[STATUS] = otp[0].split(" ")[-1].strip(".")
        if FAMILY in otp[2]:
            data[FAMILY]= otp[2].split(" ")[3]
        else:
            data[FAMILY] = None
        data[TARGET] = otp[2].split(" ")[0]
        slaves = []
        for o in otp:
            if "slave" in o:
                slaves.append(o.split(" ")[2].strip(":"))
        data[SLAVES] = slaves
        return data

    def get_priority(self, master):
        return self.parse_alternatives_display(master)[PRIORITY]

    def get_status(self, master):
        return self.parse_alternatives_display(master)[STATUS]

    def get_family(self, master):
        return self.parse_alternatives_display(master)[FAMILY]

    def get_target(self, master):
        return self.parse_alternatives_display(master)[TARGET]

    def get_slaves(self, master):
        return self.parse_alternatives_display(master)[SLAVES]

    def get_default_masters(self):
        self.provideCleanUsefullRoot()
        return self.get_masters()

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
