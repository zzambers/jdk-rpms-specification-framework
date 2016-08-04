import ntpath
import sys

import utils.pkg_name_split as split
from utils.core.configuration_specific import JdkConfiguration

import config.global_config as gc
import config.runtime_config
import outputControl.logging_access
import utils.core.base_xtest
import utils.core.unknown_java_exception as ex


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

class BaseSubpackages(MainPackagePresent):
    # providing just utility methods common for jdk packages
    def _subpkgsToString(self):
        return "`" + "`,`".join(set(
            self._getSubPackages())) + "`. Where `` is main package " + config.runtime_config.RuntimeConfig().getRpmList().getMajorPackage()

    def checkSubpackages(self, subpackages=None):
        rpms = config.runtime_config.RuntimeConfig().getRpmList()
        self._document(
            rpms.getVendor() + " should have exactly " + str(
                len(set(self._getSubPackages()))) + " subpackages: " + self._subpkgsToString())
        self._mainCheck(subpackages)


class DebugInfo(BaseSubpackages):
    def _getSubPackages(self):
        return super(DebugInfo, self)._getSubPackages() + ["debuginfo"]


class ItwSubpackages(DebugInfo):
    def _getSubPackages(self):
        return super(ItwSubpackages, self)._getSubPackages() + ["javadoc"]

    def checkSubpackages(self, subpackages=None):
        self._document("IcedTea-Web have exactly following subpackages: `" + "`,`".join(
            self._getSubPackages()) + "`. Where `` is main package " + gc.ITW)
        self._mainCheck(subpackages)


class Openjdk6(DebugInfo):
    def _getSubPackages(self):
        return super(Openjdk6, self)._getSubPackages() + self._getBasePackages()

    def _getBasePackages(self):
        return ['demo', 'devel', 'javadoc', 'src']


class Openjdk7(Openjdk6):
    def _getSubPackages(self):
        return super(Openjdk7, self)._getSubPackages() + self._getAdditionalPackages()

    def _getBasePackages(self):
        return super(Openjdk7, self)._getBasePackages() + self._getAdditionalPackages()

    def _getAdditionalPackages(self):
        return ['accessibility', 'headless']


class Openjdk8NoJit(Openjdk7):
    def _getBasePackages(self):
        return super(Openjdk8NoJit, self)._getBasePackages() + self._getJavadocZipPackage()

    def _getDebugPairs(self):
        return ["javadoc-debug", "javadoc-zip-debug"]  # this looks like error in engine

    def _getSubPackages(self):
        return super(Openjdk8NoJit, self)._getSubPackages() + self._getDebugPairs() + self._getJavadocZipPackage()

    def _getJavadocZipPackage(self):
        return ["javadoc-zip"]


class Openjdk8BaseJit(Openjdk8NoJit):
    def _getDebugPairs(self):
        r = ["debug"]  # main subpackage
        for base in self._getBasePackages():
            r.append(base + "-debug")
        return r


class Openjdk8NoJit25(Openjdk8NoJit):
    def _getBasePackages(self):
        return super(Openjdk8NoJit25, self)._getBasePackages() + self._getJavadocZipPackage()


class Openjdk8BaseJit25(Openjdk8BaseJit):
    def _getBasePackages(self):
        return super(Openjdk8BaseJit25, self)._getBasePackages() + self._getJavadocZipPackage()


class IbmBase(BaseSubpackages):
    def _getSubPackages(self):
        return super(IbmBase, self)._getSubPackages() + ["demo", "devel", "jdbc", "src"]

    def _getJavacommPkg(self):
        return ["javacomm"]


class IbmAddPlugin(IbmBase):
    def _getSubPackages(self):
        return super(IbmAddPlugin, self)._getSubPackages() + ["plugin"]


class IbmAddJavacommWithPlugin(IbmAddPlugin):
    def _getSubPackages(self):
        return super(IbmAddJavacommWithPlugin, self)._getSubPackages() + self._getJavacommPkg()


class IbmAddJavacommNoPlugin(IbmBase):
    def _getSubPackages(self):
        return super(IbmAddJavacommNoPlugin, self)._getSubPackages() + self._getJavacommPkg()


class OracleBase(BaseSubpackages):
    def _getSubPackages(self):
        return super(OracleBase, self)._getSubPackages() + ['devel', 'jdbc', 'plugin', 'src']


class Oracle7and8(OracleBase):
    def _getSubPackages(self):
        return super(Oracle7and8, self)._getSubPackages() + ['javafx']


class Oracle6(OracleBase):
    def _getSubPackages(self):
        return super(Oracle6, self)._getSubPackages() + ['demo']


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
            if rpms.getMajorVersionSimplified() == '6':
                self.csch = Openjdk6()
                return
            elif rpms.getMajorVersionSimplified() == '7':
                self.csch = Openjdk7()
                return
            else:
                if self.getCurrentArch() in (gc.getIx86archs() + gc.getX86_64Arch()):
                    self.csch = Openjdk8BaseJit()
                    return
                else:
                    self.csch = Openjdk8NoJit()
                    return

        if rpms.getVendor() == gc.IBM and rpms.isRhel():
            if rpms.getMajorVersionSimplified() == '6':
                if self.getCurrentArch() in (gc.getX86_64Arch() + gc.getIx86archs() + gc.getPpc32Arch()):
                    self.csch = IbmAddJavacommWithPlugin()
                    return
                elif self.getCurrentArch() in gc.getPower64Achs():
                    self.csch = IbmAddJavacommNoPlugin()
                    return
                else:
                    self.csch = IbmBase()
                    return

            elif rpms.getMajorVersionSimplified() =='7':
                if self.getCurrentArch() in (gc.getX86_64Arch() + gc.getIx86archs()) + gc.getPpc32Arch():
                    self.csch = IbmAddPlugin()
                    return
                else:
                    self.csch = IbmBase()
                    return

            else:
                if self.getCurrentArch() in (gc.getX86_64Arch() + gc.getIx86archs()) \
                        + gc.getPpc32Arch() + gc.getPower64BeAchs():
                    self.csch = IbmAddPlugin()
                    return
                else:
                    self.csch = IbmBase()
                    return

        if rpms.getVendor() == gc.ORACLE and rpms.isRhel():
            self.csch = Oracle7and8()
            return

        if rpms.getVendor() == "sun" and rpms.isRhel():
            self.csch = Oracle6()
            return


        self.csch = None
        raise ex.UnknownJavaVersionException("Java version or OS was not recognized by this framework.")



def testAll():
    return SubpackagesTest().execute_tests()


def documentAll():
    outputControl.logging_access.LoggingAccess().stdout("Subpackages are as expected")
    return SubpackagesTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
