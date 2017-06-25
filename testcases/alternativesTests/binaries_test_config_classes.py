from testcases.alternativesTests.binaries_test_methods import BinarySlaveTestMethods
import utils.pkg_name_split as pkgsplit
from testcases.alternativesTests.binaries_test_paths import PathTest
from utils.test_utils import get_32bit_id_in_nvra, log_failed_test
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

    def handle_policytool(self, installed_binaries, installed_slaves=None):
        self._document(POLICYTOOL + " is a binary that behaves differently than normal binaries. It has binaries in {} "
                                    "subpackages, but slaves are in {} "
                                    "subpackages.".format(" and ".join(self._policytool_binary_subpackages()),
                                                          " and ".join(self._policytool_slave_subpackages())))
        for subpackage in self._policytool_binary_subpackages():
            try:
                installed_binaries[subpackage].remove(POLICYTOOL)

            except KeyError:
                log_failed_test(self, POLICYTOOL + " binary not present in " + subpackage)
                continue
        for subpkg in self._policytool_slave_subpackages():
            try:
                installed_slaves[subpkg].remove(POLICYTOOL)
            except KeyError:
                log_failed_test(self, POLICYTOOL + " slave not present in " + subpkg)
        return installed_binaries, installed_slaves

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


class OpenJdk9(OpenJdk8):
    def _get_binary_directory_path(self, name):
        return JVM_DIR + "/" + get_32bit_id_in_nvra(pkgsplit.get_nvra(name)) + SDK_DIRECTORY

    def _check_binaries_against_hardcoded_list(self, binaries, subpackage):
        hardcoded_binaries = get_binaries_as_dict()
        if subpackage not in hardcoded_binaries.keys():
            log_failed_test(self, "Binaries in unexpected subpackage: " + subpackage)
            return
        if sorted(binaries) != hardcoded_binaries[subpackage]:
            log_failed_test(self, "Hardcode check: binaries are not as expected. Missing binaries: {}."
                            " Extra binaries: "
                                     "{}".format(diff(hardcoded_binaries[subpackage], binaries),
                                                 diff(binaries, hardcoded_binaries[subpackage])))
        return

    def check_exports_slaves(self, installed_slaves):
        return installed_slaves

    def all_jre_in_sdk_check(self, installed_binaries):
        return installed_binaries

    def _policytool_slave_subpackages(self):
        return [HEADLESS]

    def _policytool_binary_subpackages(self):
        return [DEFAULT]

    def document_jre_sdk(self, args):
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


class Ibm(BinarySlaveTestMethods):
    # classic and j9vm are folders, not binaries
    def _remove_excludes(self, binaries):
        subpackage = self._get_jre_subpackage()[0]
        excludes = get_ibm_folders()
        try:
            for e in excludes:
                binaries[subpackage].remove(e)
        except ValueError:
            pass
        finally:
            return binaries

    def remove_binaries_without_slaves(self, installed_binaries):
        subpackage = self._get_jre_subpackage()[0]
        excludes = get_ibm_k_bins() + get_ibm_ikey_bins()
        self._document(" and ".join(excludes) + " are binaries present in {} subpackage. They are not in {} subpackage "
                                                "and have no slaves in alternatives.".format(subpackage,
                                                                                           self._get_sdk_subpackage()[0]))
        for e in excludes:
            try:
                installed_binaries[subpackage].remove(e)
            except ValueError:
                log_failed_test(self, e + " not present in " + subpackage + " binaries.")
        return installed_binaries

    def handle_plugin_binaries(self, binaries, slaves=None):
        plugin_binaries = get_plugin_binaries()
        ssubpackages = self._get_jre_subpackage()
        bsubpackages = self._get_jre_subpackage() + self._get_sdk_subpackage()
        self._document("{} are binaries replacing {} subpackage. They are present in {} subpackages and their slaves"
                       " are in {} subpackages.".format(" and ".join(plugin_binaries), PLUGIN,
                                                        " and ".join(bsubpackages)
                                                        , "".join(ssubpackages)))
        self._check_plugin_binaries_and_slaves_are_present(binaries, slaves, bsubpackages, ssubpackages)
        return binaries, slaves

    def _check_plugin_binaries_and_slaves_are_present(self, binaries, slaves, bsubpackages, ssubpackages):
        for pbinary in get_plugin_binaries():
            for subpackage in bsubpackages:
                if pbinary not in binaries[subpackage]:
                    log_failed_test(self, "Missing plugin binary " + pbinary + " in " + subpackage)
            for subpackage in ssubpackages:
                if pbinary not in slaves[subpackage]:
                    log_failed_test(self, "Missing plugin slave " + pbinary + " in " + subpackage)

    def _check_plugin_bins_and_slaves_are_not_present(self, binaries, slaves, subpackages):
        for pbinary in get_plugin_binaries():
            for subpackage in subpackages:
                if pbinary in binaries[subpackage]:
                    log_failed_test(self, pbinary + " should not be in " + subpackage +
                                    " because this subpackage must not contain any plugin binaries.")
                    binaries[subpackage].remove(pbinary)
                if pbinary in slaves[subpackage]:
                    log_failed_test(self, pbinary + " should not be in " + subpackage +
                                    " because this subpackage must not contain plugin slaves.")
                    slaves[subpackage].remove(pbinary)
        return binaries, slaves


class Ibm390Architectures(Ibm):
    def handle_plugin_binaries(self, binaries, slaves=None):
        plugin_binaries = get_plugin_binaries()
        self._document("{} are not present in binaries in any subpackage. This architecture "
                       "also has no {} subpackages.".format(" and ".join(plugin_binaries), PLUGIN))
        binaries, slaves = self._check_plugin_bins_and_slaves_are_not_present(binaries, slaves,
                                                                              self._get_subpackages_with_binaries())
        return binaries, slaves


class IbmWithPluginSubpackage(Ibm):
    def _get_checked_masters(self):
        return super()._get_checked_masters() + [LIBJAVAPLUGIN]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [PLUGIN]

    def handle_plugin_binaries(self, binaries, slaves = None):
        plugin_binaries = get_plugin_binaries()
        subpackages_without_pbins = self._get_jre_subpackage() + self._get_sdk_subpackage()
        self._document("{} are binaries related with {}. They are present and have slaves only in {} "
                       "subpackages.".format(" and ".join(plugin_binaries), PLUGIN, PLUGIN))
        binaries, slaves = self._check_plugin_bins_and_slaves_are_not_present(binaries, slaves,
                                                                              subpackages_without_pbins)
        self._check_plugin_binaries_and_slaves_are_present(binaries, slaves, [PLUGIN], [PLUGIN])
        return binaries, slaves


class IbmArchMasterPlugin(IbmWithPluginSubpackage):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBJAVAPLUGIN + "." + self._get_arch()]


class Oracle6(IbmWithPluginSubpackage):

    def _get_binary_directory(self, name):
        path = self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))
        release = path.split("-")[-1]
        path = path.replace("-" + release, "")
        return path

    def _remove_excludes(self, binaries):
        return binaries

    def remove_binaries_without_slaves(self, installed_binaries):
        return installed_binaries


class OracleNoArchPlugin(Oracle6):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBNSSCKBI_SO]


class Oracle6ArchPlugin(Oracle6):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBNSSCKBI_SO + "." + self._get_arch()]

    def _get_binary_directory(self, name):
        return super()._get_binary_directory(name) + "." + self._get_arch()


class Oracle7and8(Oracle6ArchPlugin):
    def _remove_excludes(self, binaries):
        exclude_list = oracle_exclude_list()
        for exclude in exclude_list:
            self._document("{} is not a binary. It is present in {} subpackages binaries. It has "
                           "no slave in alternatives.".format(exclude, DEVEL))
            try:
                binaries[DEVEL].remove(exclude)
            except ValueError:
                log_failed_test(self, exclude + " not present in " + DEVEL)
        return binaries

    def _get_subpackages_with_binaries(self):
        subpackages = super()._get_subpackages_with_binaries()
        subpackages.append(JAVAFX)
        return subpackages

    def _get_checked_masters(self):
        masters = super()._get_checked_masters()
        masters.append(JAVAFXPACKAGER)
        return masters

    def _get_binary_directory(self, name):
        return PathTest(self.binaries_test)._get_binary_directory(name)


class Itw(BinarySlaveTestMethods):
    def check_java_cgi(self, installed_binaries):
        return installed_binaries

    def all_jre_in_sdk_check(self, installed_binaries):
        return installed_binaries

    def check_exports_slaves(self, installed_slaves):
        self._document("ITW has no exports slaves.")
        return installed_slaves

    def _get_subpackages_with_binaries(self):
        return [DEFAULT]

    def handle_plugin_binaries(self, binaries, slaves=None):
        self._document("ITW replaces plugin package for OpenJDK")
        return binaries, slaves

    def document_jre_sdk(self, args):
        return

    def doc_extra_binary(self, args):
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
        controlpanel = CONTROL_PANEL
        bins = []
        for b in installed_binaries[DEFAULT]:
            bins.append(b.replace(".itweb", ""))
        installed_binaries[DEFAULT] = bins


        try:
            installed_binaries[DEFAULT].remove(settings)
            installed_binaries[DEFAULT].append(CONTROL_PANEL)

        except ValueError:
            log_failed_test(self, settings + " binary not in " + DEFAULT + " subpackage")
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
