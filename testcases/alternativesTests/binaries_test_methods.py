from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch, log_failed_test
import os
import config.runtime_config as rc
from testcases.alternativesTests.binaries_test_paths import PathTest
from utils.test_constants import *
from utils.test_utils import two_lists_diff as diff
from utils.test_utils import passed_or_failed
from outputControl import logging_access as la


class GetAllBinariesAndSlaves(PathTest):
    rpms = rc.RuntimeConfig().getRpmList()

    def document_subpackages(self, args=None):
        self._document("Binaries and slaves are present in following subpackages: " +
                       ", ".join(self._get_subpackages_with_binaries()))

    def check_exports_slaves(self, args=None):
        jre_slaves = get_exports_slaves_jre()
        sdk_slaves = get_exports_slaves_sdk()
        jre_subpackages = self._get_jre_subpackage()
        sdk_subpackages = self._get_sdk_subpackage()
        self._document(" and ".join(jre_slaves + sdk_slaves) + " are slaves, that point at export "
                                                               "directories")
        for jsubpkg in jre_subpackages:
            for jslave in jre_slaves:
                try:
                    self.installed_slaves[jsubpkg].remove(jslave)
                    self.passed += 1
                except ValueError:
                    self.list_of_failed_tests.append(jslave + " export slave missing in " + jsubpkg)
                    self.failed += 1

        for ssubpkg in sdk_subpackages:
            for sslave in sdk_slaves:
                try:
                    self.installed_slaves[ssubpkg].remove(sslave)
                    self.passed += 1
                except ValueError:
                    self.list_of_failed_tests.append(sslave + " export slave missing in " + ssubpkg)
                    self.failed += 1
        return

    def check_subdirectory_slaves(self, args=None):
        jre_slave = "jre"
        sdk_slave = "java_sdk"
        self._document(jre_slave + " and " + sdk_slave + " are slaves that point at directories in /usr/lib/jvm.")
        jre_subpackages = self._get_jre_subpackage()
        sdk_subpackages = self._get_sdk_subpackage()
        for jsubpkg in jre_subpackages:
            try:
                self.installed_slaves[jsubpkg].remove(jre_slave)
                self.passed += 1
            except ValueError:
                self.list_of_failed_tests.append(jre_slave + " slave missing in " + jsubpkg)
                self.failed += 1

        for ssubpkg in sdk_subpackages:
                try:
                    self.installed_slaves[ssubpkg].remove(sdk_slave)
                    self.passed += 1
                except ValueError:
                    self.list_of_failed_tests.append(sdk_slave + " slave missing in " + ssubpkg)
                    self.failed += 1
        return

    def get_slaves(self, _subpkg):
        checked_masters = self._get_checked_masters()
        self._document("Checking slaves for masters:"
                       " {}".format(" and ".join(replace_archs_with_general_arch(checked_masters, self._get_arch()))))

        masters = DefaultMock().get_masters()
        clean_slaves = []
        for m in checked_masters:
            if m not in masters:
                continue
            try:
                slaves = DefaultMock().get_slaves(m)
            except MockExecutionException:
                self.binaries_test.log("No relevant slaves were present for " + _subpkg + ".", la.Verbosity.TEST)
                continue
            self.binaries_test.log("Found slaves for {}: {}".format(_subpkg, str(slaves)), la.Verbosity.TEST)

            if m in [JAVA, JAVAC]:
                clean_slaves.append(m)

            # skipping manpage slaves
            for slave in slaves:
                if not slave.endswith("1.gz"):
                    clean_slaves.append(slave)

        return clean_slaves

    def _get_all_binaries_and_slaves(self, pkgs):

        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))
            if _subpkg in subpackages_without_alternatives() + get_javadoc_dirs():
                self.binaries_test.log("Skipping binaries extraction for " + _subpkg)
                self.skipped.append(_subpkg)
                continue
            if not DefaultMock().postinstall_exception_checked(pkg):
                self.binaries_test.log("Failed to execute postinstall. Slaves will not be found for " + _subpkg)
            binary_directory_path = self._get_binary_directory_path(name)
            binaries = DefaultMock().execute_ls(binary_directory_path)

            if binaries[1] != 0:
                self.binaries_test.log("Location {} does not exist, binaries test skipped "
                                       "for ".format(binary_directory_path) + name, la.Verbosity.TEST)

                continue
            else:
                self.binaries_test.log("Binaries found at {}: {}".format(binary_directory_path,
                                                                         ", ".join(binaries[0].split("\n"))), la.Verbosity.TEST)

            slaves = self.get_slaves(_subpkg)

            self.installed_slaves[_subpkg] = slaves
            self.installed_binaries[_subpkg] = binaries[0].split("\n")

        return self.installed_binaries, self.installed_slaves


class BinarySlaveTestMethods(GetAllBinariesAndSlaves):
    # checks if all jre binaries are in sdk and deletes them from there
    def all_jre_in_sdk_check(self, args=None):
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
                    jre = self.installed_binaries[subpkg]
                    sdk = self.installed_binaries[sdk_subpkg]
                elif DEBUG_SUFFIX not in subpkg and DEBUG_SUFFIX not in sdk_subpkg:
                    sdk = self.installed_binaries[sdk_subpkg]
                    jre = self.installed_binaries[subpkg]
                else:
                    continue

                for j in jre:
                    try:
                        sdk.remove(j)
                        self.passed += 1
                    except ValueError:
                        log_failed_test(self, "Binary " + j + " is present in JRE, but is missing in SDK.")
                        self.failed += 1
        return

    def _perform_all_checks(self):
        if not passed_or_failed(self, sorted(self.installed_slaves.keys()) == sorted(self.installed_binaries.keys())):
            log_failed_test(self, "Subpackages that contain binaries and slaves do not match. Subpackages with"
                            "binaries: {}, Subpackages with slaves: {}".format(
                                                                sorted(self.installed_binaries.keys()),
                                                                sorted(self.installed_slaves.keys())))
        try:
            for subpackage in self._get_subpackages_with_binaries():
                slaves = self.installed_slaves[subpackage]
                binaries = self.installed_binaries[subpackage]
                if not passed_or_failed(self, sorted(binaries) == sorted(slaves)):
                    log_failed_test(self, "Binaries do not match slaves in {}. Missing binaries: {}"
                                    " Missing slaves: {}".format(subpackage, diff(slaves, binaries),
                                                                 diff(binaries, slaves)))
                self._check_binaries_against_hardcoded_list(binaries, subpackage)

        except KeyError as err:
            self.failed += 1
            log_failed_test(self, err.__str__())
        return

    # main check, that includes all small checks and at the end compares the binaries with slaves
    def check_binaries_with_slaves(self, pkgs):
        self._document("Every binary must have a slave in alternatives.")
        self._get_all_binaries_and_slaves(pkgs)
        self._remove_excludes()
        self.check_java_cgi()
        self.handle_policytool()
        self.remove_binaries_without_slaves()
        self.handle_plugin_binaries()
        self.all_jre_in_sdk_check()
        self.check_exports_slaves()
        self.check_subdirectory_slaves()

        self._perform_all_checks()
        self.path_test()

        for subpkg in self.installed_binaries.keys():
                    self.binaries_test.log("Presented binaries for {}: ".format(subpkg) +
                                           str(sorted(self.installed_binaries[subpkg])), la.Verbosity.TEST)
                    self.binaries_test.log("Presented slaves for {}: ".format(subpkg) +
                                           str(sorted(self.installed_slaves[subpkg])), la.Verbosity.TEST)

        self.binaries_test.log("Failed tests: " + "\n ".join(self.list_of_failed_tests), la.Verbosity.ERROR)
        return self.passed, self.failed
