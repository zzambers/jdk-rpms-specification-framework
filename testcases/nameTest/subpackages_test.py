import ntpath
import sys

import utils.pkg_name_split as split
from utils.core.configuration_specific import JdkConfiguration

import config.global_config as gc
import config.runtime_config
import outputControl.logging_access
import utils.core.base_xtest


class MainPackagePresent(JdkConfiguration):
    def _getSubPackages(self):
        return [""]

    def _mainCheck(self, subpkgs):
        expectedList = self._getSubPackages()
        subpkgSetExpected= sorted(set(expectedList))
        ssGiven = sorted(set(subpkgs))
        SubpackagesTest.hack.log("Checking number of subpackages " + str(len(ssGiven)) + " of " + SubpackagesTest.hack.current_arch + " against " + str(len(subpkgSetExpected)))
        SubpackagesTest.hack.log("Presented: " + str(ssGiven))
        SubpackagesTest.hack.log("Expected:  " + str(subpkgSetExpected))
        assert len(ssGiven) == len(subpkgSetExpected)
        for subpkg in subpkgSetExpected:
            SubpackagesTest.hack.log(
                "Checking `" + subpkg + "` of " + SubpackagesTest.hack.current_arch)
            assert subpkg in subpkgSetExpected


class DebugInfo(MainPackagePresent):
    def _getSubPackages(self):
        return super(DebugInfo, self)._getSubPackages() + ["debuginfo"]


class ItwSubpackages(DebugInfo):
    def _getSubPackages(self):
        return super(ItwSubpackages, self)._getSubPackages() + ["javadoc"]

    def checkSubpackages(self, subpackages=None):
        self._document("IcedTea-Web have exactly following subpackages: `" + "`,`".join(
            self._getSubPackages()) + "`. Where `` is main package " + gc.ITW)
        self._mainCheck(subpackages)


class BaseJdkSubpackages(DebugInfo):
    #providing just utility methods common for jdk packages
    def _subpkgsToString(self):
        return "`" + "`,`".join(set(self._getSubPackages())) + "`. Where `` is main package " + config.runtime_config.RuntimeConfig().getRpmList().getMajorPackage()

    def checkSubpackages(self, subpackages=None):
        self._document(
            "Jdk should have exactly " + str(len(set(self._getSubPackages()))) + " subpackages: " + self._subpkgsToString())
        self._mainCheck(subpackages)


class Openjdk8NoJit(BaseJdkSubpackages):
    def _getBasePackages(self):
        return [
            "accessibility",
            "demo",
            "devel",
            "headless",
            "javadoc",
            "src"]

    def _getDebugPairs(self):
        return ["javadoc-debug"] #this looks like error in engine

    def _getSubPackages(self):
        return super(Openjdk8NoJit, self)._getSubPackages() + self._getBasePackages() + self._getDebugPairs()


class Openjdk8BaseJit(Openjdk8NoJit):
    def _getDebugPairs(self):
        r = ["debug"]  # main subpackage
        for base in self._getBasePackages():
            r.append(base + "-debug")
        return r

class Openjdk8NoJit25(Openjdk8NoJit):
    def _getBasePackages(self):
        return super(Openjdk8NoJit25, self)._getBasePackages() + ["javadoc-zip"]

    def _getDebugPairs(self):
        return ["javadoc-debug", "javadoc-zip-debug"]  # this looks like error in engine


class Openjdk8BaseJit25(Openjdk8BaseJit):
    def _getBasePackages(self):
        return super(Openjdk8BaseJit25, self)._getBasePackages() + ["javadoc-zip"]


class GenericJdk(BaseJdkSubpackages):
    def _getSubPackages(self):
        return super(GenericJdk, self)._getSubPackages() + ["devel"]


class SubpackagesTest(utils.core.base_xtest.BaseTest):
    hack = None

    def test_checkAllSubpackages(self):
        rpms = self.getBuild()
        assert rpms is not None
        assert len(rpms) > 1
        subpackages = []
        for rpm in rpms:
            subpackages.append(split.get_subpackage_only(ntpath.basename(rpm)))
        self.csch.checkSubpackages(subpackages)

    def setCSCH(self):
        SubpackagesTest.hack = self
        rpms = config.runtime_config.RuntimeConfig().getRpmList()
        if rpms.getJava() == gc.ITW:
            self.csch = ItwSubpackages()
            return
        if rpms.getVendor() == gc.OPENJDK and rpms.isFedora():
            if self.getCurrentArch() in gc.getArm32Achs():
                if rpms.getOsVersionMajor() > 24:
                    self.csch = Openjdk8NoJit25()
                    return
                else:
                    self.csch = Openjdk8NoJit()
                    return
            else:
                if rpms.getOsVersionMajor() > 24:
                    self.csch = Openjdk8BaseJit25()
                    return
                else:
                    self.csch = Openjdk8BaseJit()
                    return
        if rpms.getVendor() == gc.OPENJDK and rpms.isRhel():
            self.csch = Openjdk8BaseJit()
            return
        self.csch = GenericJdk()


def testAll():
    return SubpackagesTest().execute_tests()


def documentAll():
    outputControl.logging_access.LoggingAccess().stdout("Subpackages are as expected")
    return SubpackagesTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
