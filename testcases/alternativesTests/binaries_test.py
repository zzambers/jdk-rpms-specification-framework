from outputControl import logging_access as la
import sys
import utils.core.base_xtest as bt
import config.global_config as gc
import config.runtime_config as rc
import utils.core.unknown_java_exception as ex
import utils
from testcases.alternativesTests.binaries_test_config_classes import OpenJdk8, OpenJdk7, OpenJdk6, OpenJdk9, \
    OpenJdk6PowBeArchAndX86, OpenJdk8Debug, Itw, OpenJdk9Debug, Ibm, IbmWithPluginSubpackage, IbmArchMasterPlugin, \
    Ibm390Architectures, Oracle6ArchPlugin, Oracle7and8, OracleNoArchPlugin


class BinariesTest(bt.BaseTest):
    instance = None

    def test_alternatives_binary_files(self):
        pkgs = self.getBuild()
        self.csch.check_binaries_with_slaves(pkgs)

    def setCSCH(self):
        BinariesTest.instance = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking binaries and slaves for " + rpms.getMajorPackage(), la.Verbosity.TEST)

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

            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                    self.csch = OpenJdk8Debug(BinariesTest.instance)
                    return
                else:
                    self.csch = OpenJdk8(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "9":
                if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch() + gc.getPower64LeAchs():
                    self.csch = OpenJdk9Debug(BinariesTest.instance)
                    return
                else:
                    self.csch = OpenJdk9(BinariesTest.instance)
                    return
            else:
                raise ex.UnknownJavaVersionException("Unknown OpenJDK version.")

        elif rpms.getVendor() == gc.ITW:
                self.csch = Itw(BinariesTest.instance)
                return

        elif rpms.getVendor() == gc.IBM:
            if rpms.getMajorVersionSimplified() == "7":
                if self.getCurrentArch() in (gc.getPpc32Arch() + gc.getIx86archs()):
                    self.csch = IbmWithPluginSubpackage(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = IbmArchMasterPlugin(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                    self.csch = Ibm390Architectures(BinariesTest.instance)
                    return

                else:
                    self.csch = Ibm(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in (
                            gc.getX86_64Arch() + gc.getPower64BeAchs() + gc.getIx86archs() + gc.getPpc32Arch()):
                    self.csch = IbmArchMasterPlugin(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                    self.csch = Ibm390Architectures(BinariesTest.instance)
                    return

                else:
                    self.csch = Ibm(BinariesTest.instance)
                    return
            else:
                raise ex.UnknownJavaVersionException("Unknown IBM java version.")

        elif rpms.getVendor() == gc.ORACLE or rpms.getVendor() == gc.SUN:
            if rpms.getMajorVersionSimplified() == "6":
                if self.getCurrentArch() in gc.getIx86archs():
                    self.csch = OracleNoArchPlugin(BinariesTest.instance)
                    return

                else:
                    self.csch = Oracle6ArchPlugin(BinariesTest.instance)
                    return
            elif rpms.getMajorVersionSimplified() == "7" or rpms.getMajorVersionSimplified() == "8":
                self.csch = Oracle7and8(BinariesTest.instance)
                return
            else:
                raise ex.UnknownJavaVersionException("Unknown Oracle java version")
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
