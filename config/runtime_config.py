import outputControl.logging_access
import testcases.utils.rpm_list

VERSION_STRING = "jdks_specification_framework, version 0.1"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RuntimeConfig(metaclass=Singleton):
    pass;

    def __init__(self):
        self.pkgsDir = "rpms"
        self.logsFile = "jsf.log"
        self.rpmList = None

    def getRpmList(self):
        if self.rpmList == None:
            self.rpmList = testcases.utils.rpm_list.RpmList(self.getPkgsDir())
        return self.rpmList

    def setLogsFile(self, nwFile):
        oldValue = self.logsFile;
        self.logsFile = nwFile
        outputControl.logging_access.LoggingAccess().log("Logfile set to " + nwFile + " instead of " + oldValue)

    def getLogsFile(self):
        return self.logsFile;

    def setPkgsDir(self, nwDir):
        outputControl.logging_access.LoggingAccess().log("Rpms looked for in " + nwDir + " instead of " + self.pkgsDir)
        self.pkgsDir = nwDir

    def getPkgsDir(self):
        return self.pkgsDir;

    def setFromParser(self, args):
        # logfile must go first
        if args.logfile:
            self.setLogsFile(args.logfile)
        if args.version:
            outputControl.logging_access.LoggingAccess().stdout(VERSION_STRING)
            return False;
        # later it does not meter
        outputControl.logging_access.LoggingAccess().log(VERSION_STRING)
        if args.dir:
            self.setPkgsDir(args.dir)
        return True
