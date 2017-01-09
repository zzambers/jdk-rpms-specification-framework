from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
from utils.test_utils import rename_default_subpkg
from utils.core.configuration_specific import JdkConfiguration
import os
import config.runtime_config as rc

DEBUG_SUFFIX = "-debug"
HEADLESS = "headless"
DEVEL = "devel"
DEFAULT = "default"
JVM_DIR = "/usr/lib/jvm/"
EXPORTS_DIR = "/usr/lib/jvm-exports/"
POLICYTOOL = "policytool"
SDK_LOCATION = 1
JRE_LOCATION = 0


class BaseTest(JdkConfiguration):
    def __init__(self, binariesTest):
        super(BaseTest, self).__init__()
        self.binaries_test = binariesTest
        self.skipped = []
        self.failed_tests = []

    def _get_arch(self):
        return get_id(self.binaries_test.getCurrentArch())

    # returns [[subpackages with jre binaries], [subpackages with sdk binaries]
    def _get_jre_sdk_locations(self):
        return []

    # returns subpackages that have slaves
    def _get_slave_pkgs(self):
        return []

    # name of a directory with binaries
    def _get_target(self):
        return ""

    # name of a directory of jre/java-sdk
    def _get_exports_directory(self, target):
        return ""

    # returns [[subpackages with policytool binary], [subpackages with policytool slave]]
    def _get_policytool_location(self):
        return []

    # name of a directory for jvm-exports for sdk in jdk 6
    def _get_alternative_exports_target(self, target):
        return ""


class GetAllBinariesAndSlaves(BaseTest):
    rpms = rc.RuntimeConfig().getRpmList()

    def _get_slaves(self, _subpkg):
        # all slaves for java and javac masters in all packages
        masters = DefaultMock().get_masters()
        checked_masters = ["java", "javac"]
        clean_slaves = []
        for m in checked_masters:
            if m not in masters:
                continue
            try:
                slaves = DefaultMock().get_slaves(m)
            except MockExecutionException:
                self.binaries_test.log("No relevant slaves were present for " + _subpkg + ".")
                continue
            clean_slaves.append(m)

            # skipping manpage slaves
            for slave in slaves:
                if not slave.endswith("1.gz"):
                    clean_slaves.append(slave)

        return clean_slaves

    def _get_binaries_and_exports_directories(self, _subpkg, loc):
        directories = loc[0].split("\n")

        # gets location of binaries
        target = self._get_target()

        if DEBUG_SUFFIX in _subpkg:
            target += DEBUG_SUFFIX

        if target not in directories:
            return []

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
            exports_check = DefaultMock().execute_ls(EXPORTS_DIR)
            if exports_check[1] != 0:
                dirs.append(exports_target)
            elif exports_target not in exports_check[0]:
                dirs.append((exports_target + " not present in " + EXPORTS_DIR, 2))
            else:
                dirs.append(exports_check)

        return binaries, dirs

    def get_all_binaries_and_slaves(self, pkgs):

        docs = "JRE binaries must be present in {} subpackages.".format(" and ".join(
                                    self._get_jre_sdk_locations()[JRE_LOCATION ]+ self._get_jre_sdk_locations()[SDK_LOCATION]))

        docs += "\n - JRE slaves have java master and are in {} subpackages.".format(" and ".join(
                                    self._get_slave_pkgs()[JRE_LOCATION]))

        docs += "\n - SDK binaries must be present in {} subpackages.".format(" and ".join(
                                    self._get_jre_sdk_locations()[SDK_LOCATION]))
        n = 0
        for jre in self._get_slave_pkgs()[0]:
            for sdk in self._get_slave_pkgs()[1]:

                if ("-debug" in jre and "-debug" in sdk ) or ("-debug" not in jre and "-debug" not in sdk):
                    if n > 0:
                        docs += "\n - SDK slaves are also in {} subpackage, except for slaves that are already " \
                                "present in {}.".format(sdk, jre)
                    else:
                        docs += "\n - SDK slaves have javac master and are in {} subpackage, except for slaves that " \
                                "are already present in {}.".format(sdk, jre)
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
            slaves = self._get_slaves(_subpkg)

            if len(slaves) != 0:
                installed_slaves[_subpkg] = slaves

            pkg_binaries[_subpkg], export_directories[_subpkg] = self._get_binaries_and_exports_directories(_subpkg,
                                                                                                            loc)

        return pkg_binaries, installed_slaves, export_directories


class BinarySlaveTestMethods(GetAllBinariesAndSlaves):
    # checks if slaves and binaries are present only in expected subpackages
    def _check_slave_and_binary_subpackages(self, installed_slaves, pkg_binaries):
        expected_binaries_pkgs = self._get_jre_sdk_locations()

        if sorted(expected_binaries_pkgs[JRE_LOCATION] + expected_binaries_pkgs[SDK_LOCATION]) != sorted(pkg_binaries.keys()):
            self.failed_tests.append("Subpackage binaries are not as expected.")
            self.binaries_test.log("Binaries were found in unexpected subpackages or are missing in "
                                   "certain packages.")
            self.binaries_test.log("Expected subpackages: " + str(sorted(expected_binaries_pkgs[JRE_LOCATION] +
                                                                         expected_binaries_pkgs[SDK_LOCATION])))
            self.binaries_test.log("Presented subpackages:" + str(sorted(pkg_binaries.keys())))
        expected_slave_pkgs = self._get_slave_pkgs()

        if sorted(expected_slave_pkgs[JRE_LOCATION] + expected_slave_pkgs[SDK_LOCATION]) != sorted(installed_slaves.keys()):
            self.failed_tests.append("Subpackage slaves are not as expected")
            self.binaries_test.log("Slaves were found in unexpected subpackages or are missing in "
                                   "certain packages.")
            self.binaries_test.log("Expected subpackages: " + str(sorted(expected_slave_pkgs[JRE_LOCATION] +
                                                                         expected_slave_pkgs[SDK_LOCATION])))
            self.binaries_test.log("Presented subpackages:" + str(sorted(pkg_binaries.keys())))

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
        self._document(" and ".join(jre_exp) + " are java slaves. " + " and ".join(sdk_exp) + " are javac slaves. "
                       "They have no binaries, their links point at jvm-exports and jre/sdk directories.")
        expected_slave_pkgs = self._get_slave_pkgs()

        for subpkg in expected_slave_pkgs[JRE_LOCATION]:
            for slave in jre_exp:
                if slave not in installed_slaves[subpkg]:
                    self.failed_tests.append(slave + " not present in java slaves")
                    self.binaries_test.log(slave + " not present in java slaves")
                else:
                    installed_slaves[subpkg].remove(slave)

        for subpkg in expected_slave_pkgs[SDK_LOCATION]:
            for slave in sdk_exp:
                if slave not in installed_slaves[subpkg]:
                    self.failed_tests.append(slave + " not present in javac slaves")
                    self.binaries_test.log(slave + " not present in javac slaves")
                else:
                    installed_slaves[subpkg].remove(slave)

        return installed_slaves

    # checks policytool in default pkg and merge default pkg with headless in JDK 8 for further check
    def check_policytool(self, pkg_binaries):
        policytool_location = self._get_policytool_location()
        self._document("Policytool is a special case of binary and slave." +
                       "\n - Policytool binary must be present in {} "
                       "subpackages.".format(" and ".join(self._get_policytool_location()[JRE_LOCATION])) +
                       "\n - Policytool slave must be present in {} "
                       "subpackages.".format(" and ".join(policytool_location[1])))
        def_debug_pkg = None
        def_pkg = None

        for loc in policytool_location[JRE_LOCATION]:
            if POLICYTOOL not in pkg_binaries[loc]:
                self.failed_tests.append(POLICYTOOL + " not in {} subpackage binaries.".format(loc))
                self.binaries_test.log(POLICYTOOL + " not in {} subpackage binaries.".format(loc))

            if "default" in loc:
                if HEADLESS in pkg_binaries.keys():
                    if pkg_binaries[loc] != [POLICYTOOL]:
                        self.failed_tests.append(loc + " subpackage should contain only policytool, "
                                                       "but contains: " + ",".join(pkg_binaries[loc]))
                        self.binaries_test.log(POLICYTOOL + "  subpackage should contain only policytool, "
                                                            "but contains: " + ",".join(pkg_binaries[loc]))
                    if DEBUG_SUFFIX in loc:
                        def_debug_pkg = pkg_binaries.pop(loc)
                    else:
                        def_pkg = pkg_binaries.pop(loc)
                else:
                    pkg_binaries[loc].remove(POLICYTOOL)

        if HEADLESS in policytool_location[SDK_LOCATION]:
            if def_pkg is not None:
                pkg_binaries[HEADLESS] += def_pkg
            if def_debug_pkg is not None:
                pkg_binaries[HEADLESS + DEBUG_SUFFIX] += def_debug_pkg

        return pkg_binaries

    # checks if all jre binaries are in sdk and deletes them from there
    def all_jre_in_sdk_check(self, pkg_binaries):
        expected_slave_pkgs = self._get_slave_pkgs()
        self._document("java-rmi.cgi must be present in {} binaries. It has no slave.".format(" and ".join(expected_slave_pkgs[SDK_LOCATION])))
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
                        self.failed_tests.append(j + "not in sdk")
                        self.binaries_test.log("Binary {} was present in JRE directory, "
                                               "but is missing in SDK directory.".format(j))

                # java-rmi.cgi binary check
                cgi_present = False
                for s in sdk:
                    if "java-rmi.cgi" == s:
                        sdk.remove(s)
                        cgi_present = True
                if not cgi_present:
                    self.failed_tests.append("Missing java-rmi.cgi in {}.".format(sbpkg))
                    self.binaries_test.log("Missing java-rmi.cgi in {}.".format(sbpkg))

        return expected_slave_pkgs, pkg_binaries

    # main check, that includes all small checks and at the end compares the binaries with slaves
    def _check_binaries_with_slaves(self, pkgs):

        pkg_binaries, installed_slaves, export_directories = self.get_all_binaries_and_slaves(pkgs)
        self._check_slave_and_binary_subpackages(installed_slaves, pkg_binaries)
        self._export_directories_check(export_directories)
        installed_slaves = self.jre_sdk_exports_check(installed_slaves)
        pkg_binaries = self.check_policytool(pkg_binaries)
        expected_slave_pkgs, pkg_binaries = self.all_jre_in_sdk_check(pkg_binaries)

        # compares binaries with slaves, creates decent output in case there are binaries/slaves extra/missing
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

                self.failed_tests.append("Binaries do not match slaves in " + subpkg + ". Missing binaries: {}, "
                                                                                       "Missing slaves: {}.".format(
                    not_in_binaries, not_in_slaves))
                self.binaries_test.log("Binaries do not match slaves in " + subpkg + ". Missing binaries: {}, "
                                                                                     "Missing slaves: {}.".format(
                    not_in_binaries, not_in_slaves))
                self.binaries_test.log("Presented binaries for {}: ".format(subpkg) +
                                       str(sorted(pkg_binaries[subpkg])))
                self.binaries_test.log("Presented slaves for {}: ".format(subpkg) +
                                       str(sorted(installed_slaves[subpkg])))

        assert len(self.failed_tests) == 0
