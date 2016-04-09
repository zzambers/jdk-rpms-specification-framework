from subprocess import Popen, PIPE

import outputControl.logging_access


# TODO add here generated / vendor specific / list or dictionary of possible subpkg names


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Some arches have more then one varint. rpmbuild  is keeping en eye on this so currently known trouble makers are --eval there.
# power64 arm ix86
class DynamicArches(metaclass=Singleton):
    pass;

    def __init__(self):
        self.arm32 = None
        self.ix86 = None
        self.power64 = None

    def getDynamicArches(self, arch):
        outputControl.logging_access.LoggingAccess().log("Getting dynamic arches for: " + arch)
        proc = Popen(['rpmbuild', '--eval', '%{' + arch + '}'], stdout=PIPE)
        out, err = proc.communicate()
        output = out.decode('utf-8').strip()  # utf-8 works in your case
        outputControl.logging_access.LoggingAccess().log("got: " + output)
        li = output.split(" ")
        for i in range(len(li)):
            li[i] = li[i].strip();
        return li

    def getArm32Achs(self):
        if (self.arm32 == None):
            self.arm32 = self.getDynamicArches("arm")
        return self.arm32

    def getIx86Archs(self):
        if (self.ix86 == None):
            self.ix86 = self.getDynamicArches("ix86")
        return self.ix86

    def getPower64Achs(self):
        if (self.power64 == None):
            self.power64 = self.getDynamicArches("power64")
        return self.power64


def getArm32Achs():
    # return ["armv7hl"]
    return DynamicArches().getArm32Achs()


def getPower64Achs():
    # return ["ppc64"]
    return DynamicArches().getPower64Achs()


def getIx86archs():
    # return ["i386", "i686"]
    return DynamicArches().getIx86Archs()

def getHardcodedArchs():
    return ["x86_64", "ppc", "ppc64le", "s390", "s390x", "aarch64"]

def getGeneratedArchs():
    return getIx86archs() + getPower64Achs() + getArm32Achs()

def getArchs():
    return getHardcodedArchs() + getGeneratedArchs()


def getAllArchs():
    return getArchs() + getNoarch() + getSrcrpmArch()


def getNoarch():
    return ["noarch"]


def getSrcrpmArch():
    return ["src"]


JAVA_STRING = "java"

LIST_OF_POSSIBLE_VENDORS = ["ibm", "oracle", "openjdk"]
LIST_OF_POSSIBLE_VERSIONS = ["1.6.0", "1.7.0", "1.8.0", "9" ]
