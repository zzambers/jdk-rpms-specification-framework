from utils.core.configuration_specific import JdkConfiguration
from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from utils.test_utils import rename_default_subpkg
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
import os
from utils.test_constants import *

JVM_DIR = "/usr/lib/jvm/"
EXPORTS_DIR = "/usr/lib/jvm-exports/"
SDK_LOCATION = 1
JRE_LOCATION = 0
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
JAVAWS = "javaws"
MISSING = "missing "
ITW_BIN_LOCATION = "/usr/bin"
POLICYEDITOR = 'policyeditor.itweb'


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

    def _get_expected_subpkgs(self, subpkgs):
        subpackages = []
        for a in subpkgs:
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
    def doc_and_clean_no_slave_binaries(self, pkg_binaries, installed_slaves = None):
        return pkg_binaries, installed_slaves

    # OpenJDK's policytool binary has a unique behaviour, it logs, documents it and check if it is behaving correctly.
    def check_policytool_for_jdk(self, pkg_binaries):
        return pkg_binaries

    # This is a script that executes the Java interpreter, it has no slave, so it must be documented and also does not
    # appear in IBM7 64 bit power archs and in x86_64 arch
    def check_java_cgi(self, pkg_binaries):
        expected_slave_pkgs = self._get_slave_pkgs()
        self._document("{} must be present in {} binaries. It has no slave in alternatives.".format(JAVA_RMI_CGI,
                       " and ".join(expected_slave_pkgs[SDK_LOCATION])))
        # java-rmi.cgi binary check
        for sbpkg in expected_slave_pkgs[SDK_LOCATION]:
            cgi_present = False
            for s in pkg_binaries[sbpkg]:
                if JAVA_RMI_CGI == s:
                    pkg_binaries[sbpkg].remove(s)
                    cgi_present = True
            if not cgi_present:
                self.failed_tests.append("Missing {} in {}.".format(JAVA_RMI_CGI, sbpkg))
                self.binaries_test.log("Missing {} in {}.".format(JAVA_RMI_CGI, sbpkg))

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

    def _get_32bit_id_in_nvra(self, nvra):
        parts = nvra.split(".")
        parts[-1] = get_id(parts[-1])
        nvra = ".".join(parts)
        return nvra


class PathTest(BaseTest):
    def path_test(self, binaries, expected_subpackages=None):
        self._document("All binaries must be on $PATH. If present on multiple paths, the alternatives "
                       "links must be equal.")
        path_contents = {}
        pkgs = self.binaries_test.getBuild()
        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))
            if _subpkg not in expected_subpackages:
                continue
            if not DefaultMock().postinstall_exception_checked(pkg):
                continue
            paths = self._get_paths()
            self.binaries_test.log("Given paths: " + ", ".join(paths))

            for path in paths:
                content = self._get_path_contents(path)
                if content[1] != 0:
                    content = []
                else:
                    content = content[0].split("\n")
                path_contents[path] = content

            self.binaries_test.log("Validating binaries paths for {} subpackage: ".format(_subpkg))
            for binary in binaries[_subpkg]:
                found_paths = self._binary_in_path_contents(path_contents, binary)
                if found_paths is None:
                    self.failed_tests.append(binary + " not found in any path given for " + _subpkg)
                else:
                    self.binaries_test.log("Binary {} found in {} for "
                                               "{}".format(binary, ", ".join(found_paths), _subpkg))
        self.binaries_test.log("Path test finished.")
        return

    def _get_paths(self):
        paths = DefaultMock().executeCommand(["echo $PATH"])
        if paths[1] != 0:
            raise MockExecutionException("Command echo $PATH failed.")
        paths = paths[0].split(os.pathsep)
        return paths

    def _get_path_contents(self, path):
        content = DefaultMock().execute_ls(path)
        return content

    def _binary_in_path_contents(self, path_contents, binary):
        paths = set()
        for path in path_contents.keys():
            if binary in path_contents[path]:
                paths.add(path)
        if len(paths) == 0:
            return None
        result = set()
        for p in paths:
            tg = "readlink " + p + "/" + binary
            res = DefaultMock().executeCommand([tg])
            if res[1] == 0:
                result.add(res)
            else:
                self.failed_tests.append("Command readlink " + p + "/" + binary + " failed.")
        if len(result) != 1:
            if len(result) > 1:
                self.failed_tests.append("Links of one binary do not point on same target: " + ",".join(result))
            else:
                self.failed_tests.append("Links do not point on any target.")
        return paths

