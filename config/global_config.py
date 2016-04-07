# TODO add here generated / vendor specific / list or dictionary of possible subpkg names

# TODO get this list by rpmbuild --eval power64 arm ix86


def getArm32Achs():
    return ["armv7hl"]


def getPower64Achs():
    return ["ppc64"]


def getIx86archs():
    return ["i386", "i686"]


def getArchs():
    return ["x86_64", "ppc", "ppc64le", "s390", "s390x", "aarch64"] + getIx86archs() + getPower64Achs() + getArm32Achs()


def getAllArchs():
    return getArchs() + getNoarch() + getSrcrpmArch()


def getNoarch():
    return ["noarch"]


def getSrcrpmArch():
    return ["src"]


JAVA_STRING = "java"

LIST_OF_POSSIBLE_VENDORS = ["ibm", "oracle", "openjdk"]
