import config.global_config
import outputControl.logging_access
import utils.build_downloader

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
        self.docs = False
        self.header= True
        self.archs = None

    def getRpmList(self):
        if self.rpmList == None:
            self.rpmList = utils.rpm_list.RpmList(self.getPkgsDir())
        return self.rpmList

    def setLogsFile(self, nwFile):
        oldValue = self.logsFile
        self.logsFile = nwFile
        outputControl.logging_access.LoggingAccess().log("Logfile set to " + nwFile + " instead of " + oldValue)

    def getLogsFile(self):
        return self.logsFile

    def getDocs(self):
        return self.docs

    def isHeader(self):
        return self.header

    def setPkgsDir(self, nwDir):
        outputControl.logging_access.LoggingAccess().log("Rpms looked for in " + nwDir + " instead of " + self.pkgsDir)
        self.pkgsDir = nwDir

    def getPkgsDir(self):
        return self.pkgsDir

    def setArchs(self, archString):
        if archString == "all":
            self.archs = config.global_config.getAllArchs()
        else:
            words = archString.split(",")
            self.archs= words
        outputControl.logging_access.LoggingAccess().log("archs limited/forced to " + str(self.archs))


    def getArchs(self):
        return self.archs

    def setFromParser(self, args):
        # Order matters a lot!
        # logfile must go first
        if args.logfile:
            self.setLogsFile(args.logfile)
        if args.version:
            outputControl.logging_access.LoggingAccess().stdout(VERSION_STRING)
            return False
        # later it does not matter as logging is already going to log file
        outputControl.logging_access.LoggingAccess().log(VERSION_STRING)
        # switches should go before commands, so commands can use them
        if args.dir:
            self.setPkgsDir(args.dir)
        if args.archs:
            self.setArchs(args.archs)
        if args.build:
            r = utils.build_downloader.getBuild(args.build)
            # failed? exit...
            if not r:
                return False
        if args.docs:
            # no setter - should not be set from outside
            self.docs = True
        if args.noheader:
            # no setter - should not be set from outside
            self.header = False
        return True
