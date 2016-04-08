import argparse


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GeneralParser(metaclass=Singleton):
    pass

    def _createParser(self):
        lparser = argparse.ArgumentParser()
        lparser.add_argument("-v", "--version",
                             help="display the version of the framework",
                             action="store_true")
        return lparser

    def __init__(self):
        self.parser = self._createParser()


