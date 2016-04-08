from outputControl.file_log import FileLog


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
        FileLog().println(arg2)


    def log(self, arg2):
        FileLog().println(arg2)
