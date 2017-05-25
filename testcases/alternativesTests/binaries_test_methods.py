from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch
import os
import config.runtime_config as rc
from testcases.alternativesTests.binaries_test_paths import PathTest
from utils.test_constants import *
from utils.test_utils import two_lists_diff as diff


class GetAllBinariesAndSlaves(PathTest):
    rpms = rc.RuntimeConfig().getRpmList()

    def document_subpackages(self, args):
        self._document("Binaries and slaves are present in following subpackages: " +
                       ", ".join(self._get_subpackages_with_binaries()))

    def check_exports_slaves(self, installed_slaves):
        jre_slaves = get_exports_slaves_jre()
        sdk_slaves = get_exports_slaves_sdk()
        jre_subpackages = self._get_jre_subpackage()
        sdk_subpackages = self._get_sdk_subpackage()
        self._document(" and ".join(jre_slaves + sdk_slaves) + " are slaves, that point at export "
                                                               "directories and jre/sdk binarys directories.")
        for jsubpkg in jre_subpackages:
            for jslave in jre_slaves:
                try:
                    installed_slaves[jsubpkg].remove(jslave)
                except ValueError:
                    self.failed_tests.append(jslave + " export slave missing in " + jsubpkg)

        for ssubpkg in sdk_subpackages:
            for sslave in sdk_slaves:
                try:
                    installed_slaves[ssubpkg].remove(sslave)
                except ValueError:
                    self.failed_tests.append(sslave + " export slave missing in " + ssubpkg)
        return installed_slaves

    def get_slaves(self, _subpkg):
        checked_masters = self._get_checked_masters()
        self._document("Checking slaves for masters: {}".format(" and ".join(replace_archs_with_general_arch(checked_masters, self._get_arch()))))

        masters = DefaultMock().get_masters()
        clean_slaves = []
        for m in checked_masters:
            if m not in masters:
                continue
            try:
                slaves = DefaultMock().get_slaves(m)
            except MockExecutionException:
                self.binaries_test.log("No relevant slaves were present for " + _subpkg + ".")
                continue

            if m in [JAVA, JAVAC]:
                clean_slaves.append(m)

            # skipping manpage slaves
            for slave in slaves:
                if not slave.endswith("1.gz"):
                    clean_slaves.append(slave)

        return clean_slaves

    def _get_all_binaries_and_slaves(self, pkgs):

        # map of binaries, where key = subpackage, value = binaries
        installed_binaries = {}
        # map of slaves, where key = subpackage, value = slaves
        installed_slaves = {}

        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))
            a = self._get_subpackages_with_binaries()
            if _subpkg not in a:
                continue
            if not DefaultMock().postinstall_exception_checked(pkg):
                self.skipped.append(_subpkg)
                continue
            binary_directory_path = self._get_binary_directory_path(name)
            binaries = DefaultMock().execute_ls(binary_directory_path)

            if binaries[1] != 0:
                self.binaries_test.log("Location {} does not exist, binaries test skipped "
                                       "for ".format(binary_directory_path) + name)
                continue
            slaves = self.get_slaves(_subpkg)

            installed_slaves[_subpkg] = slaves
            installed_binaries[_subpkg] = binaries[0].split("\n")

        return installed_binaries, installed_slaves


class BinarySlaveTestMethods(GetAllBinariesAndSlaves):
    # checks if all jre binaries are in sdk and deletes them from there
    def all_jre_in_sdk_check(self, installed_binaries):
        jre_subpackages = self._get_jre_subpackage()
        sdk_subpackages = self._get_sdk_subpackage()
        self._document("Jre binaries must be present in {} subpackages. Jre slaves are in {} subpackages. "
                       "Sdk binaries must be present in {} subpackages. Sdk slaves are in {} "
                       "subpackages. ".format(" and ".join(jre_subpackages + sdk_subpackages),
                                              " and ".join(jre_subpackages),
                                              " and ".join(sdk_subpackages),
                                              " and ".join(sdk_subpackages)))

        for subpkg in jre_subpackages:
            for sdk_subpkg in sdk_subpackages:
                if DEBUG_SUFFIX in subpkg and DEBUG_SUFFIX in sdk_subpkg:
                    jre = installed_binaries[subpkg]
                    sdk = installed_binaries[sdk_subpkg]
                elif DEBUG_SUFFIX not in subpkg and DEBUG_SUFFIX not in sdk_subpkg:
                    sdk = installed_binaries[sdk_subpkg]
                    jre = installed_binaries[subpkg]
                else:
                    continue

                for j in jre:
                    try:
                        sdk.remove(j)
                    except ValueError:
                        self.failed_tests.append("Binary " + j + " is present in JRE, but is missing in SDK.")

        return installed_binaries

    def _perform_all_checks(self, installed_slaves, installed_binaries):
        if sorted(installed_slaves.keys()) != sorted(installed_binaries.keys()):
            self.failed_tests.append("Subpackages that contain binaries and slaves do not match. Subpackages with"
                                     "binaries: {}, Subpackages with slaves: {}".format(
                                                                sorted(installed_binaries.keys()),
                                                                sorted(installed_slaves.keys())))
        try:
            for subpackage in self._get_subpackages_with_binaries():
                slaves = installed_slaves[subpackage]
                binaries = installed_binaries[subpackage]
                if sorted(binaries) != sorted(slaves):
                    self.failed_tests.append("Binaries do not match slaves in {}. Missing binaries: {}"
                                             " Missing slaves: {}".format(subpackage, diff(slaves, binaries),
                                                                          diff(binaries, slaves)))
                self._check_binaries_against_hardcoded_list(binaries, subpackage)

        except KeyError as err:
            self.failed_tests.append(err)
        return

    # main check, that includes all small checks and at the end compares the binaries with slaves
    def check_binaries_with_slaves(self, pkgs):
        self._document("Every binary must have a slave in alternatives.")
        installed_binaries, installed_slaves = self._get_all_binaries_and_slaves(pkgs)
        installed_binaries = self._remove_excludes(installed_binaries)
        installed_binaries = self.check_java_cgi(installed_binaries)
        installed_binaries, installed_slaves = self.handle_policytool(installed_binaries, installed_slaves)
        installed_binaries = self.remove_binaries_without_slaves(installed_binaries)
        installed_binaries, installed_slaves = self.handle_plugin_binaries(installed_binaries, installed_slaves)
        self.all_jre_in_sdk_check(installed_binaries)
        installed_slaves = self.check_exports_slaves(installed_slaves)

        self._perform_all_checks(installed_slaves, installed_binaries)
        self.path_test(installed_binaries, self._get_subpackages_with_binaries())

        for subpkg in installed_binaries.keys():
                    self.binaries_test.log("Presented binaries for {}: ".format(subpkg) +
                                           str(sorted(installed_binaries[subpkg])))
                    self.binaries_test.log("Presented slaves for {}: ".format(subpkg) +
                                           str(sorted(installed_slaves[subpkg])))

        self.binaries_test.log("Failed tests: " + ", ".join(self.failed_tests))
        print(installed_binaries)
        print(installed_slaves)
        print(self.failed_tests)
        assert len(self.failed_tests) == 0
