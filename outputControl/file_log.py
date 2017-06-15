import datetime as dt

import config.runtime_config


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class FileLog(metaclass=Singleton):
    pass

    def __init__(self):
        self.target = open(config.runtime_config.RuntimeConfig().getLogsFile(), 'w')
        self.println("#" + dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))

    def println(self, arg2):
        self.target.write(arg2)
        self.target.write("\n")
        self.target.flush()


class DefaultLog(metaclass=Singleton):
    def __init__(self):
        self.target = open("verbose_log_file.log", 'w')
        self.println("#" + dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))

    def println(self, arg2):
        self.target.write(arg2)
        self.target.write("\n")
        self.target.flush()


