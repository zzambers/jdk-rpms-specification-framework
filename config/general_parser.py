import argparse

import config.runtime_config


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def _createParser():
    lparser = argparse.ArgumentParser()
    lparser.add_argument("-v", "--version",
                         help="display the version of the framework",
                         action="store_true")
    lparser.add_argument("-o", "--docs",
                         help="instead fo testrun, generates documentation",
                         action="store_true")
    lparser.add_argument("-d", "--dir",
                         help="set directory where to search for rpms. Dir with rpm files only, "
                              "or subdirs - architectures, which each have its builds. Default: " + config.runtime_config.RuntimeConfig().getPkgsDir())
    lparser.add_argument("-l", "--logfile",
                         help="target file for verbose output. Default: " + config.runtime_config.RuntimeConfig().getLogsFile())
    return lparser


class GeneralParser(metaclass=Singleton):
    pass

    def __init__(self):
        self.parser = _createParser()
