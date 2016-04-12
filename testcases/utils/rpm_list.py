import re
import ntpath
import testcases.utils.test_utils
from outputControl import logging_access
import testcases.utils.pkg_name_split as split
import config.global_config as gc


class RpmList:
    """Class to hold list of file, providing various operations abov themlike get bny arch, get by build (arch+noarch), get srpm and so on"""

    def __init__(self, ddir):
        self.files = testcases.utils.test_utils.get_rpms(ddir)
        self.topDirs = testcases.utils.test_utils.get_top_dirs(ddir)
        self.names = []
        for file in self.files:
            self.names.append(ntpath.basename(file))
        allFiles = testcases.utils.test_utils.get_files(ddir)
        logging_access.LoggingAccess().log("Loaded list of " + str(len(self.files)) + " rpms from  directory " + ddir)
        if len(self.files) != len(allFiles):
            logging_access.LoggingAccess().log("Warning, some files in  " + ddir + " - " + str(
                len(allFiles) - len(self.files)) + " are NOT rpms. Ignored")

    def getAllNames(self):
        if len(self.names) == 0:
            raise BaseException("No packages loaded")
        return self.names

    def getAllFiles(self):
        if len(self.files) == 0:
            raise BaseException("No packages loaded")
        return self.files

    # thsoe two methods are wierd, but most simpel way to recognize if one build is there, or if bre/koji task was downlaoded
    # single uild form mock have all rpms in singe directory
    # task is stored by archs - each arch is directory and have oe build (with exception of src.rpm and noarch whcih are in "theirs archs"
    def shouldBeBrewDownload(self):
        return len(self.topDirs) != 0

    def shouldBeSingleBuild(self):
        return len(self.topDirs) == 0

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
        return self.expectSingleMeberSet(split.get_major_ver, "version")

    def getMajorVersionSimplified(self):
        """Returns just number. instead of 1.7.1 or 1.8.0 return 7 or 8. Of course for 9 and more returns 9 and more"""
        vers = self.getMajorVersion()
        old_naming_regex = re.compile("^[0-9].[0-9].[0-9]$")
        if old_naming_regex.match(vers):
            return vers.split(".")[1]
        return vers

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

    def getPackages(self):
        """This method is misleading and is getting nothing saying set of pacakges"""
        pset, props = self.getSetProperty(split.get_package_name)
        return pset

    def getSubpackageOnly(self):
        """This method is misleading and is getting nothing saying set of sub-pacakges suffixes only"""
        pset, props = self.getSetProperty(split.get_subpackage_only)
        return pset

    def getAllArches(self):
        pset, props = self.getSetProperty(split.get_arch)
        return pset

    def getNativeArches(self):
        pset = self.getAllArches()
        return pset - set(gc.getNoarch()) - set(gc.getSrcrpmArch())

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
        paths = self.getPackagesByArch(gc.getSrcrpmArch()[0])
        if len(paths) == 0:
            return None
        if len(paths) == 1:
            return paths[0]
        raise Exception("None or one srpm can be in. Found " + str(len(paths)) + ":" + ",".join(paths))

    def getNoArchesPackages(self):
        paths = self.getPackagesByArch(gc.getNoarch()[0])
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
        return self.getDist().startswith("fc")

    def isRhel(self):
        return self.getDist().startswith("el")

    def getOs(self):
        if self.isFedora():
            return gc.FEDORA
        if self.isRhel():
            return gc.RHEL
        return None

    def getOsVersion(self):
        if self.isFedora():
            return self.getDist()[2:]
        if self.isRhel():
            return str(self.getDist()[2:]).replace("_",".")
        return None

    def getOsVersionMajor(self):
        return re.sub("\..*","",self.getOsVersion())

