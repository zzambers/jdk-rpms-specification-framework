import ntpath
import sys

from utils.core.configuration_specific import JdkConfiguration
import config.global_config as gc
import config.runtime_config
import outputControl.logging_access
import utils.core.base_xtest
import utils.core.unknown_java_exception as ex
from utils.test_constants import *
from outputControl import logging_access as la
from utils import pkg_name_split as split


class MainPackagePresent(JdkConfiguration):
    def _getSubPackages(self):
        return [""]

    def _mainCheck(self, subpkgs):
        expectedList = self._getSubPackages()
        subpkgSetExpected= sorted(set(expectedList))
        ssGiven = sorted(set(subpkgs))
        SubpackagesTest.instance.log("Checking number of subpackages " + str(len(ssGiven)) +
                                     " of " + SubpackagesTest.instance.current_arch + " against "
                                     + str(len(subpkgSetExpected)), la.Verbosity.TEST)
        SubpackagesTest.instance.log("Presented: " + str(ssGiven), la.Verbosity.TEST)
        SubpackagesTest.instance.log("Expected:  " + str(subpkgSetExpected), la.Verbosity.TEST)
        assert len(ssGiven) == len(subpkgSetExpected)
        for subpkg in subpkgSetExpected:
            SubpackagesTest.instance.log(
                "Checking `" + subpkg + "` of " + SubpackagesTest.instance.current_arch, la.Verbosity.TEST)
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

    def _getSubPackages(self):
        return super()._getSubPackages() + ["debuginfo"]


class JDKBase(BaseSubpackages):
    def _getSubPackages(self):
        return super()._getSubPackages() + [DEVEL, "demo", "src"]


class ItwSubpackages(BaseSubpackages):
    def _getSubPackages(self):
        return super(ItwSubpackages, self)._getSubPackages() + [JAVADOC]

    def checkSubpackages(self, subpackages=None):
        self._document("IcedTea-Web has exactly following subpackages: `" + "`,`".join(
            self._getSubPackages()) + "`. Where `` is main package " + gc.ITW)
        self._mainCheck(subpackages)


class OpenJdk6(JDKBase):
    def _getSubPackages(self):
        return super()._getSubPackages() + [JAVADOC]


class OpenJdk7(OpenJdk6):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["accessibility", HEADLESS]


class OpenJdk8(OpenJdk7):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + ["javadoc-zip", "javadoc-debug", "javadoc-zip-debug"]

        return subpackages

    def _get_debuginfo(self):
        return ["demo-debuginfo",
                "devel-debuginfo",
                "headless-debuginfo"]

    def _get_debug_debuginfo(self):
        return ["debug-debuginfo",
                "demo-debug-debuginfo",
                "devel-debug-debuginfo",
                "headless-debug-debuginfo"]

    def _get_debug_subpackages(self):
        return ["accessibility-debug",
                "debug",
                "demo-debug",
                "devel-debug",
                "headless-debug",
                "src-debug"]


class OpenJdk8Debug(OpenJdk8):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + self._get_debug_subpackages()
        return subpackages


class OpenJdk8JFX(OpenJdk8Debug):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["openjfx",
                                            "openjfx-debug",
                                            "openjfx-devel",
                                            "openjfx-devel-debug"]


class OpenJdk8DebugDebuginfo(OpenJdk8Debug):
    def _getSubPackages(self):
        return super()._getSubPackages() + self._get_debuginfo() + self._get_debug_debuginfo() + ["debugsource"]


class OpenJdk8Debuginfo(OpenJdk8):
    def _getSubPackages(self):
        return super()._getSubPackages() + self._get_debuginfo() + ["debugsource"]


class OpenJdk8JFXDebuginfo(OpenJdk8JFX):
    def _getSubPackages(self):
        return super()._getSubPackages() + self._get_debuginfo() + self._get_debug_debuginfo() + ["debugsource"]


class OpenJdk9Debuginfo(OpenJdk8Debuginfo):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods"]


class OpenJdk9(OpenJdk8):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods"]


class OpenJdk9DebugDebuginfo(OpenJdk8DebugDebuginfo):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods", "jmods-debug"]


class OpenJdk9Debug(OpenJdk8Debug):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods", "jmods-debug"]


class OracleAndIbmBase(JDKBase):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + ["jdbc"]
        subpackages.remove("debuginfo")
        return subpackages


class OracleAndIbmAddPlugin(OracleAndIbmBase):
    def _getSubPackages(self):
        return super()._getSubPackages() + [PLUGIN]


class Oracle7and8(OracleAndIbmAddPlugin):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages.remove("demo")
        subpackages.append(JAVAFX)
        return subpackages


class SubpackagesTest(utils.core.base_xtest.BaseTest):
    instance = None

    def test_checkAllSubpackages(self):
        rpms = self.getBuild()
        assert rpms is not None
        assert len(rpms) > 1
        subpackages = []
        for rpm in rpms:
            subpackages.append(split.get_subpackage_only(ntpath.basename(rpm)))
        self.csch.checkSubpackages(subpackages)

    def setCSCH(self):
        SubpackagesTest.instance = self
        rpms = config.runtime_config.RuntimeConfig().getRpmList()
        if rpms.getJava() == gc.ITW:
            self.csch = ItwSubpackages()
            return

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == '6':
                self.csch = OpenJdk6()
                return
            elif rpms.getMajorVersionSimplified() == '7':
                self.csch = OpenJdk7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                if rpms.isRhel():
                    if self.getCurrentArch() in gc.getPpc32Arch() + gc.getS390Arch() + gc.getS390xArch():
                        self.csch = OpenJdk8()
                        return
                    else:
                        self.csch = OpenJdk8Debug()
                        return
                elif rpms.isFedora():
                    if int(rpms.getOsVersion()) < 27:
                        if self.getCurrentArch() in gc.getArm32Achs():
                            self.csch = OpenJdk8()
                            return
                        elif self.getCurrentArch() in gc.getAarch64Arch() + gc.getPower64Achs():
                            self.csch = OpenJdk8Debug()
                            return
                        elif self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                            self.csch = OpenJdk8JFX()
                            return
                        else:
                            raise ex.UnknownJavaVersionException("Check for this arch is not implemented for given OS.")
                    if int(rpms.getOsVersion()) > 26:
                        if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                            self.csch = OpenJdk8JFXDebuginfo()
                            return
                        elif self.getCurrentArch() in gc.getArm32Achs() + gc.getS390xArch():
                            self.csch = OpenJdk8Debuginfo()
                            return
                        elif self.getCurrentArch() in gc.getAarch64Arch() + gc.getPower64Achs():
                            self.csch = OpenJdk8DebugDebuginfo()
                            return
                        else:
                            raise ex.UnknownJavaVersionException("Check for this arch is not implemented for given OS.")

                else:
                    raise ex.UnknownJavaVersionException("Unrecognized OS.")
            elif rpms.getMajorVersionSimplified() == "9":
                if rpms.isFedora():
                    if int(rpms.getOsVersion()) < 27:
                        if self.getCurrentArch() in gc.getArm32Achs():
                            self.csch = OpenJdk9()
                            return
                        elif self.getCurrentArch() in gc.getAarch64Arch() + gc.getPower64Achs():
                            self.csch = OpenJdk9Debug()
                            return
                        # jfx in the future?
                        elif self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                            self.csch = OpenJdk9Debug()
                            return
                        else:
                            raise ex.UnknownJavaVersionException("Check for this arch is not implemented for given OS.")
                    if int(rpms.getOsVersion()) > 26:
                        # jfx in the future?
                        if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                            self.csch = OpenJdk9DebugDebuginfo()
                            return
                        elif self.getCurrentArch() in gc.getArm32Achs():
                            self.csch = OpenJdk9Debuginfo()
                            return
                        elif self.getCurrentArch() in gc.getAarch64Arch() + gc.getPower64Achs() + gc.getS390xArch():
                            self.csch = OpenJdk9DebugDebuginfo()
                            return
                        else:
                            raise ex.UnknownJavaVersionException("Check for this arch is not implemented for given OS.")
                else:
                    raise ex.UnknownJavaVersionException("Unrecognized OS.")

            else:
                raise ex.UnknownJavaVersionException("Unknown OpenJDK version.")

        if rpms.getVendor() == gc.SUN:
            self.csch = OracleAndIbmAddPlugin()
            return
        if rpms.getVendor() == gc.ORACLE:
            self.csch = Oracle7and8()
            return
        if rpms.getVendor() == gc.IBM:
            if rpms.getMajorVersionSimplified() == "7":
                if self.getCurrentArch() in gc.getPpc32Arch() + gc.getIx86archs() + gc.getX86_64Arch():
                    self.csch = OracleAndIbmAddPlugin()
                    return
                else:
                    self.csch = OracleAndIbmBase()
                    return
            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getPpc32Arch() + gc.getIx86archs() + gc.getX86_64Arch() +\
                                            gc.getPower64BeAchs():
                    self.csch = OracleAndIbmAddPlugin()
                    return
                else:
                    self.csch = OracleAndIbmBase()
                    return
            else:
                raise ex.UnknownJavaVersionException("Ibm java version unknown.")

        raise ex.UnknownJavaVersionException("Java version or OS was not recognized by this framework.")



def testAll():
    return SubpackagesTest().execute_tests()


def documentAll():
    outputControl.logging_access.LoggingAccess().stdout("Subpackage conventions:")
    return SubpackagesTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
