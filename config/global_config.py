import outputControl.logging_access
from utils import rpmbuild_utils

# The get_methods nor find_on_disc are order-granting. However they seems to be sorted... Sometimes. So this switch will ensure it.

leSort = True


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Some arches have more then one varint. rpmbuild  is keeping an eye on this so currently known trouble makers are --eval there.
# power64 arm ix86
class DynamicArches(metaclass=Singleton):
    pass;

    def __init__(self):
        self.arm32 = None
        self.ix86 = None
        self.power64 = None

    def getDynamicArches(self, arch):
        outputControl.logging_access.LoggingAccess().log("Getting dynamic arches for: " + arch)
        output= rpmbuild_utils.rpmbuildEval(arch)
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

    def getPower64BeAchs(self):
        achs = []
        for arch in self.getPower64Achs():
            if not 'le' in arch:
                achs.append(arch)
        return achs

    def getPower64LeAchs(self):
        achs = []
        for arch in self.getPower64Achs():
            if 'le' in arch:
                achs.append(arch)
                return achs

def getArm32Achs():
    # return ["armv7hl"]
    return DynamicArches().getArm32Achs()


def getPower64LeAchs():
    # return ["ppc64le"]
    return DynamicArches().getPower64LeAchs()


def getPower64BeAchs():
    # return ["ppc64","ppc64p7"]
    return DynamicArches().getPower64BeAchs()


def getPower64Achs():
    # return ["ppc64","ppc64p7","ppc64le"]
    return DynamicArches().getPower64Achs()


def getIx86archs():
    # return ["i386", "i686"]
    return DynamicArches().getIx86Archs()


def getHardcodedArchs():
    return getX86_64Arch() + getPpc32Arch() + getS390Arch() + getS390xArch() + getAarch64Arch()


def getGeneratedArchs():
    return getIx86archs() + getPower64Achs() + getArm32Achs() + getPower64LeAchs()


def getArchs():
    return getHardcodedArchs() + getGeneratedArchs()


def getAllArchs():
    return getArchs() + getNoarch() + getSrcrpmArch()


def getNoarch():
    return ["noarch"]


def getSrcrpmArch():
    return ["src"]


def getX86_64Arch():
    return ["x86_64"]


def getPpc32Arch():
    return ["ppc"]


def getS390Arch():
    return ["s390"]


def getS390xArch():
    return ["s390x"]


def getAarch64Arch():
    return ["aarch64"]


JAVA_STRING = "java"

FEDORA = "Fedora"
RHEL = "RHEL"

OPENJDK = "openjdk"
ITW = "icedtea-web"
IBM = "ibm"
ORACLE = "oracle"

LIST_OF_PROPRIETARY_VENDORS = [IBM, ORACLE]
LIST_OF_OPEN_VENDORS_EXCEPT_ITW = [OPENJDK]
LIST_OF_OPEN_VENDORS = LIST_OF_OPEN_VENDORS_EXCEPT_ITW + [ITW]
LIST_OF_POSSIBLE_VENDORS = LIST_OF_PROPRIETARY_VENDORS + LIST_OF_OPEN_VENDORS
LIST_OF_POSSIBLE_VENDORS_WITHOUT_ITW = LIST_OF_PROPRIETARY_VENDORS + LIST_OF_OPEN_VENDORS_EXCEPT_ITW
LIST_OF_LEGACY_VERSIONS = ["1.6.0", "1.7.0", "1.8.0"]
LIST_OF_NEW_VERSIONS = ["9"]
LIST_OF_POSSIBLE_VERSIONS = [ITW] + LIST_OF_LEGACY_VERSIONS + LIST_OF_NEW_VERSIONS
LIST_OF_POSSIBLE_VERSIONS_WITHOUT_ITW = LIST_OF_LEGACY_VERSIONS + LIST_OF_NEW_VERSIONS
