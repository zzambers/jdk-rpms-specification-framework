""""Test whether the content of gc.dir is sane"""
import sys
import re
import config.general_parser
import config.runtime_config
import testcases.utils.base_test
import config.global_config as gc


class InitTest(testcases.utils.base_test.BaseTest):
    def test_java(self):
        java = config.runtime_config.RuntimeConfig().getRpmList().getJava()
        self.log("prefix is: " + java)
        assert java is not None

    def test_majorVersion(self):
        version = config.runtime_config.RuntimeConfig().getRpmList().getMajorVersion()
        self.log("Major version is: " + version)
        assert version is not None

    def test_majorVersionSimplified(self):
        version = config.runtime_config.RuntimeConfig().getRpmList().getMajorVersionSimplified()
        self.log("Major version simplified is: " + str(version))
        assert re.compile("[0-9]+").match(version) or version == gc.ITW

    def test_vendor(self):
        vendor = config.runtime_config.RuntimeConfig().getRpmList().getVendor()
        self.log("Vendor is: " + vendor)
        assert vendor is not None

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
        l=config.runtime_config.RuntimeConfig().getRpmList()
        self.log("Os: "+l.getOs())
        self.log("Version: " + l.getOsVersion())
        self.log("Version major: " + l.getOsVersionMajor())
        assert l.isFedora() | l.isRhel()
        assert l.isFedora() != l.isRhel()
        assert l.getOs() is not None
        assert l.getOsVersion() is not None
        assert l.getOsVersionMajor() is not None

def testAll():
    return InitTest().execute_tests()


def main(argv):
    testcases.utils.base_test.defaultMain(argv, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
