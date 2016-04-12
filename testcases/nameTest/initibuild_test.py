""""Test whether the content of gc.dir is sane"""
import re
import sys

import config.general_parser
import config.global_config as gc
import config.runtime_config
import testcases.utils.base_xtest
from outputControl import logging_access as la
from testcases.utils.configuration_specific import JdkConfiguration


class InitTestSpecialChecks(JdkConfiguration):
    pass


class ItwVersionCheck(InitTestSpecialChecks):

    def checkMajorVersionSimplified(self, version=None):
        self._document("IcedTea-Web do not have any version contained in name.")
        la.LoggingAccess().log("ITW special call for checkMajorVersionSimplified")
        assert version == gc.ITW

    def checkMajorVersion(self, version=None):
        self.checkMajorVersionSimplified(version)

    def checkPrefix(self, version=None):
        self._document("IcedTea-Web do not have any prefix-based name. It is just " + gc.ITW + ".")
        la.LoggingAccess().log("ITW special call for checkPrefix")
        assert version == gc.ITW

    def checkVendor(self, vendor=None):
        self._document("IcedTea-Web do not have any vendor in name. It is just " + gc.ITW + ".")
        la.LoggingAccess().log("ITW special call for checkVendor")
        assert vendor == gc.ITW

class OthersVersionCheck(InitTestSpecialChecks):

    def checkMajorVersionSimplified(self, version=None):
        self._document(
            "All jdsk (except icedtea-web) have major version in name. eg: java-1.8.0-openjdk or java-9-oracle." \
            " For legacy JDK (like jdk 1.6.0 or 1.7.1) the major version is included as middle number." \
            " For modern jdks (jdk 9+)  the major version is just plain number. Eg.: java-9-ibm."
            " The extracted middle number *is* number")
        la.LoggingAccess().log("non itw call for checkMajorVersionSimplified")
        assert re.compile("[0-9]+").match(version)
        assert int(version) > 0

    def checkMajorVersion(self, version=None):
        self._document("The version string in middle of package name is one of: " + ",".join(
            gc.LIST_OF_POSSIBLE_VERSIONS_WITHOUT_ITW))
        assert version in gc.LIST_OF_POSSIBLE_VERSIONS_WITHOUT_ITW

    def checkPrefix(self, version=None):
        self._document("prefix of each java package is " + gc.JAVA_STRING + ".")
        la.LoggingAccess().log("non itw call for checkPrefix")
        assert version == gc.JAVA_STRING

    def checkVendor(self, vendor=None):
        self._document("The vendor string, suffix of package name is one of: " + ",".join(
            gc.LIST_OF_POSSIBLE_VENDORS_WITHOUT_ITW))
        la.LoggingAccess().log("non itw call for checkVendor")
        assert vendor in gc.LIST_OF_POSSIBLE_VENDORS_WITHOUT_ITW

class InitTest(testcases.utils.base_xtest.BaseTest):
    def test_java(self):
        java = config.runtime_config.RuntimeConfig().getRpmList().getJava()
        self.log("prefix is: " + java)
        assert java is not None
        self.csch.checkPrefix(java)

    def test_majorVersion(self):
        version = config.runtime_config.RuntimeConfig().getRpmList().getMajorVersion()
        self.log("Major version is: " + version)
        assert version is not None
        self.csch.checkMajorVersion(version)

    def test_majorVersionSimplified(self):
        version = config.runtime_config.RuntimeConfig().getRpmList().getMajorVersionSimplified()
        self.log("Major version simplified is: " + str(version))
        assert version is not None
        self.csch.checkMajorVersionSimplified(version)

    def test_vendor(self):
        vendor = config.runtime_config.RuntimeConfig().getRpmList().getVendor()
        self.log("Vendor is: " + vendor)
        assert vendor is not None
        self.csch.checkVendor(vendor)

    def test_package(self):
        pkgs = config.runtime_config.RuntimeConfig().getRpmList().getPackages()
        self.log("Found pacakges are: " + ",".join(pkgs))
        assert len(pkgs) > 0

    def test_majorPackage(self):
        java = config.runtime_config.RuntimeConfig().getRpmList().getMajorPackage()
        self.log("Package is: " + java)
        assert java is not None

    def test_subpackage(self):
        subpkgs = config.runtime_config.RuntimeConfig().getRpmList().getSubpackageOnly()
        self.log("found subpackages only are: `" + "`,`".join(subpkgs) + "`")
        assert len(subpkgs) > 0

    def test_version(self):
        java = config.runtime_config.RuntimeConfig().getRpmList().getVersion()
        self.log("Version is: " + java)
        assert java is not None

    def test_release(self):
        java = config.runtime_config.RuntimeConfig().getRpmList().getRelease()
        self.log("Release is: " + java)
        assert java is not None

    def test_dist(self):
        java = config.runtime_config.RuntimeConfig().getRpmList().getDist()
        self.log("Dist is: " + java)
        assert java is not None

    def test_arches(self):
        arches = config.runtime_config.RuntimeConfig().getRpmList().getAllArches()
        self.log("All arches are: " + ",".join(arches))
        assert len(arches) > 1

    def test_nativeArches(self):
        nativeArches = config.runtime_config.RuntimeConfig().getRpmList().getNativeArches()
        self.log("All native arches: " + ",".join(nativeArches))
        assert len(nativeArches) > 0

    def test_srpmPackage(self):
        srpm = config.runtime_config.RuntimeConfig().getRpmList().getSrpm()
        self.log("SrcRpm: " + str(srpm))
        # no assert, it can be None or exactly one file. On anything else getSrpm should throw exception

    def test_noarchesPackages(self):
        noarches = config.runtime_config.RuntimeConfig().getRpmList().getNoArchesPackages()
        self.log("all no arches packages are: ")
        for pkg in noarches:
            self.log("  " + pkg)
        assert len(noarches) > 0

    def test_nativeArchesPackages(self):
        nativeArches = config.runtime_config.RuntimeConfig().getRpmList().getNativeArches()
        for na in nativeArches:
            arches = config.runtime_config.RuntimeConfig().getRpmList().getPackagesByArch(na)
            self.log("all " + na + " packages are: ")
            for pkg in arches:
                self.log("  " + pkg)
            assert len(arches) > 0

    def test_builds(self):
        nativeArches = config.runtime_config.RuntimeConfig().getRpmList().getNativeArches()
        for na in nativeArches:
            arches = config.runtime_config.RuntimeConfig().getRpmList().getBuildWithoutSrpm(na)
            self.log("build for " + na + " without srpm: ")
            for pkg in arches:
                self.log("  " + pkg)
            assert len(arches) > 0

    def test_completeBuilds(self):
        nativeArches = config.runtime_config.RuntimeConfig().getRpmList().getNativeArches()
        for na in nativeArches:
            arches = config.runtime_config.RuntimeConfig().getRpmList().getCompleteBuild(na)
            self.log("build for " + na + ": ")
            for pkg in arches:
                self.log("  " + pkg)
            assert len(arches) > 0

    def test_os(self):
        l = config.runtime_config.RuntimeConfig().getRpmList()
        self.log("Os: " + l.getOs())
        self.log("Version: " + l.getOsVersion())
        self.log("Version major: " + l.getOsVersionMajor())
        assert l.isFedora() | l.isRhel()
        assert l.isFedora() != l.isRhel()
        assert l.getOs() is not None
        assert l.getOsVersion() is not None
        assert l.getOsVersionMajor() is not None

    def setCSCH(self):
        if config.runtime_config.RuntimeConfig().getRpmList().getJava() == gc.ITW:
            self.log("Set ItwVersionCheck")
            self.csch = ItwVersionCheck()
        else:
            self.log("Set OthersVersionCheck")
            self.csch = OthersVersionCheck()


def testAll():
    return InitTest().execute_tests()


def documentAll():
    return InitTest().execute_special_docs()


def main(argv):
    testcases.utils.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
