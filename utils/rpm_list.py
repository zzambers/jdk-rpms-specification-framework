import ntpath
import re
from utils import pkg_name_split as ns
import config.global_config
import config.runtime_config
from outputControl import logging_access as la
from utils import pkg_name_split as split
import utils.test_utils
import utils.test_constants



class RpmList:
    """Class to hold list of file, providing various operations above them like get any arch, get by build (arch+noarch)
    , get srpm and so on"""

    def __init__(self, ddir):
        self.files = utils.test_utils.get_rpms(ddir)
        self.topDirs = utils.test_utils.get_top_dirs(ddir)
        self.names = []
        for file in self.files:
            name = ntpath.basename(file)
            for part in utils.test_constants.IGNOREDNAMEPARTS:
                name = name.replace(part, "")
            self.names.append(name)
        allFiles = utils.test_utils.get_files(ddir)
        la.LoggingAccess().log("Loaded list of " + str(len(self.files)) + " rpms from  directory " + ddir,
                               la.Verbosity.TEST)
        if len(self.files) != len(allFiles):
            la.LoggingAccess().log("Warning, some files in  " + ddir + " - " + str(
                len(allFiles) - len(self.files)) + " are NOT rpms. Ignored", la.Verbosity.TEST)

    def getAllNames(self):
        if len(self.names) == 0:
            raise BaseException("No packages loaded")
        return self.names

    def getAllFiles(self):
        if len(self.files) == 0:
            raise BaseException("No packages loaded")
        return self.files

    def shouldBeBrewDownload(self):
        return len(self.getNativeArches()) != 1

    def shouldBeSingleBuild(self):
        return len(self.getNativeArches()) == 1

    def getSetProperty(self, function):
        props = []
        for n in self.names:
            props.append(function(n))
        return set(props), props

    def expectSingleMeberSet(self, function, pname):
        pset, props = self.getSetProperty(function)
        if len(pset) == 0:
            raise Exception("No " + pname + " found")
        if len(pset) != 1:
            raise Exception("Expected only one " + pname + " - found: " + ",".join(pset))
        return props[0]

    def getMajorVersion(self):
        return ns.simplify_new_version(".".join(self.getVersion().split(".")[:3]))

    def getMajorVersionSimplified(self):
        """Returns just number. instead of 1.7.1 or 1.8.0 return 7 or 8. Of course for 9 and more returns 9 and more"""
        vers = self.getMajorVersion()
        return ns.simplify_version(vers)

    def getDebugSuffix(self):
        for file in self.files:
            if "-slowdebug" in file:
                return "-slowdebug"
        for file in self.files:
            if "-debug" in file:
                return "-debug"
        return "-sethasnodebugsuffix"

    def getJava(self):
        return self.expectSingleMeberSet(split.get_javaprefix, "java prefix")

    def getVendor(self):
        return self.expectSingleMeberSet(split.get_vendor, "vendor")

    def getMajorPackage(self):
        return self.expectSingleMeberSet(split.get_major_package_name, "major package")

    def getVersion(self):
        return self.expectSingleMeberSet(split.get_minor_ver, "version")

    def getRelease(self):
        return self.expectSingleMeberSet(split.get_release, "release")

    def getDist(self):
        return self.expectSingleMeberSet(split.get_dist, "dist")

    def getNvr(self):
        return self.expectSingleMeberSet(split.get_name_version_release, "name version release")

    def getPackages(self):
        """This method is misleading and is getting nothing saying set of packages"""
        pset, props = self.getSetProperty(split.get_package_name)
        return pset

    def getSubpackageOnly(self):
        """This method is misleading and is getting nothing saying set of sub-pacakges suffixes only"""
        pset, props = self.getSetProperty(split.get_subpackage_only)
        return pset

    def getAllArches(self):
        if config.runtime_config.RuntimeConfig().getArchs() is not None:
            return set(config.runtime_config.RuntimeConfig().getArchs())
        pset, props = self.getSetProperty(split.get_arch)
        return pset

    def getNativeArches(self):
        if config.runtime_config.RuntimeConfig().getArchs() is not None:
            return set(utils.test_utils.removeNoarchSrpmArch(config.runtime_config.RuntimeConfig().getArchs()))
        pset, props = self.getSetProperty(split.get_arch)
        return pset - set(config.global_config.getNoarch()) - set(config.global_config.getSrcrpmArch())

    def getRealNativeArches(self):
        pset, props = self.getSetProperty(split.get_arch)
        return pset - set(config.global_config.getNoarch()) - set(config.global_config.getSrcrpmArch())

    def getPackagesByArch(self, arch):
        filepaths = []
        names = []
        for idx, val in enumerate(self.files):
            if split.get_arch(self.names[idx]) == arch:
                filepaths.append(val)
                names.append(self.names[idx])
        if len(set(names)) != len(names):
            raise Exception("Some files are duplicated for given arch")
        return filepaths

    def getSrpm(self):
        paths = self.getPackagesByArch(config.global_config.getSrcrpmArch()[0])
        if len(paths) == 0:
            return None
        if len(paths) == 1:
            return paths[0]
        raise Exception("None or one srpm can be in. Found " + str(len(paths)) + ":" + ",".join(paths))

    def getNoArchesPackages(self):
        paths = self.getPackagesByArch(config.global_config.getNoarch()[0])
        return paths

    def getBuildWithoutSrpm(self, arch):
        return self.getPackagesByArch(arch) + self.getNoArchesPackages()

    def getCompleteBuild(self, arch):
        srpm = self.getSrpm()
        if srpm is None:
            return self.getBuildWithoutSrpm(arch)
        bb = self.getBuildWithoutSrpm(arch)
        bb.append(srpm)
        return bb

    def isFedora(self):
        return isFedora(self.getDist())

    def isItw(self):
        return isItw(self.getJava())

    def isRhel(self):
        return isRhel(self.getDist())

    def isEpel(self):
        return isEpel(self.getDist())

    def getOs(self):
        return getOs(self.getDist())

    def getOsVersion(self):
        if self.isFedora():
            return self.getDist()[2:]
        if self.isRhel():
            return str(self.getDist()[2]).replace("_",".")
        if self.isEpel():
            return str(self.getDist()[4:]).replace("_",".")
        return None

    def getOsVersionMajor(self):
        os = self.getOsVersion()
        return int(re.sub("\..*","", os))

    def getRpmWholeName(self, pkg, arch):
        defaultrpm = "nonexistent"
        for rpm in self.getPackagesByArch(arch):
            if ns.get_subpackage_only(rpm) == "":
                defaultrpm = rpm
            if pkg in rpm and not pkg + utils.test_constants.get_debug_suffix() in rpm:
                return rpm
        return defaultrpm.replace("rpms/", "")


def isFedora(dist):
    return dist.startswith("fc")


def isRhel(dist):
    return dist.startswith("el")


def isEpel(dist):
    return dist.startswith("epel")


def isItw(dist):
    return dist == config.global_config.ITW


def getOs(dist):
    if isFedora(dist):
        return config.global_config.FEDORA
    if isRhel(dist) or isEpel(dist):
        return config.global_config.RHEL
    return None
