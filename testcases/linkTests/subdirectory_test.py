import os
import sys
import copy
import outputControl.logging_access as la
import config.runtime_config as rc
import utils.core.base_xtest as bt
import config.global_config as gc
from utils.core.configuration_specific import JdkConfiguration
from utils.mock.mock_executor import DefaultMock
from utils.test_utils import rename_default_subpkg, replace_archs_with_general_arch, passed_or_failed, get_arch
import utils.pkg_name_split as pkgsplit
from utils.test_utils import get_32bit_id_in_nvra, log_failed_test
from utils.test_constants import *
from utils.core.unknown_java_exception import UnknownJavaVersionException
from outputControl import dom_objects as do

class BaseMethods(JdkConfiguration):
    """ This class tests whether the subdirectories in /usr/lib/jvm are as expected  """

    def __init__(self):
        super().__init__()
        self.list_of_failed_tests = []
        self.rpms = rc.RuntimeConfig().getRpmList()
        self.failed = 0
        self.passed = 0

    def _get_arch(self):
        """ Returns architecture in 32 bit identifier """
        return get_arch(SubdirectoryTest.instance)

    def _get_major_version(self):
        """ Returns major version (eg. 1.8.0 or 9 in case of jdk9"""
        return self.rpms.getMajorVersion()

    def _get_nvra_suffix(self, name):
        """ Getter for the name of main jdk/sdk directory"""
        return get_32bit_id_in_nvra(pkgsplit.get_nvra(name))

    def _get_expected_subdirectories(self, name):
        """ Expected set of subdirectories"""
        return {}

    def _get_jre_link(self, expected_link):
        """ Creating path to jre directory """
        return expected_link + "/jre"

    def document_subdirs(self, args):
        """ Only doc method, called automatically by the framework, should not be executed as part of the test."""
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

    def _remove_fake_subdirectories(self, subdirectories):
        """ There are created jce-1.x.x dirs by the engine of the framework for oracle and IBM java, that are made
        during the installation, since we only extract, we crate them at mock init, this deletes them to avoid mess
        in tests."""
        return subdirectories

    def _test_subdirectories_equals(self, subdirectories, expected_subdirectories, _subpkg, name):
        """ Check whether the subdirectories in /usr/lib/jvm are as expected, logs and counts fails/passes"""
        testcase = do.Testcase("BaseMethods", "test_subdirectories_equals")
        do.Tests().add_testcase(testcase)
        passed_or_failed(self, sorted(subdirectories) == sorted(expected_subdirectories))
        for subdirectory in expected_subdirectories:
            testcase = do.Testcase("BaseMethods", "test_subdirectories_equals " + subdirectory)
            do.Tests().add_testcase(testcase)
            if not passed_or_failed(self, subdirectory in subdirectories):
                log_failed_test(self, "Missing {} subdirectory in {} "
                                      "subpackage".format(subdirectory, _subpkg))
                testcase.set_log_file("none")
                testcase.set_view_file_stub("Missing {} subdirectory in {} subpackage".format(subdirectory, _subpkg))
        for subdirectory in subdirectories:
            testcase = do.Testcase("BaseMethods", "test_subdirectories_equals " + subdirectory)
            do.Tests().add_testcase(testcase)
            if not passed_or_failed(self, subdirectory in expected_subdirectories):
                log_failed_test(self, "Extra {} subdirectory in {} subpackage".format(subdirectory, _subpkg))
                testcase.set_log_file("none")
                testcase.set_view_file_stub("Missing {} subdirectory in {} subpackage".format(subdirectory, _subpkg))

    def _test_links_are_correct(self, subdirectories, name, _subpkg):
        """ Tests if all the symlinks in /usr/lib/jvm ('fake subdirectories') are pointing at correct target (usually
        /usr/lib/jvm/nvr(a)) """
        SubdirectoryTest.instance.log("Testing subdirectory links: ")
        for subdirectory in subdirectories:
            testcase = do.Testcase("BaseMethods", "test_links_are_correct " + subdirectory)
            do.Tests().add_testcase(testcase)
            expected_link = JVM_DIR + "/" + self._get_nvra_suffix(name)

            # skipping created subdirs at mock init, are dirs, not links
            if "jce" in subdirectory:
                SubdirectoryTest.instance.log(subdirectory + " is a directory.")
                continue

            if "jre" in subdirectory:
                expected_link = self._get_jre_link(expected_link)

            readlink = DefaultMock().executeCommand(["readlink -f {}".format(JVM_DIR + "/" + subdirectory)])
            if readlink[1] != 0:
                log_failed_test(self, subdirectory + " is not a link! Subdirectory test link failed for " +
                                _subpkg)
                testcase.set_log_file("none")
                testcase.set_view_file_stub(subdirectory + " is not a link! Subdirectory test link failed for " +
                                _subpkg)
                self.failed += 1
            elif readlink[0] != expected_link:
                log_failed_test(self, " {} should point at {} but points at {} ".format(subdirectory,
                                                                                        expected_link,
                                                                                        readlink[0]))
                testcase.set_log_file("none")
                testcase.set_view_file_stub(" {} should point at {} but points at {} ".format(subdirectory,
                                                                                        expected_link,
                                                                                        readlink[0]))
                self.failed += 1
            else:
                SubdirectoryTest.instance.log("Subdirectory link check successful for " + subdirectory)
                self.passed += 1

    def _subdirectory_test(self, pkgs):
        """ Main method for the test, that is called when the test suite is started, does all the work """
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
                log_failed_test(self, "Warning: " + JVM_DIR + " does not exist, skipping subdirectory test for"
                                " given subpackage {}".format(_subpkg))

                continue
            subdirectories = subdirectories[0].split("\n")
            subdirectories = self._remove_fake_subdirectories(subdirectories)
            expected_subdirectories = self._get_expected_subdirectories(name)[_subpkg]
            expected_subdirectories.append(self._get_nvra_suffix(name))
            expected_subdirectories = set(expected_subdirectories)
            SubdirectoryTest.instance.log("Testing subdirectories for {}:".format(name), la.Verbosity.TEST)
            SubdirectoryTest.instance.log("Expected: " + str(sorted(expected_subdirectories)),
                                          la.Verbosity.TEST)
            SubdirectoryTest.instance.log("Presented: " + str(sorted(subdirectories)), la.Verbosity.TEST)
            self._test_subdirectories_equals(subdirectories, expected_subdirectories, _subpkg, name)
            self._test_links_are_correct(subdirectories, name, _subpkg)

        if len(self.list_of_failed_tests) != 0:
            SubdirectoryTest.instance.log("Summary of failed tests: " + "\n        ".join(self.list_of_failed_tests),
                                          la.Verbosity.ERROR)
        return self.passed, self.failed


# here follow configuration classes, determining the unique set of subdirectories for each class
class OpenJdk6(BaseMethods):
    def _get_expected_subdirectories(self, name):
        return {DEFAULT: ["jre",
                          "jre" + "-" + self._get_major_version(),
                          "jre" + "-" + self.rpms.getVendor(),
                          "jre" + "-" + self._get_major_version() + "-" + self.rpms.getVendor(),
                          ],
                DEVEL: ["java",
                        "java" + "-" + self._get_major_version(),
                        "java" + "-" + self.rpms.getVendor(),
                        "java" + "-" + self._get_major_version() + "-" + self.rpms.getVendor(),
                        ]}

    def _get_nvra_suffix(self, name):
        directory = pkgsplit.get_name_version_release(name)
        unnecessary_part = directory.split("-")[-1]
        # jdk6 has shorter name of the subdirectory, only name-version
        directory = directory.replace("-" + unnecessary_part, "")
        return directory


class OpenJdk6PowerBeArchAndX86(OpenJdk6):
    def _get_nvra_suffix(self, name):
        return super()._get_nvra_suffix(name) + "." + self._get_arch()

    def _get_expected_subdirectories(self, name):
        """ ojdk6 on some architectures has architecture included in the subdirs """
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[DEFAULT].remove("jre" + "-" + self._get_major_version() + "-" + self.rpms.getVendor())
        subdirs[DEFAULT].append("jre" + "-" + self._get_major_version() + "-" + self.rpms.getVendor() + "." +
                                self._get_arch())
        subdirs[DEVEL].remove("java" + "-" + self._get_major_version() + "-" + self.rpms.getVendor())
        subdirs[DEVEL].append("java" + "-" + self._get_major_version() + "-" + self.rpms.getVendor() + "." +
                              self._get_arch())
        return subdirs


class OpenJdk7(OpenJdk6):
    def _get_nvra_suffix(self, name):
        """ From jdk7 there is regular /usr/lib/jvm/nvra """
        nvra = super(OpenJdk6, self)._get_nvra_suffix(name)
        return nvra

    def _get_expected_subdirectories(self, name):
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[HEADLESS] = subdirs[DEFAULT]
        subdirs[HEADLESS].append(self._get_nvra_suffix(name).replace("java", "jre", 1))
        subdirs[DEFAULT] = []
        return subdirs


class Oracle7(OpenJdk6):
    def _get_nvra_suffix(self, name):
        """ From jdk7 there is regular /usr/lib/jvm/nvra """
        nvra = super(OpenJdk6, self)._get_nvra_suffix(name)
        return nvra

    def _get_expected_subdirectories(self, name):
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[DEFAULT].append(self._get_nvra_suffix(name).replace("java", "jre", 1))
        return subdirs

    def _remove_fake_subdirectories(self, subdirectories):
        subdirs = copy.copy(subdirectories)
        fake_subs = ['jce-1.7.0-oracle', 'jce-1.8.0-oracle']
        for fs in fake_subs:
            try:
                subdirs.remove(fs)
            except ValueError:
                SubdirectoryTest.instance.log(fs + " should be created in /usr/lib/jvm for plugin package purpose.")
        return subdirs


class Ibm7(Oracle7):
    def _remove_fake_subdirectories(self, subdirectories):
        return subdirectories

    def _get_major_version(self):
        """ IBM has a 1.7.1 java naming convention, but the alternatives version is still 1.7.0 """
        return "1.7.0"

    def _get_expected_subdirectories(self, name):
        subdirs = super()._get_expected_subdirectories(name)
        subdirs[DEFAULT].append("jce" + "-" + self._get_major_version() + "-" + self.rpms.getVendor())
        return subdirs


class Ibm8(Ibm7):
    def _get_major_version(self):
        return self.rpms.getMajorVersion()


class Ibm8Rhel8(OpenJdk7):
    pass



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


class ITW(BaseMethods):
    """ No test for ITW, since everything is in /usr/bin"""
    def _subdirectory_test(self, pkgs):
        SubdirectoryTest.instance.log("Iced Tea web binaries are in /usr/bin, no subdirectories with n-v-r-a are "
                                      "created. This test is skipped for icedtea-web packages.", la.Verbosity.TEST)
        return self.passed, self.failed

    def document_subdirs(self, args):
        self._document("IcedTea-web has no subdirectories in " + JVM_DIR)


class SubdirectoryTest(bt.BaseTest):
    instance = None

    def test_subdirectories(self):
        pkgs = self.getBuild()
        return self.csch._subdirectory_test(pkgs)

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
            elif int(rpms.getMajorVersionSimplified()) >= 9:
                if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch() + gc.getPower64LeAchs() \
                        + gc.getAarch64Arch() + gc.getPower64BeAchs():
                    self.csch = OpenJdk9D()
                    return
                else:
                    self.csch = OpenJdk9()
                    return
            else:
                raise UnknownJavaVersionException("Unknown OpenJDK version.")
        elif rpms.getVendor() == gc.SUN:
            if self.getCurrentArch() in gc.getX86_64Arch():
                self.csch = OpenJdk6PowerBeArchAndX86()
                return
            else:
                self.csch = OpenJdk6()
                return
        elif rpms.getVendor() == gc.ORACLE:
            if rpms.getMajorVersionSimplified() == "7":
                self.csch = Oracle7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = Oracle7()
                return
            else:
                raise UnknownJavaVersionException("Unknown Oracle java version.")
        elif rpms.getVendor() == gc.IBM:
            if rpms.getOsVersionMajor() < 8:
                if rpms.getMajorVersionSimplified() == "7":
                    self.csch = Ibm7()
                    return
                elif rpms.getMajorVersionSimplified() == "8":
                    self.csch = Ibm8()
                    return
                else:
                    raise UnknownJavaVersionException("Unknown IBM java version.")
            else:
                self.csch = Ibm8Rhel8()
                return

        elif rpms.getVendor() == gc.ITW:
            self.csch = ITW()
            return

        else:
            raise UnknownJavaVersionException("Unknown vendor, configuration specific check could not be set.")


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
