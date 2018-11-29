import outputControl.file_log
from enum import Enum


class Verbosity(Enum):
    ERROR = 1
    TEST = 2
    JTREG = 3
    MOCK = 4


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class LoggingAccess(metaclass=Singleton):
    pass

    def stdout(self, arg2):
        print(arg2)
        self.log(arg2, Verbosity.ERROR)

    def log(self, logmsg, verbosity=Verbosity.TEST, jtregfilename=""):
        from config.runtime_config import RuntimeConfig
        if verbosity.value <= RuntimeConfig().get_verbosity().value:
            outputControl.file_log.FileLog().println(logmsg)
        if verbosity == verbosity.JTREG:
            if logmsg == "" and jtregfilename != "":
                outputControl.file_log.JtregLog().__init__(jtregfilename)
            else:
                outputControl.file_log.JtregLog(jtregfilename).println(logmsg)
        outputControl.file_log.DefaultLog().println(logmsg)

