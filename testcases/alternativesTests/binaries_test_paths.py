from utils.core.configuration_specific import JdkConfiguration
from utils.mock.mock_executor import DefaultMock
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_execution_exception import MockExecutionException
from utils.test_utils import rename_default_subpkg
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
import os
from utils.test_constants import *
from utils.test_utils import get_32bit_id_in_nvra


class BaseTest(JdkConfiguration):
    def __init__(self, binariesTest):
        super(BaseTest, self).__init__()
        self.binaries_test = binariesTest
        self.skipped = []
        self.failed_tests = []


    def remove_binaries_without_slaves(self, installed_binaries):
        return installed_binaries

    def _remove_excludes(self, binaries):
        return binaries

    def check_exports_slaves(self, installed_slaves):
        return installed_slaves

    def handle_policytool(self, installed_binaries, installed_slaves=None):
        return installed_binaries, installed_slaves

    def _check_binaries_against_hardcoded_list(self, binaries, subpackage):
        return

    def handle_plugin_binaries(self, binaries, slaves=None):
        return binaries, slaves

    def _get_binary_directory(self, name):
        return get_32bit_id_in_nvra(pkgsplit.get_nvra(name))

    def _get_sdk_subpackage(self):
        return [DEVEL]

    def _get_sdk_debug_subpackage(self):
        return [DEVEL + DEBUG_SUFFIX]

    def _get_binary_directory_path(self, name):
        dir = JVM_DIR + "/" + self._get_binary_directory(name)
        if DEBUG_SUFFIX + "-" in name:
            dir += DEBUG_SUFFIX
        if DEVEL in name or JAVAFX in name:
            return dir + SDK_DIRECTORY
        else:
            return dir + JRE_DIRECTORY

    def _check_binaries_against_harcoded_list(self, binaries, subpackage):
        return

    def _get_jre_subpackage(self):
        return [DEFAULT]

    def _get_checked_masters(self):
        return [JAVA, JAVAC]

    # returns architecture in 32bit identifier
    def _get_arch(self):
        return get_id(self.binaries_test.getCurrentArch())

    def _get_subpackages_with_binaries(self):
        return [DEFAULT, DEVEL]

    # This is a script that executes the Java interpreter, it has no slave, so it must be documented and also does not
    # appear in IBM7 64 bit power archs and in x86_64 arch
    def check_java_cgi(self, installed_binaries):
        self._document(
            "{} must be present in {} binaries. It has no slave in alternatives.".format(JAVA_RMI_CGI, DEVEL))
        # java-rmi.cgi binary check
        for subpackage in self._get_sdk_subpackage():
            try:
                installed_binaries[subpackage].remove(JAVA_RMI_CGI)
            except ValueError:
                self.failed_tests.append("Missing {} in {}.".format(JAVA_RMI_CGI, DEVEL))
        return installed_binaries

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

