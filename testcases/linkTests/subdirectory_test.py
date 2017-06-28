import os
import sys
import copy
import outputControl.logging_access as la
import config.runtime_config as rc
import utils.core.base_xtest as bt
import config.global_config as gc
from utils.core.configuration_specific import JdkConfiguration
from utils.mock.mock_executor import DefaultMock
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch
import utils.pkg_name_split as pkgsplit
from utils.test_utils import get_32bit_id_in_nvra, log_failed_test
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
from utils.test_constants import *


class BaseMethods(JdkConfiguration):
    def __init__(self):
        super().__init__()
        self.failed = []
        self.rpms = rc.RuntimeConfig().getRpmList()

    # returns architecture in 32bit identifier
    def _get_arch(self):
        return get_id(SubdirectoryTest.instance.getCurrentArch())

    # this is the only directory
    def _get_nvra_suffix(self, name):
        return get_32bit_id_in_nvra(pkgsplit.get_nvra(name))

    def _get_expected_subdirectories(self, name):
        return {}

    def _get_jre_link(self, expected_link):
        return expected_link + "/jre"

    def document_subdirs(self, args):
        name = self.rpms.getNvr() + "." + self._get_arch()
        dirs = self._get_expected_subdirectories(name)
        docs = JVM_DIR + " must contain following subdirectories: \n"
        docs += " Each subpackage with binaries has a main subdirectory: " + \
                "".join(replace_archs_with_general_arch([self._get_nvra_suffix(name)], self._get_arch())) + "\n"

        for subdir in dirs.keys():
            docs += " - {} subpackage contains also following subdirectories: ".format(subdir) + \
                    ", ".join(replace_archs_with_general_arch(dirs[subdir], self._get_arch())) + "\n"
        docs += "Those directories are links to the main subdirectory."

        self._document(docs)

    def _test_subdirectories_equals(self, subdirectories, expected_subdirectories, _subpkg, name):
        if sorted(subdirectories) != sorted(expected_subdirectories):
            for subdirectory in expected_subdirectories:
                if subdirectory not in subdirectories:
                    log_failed_test(self, "Missing {} subdirectory in {} "
                                          "subpackage".format(subdirectory, _subpkg))
            for subdirectory in subdirectories:
                if subdirectory not in expected_subdirectories:
                    log_failed_test(self, "Extra {} subdirectory in {} subpackage".format(subdirectory, _subpkg))
        else:
                SubdirectoryTest.instance.log("Subdirectory test for {} finished, no fails occured.".format(name))

    def _test_links_are_correct(self, expected_subdirectories, name, _subpkg):
        SubdirectoryTest.instance.log("Testing subdirectory links: ")
        for subdirectory in expected_subdirectories:
            expected_link = JVM_DIR + "/" + self._get_nvra_suffix(name)
            if "jre" in subdirectory:
                expected_link = self._get_jre_link(expected_link)

            readlink = DefaultMock().executeCommand(["readlink -f {}".format(JVM_DIR + "/" + subdirectory)])
            if readlink[1] != 0:
                log_failed_test(self, subdirectory + " is not a link! Subdirectory test link failed for " +
                                _subpkg)
            elif readlink[0] != expected_link:
                log_failed_test(self, " {} should point at {} but points at {} ".format(subdirectory,
                                                                                        expected_link,
                                                                                        readlink[0]))
            else:
                SubdirectoryTest.instance.log("Subdirectory link check successful for " + subdirectory)

    def _subdirectory_test(self, pkgs):
        for pkg in pkgs:
            name = os.path.basename(pkg)
            _subpkg = rename_default_subpkg(pkgsplit.get_subpackage_only(name))
            if _subpkg not in self._get_expected_subdirectories(name).keys():
                continue
            if not DefaultMock().postinstall_exception_checked(pkg):
                SubdirectoryTest.instance.log("Skipping subdirectory test for {}".format(_subpkg), la.Verbosity.TEST)
                continue

            subdirectories = DefaultMock().execute_ls(JVM_DIR)
            if subdirectories[1] != 0:
                SubdirectoryTest.instance.log("Warning: " + JVM_DIR + " does not exist, skipping subdirectory test for"
                                                                      " given subpackage {}".format(_subpkg),
                                              la.Verbosity.TEST)
                continue
            subdirectories = subdirectories[0].split("\n")
            expected_subdirectories = self._get_expected_subdirectories(name)[_subpkg]
            expected_subdirectories.append(self._get_nvra_suffix(name))
            expected_subdirectories = set(expected_subdirectories)
            SubdirectoryTest.instance.log("Testing subdirectories for {}:".format(name), la.Verbosity.TEST)
            SubdirectoryTest.instance.log("Expected: " + str(sorted(expected_subdirectories)),
                                          la.Verbosity.TEST)
            SubdirectoryTest.instance.log("Presented: " + str(sorted(subdirectories)), la.Verbosity.TEST)
            self._test_subdirectories_equals(subdirectories, expected_subdirectories, _subpkg, name)
            self._test_links_are_correct(expected_subdirectories, name, _subpkg)

        if len(self.failed) != 0:
            SubdirectoryTest.instance.log("Summary of failed tests: " + "\n        ".join(self.failed),
                                          la.Verbosity.ERROR)
        assert(len(self.failed) == 0)


class OpenJdk6(BaseMethods):
    def _get_expected_subdirectories(self, name):
        return {DEFAULT: ["jre",
                          "jre" + "-" + self.rpms.getMajorVersion(),
                          "jre" + "-" + self.rpms.getVendor(),
                          "jre" + "-" + self.rpms.getMajorVersion() + "-" + self.rpms.getVendor(),
                          ],
                DEVEL: ["java",
                        "java" + "-" + self.rpms.getMajorVersion(),
                        "java" + "-" + self.rpms.getVendor(),
                        "java" + "-" + self.rpms.getMajorVersion() + "-" + self.rpms.getVendor(),
                        ]}

    def _get_nvra_suffix(self, name):
        directory = pkgsplit.get_name_version_release(name)
        unnecessary_part = directory.split("-")[-1]
        directory = directory.replace("-" + unnecessary_part, "")
        return directory


class OpenJdk6PowerBeArchAndX86(OpenJdk6):
    def _get_nvra_suffix(self, name):
        return super()._get_nvra_suffix(name) + "." + self._get_arch()

    def _get_expected_subdirectories(self, name):
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[DEFAULT].remove("jre" + "-" + self.rpms.getMajorVersion() + "-" + self.rpms.getVendor())
        subdirs[DEFAULT].append("jre" + "-" + self.rpms.getMajorVersion() + "-" + self.rpms.getVendor() + "." +
                                self._get_arch())
        subdirs[DEVEL].remove("java" + "-" + self.rpms.getMajorVersion() + "-" + self.rpms.getVendor())
        subdirs[DEVEL].append("java" + "-" + self.rpms.getMajorVersion() + "-" + self.rpms.getVendor() + "." +
                              self._get_arch())
        return subdirs


class OpenJdk7(OpenJdk6):
    def _get_nvra_suffix(self, name):
        nvra = super(OpenJdk6, self)._get_nvra_suffix(name)
        return nvra

    def _get_expected_subdirectories(self, name):
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[HEADLESS] = subdirs[DEFAULT]
        subdirs[HEADLESS].append(self._get_nvra_suffix(name).replace("java", "jre", 1))
        subdirs[DEFAULT] = []
        return subdirs


class OpenJdk8Debug(OpenJdk7):
    def _get_expected_subdirectories(self, name):
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[HEADLESS + DEBUG_SUFFIX] = copy.copy(subdirs[HEADLESS])
        subdirs[DEFAULT + DEBUG_SUFFIX] = copy.copy(subdirs[DEFAULT])
        subdirs[DEVEL + DEBUG_SUFFIX] = copy.copy(subdirs[DEVEL])
        return subdirs

    def _get_nvra_suffix(self, name):
        nvra = super()._get_nvra_suffix(name)
        if DEBUG_SUFFIX in name:
            nvra = nvra + DEBUG_SUFFIX
        return nvra


class OpenJdk9D(OpenJdk8Debug):
    def _get_jre_link(self, expected_link):
        return expected_link


class OpenJdk9(OpenJdk7):
    def _get_jre_link(self, expected_link):
        return expected_link


class SubdirectoryTest(bt.BaseTest):
    instance = None

    def test_subdirectories(self):
        pkgs = self.getBuild()
        self.csch._subdirectory_test(pkgs)

    def setCSCH(self):
        SubdirectoryTest.instance = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking subdirectories for: " + rpms.getMajorPackage(), la.Verbosity.TEST)
        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                if self.current_arch in (gc.getPower64BeAchs() + gc.getX86_64Arch()):
                    self.csch = OpenJdk6PowerBeArchAndX86()
                    return
                else:
                    self.csch = OpenJdk6()
                    return
            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = OpenJdk7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch() + gc.getPower64LeAchs() \
                        + gc.getAarch64Arch() + gc.getPower64BeAchs():
                    self.csch = OpenJdk8Debug()
                    return
                else:
                    self.csch = OpenJdk7()
                    return
            elif rpms.getMajorVersionSimplified() == "9":
                if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch() + gc.getPower64LeAchs() \
                        + gc.getAarch64Arch() + gc.getPower64BeAchs():
                    self.csch = OpenJdk9D()
                    return
                else:
                    self.csch = OpenJdk9()
                    return
        return


def testAll():
    return SubdirectoryTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Java subdirectory conventions:")
    return SubdirectoryTest().execute_special_docs()


def main(argv):
    bt.defaultMain(argv, documentAll, testAll)
    return SubdirectoryTest().execute_special_docs()


if __name__ == "__main__":
    main(sys.argv[1:])
