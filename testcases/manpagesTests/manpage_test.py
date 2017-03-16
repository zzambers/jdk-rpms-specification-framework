from outputControl import logging_access as la
import sys
import utils.core.base_xtest as bt
import config.global_config as gc
import utils
from utils.core.configuration_specific import JdkConfiguration
import os
import utils.pkg_name_split as pkgsplit
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch
import utils.core.unknown_java_exception as ex
from utils.mock.mock_executor import DefaultMock
import config.runtime_config as rc
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id

MANPAGE_SUFFIX = ".1.gz"
SUBPACKAGE = "subpackage"
MANPAGE = "Man page"
SDK_BINARIES = "SDK binaries"
JAVA_RMI_CGI = "java-rmi.cgi"
MANPAGE_FOR_BINARY = MANPAGE + " file for binary"
MAN_DIR = "/usr/share/man/man1"
WAS_NOT_FOUND = "was not found"
JAVAC = "javac"
JAVA = "java"
POLICYTOOL = "policytool"
DEFAULT = "default"
DEVEL = "devel"
FILE = 1
LINK = 0
HEADLESS = "headless"
DEBUG_SUFFIX = "-debug"


# this test expects that binaries are equal to its slaves (checked in binaries_test)
class ManpageTestMethods(JdkConfiguration):
    skipped = []
    failed = []
    rpms = rc.RuntimeConfig().getRpmList()

    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-" + self.rpms.getMajorPackage() + MANPAGE_SUFFIX]

    def _get_subpackages(self):
        return []

    def _clean_up_binaries(self, binaries, master):
        return binaries

    def _get_arch(self):
        return get_id(ManpageTests.instance.getCurrentArch())

    def _clean_default_mpges(self, default_mans, all_mpgs):
        extracted_mpges = list(set(all_mpgs) - set(default_mans))
        return extracted_mpges

    def _clean_debug_subpackages(self, bins):
        return

    # wont be doc-ed, is already handled in binary test
    def _remove_java_rmi_cgi(self, binaries):
        if JAVA_RMI_CGI in binaries:
            binaries.remove(JAVA_RMI_CGI)
        return binaries

    def man_page_test(self, pkgs):
        self._document("Every binary must have a man page. \n - Man pages are in {} directory.".format(MAN_DIR))
        self.failed = []
        bins = {}
        manpages_without_postscript = {}
        manpages_with_postscript = {}

        DefaultMock().provideCleanUsefullRoot()
        default_mans = DefaultMock().execute_ls(MAN_DIR)[0].split("\n")

        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))
            # expects binaries are only in devel/default/headless subpackage, is consistent with binaries test
            if _subpkg not in self._get_subpackages():
                continue

            DefaultMock().importRpm(pkg)

            manpages = DefaultMock().execute_ls(MAN_DIR)[0].split("\n")
            manpages = self._clean_default_mpges(default_mans, manpages)
            if len(manpages) != 0:
                manpages_without_postscript[_subpkg] = manpages

            if not DefaultMock().postinstall_exception_checked(pkg):
                self.skipped.append(_subpkg)
                continue

            manpages = DefaultMock().execute_ls(MAN_DIR)[0].split("\n")
            manpages = self._clean_default_mpges(default_mans, manpages)
            if len(manpages) != 0:
                manpages_with_postscript[_subpkg] = manpages
            masters = DefaultMock().get_masters()

            checked_masters = [JAVA, JAVAC]
            ManpageTests.instance.log("Checking man pages for masters: {}.".format(checked_masters))

            for m in masters:
                if m not in checked_masters:
                    continue

                tg = DefaultMock().get_target(m)
                tg = tg.strip(m)

                binaries = DefaultMock().execute_ls(tg)[0].split("\n")
                binaries = self._clean_up_binaries(binaries, m)
                binaries = self._remove_java_rmi_cgi(binaries)
                bins[_subpkg] = binaries

        packages = self._get_subpackages()

        ManpageTests.instance.log("Cleaning {} from JRE binaries "
                                  "(JRE bins do not have man pages in {}.)" .format(SDK_BINARIES, DEVEL))
        devel_bins = []
        ManpageTests.instance.log("Original " + SDK_BINARIES + ": " + ", ".join(bins[DEVEL]))

        for b in bins[packages[1]]:
            if b not in bins[packages[0]]:
                devel_bins.append(b)
        self._clean_debug_subpackages(bins)
        ManpageTests.instance.log(SDK_BINARIES + " without JRE binaries: " + ", ".join(devel_bins))
        bins[packages[1]] = devel_bins

        self._manpages_check_with_command_man(bins, pkgs)
        self.manpages_with_out_postscript_check(manpages_without_postscript, default_mans, bins)
        self.manpages_with_postscript_check(manpages_with_postscript, bins)

        ManpageTests.instance.log("Failed tests: " + ", ".join(self.failed))
        assert(len(self.failed) == 0)

    # master man pages with command
    def _manpages_check_with_command_man(self, bins, pkgs):
        for subpkg in bins.keys():
            pack = None
            for pkg in pkgs:
                if subpkg == utils.test_utils.rename_default_subpkg(pkgsplit.get_subpackage_only(os.path.basename(pkg))):
                    pack = pkg
                    break
            if pack is None:
                raise AttributeError("Error occured during searching for snapshot.")
            DefaultMock().install_postscript(pack)
            for b in bins[subpkg]:
                o, r = DefaultMock().executeCommand(["man " + b])
                if r != 0:
                    self.failed.append("Command: man {} failed for {} {}.".format(b, subpkg, SUBPACKAGE))
                    ManpageTests.instance.log("Command: man {} has failed for {} {}. "
                                              "Error output: {} , {}.".format(b, subpkg, SUBPACKAGE, o, r))

    # man pages without postscript check, should be there once - only file
    def manpages_with_out_postscript_check(self, manpages_without_postscript=None, default_mans=None, bins=None):
        docs = "When rpm is installed, man page file exists for each binary and is suffixed with " \
               "{} suffix.".format(replace_archs_with_general_arch(self._get_manpage_suffixes(DEFAULT),
                                                                   self._get_arch())[FILE])
        self._document(docs)
        for subpkg in manpages_without_postscript.keys():
            unpacked_mpges = self._clean_default_mpges(default_mans, manpages_without_postscript[subpkg])
            for binary in bins[subpkg]:
                found = False
                for manpage in unpacked_mpges:
                    if binary in manpage:
                        found = True
                        break
                if not found:
                    self.failed.append(MANPAGE_FOR_BINARY + " " + binary + " " + WAS_NOT_FOUND)
                    ManpageTests.instance.log(MANPAGE_FOR_BINARY + " " + binary + " " + WAS_NOT_FOUND)

    # man pages with postscript check, should be there twice  - link and man page file
    def manpages_file_debug_subpackages_doc(self, args):
        rpms_by_arch = self.rpms.getPackagesByArch(ManpageTests.instance.getCurrentArch())
        has_debug = False
        for rpm in rpms_by_arch:
            if HEADLESS + DEBUG_SUFFIX in rpm:
                has_debug = True
                break

        if has_debug:
            self._document(" For debug subpackages, manpage file is suffixed " \
                    "with {}.".format(replace_archs_with_general_arch((self._get_manpage_suffixes(DEBUG_SUFFIX)),
                                                                      self._get_arch())[FILE]))
        return

    def manpages_with_postscript_check(self, manpages_with_postscript=None, bins=None):
        self._document("Each man page file has an alternatives record without full NVRA, only with "
                       "{} suffix.".format(replace_archs_with_general_arch(self._get_manpage_suffixes(DEFAULT), self._get_arch())[LINK]))
        for subpackage in manpages_with_postscript.keys():
            checked_manpages_suffixes = self._get_manpage_suffixes(subpackage)
            installed_mpges = manpages_with_postscript[subpackage]
            for bin in bins[subpackage]:
                for suffix in checked_manpages_suffixes:
                    if bin + suffix not in installed_mpges:
                        if suffix == checked_manpages_suffixes[LINK]:
                            link_or_file = "Link"
                        else:
                            link_or_file = MANPAGE + " file"
                        self.failed.append(
                            "{} {} could not be found in man directory for {} "
                            "{}.".format(link_or_file, bin + suffix, subpackage, SUBPACKAGE))


class OpenJdk6(ManpageTestMethods):
    #policytool binary is an exception, it has binary in default but slave in devel, expects policytool is in order
    def _clean_up_binaries(self, binaries, master):
        if master == JAVAC:
            binaries.append(POLICYTOOL)
            return binaries
        else:
            binaries.remove(POLICYTOOL)
        return binaries

    def _get_subpackages(self):
        return [DEFAULT, DEVEL, ]


class OpenJdk7(ManpageTestMethods):
    # default subpackage has no alternatives, no slaves, no manpages
    def _get_subpackages(self):
        return [HEADLESS, DEVEL]

    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-" + self.rpms.getNvr() + "." + self._get_arch() + MANPAGE_SUFFIX]

    # policytool binary is in devel and default, slave in devel
    def _clean_up_binaries(self, binaries, master):
        return binaries


class OpenJdk8(OpenJdk7):
    # policytool binary is in default and devel, but slave in headless
    def _clean_up_binaries(self, binaries, master):
        if master == JAVA:
            binaries.append(POLICYTOOL)
        return binaries


class OpenJdk8WithDebug(OpenJdk8):
    def _clean_debug_subpackages(self, bins):
        devel_bins = []
        ManpageTests.instance.log("Original debug " + SDK_BINARIES + ": " + ", ".join(bins[self._get_subpackages()[3]]))
        for b in bins[self._get_subpackages()[3]]:
            if b not in bins[self._get_subpackages()[2]]:
                devel_bins.append(b)
        bins[DEVEL + DEBUG_SUFFIX] = devel_bins
        return

    def _get_subpackages(self):
        return [HEADLESS, DEVEL, HEADLESS + DEBUG_SUFFIX, DEVEL + DEBUG_SUFFIX]

    def _get_manpage_suffixes(self, subpackage):
        if DEBUG_SUFFIX in subpackage:
            return [MANPAGE_SUFFIX, "-" + self.rpms.getNvr() + "." + self._get_arch() + DEBUG_SUFFIX + MANPAGE_SUFFIX]
        else:
            return super()._get_manpage_suffixes(subpackage)


class ManpageTests(bt.BaseTest):
    instance = None

    def test_manpages(self):
        pkgs = self.getBuild()
        self.csch.man_page_test(pkgs)

    def setCSCH(self):
        ManpageTests.instance = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking man pages for " + rpms.getMajorPackage())

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = OpenJdk6()
                return

            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = OpenJdk7()
                return

            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getX86_64Arch() + gc.getIx86archs():
                    self.csch = OpenJdk8WithDebug()
                    return
                else:
                    self.csch = OpenJdk8()
                    return

            else:
                raise ex.UnknownJavaVersionException("Unknown java version.")
        else:
            raise ex.UnknownJavaVersionException("Unknown platform, java was not identified.")


def testAll():
    return ManpageTests().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Man page conventions:")
    return ManpageTests().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)
    return ManpageTests().execute_special_docs()


if __name__ == "__main__":
    main(sys.argv[1:])
