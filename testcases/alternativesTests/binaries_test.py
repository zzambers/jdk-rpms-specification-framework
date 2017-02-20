from outputControl import logging_access as la
import sys
import utils.core.base_xtest as bt
import config.global_config as gc
import config.runtime_config as rc
import utils.core.unknown_java_exception as ex
import utils
from testcases.alternativesTests.binaries_test_config_classes import OpenJdk8, OpenJdk7, OpenJdk8Intel,\
    OpenJdk6PowBeArchAndX86, OpenJdk6, IbmBaseMethods, IbmWithPluginSubpkg, IbmS390Archs, IbmArchMasterPlugin


class BinariesTest(bt.BaseTest):
    instance = None

    def test_alternatives_binary_files(self):
        pkgs = self.getBuild()
        self.csch._check_binaries_with_slaves(pkgs)

    def setCSCH(self):
        BinariesTest.instance = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking binaries and slaves for " + rpms.getMajorPackage())

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                if self.getCurrentArch() in (gc.getX86_64Arch() + gc.getPower64BeAchs()):
                    self.csch = OpenJdk6PowBeArchAndX86(BinariesTest.instance)
                    return
                else:
                    self.csch = OpenJdk6(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "7" :
                self.csch = OpenJdk7(BinariesTest.instance)
                return

            elif rpms.getMajorVersionSimplified() == "8" and self.getCurrentArch() in gc.getX86_64Arch() + gc.getIx86archs():
                self.csch = OpenJdk8Intel(BinariesTest.instance)
                return

            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = OpenJdk8(BinariesTest.instance)
                return

            else:
                raise ex.UnknownJavaVersionException("Unknown OpenJDK version.")

        elif rpms.getVendor() == gc.IBM:
            if rpms.getMajorVersionSimplified() == "7":
                if self.getCurrentArch() in (gc.getPpc32Arch() +  gc.getIx86archs()):
                    self.csch = IbmWithPluginSubpkg(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = IbmArchMasterPlugin(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                    self.csch = IbmS390Archs(BinariesTest.instance)
                    return

                else:
                    self.csch = IbmBaseMethods(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in (gc.getX86_64Arch() + gc.getPower64BeAchs() + gc.getIx86archs() + gc.getPpc32Arch()):
                    self.csch = IbmArchMasterPlugin(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                    self.csch = IbmS390Archs(BinariesTest.instance)
                    return

                else:
                    self.csch = IbmBaseMethods(BinariesTest.instance)
                    return

            else:
                raise ex.UnknownJavaVersionException("Unknown IBM java version.")

        else:
            raise ex.UnknownJavaVersionException("Unknown platform, java was not identified.")


def testAll():
    return BinariesTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Binaries and slave conventions")
    return BinariesTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)
    return BinariesTest().execute_special_docs()


if __name__ == "__main__":
    main(sys.argv[1:])
