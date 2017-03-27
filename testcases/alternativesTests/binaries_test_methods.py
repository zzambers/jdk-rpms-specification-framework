from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch
import os
import config.runtime_config as rc
from testcases.alternativesTests.binaries_test_paths import PathTest, JAVA,JRE_LOCATION,\
SDK_LOCATION,DEBUG_SUFFIX, JAVAC, JVM_DIR, BINARIES, SUBPACKAGES, EXPECTED_SUBPACKAGES, PRESENTED_SUBPACKAGES, \
SLAVE, SLAVES, NOT_PRESENT_IN, BINARY, MISSING, PRESENTED, MUST_BE_IN


class GetAllBinariesAndSlaves(PathTest):
    rpms = rc.RuntimeConfig().getRpmList()

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

    def _get_binaries_and_exports_directories(self, _subpkg, loc, name):
        directories = loc[0].split("\n")

        # gets location of binaries
        target = self._get_target(name)

        if DEBUG_SUFFIX in _subpkg:
            target += DEBUG_SUFFIX

        if target not in directories:
            self.failed_tests.append("Directory {} was not found".format(target))
            self.binaries_test.log("Directory {}, where the {}are supposed to be located, was not found."
                                   " Either it does not exist, or the the path is invalid.".format(target, BINARIES))
            return [], []

        binariesJRE = DefaultMock().execute_ls(JVM_DIR + target + "/jre/bin")
        binariesSDK = DefaultMock().execute_ls(JVM_DIR + target + "/bin")
        binaries = []
        dirs = []

        if binariesJRE[1] == 0:
            binariesJRE = binariesJRE[0].split("\n")
            for bin in binariesJRE:
                binaries.append(bin)
            dirs.append(DefaultMock().execute_ls(JVM_DIR + target + "/jre"))
            dirs.append(DefaultMock().execute_ls(self._get_exports_directory(target)))

        if binariesSDK[1] == 0:
            exports_target = self._get_alternative_exports_target(target)
            binariesSDK = binariesSDK[0].split("\n")
            for bin in binariesSDK:
                binaries.append(bin)
            dirs.append(DefaultMock().execute_ls(JVM_DIR + target))
            self.exports_dir_check(dirs, exports_target, _subpkg)

        binaries = self._clean_bin_dir_for_ibm(binaries)
        return binaries, dirs

    def get_all_binaries_and_slaves(self, pkgs):
        docs = "JRE binaries must be present in {} subpackages.".format(" and ".join(
                                    self._get_jre_sdk_locations()[JRE_LOCATION] +
                                    self._get_jre_sdk_locations()[SDK_LOCATION]))

        docs += "\n - JRE slaves have {} master and are in {} subpackages.".format(JAVA," and ".join(
                                    self._get_slave_pkgs()[JRE_LOCATION]))

        docs += "\n - SDK binaries must be present in {} subpackages.".format(" and ".join(
                                    self._get_jre_sdk_locations()[SDK_LOCATION]))
        n = 0
        for jre in self._get_slave_pkgs()[0]:
            for sdk in self._get_slave_pkgs()[1]:

                if (DEBUG_SUFFIX in jre and DEBUG_SUFFIX in sdk ) or (DEBUG_SUFFIX not in jre and DEBUG_SUFFIX not in sdk):
                    if n > 0:
                        docs += "\n - SDK slaves are also in {} subpackage, except for slaves that are already " \
                                "present in {} subpackage.".format(sdk, jre)
                    else:
                        docs += "\n - SDK slaves have {} master and are in {} subpackage, except for slaves that " \
                                "are already present in {} subpackage.".format(JAVAC, sdk, jre)
                        n += 1

        self._document(docs)
        # map of binaries, where key = subpackage, value = binaries
        pkg_binaries = {}
        # map of slaves, where key = subpackage, value = slaves
        installed_slaves = {}
        # map that stores information about slaves that point on directories instead of binaries
        export_directories = {}

        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))

            if not DefaultMock().postinstall_exception_checked(pkg):
                self.skipped.append(_subpkg)
                continue
            loc = DefaultMock().execute_ls(JVM_DIR)

            if loc[1] != 0:
                self.binaries_test.log("Location {} does not exist, binaries test skipped for ".format(JVM_DIR) + name)
                self.skipped.append(_subpkg)
                continue
            slaves = self.get_slaves(_subpkg)

            installed_slaves[_subpkg] = slaves
            pkg_binaries[_subpkg], export_directories[_subpkg] = self._get_binaries_and_exports_directories(_subpkg,
                                                                                                            loc, name)
        return pkg_binaries, installed_slaves, export_directories


class BinarySlaveTestMethods(GetAllBinariesAndSlaves):
    # checks if slaves and binaries are present only in expected subpackages
    def _check_slave_and_binary_subpackages(self, installed_slaves, pkg_binaries):
        expected_binaries_pkgs = self._get_expected_subpkgs(self._get_jre_sdk_locations())
        if sorted(expected_binaries_pkgs) != sorted(list(pkg_binaries.keys())):
            self.failed_tests.append(SUBPACKAGES + ", that contain " + BINARIES + ", are wrong.")
            self.binaries_test.log(BINARIES + " were found in unexpected " + SUBPACKAGES + " or are missing in "
                                   "some " + SUBPACKAGES)
            self.binaries_test.log(EXPECTED_SUBPACKAGES + str(sorted(expected_binaries_pkgs)))
            self.binaries_test.log(PRESENTED_SUBPACKAGES + str(sorted(pkg_binaries.keys())))

        if sorted(expected_binaries_pkgs) != sorted(list(installed_slaves.keys())):
            self.failed_tests.append(SUBPACKAGES + ", that contain " + SLAVE + ", are wrong.")
            self.binaries_test.log(BINARIES + " were found in unexpected " + SUBPACKAGES + " or are missing in "
                                                                                           "some " + SUBPACKAGES)
            self.binaries_test.log(EXPECTED_SUBPACKAGES + str(sorted(expected_binaries_pkgs)))
            self.binaries_test.log(PRESENTED_SUBPACKAGES + str(sorted(pkg_binaries.keys())))

        return

    # checks if exports and jre/sdk directories are in place, does not check default for JDK 7/8
    def _export_directories_check(self, export_directories):
        expected_slave_pkgs = self._get_slave_pkgs()
        for subpkg in (expected_slave_pkgs[JRE_LOCATION] + expected_slave_pkgs[SDK_LOCATION]):
            for dir in export_directories[subpkg]:
                if dir[1] != 0:
                    self.failed_tests.append("Export directory check error: " + dir[0] + " for subpackage " + subpkg)
                    self.binaries_test.log("Export directories are not as expected. {} error occurred "
                                           "for {} subpackage.".format(dir, subpkg))
        return

    # checks if exports and jre/sdk slaves are present
    def jre_sdk_exports_check(self, installed_slaves):
        jre_exp = ["jre_exports", "jre"]
        sdk_exp = ["java_sdk_exports", "java_sdk"]
        self._document(" and ".join(jre_exp) + " are "+ JAVA + " " + SLAVES + ", " + " and ".join(sdk_exp) +
                       " are " + JAVAC + " " + SLAVES +
                       "- they are not binaries, their links point at jvm-exports and jre/sdk directories.")
        expected_slave_pkgs = self._get_slave_pkgs()

        for subpkg in expected_slave_pkgs[JRE_LOCATION]:
            for slave in jre_exp:
                if slave not in installed_slaves[subpkg]:
                    self.failed_tests.append(slave + NOT_PRESENT_IN + JAVA + " " + SLAVES)
                    self.binaries_test.log(slave + NOT_PRESENT_IN + JAVA + " " + SLAVES)
                else:
                    installed_slaves[subpkg].remove(slave)

        for subpkg in expected_slave_pkgs[SDK_LOCATION]:
            for slave in sdk_exp:
                if slave not in installed_slaves[subpkg]:
                    self.failed_tests.append(slave + NOT_PRESENT_IN + JAVAC + " " + SLAVES)
                    self.binaries_test.log(slave + NOT_PRESENT_IN + JAVAC + " " + SLAVES)
                else:
                    installed_slaves[subpkg].remove(slave)

        return installed_slaves

    # checks if all jre binaries are in sdk and deletes them from there
    def _all_jre_in_sdk_check(self, pkg_binaries):
        expected_slave_pkgs = self._get_slave_pkgs()
        for subpkg in expected_slave_pkgs[JRE_LOCATION]:
            for sbpkg in expected_slave_pkgs[1]:
                if DEBUG_SUFFIX in subpkg and DEBUG_SUFFIX in sbpkg:
                    jre = pkg_binaries[subpkg]
                    sdk = pkg_binaries[sbpkg]
                elif DEBUG_SUFFIX not in subpkg and DEBUG_SUFFIX not in sbpkg:
                    sdk = pkg_binaries[sbpkg]
                    jre = pkg_binaries[subpkg]
                else:
                    continue

                for j in jre:
                    if j in sdk:
                        sdk.remove(j)
                    else:
                        self.failed_tests.append(j + " not in sdk")
                        self.binaries_test.log(BINARY + j + " was present in JRE directory, "
                                               "but is missing in SDK directory.")

        return pkg_binaries

    # main check, that includes all small checks and at the end compares the binaries with slaves
    def _check_binaries_with_slaves(self, pkgs):
        pkg_binaries, installed_slaves, export_directories = self.get_all_binaries_and_slaves(pkgs)
        self._check_slave_and_binary_subpackages(installed_slaves, pkg_binaries)
        self._export_directories_check(export_directories)
        self.document_plugin_and_related_binaries(pkg_binaries, installed_slaves)
        installed_slaves = self.jre_sdk_exports_check(installed_slaves)
        pkg_binaries = self.check_policytool_for_jdk(pkg_binaries)
        pkg_binaries, installed_slaves = self.doc_and_clean_no_slave_binaries(pkg_binaries, installed_slaves)
        pkg_binaries = self._all_jre_in_sdk_check(pkg_binaries)
        pkg_binaries = self.check_java_cgi(pkg_binaries)
        self.path_test(pkg_binaries, self._get_expected_subpkgs(self._get_slave_pkgs()))

        # compares binaries with slaves, creates decent error output in case there are binaries/slaves extra/missing
        missplaced = set([])
        jre_loc = self._get_slave_pkgs()[JRE_LOCATION][0]
        sdk_loc = self._get_slave_pkgs()[SDK_LOCATION][0]
        for subpkg in pkg_binaries.keys():
            if sorted(pkg_binaries[subpkg]) != sorted(installed_slaves[subpkg]):
                not_in_slaves = []
                not_in_binaries = []
                for bin in pkg_binaries[subpkg]:
                    if bin not in installed_slaves[subpkg]:
                        not_in_slaves.append(bin)
                for slave in installed_slaves[subpkg]:
                    if slave not in pkg_binaries[subpkg]:
                        not_in_binaries.append(slave)
                if jre_loc is not None and sdk_loc is not None:
                    for b in not_in_binaries + not_in_slaves:
                        if b in pkg_binaries[jre_loc] and pkg_binaries[sdk_loc]:
                            if b in installed_slaves[sdk_loc]:
                                if b in not_in_binaries:
                                    not_in_binaries.remove(b)
                                else:
                                    not_in_slaves.remove(b)
                                missplaced.add(b)

                if len(not_in_binaries) != 0 or len(not_in_slaves) != 0:
                    self.failed_tests.append(BINARIES + "do not match " + SLAVES + "in " + subpkg + ". " +
                                             MISSING + BINARIES + ": {}, ".format(not_in_binaries) + MISSING + SLAVES +
                                             ": {}.".format(not_in_slaves))
                    self.binaries_test.log(BINARIES + "do not match " + SLAVES + "in " + subpkg + ". " +
                                           MISSING + BINARIES + ": {}, ".format(not_in_binaries) + MISSING + SLAVES +
                                           ": {}.".format(not_in_slaves))

                    self.binaries_test.log(PRESENTED + BINARIES + "for {}: ".format(subpkg) +
                                           str(sorted(pkg_binaries[subpkg])))
                    self.binaries_test.log(PRESENTED + SLAVES + "for {}: ".format(subpkg) +
                                           str(sorted(installed_slaves[subpkg])))
        for mp in missplaced:
            self.failed_tests.append("Missplaced " + SLAVE + mp + ", it" + MUST_BE_IN + jre_loc + " " + SLAVES +
                                     ", but is in " + sdk_loc + " " + SLAVES)

            self.binaries_test.log("Missplaced " + SLAVE + mp + ", it" + MUST_BE_IN + jre_loc + " " + SLAVES +
                                   ", but is in " + sdk_loc + " " + SLAVES)

        self.binaries_test.log("Failed tests: " + ", ".join(self.failed_tests))
        assert len(self.failed_tests) == 0
