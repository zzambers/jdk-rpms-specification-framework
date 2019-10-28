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
from utils.test_utils import passed_or_failed
from outputControl import dom_objects as do


class MainPackagePresent(JdkConfiguration):

    def __init__(self):
        super().__init__()
        self.failed = 0
        self.passed = 0


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
        if not passed_or_failed(self, ssGiven == subpkgSetExpected,
                                "Set of subpkgs not as expected. Differences will follow."):
            for subpkg in subpkgSetExpected:
                SubpackagesTest.instance.log(
                    "Checking `" + subpkg + "` of " + SubpackagesTest.instance.current_arch, la.Verbosity.TEST)
                passed_or_failed(self, subpkg in ssGiven, subpkg + " is missing in given set of rpms.")



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
        return self.passed, self.failed

    def _getSubPackages(self):
        return super()._getSubPackages() + ["debuginfo"]


class JDKBase(BaseSubpackages):
    def _getSubPackages(self):
        return super()._getSubPackages() + [DEVEL, "demo", "src"]


class ItwSubpackages(MainPackagePresent):
    def _getSubPackages(self):
        return super(ItwSubpackages, self)._getSubPackages() + [JAVADOC, DEVEL]

    def checkSubpackages(self, subpackages=None):
        self._document("IcedTea-Web has exactly following subpackages: `" + "`,`".join(
            self._getSubPackages()) + "`. Where `` is main package " + gc.ITW)
        self._mainCheck(subpackages)
        return self.passed, self.failed


class OpenJdk6(JDKBase):
    def _getSubPackages(self):
        return super()._getSubPackages() + [JAVADOC]


class OpenJdk7(OpenJdk6):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["accessibility", HEADLESS]


class OpenJdk8(OpenJdk7):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + ["javadoc-zip"]

        return subpackages

    def _get_debuginfo(self):
        return ["demo-debuginfo",
                "devel-debuginfo",
                "headless-debuginfo"]

    def _get_debug_debuginfo(self):
        return ["demo" + get_debug_suffix() + "-debuginfo",
                "devel" + get_debug_suffix() + "-debuginfo",
                "headless" + get_debug_suffix() + "-debuginfo",
                get_debug_suffix().replace("-", "", 1) + "-debuginfo"]

    def _get_debug_subpackages(self):
        return ["accessibility" + get_debug_suffix(),
                "demo" + get_debug_suffix(),
                "devel" + get_debug_suffix(),
                "headless" + get_debug_suffix(),
                "src" + get_debug_suffix(),
                get_debug_suffix().replace("-", "", 1)]

    def _get_javadoc_debug(self):
        return ["javadoc" + get_debug_suffix(), "javadoc-zip" + get_debug_suffix()]


class OpenJdk8Debug(OpenJdk8):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + super()._get_debug_subpackages()
        return subpackages


class OpenJdk8JFX(OpenJdk8Debug):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["openjfx",
                                            "openjfx" + get_debug_suffix(),
                                            "openjfx-devel",
                                            "openjfx-devel" + get_debug_suffix()]


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

    def _get_javadoc_debug(self):
        return []

    def _get_debuginfo(self):
        return ["devel-debuginfo",
                "headless-debuginfo"]


class OpenJdk9(OpenJdk8):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods"]

    def _get_javadoc_debug(self):
        return []


class OpenJdk10(OpenJdk9Debuginfo):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages.remove("accessibility")
        subpackages = subpackages + ["debugsource"] + self._get_debuginfo()
        return subpackages


class OpenJdk9DebugDebuginfo(OpenJdk8DebugDebuginfo):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods", "jmods" + get_debug_suffix()]

    def _get_debug_debuginfo(self):
        return ["devel" + get_debug_suffix() + "-debuginfo",
                "headless" + get_debug_suffix() + "-debuginfo"]


class OpenJdk10DebugDebuginfo(OpenJdk9DebugDebuginfo):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages.remove("accessibility")
        subpackages.remove("accessibility" + get_debug_suffix())
        return subpackages

    def _get_debuginfo(self):
        return ["devel-debuginfo",
                "headless-debuginfo"]

    def _get_debug_debuginfo(self):
        return [get_debug_suffix().replace("-", "", 1) + "-debuginfo",
                "devel" + get_debug_suffix() + "-debuginfo",
                "headless" + get_debug_suffix() + "-debuginfo"]

    def _get_debug_subpackages(self):
        return ["accessibility" + get_debug_suffix(),
                "slowdebug",
                "demo" + get_debug_suffix(),
                "devel" + get_debug_suffix(),
                "headless" + get_debug_suffix(),
                "src" + get_debug_suffix()]

    def _get_javadoc_debug(self):
        return ["javadoc-slowdebug", "javadoc-zip-slowdebug"]


class OpenJdk11(OpenJdk8):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages.remove("accessibility")
        return subpackages

class OpenJdk11armv7hl(OpenJdk11):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages.append("debugsource")
        subpackages.append(DEVEL + "-debuginfo")
        subpackages.append(HEADLESS + "-debuginfo")
        subpackages.append("jmods")
        return subpackages

class OpenJdk11Debug(OpenJdk8Debug):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages.remove("accessibility")
        subpackages.remove("accessibility" + get_debug_suffix())
        subpackages.append("jmods")
        subpackages.append("jmods" + get_debug_suffix())
        subpackages.append("debugsource")
        subpackages += self._get_debuginfo()  + self._get_debug_debuginfo()
        return subpackages

    def _get_debug_debuginfo(self):
        subpackages = super()._get_debug_debuginfo()
        subpackages.remove("demo" + get_debug_suffix() + "-debuginfo")
        return subpackages

    def _get_debuginfo(self):
        subpackages = super(OpenJdk11Debug, self)._get_debuginfo()
        subpackages.remove("demo-debuginfo")
        return subpackages


class OpenJdk9Debug(OpenJdk8Debug):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["jmods", "jmods" + get_debug_suffix()]


class OpenJdk12(OpenJdk11):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + super()._get_debuginfo()
        subpackages.remove("demo-debuginfo")
        subpackages.append("debugsource")
        subpackages.append("jmods")
        return subpackages

class OpenJdk12Debug(OpenJdk11Debug):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages()
        subpackages += ["javadoc-zip" + get_debug_suffix(), "javadoc" + get_debug_suffix()]
        subpackages += self._get_debug_subpackages()
        subpackages += self._get_debug_debuginfo()
        subpackages += self._get_debuginfo()
        return subpackages

    def _get_debug_subpackages(self):
        subpackages = super(OpenJdk12Debug, self)._get_debug_subpackages()
        subpackages.remove("accessibility" + get_debug_suffix())
        return subpackages

    def _get_debug_debuginfo(self):
        subpackages = super(OpenJdk12Debug, self)._get_debug_debuginfo()
        return subpackages


class OracleAndIbmBase(JDKBase):
    def _getSubPackages(self):
        subpackages = super()._getSubPackages() + ["jdbc", HEADLESS]
        subpackages.remove("debuginfo")
        return subpackages


class OracleAndIbmAddPlugin(OracleAndIbmBase):
    def _getSubPackages(self):
        return super()._getSubPackages() + [PLUGIN]


class Ibm8withWS(OracleAndIbmAddPlugin):
    def _getSubPackages(self):
        return super()._getSubPackages() + ["webstart"]


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
        subpackages = []
        for rpm in rpms:
            subpackages.append(split.get_subpackage_only(ntpath.basename(rpm)))
        return self.csch.checkSubpackages(subpackages)

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
                        self.csch = OpenJdk8Debuginfo()
                        return
                    else:
                        self.csch = OpenJdk8DebugDebuginfo()
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

            elif rpms.getMajorVersionSimplified() == '10':
                if rpms.getDist() == gc.FEDORA or rpms.getOsVersionMajor() > 7:
                    if self.getCurrentArch() in gc.getArm32Achs():
                        self.csch = OpenJdk10()
                        return
                    else:
                        self.csch = OpenJdk10DebugDebuginfo()
                        return
            elif rpms.getMajorVersionSimplified() == '11':
                if self.getCurrentArch() in gc.getPpc32Arch() + gc.getS390Arch():
                    self.csch = OpenJdk11()
                    return
                elif self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = OpenJdk11armv7hl()
                    return
                else:
                    self.csch = OpenJdk11Debug()
                    return
            elif int(rpms.getMajorVersionSimplified()) >= 12:
                if self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = OpenJdk12()
                    return
                self.csch = OpenJdk12Debug()
                return
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
                                            gc.getPower64BeAchs() + gc.getPower64LeAchs():
                    self.csch = Ibm8withWS()
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
