from testcases.alternativesTests.binaries_test_methods import BinarySlaveTestMethods
import utils.pkg_name_split as pkgsplit
from testcases.alternativesTests.binaries_test_paths import PathTest
from utils.test_utils import get_32bit_id_in_nvra, log_failed_test, passed_or_failed
from utils.test_constants import *
from utils.test_utils import two_lists_diff as diff
from utils.mock.mock_executor import DefaultMock


class OpenJdk6(BinarySlaveTestMethods):
    def _get_binary_directory(self, name):
        directory = super()._get_binary_directory(name)
        unnecessary_part = directory.split("-")[-1]
        directory = directory.replace("-" + unnecessary_part, "")
        return directory

    def _policytool_binary_subpackages(self):
        return self._get_subpackages_with_binaries()

    def handle_policytool(self, args=None):
        self._document(POLICYTOOL + " is a binary that behaves differently than normal binaries. It has binaries in {} "
                                    "subpackages, but slaves are in {} "
                                    "subpackages.".format(" and ".join(self._policytool_binary_subpackages()),
                                                          " and ".join(self._policytool_slave_subpackages())))
        for subpackage in self._policytool_binary_subpackages():
            try:
                self.installed_binaries[subpackage].remove(POLICYTOOL)
                self.passed += 1

            except KeyError:
                log_failed_test(self, POLICYTOOL + " binary not present in " + subpackage)
                self.failed += 1
                continue
        for subpkg in self._policytool_slave_subpackages():
            try:
                self.installed_slaves[subpkg].remove(POLICYTOOL)
                self.passed += 1
            except KeyError:
                log_failed_test(self, POLICYTOOL + " slave not present in " + subpkg)
                self.failed += 1
            except ValueError:
                log_failed_test(self, POLICYTOOL + " slave not present in " + subpkg)
                self.failed += 1
        return

    def _policytool_slave_subpackages(self):
        return self._get_sdk_subpackage()


class OpenJdk6PowBeArchAndX86(OpenJdk6):
    def _get_binary_directory(self, name):
        return super()._get_binary_directory(name) + "." + self._get_arch()


class OpenJdk7(OpenJdk6):
    def _get_binary_directory(self, name):
        return super(PathTest, self)._get_binary_directory(name)

    def _get_subpackages_with_binaries(self):
        return [DEFAULT, HEADLESS, DEVEL]

    def _policytool_binary_subpackages(self):
        return [DEFAULT, DEVEL]

    def _policytool_slave_subpackages(self):
        return self._get_sdk_subpackage()

    def _get_jre_subpackage(self):
        return [HEADLESS]


class OpenJdk8(OpenJdk7):
    def _policytool_slave_subpackages(self):
        return [HEADLESS]


class OpenJdk8Debug(OpenJdk8):
    def _policytool_binary_subpackages(self):
        return super()._policytool_binary_subpackages() + [DEVEL + DEBUG_SUFFIX, DEFAULT + DEBUG_SUFFIX]

    def _policytool_slave_subpackages(self):
        return super()._policytool_slave_subpackages() + [HEADLESS + DEBUG_SUFFIX]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [HEADLESS + DEBUG_SUFFIX, DEVEL + DEBUG_SUFFIX,
                                                           DEFAULT + DEBUG_SUFFIX]

    def _get_jre_subpackage(self):
        return super()._get_jre_subpackage() + [HEADLESS + DEBUG_SUFFIX]

    def _get_sdk_subpackage(self):
        return super()._get_sdk_subpackage() + [DEVEL + DEBUG_SUFFIX]


class OpenJDK8JFX(OpenJdk8Debug):
    def _jfx_check(self, list_of_elements, subpackage, slave_or_bin):
        jfx_bins = get_openjfx_binaries()
        for jfxbin in jfx_bins:
            try:
                list_of_elements[subpackage].remove(jfxbin)
                self.passed += 1
            except ValueError:
                log_failed_test(self, jfxbin + " " + slave_or_bin + " not found in " + subpackage)
                self.failed += 1
        return

    def remove_binaries_without_slaves(self, args=None):
        for subpackage in self.installed_binaries.keys():
            # subpackage == DEVEL or subpackage == DEVEL + DEBUG_SUFFIX or
            if "openjfx-devel" in subpackage:
                self._jfx_check(self.installed_binaries, subpackage, "binary")
        return


class OpenJdk8NoExports(OpenJdk8):
    # if get_var() == OJDK8 else OpenJDK8JFX if get_var() == OJDK8JFX else OpenJdk8Debug

    def check_exports_slaves(self, args=None):
        jre_subpackages = self._get_jre_subpackage()
        sdk_subpackages = self._get_sdk_subpackage()
        self._document(" and ".join([JRE, SDK]) + " are slaves, that point at jre/sdk binary directories.")
        for jsubpkg in jre_subpackages:
            try:
                self.installed_slaves[jsubpkg].remove(JRE)
                self.passed += 1
            except ValueError:
                self.list_of_failed_tests.append(JRE + " export slave missing in " + jsubpkg)
                self.failed += 1

        for ssubpkg in sdk_subpackages:
            try:
                self.installed_slaves[ssubpkg].remove(SDK)
                self.passed += 1
            except ValueError:
                self.list_of_failed_tests.append(SDK + " export slave missing in " + ssubpkg)
                self.failed += 1
        return


class OpenJdk8NoExportsDebugJFX(OpenJDK8JFX):

    def check_exports_slaves(self, args=None):
        OpenJdk8NoExports.check_exports_slaves(self)
        return


class OpenJdk8NoExportsDebug(OpenJdk8Debug):
    def check_exports_slaves(self, args=None):
        OpenJdk8NoExports.check_exports_slaves(self)
        return


class OpenJdk9(OpenJdk8):
    def _get_binary_directory_path(self, name):
        return JVM_DIR + "/" + get_32bit_id_in_nvra(pkgsplit.get_nvra(name)) + SDK_DIRECTORY

    def _check_binaries_against_hardcoded_list(self, binaries, subpackage):
        hardcoded_binaries = get_binaries_as_dict()
        if not passed_or_failed(self, subpackage in hardcoded_binaries.keys()):
            log_failed_test(self, "Binaries in unexpected subpackage: " + subpackage)
            return
        if not passed_or_failed(self, sorted(binaries) == hardcoded_binaries[subpackage]):
            log_failed_test(self, "Hardcode check: binaries are not as expected. Missing binaries: {}."
                            " Extra binaries: "
                            "{}".format(diff(hardcoded_binaries[subpackage], binaries),
                                        diff(binaries, hardcoded_binaries[subpackage])))
        return

    def check_exports_slaves(self, args=None):
        return

    def all_jre_in_sdk_check(self, args=None):
        return

    def _policytool_slave_subpackages(self):
        return [HEADLESS]

    def _policytool_binary_subpackages(self):
        return [DEFAULT]

    def document_jre_sdk(self, args=None):
        return


class OpenJdk9Debug(OpenJdk9):
    def _get_binary_directory_path(self, name):
        if DEBUG_SUFFIX in name:
            return JVM_DIR + "/" + get_32bit_id_in_nvra(pkgsplit.get_nvra(name)) + DEBUG_SUFFIX + "/" + SDK_DIRECTORY
        else:
            return super()._get_binary_directory_path(name)

    def _policytool_binary_subpackages(self):
        return super()._policytool_binary_subpackages() + [DEFAULT + DEBUG_SUFFIX]

    def _policytool_slave_subpackages(self):
        return super()._policytool_slave_subpackages() + [HEADLESS + DEBUG_SUFFIX]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [HEADLESS + DEBUG_SUFFIX, DEVEL + DEBUG_SUFFIX,
                                                           DEFAULT + DEBUG_SUFFIX]


class OpenJdk10(OpenJdk9):
    pass


class OpenJdk10Debug(OpenJdk9Debug):

    def _policytool_binary_subpackages(self):
        return []

    def _policytool_slave_subpackages(self):
        return []

    def _get_subpackages_with_binaries(self):
        subpackages = super()._get_subpackages_with_binaries()
        subpackages.remove(DEFAULT)
        subpackages.remove(DEFAULT + DEBUG_SUFFIX)
        return subpackages

    def handle_policytool(self, args=None):
        self._document("From JDK 10, there is no policytool.")
        return


class Ibm(BinarySlaveTestMethods):
    # classic and j9vm are folders, not binaries
    def _remove_excludes(self):
        subpackage = self._get_jre_subpackage()[0]
        excludes = get_ibm_folders()
        try:
            for e in excludes:
                self.installed_binaries[subpackage].remove(e)
        except ValueError:
            pass
        finally:
            return

    def remove_binaries_without_slaves(self, args=None):
        subpackage = self._get_jre_subpackage()[0]
        excludes = get_ibm_k_bins() + get_ibm_ikey_bins()
        self._document(" and ".join(excludes) + " are binaries present in {} subpackage. They are not in {} subpackage "
                                                "and have no slaves in alternatives.".format(subpackage,
                                                                                           self._get_sdk_subpackage()[0]))
        for e in excludes:
            try:
                self.installed_binaries[subpackage].remove(e)
                self.passed += 1
            except ValueError:
                log_failed_test(self, e + " not present in " + subpackage + " binaries.")
                self.failed += 1
        return

    def handle_plugin_binaries(self, args=None):
        plugin_binaries = get_plugin_binaries()
        ssubpackages = self._get_jre_subpackage()
        bsubpackages = self._get_jre_subpackage() + self._get_sdk_subpackage()
        self._document("{} are binaries replacing {} subpackage. They are present in {} subpackages and their slaves"
                       " are in {} subpackages.".format(" and ".join(plugin_binaries), PLUGIN,
                                                        " and ".join(bsubpackages)
                                                        , "".join(ssubpackages)))
        self._check_plugin_binaries_and_slaves_are_present(bsubpackages, ssubpackages)
        return

    def _check_plugin_binaries_and_slaves_are_present(self, bsubpackages, ssubpackages):
        for pbinary in get_plugin_binaries():
            for subpackage in bsubpackages:
                if not passed_or_failed(self, pbinary in self.installed_binaries[subpackage]):
                    log_failed_test(self, "Missing plugin binary " + pbinary + " in " + subpackage)
            for subpackage in ssubpackages:
                if not passed_or_failed(self, pbinary not in self.installed_slaves[subpackage]):
                    log_failed_test(self, "Missing plugin slave " + pbinary + " in " + subpackage)

    def _check_plugin_bins_and_slaves_are_not_present(self, subpackages):
        for pbinary in get_plugin_binaries():
            for subpackage in subpackages:
                if not passed_or_failed(self, pbinary not in self.installed_binaries[subpackage]):
                    log_failed_test(self, pbinary + " should not be in " + subpackage +
                                    " because this subpackage must not contain any plugin binaries.")
                    self.installed_binaries[subpackage].remove(pbinary)
                if not passed_or_failed(self, pbinary not in self.installed_slaves[subpackage]):
                    log_failed_test(self, pbinary + " should not be in " + subpackage +
                                    " because this subpackage must not contain plugin slaves.")
                    self.installed_slaves[subpackage].remove(pbinary)
        return


class Ibm390Architectures(Ibm):
    def handle_plugin_binaries(self, args=None):
        plugin_binaries = get_plugin_binaries()
        self._document("{} are not present in binaries in any subpackage. This architecture "
                       "also has no {} subpackages.".format(" and ".join(plugin_binaries), PLUGIN))
        self._check_plugin_bins_and_slaves_are_not_present(self._get_subpackages_with_binaries())
        return


class IbmWithPluginSubpackage(Ibm):
    def _get_checked_masters(self):
        return super()._get_checked_masters() + [LIBJAVAPLUGIN]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [PLUGIN]

    def handle_plugin_binaries(self, args=None):
        plugin_binaries = get_plugin_binaries()
        subpackages_without_pbins = self._get_jre_subpackage() + self._get_sdk_subpackage()
        self._document("{} are binaries related with {}. They are present and have slaves only in {} "
                       "subpackages.".format(" and ".join(plugin_binaries), PLUGIN, PLUGIN))
        self._check_plugin_bins_and_slaves_are_not_present(subpackages_without_pbins)
        self._check_plugin_binaries_and_slaves_are_present([PLUGIN], [PLUGIN])
        return


class IbmArchMasterPlugin(IbmWithPluginSubpackage):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBJAVAPLUGIN + "." + self._get_arch()]


class Oracle6(IbmWithPluginSubpackage):
    def _get_binary_directory(self, name):
        path = self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))
        release = path.split("-")[-1]
        path = path.replace("-" + release, "")
        return path

    def _remove_excludes(self):
        return

    def remove_binaries_without_slaves(self, args=None):
        return

    def handle_plugin_binaries(self, args=None):
        plugin_binaries = get_plugin_binaries()
        self._document("{} are no longer present in binaries in any subpackage.".format(" and ".join(plugin_binaries)))
        self._check_plugin_bins_and_slaves_are_not_present(self._get_subpackages_with_binaries())
        return

    def _get_subpackages_with_binaries(self):
        return BinarySlaveTestMethods(self.binaries_test)._get_subpackages_with_binaries()


class OracleNoArchPlugin(Oracle6):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBNSSCKBI_SO]


class Oracle6ArchPlugin(Oracle6):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBNSSCKBI_SO + "." + self._get_arch()]

    def _get_binary_directory(self, name):
        return super()._get_binary_directory(name) + "." + self._get_arch()


class Oracle7(Oracle6ArchPlugin):
    def _remove_excludes(self):
        exclude_list = oracle_exclude_list()
        for exclude in exclude_list:
            self._document("{} is not a binary. It is present in {} subpackages binaries. It has "
                           "no slave in alternatives.".format(exclude, DEVEL))
            try:
                self.installed_binaries[DEVEL].remove(exclude)
                self.passed += 1
            except ValueError:
                log_failed_test(self, exclude + " not present in " + DEVEL)
                self.failed += 1
        return

    def _get_subpackages_with_binaries(self):
        subpackages = BinarySlaveTestMethods(self.binaries_test)._get_subpackages_with_binaries()
        subpackages.append(JAVAFX)
        return subpackages

    def _get_checked_masters(self):
        masters = super()._get_checked_masters()
        masters.append(JAVAFXPACKAGER)
        return masters

    def _get_binary_directory(self, name):
        return PathTest(self.binaries_test)._get_binary_directory(name)


class Oracle8(Oracle7):
    def handle_plugin_binaries(self, args=None):
        return IbmWithPluginSubpackage(self.binaries_test).handle_plugin_binaries()


class Itw(BinarySlaveTestMethods):
    def check_java_cgi(self, args=None):
        return

    def all_jre_in_sdk_check(self, args=None):
        return

    def check_exports_slaves(self, args=None):
        self._document("ITW has no exports slaves.")
        return

    def _get_subpackages_with_binaries(self):
        return [DEFAULT]

    def handle_plugin_binaries(self, args=None):
        self._document("ITW replaces plugin package for OpenJDK")
        return

    def document_jre_sdk(self, args=None):
        return

    def doc_extra_binary(self, args=None):
        self._document(ITWEB_SETTINGS + " is an iced-tea binary. Its slave is " + CONTROL_PANEL)

    def _get_all_binaries_and_slaves(self, pkgs):
        DefaultMock().provideCleanUsefullRoot()
        original_binaries = DefaultMock().execute_ls(USR_BIN)[0].split("\n")
        installed_binaries, installed_slaves = super()._get_all_binaries_and_slaves(pkgs)
        installed_binaries = self._remove_links_from_usr_bin(installed_binaries)
        for subpackage in installed_binaries.keys():
            all_binaries = installed_binaries[subpackage]
            installed_binaries[subpackage] = diff(all_binaries, original_binaries)

        settings = ITWEB_SETTINGS
        bins = []
        for b in installed_binaries[DEFAULT]:
            bins.append(b.replace(".itweb", ""))
        installed_binaries[DEFAULT] = bins

        try:
            installed_binaries[DEFAULT].remove(settings)
            installed_binaries[DEFAULT].append(CONTROL_PANEL)
            self.passed += 1

        except ValueError:
            log_failed_test(self, settings + " binary not in " + DEFAULT + " subpackage")
            self.failed += 1
        return installed_binaries, installed_slaves
    
    def _get_binary_directory_path(self, name):
        return USR_BIN

    def _get_checked_masters(self):
        return [LIBJAVAPLUGIN + "." + self._get_arch()]

    def _remove_links_from_usr_bin(self, installed_binaries):
        # perhaps doc
        links = []
        for b in installed_binaries[DEFAULT]:
            if ".itweb" not in b:
                links.append(b)
        for l in links:
            installed_binaries[DEFAULT].remove(l)
        return installed_binaries
