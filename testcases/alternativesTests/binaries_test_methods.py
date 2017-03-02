from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
from utils.test_utils import rename_default_subpkg
from utils.core.configuration_specific import JdkConfiguration
import os
import config.runtime_config as rc

JAVA_CGI = "java-rmi.cgi"
DEBUG_SUFFIX = "-debug"
HEADLESS = "headless"
DEVEL = "devel"
DEFAULT = "default"
JVM_DIR = "/usr/lib/jvm/"
EXPORTS_DIR = "/usr/lib/jvm-exports/"
POLICYTOOL = "policytool"
SDK_LOCATION = 1
JRE_LOCATION = 0
PLUGIN = "plugin"
JAVA = "java"
JAVAC = "javac"
SUBPACKAGE = "subpackage "
SUBPACKAGES = "subpackages "
PRESENTED = "presented "
PRESENTED_SUBPACKAGES = PRESENTED + SUBPACKAGES + ": "
EXPECTED_SUBPACKAGES = "expected " + SUBPACKAGES + ": "
SLAVES = "slaves "
BINARIES = "binaries "
NOT_PRESENT_IN = " not present in "
CAN_NOT_BE_IN = " can not be in "
MUST_BE_IN = " must be in "
BINARY = "binary "
SLAVE = "slave "
BECAUSE_THIS_ARCH_HAS_NO = ", because this architecture has no "
JCONTROL = "jcontrol"
CONTROL_PANEL = "ControlPanel"
JAVAWS = "javaws"
MISSING = "missing "
LIBJAVAPLUGIN = "libjavaplugin.so"
LIBNSSCKBI_SO = "libnssckbi.so"
JAVAFXPACKAGER = "javafxpackager"
JMC_INI = "jmc.ini"


class BaseTest(JdkConfiguration):
    def __init__(self, binariesTest):
        super(BaseTest, self).__init__()
        self.binaries_test = binariesTest
        self.skipped = []
        self.failed_tests = []

    # ibm binaries contains some extra files and folders, this method is overridden in Ibm config classes and
    # safely removes them, so there is no unexpected collision with JDK or Oracle binaries.
    def _clean_bin_dir_for_ibm(self, binaries):
        return binaries

     # this handles everything connected to plugin - jcontrol, ControlPanel, javaws binaries,
     # slaves, where they should be and plugin subpackage - if it is present on current arch
    def document_plugin_and_related_binaries(self, pkg_binaries, installed_slaves = None):
        return

    def _get_checked_masters(self):
        return [JAVA, JAVAC]

    def _get_expected_subpkgs(self):
        l = self._get_jre_sdk_locations()
        subpackages = []
        for a in l:
            for b in a:
                subpackages.append(b)
        return subpackages

    # returns architecture in 32bit identifier
    def _get_arch(self):
        return get_id(self.binaries_test.getCurrentArch())

    # returns [[subpackages with jre binaries], [subpackages with sdk binaries]
    def _get_jre_sdk_locations(self):
        return []

    # returns subpackages that have slaves
    def _get_slave_pkgs(self):
        return []

    # name of a directory with binaries
    def _get_target(self, name):
        return self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))

    # name of a directory of jre/java-sdk
    def _get_exports_directory(self, target):
        return ""

    # returns [[subpackages with policytool binary], [subpackages with policytool slave]]
    def _get_policytool_location(self):
        return []

    # name of a directory for jvm-exports for sdk in jdk 6
    def _get_alternative_exports_target(self, target):
        return target

    # documents and logs all no slave - binaries, does not include them in fail output, even though they got no slaves
    def doc_and_clean_no_slave_binaries(self, pkg_binaries):
        return pkg_binaries

    # OpenJDK's policytool binary has a unique behaviour, it logs, documents it and check if it is behaving correctly.
    def check_policytool_for_jdk(self, pkg_binaries):
        return pkg_binaries

    # This is a script that exectures the Java interpreter, it has no slave, so it must be documented and also does not
    # appear in IBM7 64 bit power archs and in x86_64 arch
    def check_java_cgi(self, pkg_binaries):
        expected_slave_pkgs = self._get_slave_pkgs()
        self._document("{} must be present in {} binaries. It has no slave in alternatives.".format(JAVA_CGI,
                       " and ".join(expected_slave_pkgs[SDK_LOCATION])))
        # java-rmi.cgi binary check
        for sbpkg in expected_slave_pkgs[SDK_LOCATION]:
            cgi_present = False
            for s in pkg_binaries[sbpkg]:
                if JAVA_CGI == s:
                    pkg_binaries[sbpkg].remove(s)
                    cgi_present = True
            if not cgi_present:
                self.failed_tests.append("Missing {} in {}.".format(JAVA_CGI, sbpkg))
                self.binaries_test.log("Missing {} in {}.".format(JAVA_CGI, sbpkg))

        return pkg_binaries

    # checks existence of exports directory, where point export slaves
    def exports_dir_check(self, dirs, exports_target=None, _subpkg = None):
        self._document("Exports slaves point at {} directory. ".format(EXPORTS_DIR))
        exports_check = DefaultMock().execute_ls(EXPORTS_DIR)
        if exports_check[1] != 0:
            dirs.append(("Exports directory does not exist: " + exports_target, 2))
        elif exports_target not in exports_check[0]:
            dirs.append((exports_target + " not present in " + EXPORTS_DIR, 2))
        else:
            dirs.append(exports_check)
        return

    def _has_plugin_subpkg(self):
        return []

    def _get_32bit_id_in_nvra(self, nvra):
        parts = nvra.split(".")
        parts[-1] = get_id(parts[-1])
        nvra = ".".join(parts)
        return nvra


class GetAllBinariesAndSlaves(BaseTest):
    rpms = rc.RuntimeConfig().getRpmList()

    def get_slaves(self, _subpkg):
        checked_masters = self._get_checked_masters()
        self._document("Checking slaves for masters: {}".format(" and ".join(checked_masters)))

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
        expected_binaries_pkgs = self._get_expected_subpkgs()
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
        pkg_binaries = self.doc_and_clean_no_slave_binaries(pkg_binaries)
        pkg_binaries = self._all_jre_in_sdk_check(pkg_binaries)
        pkg_binaries = self.check_java_cgi(pkg_binaries)

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

        assert len(self.failed_tests) == 0
