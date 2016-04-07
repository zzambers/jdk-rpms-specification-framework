import datetime as dt


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class FileLog:
    target = None;

    def __init__(self):
        self.target = open("jsf.log", 'w');
        self.println("#" + dt.datetime.today().strftime("%Y-%m-%d %H:%m:%S"))

    def println(self, arg2):
        self.target.write(arg2)
        self.target.write("\n")
