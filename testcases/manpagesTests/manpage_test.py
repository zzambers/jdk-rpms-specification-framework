from outputControl import logging_access as la
import sys
import utils.core.base_xtest as bt
import config.global_config as gc
import utils
from utils.core.configuration_specific import JdkConfiguration
import os
import utils.pkg_name_split as pkgsplit
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch, log_failed_test, passed_or_failed
import utils.core.unknown_java_exception as ex
from utils.mock.mock_executor import DefaultMock
import config.runtime_config as rc
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
from utils.test_constants import *


MANPAGE_SUFFIX = ".1.gz"
SUBPACKAGE = "subpackage"
MANPAGE = "Man page"
SDK_BINARIES = "SDK binaries"
MANPAGE_FOR_BINARY = MANPAGE + " file for binary"
FILE = 1
LINK = 0



class ManpageTestMethods(JdkConfiguration):

    """
    This test expects that binaries are equal to its slaves (checked in binaries_test). Only binaries are used as a
    source of expected manpages.

    This checks if all binaries have its manpages and if all the manpages have links.

    IBM java does not have any manpages, so the test is skipped.
    """
    def __init__(self):
        super().__init__()
        self.passed = 0
        self.failed = 0
        self.list_of_failed_tests = []

    skipped = []
    rpms = rc.RuntimeConfig().getRpmList()

    def _remove_excludes(self, binaries):
        excludes = self._get_excludes()
        if len(excludes) == 0:
            return binaries
        for e in excludes:
            if e in binaries:
                binaries.remove(e)
        return binaries

    def _get_extra_bins(self, plugin_bin_content):
        return []

    def iced_tea_web_check(self, manpages_with_postcript=None, manpages_without_postscript=None):
        return

    def _get_manpage_files_names(self, list_of_bins, usr_bin_content):
        return list_of_bins

    def _get_manpage_link_names(self, list_of_links):
        return list_of_links

    def _get_checked_masters(self):
        return []

    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-" + self.rpms.getMajorPackage() + MANPAGE_SUFFIX]

    def _get_subpackages(self):
        return []

    def _clean_up_binaries(self, binaries, master, usr_bin):
        return binaries

    def _get_arch(self):
        return get_id(ManpageTests.instance.getCurrentArch())

    def _clean_default_mpges(self, default_mans, all_mpgs):
        extracted_mpges = list(set(all_mpgs) - set(default_mans))
        return extracted_mpges

    def _clean_debug_subpackages(self, bins):
        return

    def binaries_without_manpages(self, binaries=None):
        return binaries

    # wont be doc-ed, is already handled in binary test
    def _remove_java_rmi_cgi(self, binaries):
        if JAVA_RMI_CGI in binaries:
            binaries.remove(JAVA_RMI_CGI)
        return binaries

    def _get_target(self, master):
        return DefaultMock().get_target(master).strip(master)

    def _itw_plugin_bin_location(self):
        return "/usr/lib"

    def _get_excludes(self):
        return []

    def _clean_sdk_from_jre(self, bins, packages):
        ManpageTests.instance.log("Cleaning {} from JRE binaries "
                                  "(JRE bins do not have man pages in {}.)".format(SDK_BINARIES, DEVEL),
                                  la.Verbosity.TEST)

        devel_bins = []
        ManpageTests.instance.log("Original " + SDK_BINARIES + ": " + ", ".join(bins[DEVEL]), la.Verbosity.TEST)

        for b in bins[packages[1]]:
            if b not in bins[packages[0]]:
                devel_bins.append(b)
        self._clean_debug_subpackages(bins)
        ManpageTests.instance.log(SDK_BINARIES + " without JRE binaries: " + ", ".join(devel_bins), la.Verbosity.TEST)
        bins[packages[1]] = devel_bins
        return bins

    def manpage_file_check(self, bins, subpackage=None, plugin_bin_content=None, manpages_without_postscript=None):
        """
        Each man page is a file, located in /usr/shared/man, it has a specified name bin-nvra.1.gz. It must be present
        for every binary in the given subpackages. JDK 10 has some of the pages missing, this is
        solved as exclude. Any exclude must be always documented in _document.
        """
        self._document("When rpm is installed, man page file exists for each binary "
                       "with {} suffix.".format(replace_archs_with_general_arch(self._get_manpage_suffixes(DEFAULT),
                                                self._get_arch())[FILE]))
        binaries = self._get_manpage_files_names(bins[subpackage], plugin_bin_content)
        manpage_files = manpages_without_postscript[subpackage]
        # now check that every binary has a man file
        for b in binaries:
            manpage = b + self._get_manpage_suffixes(subpackage)[FILE]
            if not passed_or_failed(self, manpage in manpage_files):
                log_failed_test(self, manpage + " man page file not in " + subpackage)
        return manpage_files

    def manpage_links_check(self, bins, subpackage=None, manpages_with_postscript=None, manpage_files=None):
        """
        Each man page has a link, that is located in /usr/shared/man/ and has a specific name bin.1.gz. This link
        points to alternatives. It must be present for every binary in given subpackages (except exludes).
        """
        self._document("Each man page slave has {} suffix.".format(self._get_manpage_suffixes(DEFAULT)[LINK]))
        links = self._get_manpage_link_names(bins[subpackage])
        # now remove all files from man pages
        manpage_links = list(set(manpages_with_postscript[subpackage]) - set(manpage_files))

        for l in links:
            link = l + self._get_manpage_suffixes(subpackage)[LINK]
            if not passed_or_failed(self, link in manpage_links):
                log_failed_test(self, link + " man page link not in " + subpackage)

    def man_page_test(self, pkgs):
        self._document("Every binary must have a man page. If binary has a slave, then man page has also its slave."
                       " \n - Man pages are in {} directory.".format(MAN_DIR))
        bins = {}
        manpages_without_postscript = {}
        manpages_with_postscript = {}

        DefaultMock().provideCleanUsefullRoot()
        default_mans = DefaultMock().execute_ls(MAN_DIR)[0].split("\n")
        usr_bin_content = DefaultMock().execute_ls("/usr/bin")[0].split("\n")
        plugin_bin_content = DefaultMock().execute_ls(self._itw_plugin_bin_location())[0].split("\n")

        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))
            # expects binaries are only in devel/default/headless subpackage, is consistent with binaries test
            if _subpkg not in self._get_subpackages():
                continue

            # first check links
            if not DefaultMock().postinstall_exception_checked(pkg):
                self.skipped.append(_subpkg)
                continue
            masters = DefaultMock().get_masters()

            checked_masters = self._get_checked_masters()

            for m in masters:
                if m not in checked_masters:
                    continue
                tg = self._get_target(m)
                binaries = DefaultMock().execute_ls(tg)[0].split("\n")
                binaries = self._clean_up_binaries(binaries, m, usr_bin_content)
                binaries = self._remove_java_rmi_cgi(binaries)
                binaries = self._remove_excludes(binaries)
                try:
                    plugin_binaries = self._get_extra_bins(plugin_bin_content)
                except NotADirectoryError:
                    self.failed += 1
                    log_failed_test(self, "/usr/bin directory not found, this is unexpected behaviour and the test will"
                                          " not be executed.")
                    return

                ManpageTests.instance.log("Binaries found for {}: ".format(tg) + ", ".join(binaries + plugin_binaries))
                bins[_subpkg] = binaries + plugin_binaries

            # check links
            manpages = self._clean_default_mpges(default_mans, DefaultMock().execute_ls(MAN_DIR)[0].split("\n"))

            if len(manpages) != 0:
                manpages_with_postscript[_subpkg] = manpages
                ManpageTests.instance.log("Manpages found: " + ", ".join(manpages))
            else:
                ManpageTests.instance.log("Warning: {} subpackage does not contain any binaries".format(_subpkg))

            # then check files
            DefaultMock().importRpm(pkg)
            manpages_without_postscript[_subpkg] = self._clean_default_mpges(default_mans,
                                                                             DefaultMock().execute_ls(MAN_DIR)[0]
                                                                             .split("\n"))
        bins = self._clean_sdk_from_jre(bins, self._get_subpackages())
        bins = self.binaries_without_manpages(bins)

        # then compare man files with binaries and man links with links
        for subpackage in bins.keys():
            manpage_files = self.manpage_file_check(bins, subpackage, plugin_bin_content, manpages_without_postscript)
            self.manpage_links_check(bins, subpackage, manpages_with_postscript, manpage_files)

        self.iced_tea_web_check(manpages_with_postscript, manpages_without_postscript)

        ManpageTests.instance.log("Failed tests summary: " + ", ".join(self.list_of_failed_tests), la.Verbosity.ERROR)
        return self.passed, self.failed

        # only doc-used method, does not execute any tests whatsoever
    def manpages_file_debug_subpackages_doc(self, args):
        rpms_by_arch = self.rpms.getPackagesByArch(ManpageTests.instance.getCurrentArch())
        has_debug = False
        for rpm in rpms_by_arch:
            if HEADLESS + DEBUG_SUFFIX in rpm:
                has_debug = True
                break

        if has_debug:
            self._document(" For debug subpackages, man page file is suffixed "
                           "with {}.".format(replace_archs_with_general_arch((self._get_manpage_suffixes(DEBUG_SUFFIX)),
                                                                             self._get_arch())[FILE]))
        return


class OpenJdk6(ManpageTestMethods):
    # policytool binary is an exception, it has binary in default but slave in devel, expects policytool is in order
    def _clean_up_binaries(self, binaries, master, usr_bin):
        if master == JAVAC:
            binaries.append(POLICYTOOL)
            return binaries
        else:
            binaries.remove(POLICYTOOL)
        return binaries

    def _get_subpackages(self):
        return [DEFAULT, DEVEL]

    def _get_checked_masters(self):
        return [JAVA, JAVAC]


class OpenJdk7(OpenJdk6):
    # default subpackage has no alternatives, no slaves, no manpages
    def _get_subpackages(self):
        return [HEADLESS, DEVEL]

    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-" + self.rpms.getNvr() + "." + self._get_arch() + MANPAGE_SUFFIX]

    # policytool binary is in devel and default, slave in devel
    def _clean_up_binaries(self, binaries, master, usr_bin):
        return binaries


class OpenJdk8(OpenJdk7):
    # policytool binary is in default and devel, but slave in headless
    def _clean_up_binaries(self, binaries, master, usr_bin):
        if master == JAVA:
            binaries.append(POLICYTOOL)
        return binaries


class OpenJdk8WithDebug(OpenJdk8):
    def _clean_debug_subpackages(self, bins):
        devel_bins = []
        ManpageTests.instance.log("Original debug " + SDK_BINARIES + ": " + ", ".join(bins[self._get_subpackages()[3]]),
                                  la.Verbosity.TEST)
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


class OpenJdk10(OpenJdk8):
    def _clean_up_binaries(self, binaries, master, usr_bin):
        return binaries

    def binaries_without_manpages(self, binaries=None):
        binaries_list = ["jdeprscan", "jhsdb", "jimage", "jlink", "jmod", "jshell"]
        self._document("In JDK 10, there are multiple binaries, that are missing manpages in "
                       "devel subpackage: " + ", ".join(binaries_list))
        for item in binaries_list:
            binaries[DEVEL].remove(item)
        return binaries


class OpenJdk10Debug(OpenJdk8WithDebug):
    def _clean_up_binaries(self, binaries, master, usr_bin):
        return binaries

    def binaries_without_manpages(self, binaries=None):
        binaries_list = ["jdeprscan", "jhsdb", "jimage", "jlink", "jmod", "jshell"]
        self._document("In JDK 10, there are multiple binaries, that are missing manpages in devel and devel-slowdebug "
                       "subpackage: " + ", ".join(binaries_list))
        for item in binaries_list:
            binaries[DEVEL].remove(item)
            binaries[DEVEL + DEBUG_SUFFIX].remove(item)
        return binaries


class OpenJdk10Debugx64(OpenJdk10Debug):
    def binaries_without_manpages(self, binaries=None):
        binaries_list = ["jdeprscan", "jhsdb", "jimage", "jlink", "jmod", "jshell", "jaotc"]
        self._document("In JDK 10, there are multiple binaries, that are missing manpages in devel and devel-slowdebug "
                       "subpackage: " + ", ".join(binaries_list))
        bins = super().binaries_without_manpages(binaries)
        bins[DEVEL].remove("jaotc")
        bins[DEVEL + DEBUG_SUFFIX].remove("jaotc")
        return bins


class ITW(ManpageTestMethods):
    def _clean_sdk_from_jre(self, bins, packages):
        return bins

    def _clean_up_binaries(self, binaries, master, usr_bin):
        bins = self._clean_default_mpges(usr_bin, binaries)
        bs = []
        for b in bins:
            bs.append(b.replace(".itweb", ""))
        return bs

    def _get_subpackages(self):
        return [DEFAULT]

    def _get_checked_masters(self):
        return [LIBJAVAPLUGIN + "." + self._get_arch()]

    def _get_target(self, master):
        return "/usr/bin"

    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-itweb" + MANPAGE_SUFFIX]

    def _itw_plugin_bin_location(self):
        return "/usr/lib"

    def _itw_plugin_link_location(self):
        return "/usr/lib/mozilla/plugins"

    def _get_extra_bins(self, plugin_bin_content):
        ls = DefaultMock().execute_ls(self._itw_plugin_bin_location())
        if ls[1] != 0:
            raise NotADirectoryError("dir not found")
        plugin_bin = list(set(ls[0].split("\n")) - set(plugin_bin_content))
        return plugin_bin

    # manpage files might differ from binary names
    def _get_manpage_files_names(self, list_of_bins, plugin_bin_content):
        bins = []
        for binary in list_of_bins:
            if binary == ICED_TEA_PLUGIN_SO:
                bins.append("icedteaweb-plugin")
            else:
                bins.append(binary)

        return bins

    # bin links might differ from binaries
    def _get_manpage_link_names(self, list_of_bins):
        links = []
        for binary in list_of_bins:
            if binary == "itweb-settings":
                links.append("ControlPanel")
            elif binary == ICED_TEA_PLUGIN_SO:
                links.append("javaplugin")
            else:
                links.append(binary)

        # binary links
        return links

    def iced_tea_web_check(self, manpages_with_postcript=None, manpages_without_postscript=None):
        itw_manpage_link = "IcedTea-Web.1.gz"
        itw_manpage_file = "icedtea-web.1.gz"
        self._document("IcedTea Web has an " + itw_manpage_file + " man page, that has no binary and " +
                       itw_manpage_link + " man page, that has no slave.")
        if not passed_or_failed(self, itw_manpage_file in manpages_without_postscript[DEFAULT]):
            log_failed_test(self, itw_manpage_file + " manpage file missing in " + DEFAULT)
        if not passed_or_failed(self, itw_manpage_link in manpages_with_postcript[DEFAULT]):
            log_failed_test(self, itw_manpage_link + " manpage link missing in " + DEFAULT)
        return


class Itw64Bit(ITW):
    def _itw_plugin_bin_location(self):
        return "/usr/lib64"

    def _itw_plugin_link_location(self):
        return "/usr/lib64/mozilla/plugins"


class Oracle(ManpageTestMethods):
    def _get_subpackages(self):
        return [DEFAULT, DEVEL, PLUGIN]

    def _clean_up_binaries(self, binaries, master, usr_bin):
        return binaries

    def _get_checked_masters(self):
        return [JAVA, JAVAC]

    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-" + self.rpms.getNvr() + "." + self._get_arch() + MANPAGE_SUFFIX]

    def _get_excludes(self):
        return oracle_exclude_list()


class Oracle6(Oracle):
    def _get_manpage_suffixes(self, subpackage):
        return [MANPAGE_SUFFIX, "-" + self.rpms.getMajorPackage() + "." + self._get_arch() + MANPAGE_SUFFIX]

    def _get_excludes(self):
        return []


class Ibm(ManpageTestMethods):
    def man_page_test(self, pkgs):
        self._document("Ibm binaries do not have manpages.")
        return self.passed, self.failed

    def manpage_file_check(self, bins, subpackage=None, plugin_bin_content=None, manpages_without_postscript=None):
        return

    def manpage_links_check(self, bins, subpackage=None, manpages_with_postscript=None, manpage_files=None):
        return


class ManpageTests(bt.BaseTest):
    instance = None

    def test_manpages(self):
        pkgs = self.getBuild()
        return self.csch.man_page_test(pkgs)

    def setCSCH(self):
        ManpageTests.instance = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking man pages for " + rpms.getMajorPackage(), la.Verbosity.TEST)

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = OpenJdk6()
                return

            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = OpenJdk7()
                return

            elif rpms.getMajorVersionSimplified() == "8"\
                    or rpms.getMajorVersionSimplified() == "9":
                if self.getCurrentArch() in gc.getX86_64Arch() + gc.getIx86archs():
                    self.csch = OpenJdk8WithDebug()
                    return
                else:
                    self.csch = OpenJdk8()
                    return
            elif int(rpms.getMajorVersionSimplified()) >= 10:
                if self.getCurrentArch() in gc.getArm32Achs():
                    self.csch = OpenJdk10()
                    return
                elif self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = OpenJdk10Debugx64()
                    return
                else:
                    self.csch = OpenJdk10Debug()
                    return

            else:
                raise ex.UnknownJavaVersionException("Unknown java version.")

        elif rpms.getVendor() == gc.ITW:
            if self.getCurrentArch() in gc.getX86_64Arch() + gc.getPower64Achs() + \
                    gc.getAarch64Arch() + gc.getS390xArch():
                self.csch = Itw64Bit()
                return
            else:
                self.csch = ITW()
                return
        elif rpms.getVendor() == gc.SUN or rpms.getVendor() == gc.ORACLE:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = Oracle6()
                return
            elif rpms.getMajorVersionSimplified() == "7" or rpms.getMajorVersionSimplified() == "8":
                self.csch = Oracle()
                return
            else:
                raise ex.UnknownJavaVersionException("Unknown java version.")

        elif rpms.getVendor() == gc.IBM:
            self.csch = Ibm()
            return

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