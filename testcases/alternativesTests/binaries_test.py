import sys
import utils.core.base_xtest as bt
from outputControl import logging_access as la
import config.global_config as gc
import config.runtime_config as rc
import utils.core.unknown_java_exception as ex
import utils
import testcases.alternativesTests.binaries_test_config_classes as tcc
from utils.test_constants import *


class BinariesTest(bt.BaseTest):
    """
    Base class for binaries test. This does nothing but configure the csch and returns.
    No methods should be placed here.
    """
    instance = None
    var = None

    def test_alternatives_binary_files(self):
        pkgs = self.getBuild()
        return self.csch.check_binaries_with_slaves(pkgs)

    def setCSCH(self):
        BinariesTest.instance = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking binaries and slaves for " + rpms.getMajorPackage(), la.Verbosity.TEST)

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                if self.getCurrentArch() in (gc.getX86_64Arch() + gc.getPower64BeAchs()):
                    self.csch = tcc.OpenJdk6PowBeArchAndX86(BinariesTest.instance)
                    return
                else:
                    self.csch = tcc.OpenJdk6(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = tcc.OpenJdk7(BinariesTest.instance)
                return

            elif rpms.getMajorVersionSimplified() == "8":
                if rpms.isFedora():
                    if int(rpms.getOsVersion()) > 26:
                        if self.getCurrentArch() in gc.getAarch64Arch() + gc.getPower64LeAchs() + gc.getPower64BeAchs():
                            self.csch = tcc.OpenJdk8NoExportsDebug(BinariesTest.instance)
                            return
                        elif self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                            self.csch = tcc.OpenJdk8NoExportsDebugJFX(BinariesTest.instance)
                            return
                        else:
                            self.csch = tcc.OpenJdk8NoExports(BinariesTest.instance)
                    elif int(rpms.getOsVersion()) > 24:
                        if self.getCurrentArch() in gc.getAarch64Arch()+ gc.getPower64LeAchs() + gc.getPower64BeAchs():
                            self.csch = tcc.OpenJdk8Debug(BinariesTest.instance)
                            return
                        elif self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                            self.csch = tcc.OpenJDK8JFX(BinariesTest.instance)
                            return
                        else:
                            self.csch = tcc.OpenJdk8(BinariesTest.instance)
                            return
                    else:
                        raise ex.UnknownJavaVersionException("Outdated version of fedora OpenJDK.")

                else:
                    if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch() + gc.getAarch64Arch() + \
                            gc.getPower64Achs():
                        self.csch = tcc.OpenJdk8Debug(BinariesTest.instance)
                        return
                    else:
                        self.csch = tcc.OpenJdk8(BinariesTest.instance)
                        return

            elif rpms.getMajorVersionSimplified() == "9":
                if self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = tcc.OpenJdk9(BinariesTest.instance)
                    return
                else:
                    self.csch = tcc.OpenJdk9Debug(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "10":
                if self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = tcc.OpenJdk10(BinariesTest.instance)
                    return
                elif self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = tcc.OpenJdk10x64(BinariesTest.instance)
                    return
                else:
                    self.csch = tcc.OpenJdk10Debug(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "11":
                if self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = tcc.OpenJdk11(BinariesTest.instance)
                    return
                elif self.getCurrentArch() in gc.getX86_64Arch() + gc.getAarch64Arch():
                    self.csch = tcc.OpenJdk11x64(BinariesTest.instance)
                    return
                elif self.getCurrentArch() in gc.getS390xArch():
                    self.csch = tcc.OpenJdk11NoJhsdb(BinariesTest.instance)
                    return
                else:
                    if rpms.isRhel() and self.getCurrentArch() in gc.getS390Arch() + gc.getPpc32Arch():
                        self.csch = tcc.OpenJdk11NoDebugNoJhsdb(BinariesTest.instance)
                    else:
                        self.csch = tcc.OpenJdk11Debug(BinariesTest.instance)
                    return
            elif int(rpms.getMajorVersionSimplified()) >= 12:
                if self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = tcc.OpenJdk12(BinariesTest.instance)
                    return
                elif self.getCurrentArch() in gc.getX86_64Arch() + gc.getAarch64Arch():
                    self.csch = tcc.OpenJdk12x64(BinariesTest.instance)
                    return
                elif self.getCurrentArch() in gc.getS390xArch():
                    self.csch = tcc.OpenJdk12NoJhsdb(BinariesTest.instance)
                    return
                else:
                    if rpms.isRhel() and self.getCurrentArch() in gc.getS390Arch() + gc.getPpc32Arch():
                        self.csch = tcc.OpenJdk12NoDebugNoJhsdb(BinariesTest.instance)
                    else:
                        self.csch = tcc.OpenJdk12Debug(BinariesTest.instance)
                    return
            else:
                raise ex.UnknownJavaVersionException("Unknown OpenJDK version.")

        elif rpms.getVendor() == gc.ITW:
                self.csch = tcc.Itw(BinariesTest.instance)
                return

        elif rpms.getVendor() == gc.IBM:
            if rpms.getMajorVersionSimplified() == "7":
                if self.getCurrentArch() in (gc.getPpc32Arch() + gc.getIx86archs()):
                    self.csch = tcc.IbmWithPluginSubpackage(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = tcc.IbmArchMasterPlugin(BinariesTest.instance)
                    return

                elif self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                    self.csch = tcc.Ibm390Architectures(BinariesTest.instance)
                    return

                else:
                    self.csch = tcc.Ibm(BinariesTest.instance)
                    return

            elif rpms.getMajorVersionSimplified() == "8":
                if rpms.getOsVersionMajor() == 7:
                    if self.getCurrentArch() in (
                                gc.getX86_64Arch() + gc.getPower64BeAchs() + gc.getIx86archs() + gc.getPpc32Arch()):
                        self.csch = tcc.IbmArchMasterPlugin(BinariesTest.instance)
                        return

                    elif self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                        self.csch = tcc.Ibm390Architectures(BinariesTest.instance)
                        return

                    else:
                        self.csch = tcc.Ibm(BinariesTest.instance)
                        return
                elif rpms.getOsVersionMajor() == 8:
                    if self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch():
                        self.csch = tcc.Ibm8Rhel8S390X(BinariesTest.instance)
                        return
                    self.csch = tcc.Ibm8Rhel8(BinariesTest.instance)
                    return
            else:
                raise ex.UnknownJavaVersionException("Unknown IBM java version.")

        elif rpms.getVendor() == gc.ORACLE or rpms.getVendor() == gc.SUN:
            if rpms.getMajorVersionSimplified() == "6":
                if self.getCurrentArch() in gc.getIx86archs():
                    self.csch = tcc.OracleNoArchPlugin(BinariesTest.instance)
                    return

                else:
                    self.csch = tcc.Oracle6ArchPlugin(BinariesTest.instance)
                    return
            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = tcc.Oracle7(BinariesTest.instance)
                return
            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = tcc.Oracle8(BinariesTest.instance)
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
