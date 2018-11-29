import sys
import os
from utils.core.configuration_specific import JdkConfiguration
from utils.mock.mock_executor import DefaultMock
import config.runtime_config
import config.global_config as gc
import utils.core.unknown_java_exception as ex
from outputControl import logging_access as la
import utils.core.base_xtest
import utils.rpm_list
import utils.pkg_name_split
import utils.mock.mock_execution_exception
from utils.test_constants import *
from utils.test_utils import log_failed_test, rename_default_subpkg, passed_or_failed
from outputControl import dom_objects as do

PREFIX_160 = "160"
PREFIX_170 = "170"
PREFIX_180 = "180"
PREFIX_190 = "190"
LEN_5 = 5
LEN_6 = 6
LEN_7 = 7


class PriorityTest(JdkConfiguration):

    _success_list = []
    _debug_check_fail_list = []

    rpms = config.runtime_config.RuntimeConfig().getRpmList()

    def __init__(self, length, prefix):
        super(PriorityTest, self).__init__()
        self.length = length
        self.prefix = prefix
        self.list_of_failed_tests = []
        self.passed = 0
        self.failed = 0

    def _get_priority(self, master):
        """ This method calls chroot in mock and gets priority from pre-configured methods. """
        priority = DefaultMock().get_priority(master)
        if priority is None:
            PriorityCheck.instance.log("Priority not found in output for master " + master + ", output is invalid.",
                                       la.Verbosity.TEST)
            return None
        return priority

    def check_length(self, priority):
        """ This method checks whether the length of priority is as expected. """
        self._document("Priority for {} should be ".format(self.rpms.getMajorPackage()) + str(self.length) + " digit.")
        PriorityCheck.instance.log("Checking priority length.", la.Verbosity.TEST)

        testcase = do.Testcase("PriorityTest", "check_length")
        do.Tests().add_testcase(testcase)
        if not passed_or_failed(self, len(priority) == self.length):
            PriorityCheck.instance.log("Priority should be {}-digit, but is {}.".format(self.length, len(priority)),
                                       la.Verbosity.ERROR)
            testcase.set_log_file("none")
            testcase.set_view_file_stub("Priority should be {}-digit, but is {}.".format(self.length, len(priority)))
            return False

        return True

    def check_prefix(self, priority):
        """ This method checks if the prefix is as expected. In general, the prefix is based on major version. """
        self._document("Prefix is based on major version, in this case it should be " + self.prefix + ".")
        PriorityCheck.instance.log("Checking priority prefix.", la.Verbosity.TEST)

        testcase = do.Testcase("PriorityTest", "check_prefix")
        do.Tests().add_testcase(testcase)
        if not passed_or_failed(self, priority.startswith(self.prefix, 0, len(self.prefix))):
            PriorityCheck.instance.log("Priority prefix not as expected, should be {}.".format(self.prefix),
                                       la.Verbosity.TEST)
            testcase.set_log_file("none")
            testcase.set_view_file_stub("Priority prefix not as expected, should be {}.".format(self.prefix))
            return False

        return True

    def check_debug_packages(self, pkg_priorities):
        """ Debug packages must have lower priority than normal packages. The standard difference is +-1."""
        self._document("Debug package should have lower priority than normal package.")
        pkgs = pkg_priorities.keys()

        for pkg in pkgs:
            if DEBUG_SUFFIX in pkg:
                name = pkg.replace(DEBUG_SUFFIX, "")
            else:
                continue

            for p in pkgs:
                if name == p:
                    master_and_priority_debug = pkg_priorities[pkg]
                    master_and_priority = pkg_priorities[p]
                else:
                    continue
                master = master_and_priority.keys()

                for m in master:
                    testcase = do.Testcase("PriorityTest", "check_debug_packages " + m)
                    do.Tests().add_testcase(testcase)
                    if not passed_or_failed(self, int(master_and_priority[m]) > int(master_and_priority_debug[m])):
                        log_failed_test(self, "Debug subpackage priority check failed for " + name +
                                        ", master " + master + ". Debug package should have lower priority. " +
                                        "Main package priority: {} Debug package"
                                        " priority: {}".format(master_and_priority[m], master_and_priority_debug[m]))
                        testcase.set_log_file("none")
                        testcase.set_view_file_stub("Debug subpackage priority check failed for " + name)


class MajorCheck(PriorityTest):
    def _check_priorities(self, pkgs):

        _default_masters = DefaultMock().get_default_masters()

        # stores a dict of {pkg_name : {master : priority }}
        _pkgPriorities = {}

        for pkg in pkgs:
            pkg_name = rename_default_subpkg(utils.pkg_name_split.get_subpackage_only(os.path.basename(pkg)))

            if pkg_name in subpackages_without_alternatives():
                PriorityCheck.instance.log(pkg + " is not expected to contain postscript, skipping check.")
                continue

            # must be here anyway, since it creates the snapshot
            if not DefaultMock().postinstall_exception_checked(pkg):
                # logs itself in mock
                continue

            _pkgPriorities[pkg_name] = {}

            masters = DefaultMock().get_masters()
            for m in masters:
                if m in _default_masters:
                    continue

                priority = self._get_priority(m)
                if priority is None:
                    PriorityCheck.instance.log("Failed to get priority, skipping check for " + pkg_name)
                    continue

                if (self.check_length(priority) and
                        self.check_prefix(priority)):
                    self._success_list.append(os.path.basename(pkg))
                    PriorityCheck.instance.log("Priority " + priority + " valid for " + pkg_name +
                                               " package, master " + m, la.Verbosity.TEST)

                    _pkgPriorities[pkg_name].update({m : priority})

                else:
                    log_failed_test(self, "Priority " + priority + " invalid for " + os.path.basename(pkg) +
                                    " package, master " + m)

        PriorityCheck.instance.log("Checking debug packages priorities.", la.Verbosity.TEST)
        self.check_debug_packages(_pkgPriorities)
        PriorityCheck.instance.log("Successful for: " + str(self._success_list), la.Verbosity.TEST)
        PriorityCheck.instance.log("Failed for: " + str(self.list_of_failed_tests), la.Verbosity.ERROR)
        PriorityCheck.instance.log("Debug package priority check failed for: " + str(self._debug_check_fail_list),
                                   la.Verbosity.ERROR)
        return self.passed, self.failed


class OpenJdk6(MajorCheck):
    def __init__(self):
        super().__init__(LEN_5, PREFIX_160)


class OpenJdk7(MajorCheck):
    def __init__(self):
        super().__init__(LEN_7, PREFIX_170)


class OpenJdk8(MajorCheck):
    def __init__(self):
        super().__init__(LEN_7, PREFIX_180)


class OpenJdk9(MajorCheck):
    def __init__(self):
        super().__init__(1, 1)

    def check_prefix(self, priority):
        self._document("Priority for jdk 9 and 10 is always 1 for normal packages and 0 for debug packages.")
        return True


class ProprietaryJava6(MajorCheck):
    def __init__(self):
        super().__init__(LEN_6, PREFIX_160)


class ProprietaryJava7(MajorCheck):
    def __init__(self):
        super().__init__(LEN_6, PREFIX_170)


class ProprietaryJava8(MajorCheck):
    def __init__(self):
        super().__init__(LEN_6, PREFIX_180)


class IcedTeaWeb(MajorCheck):
    def __init__(self):
        super().__init__(LEN_5, PREFIX_180)


class PriorityCheck(utils.core.base_xtest.BaseTest):
    instance = None

    def test_priority(self):
        pkgs = self.getBuild()
        return self.csch._check_priorities(pkgs)

    def setCSCH(self):
        PriorityCheck.instance = self
        rpms = config.runtime_config.RuntimeConfig().getRpmList()
        self.log("Checking priority for " + rpms.getVendor(), la.Verbosity.TEST)

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = OpenJdk6()
                return
            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = OpenJdk7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = OpenJdk8()
                return
            elif int(rpms.getMajorVersionSimplified()) >= 9:
                self.csch = OpenJdk9()
                return
            else:
                raise ex.UnknownJavaVersionException("Unknown JDK version.")
        elif rpms.getVendor() == gc.SUN:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = ProprietaryJava6()
                return
        elif rpms.getVendor() == gc.IBM or rpms.getVendor() == gc.ORACLE:
            if rpms.getMajorVersionSimplified() == "7":
                self.csch = ProprietaryJava7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = ProprietaryJava8()
                return
            else:
                raise ex.UnknownJavaVersionException("Unknown " + rpms.getVendor() + " version.")
        elif rpms.getVendor() == gc.ITW:
            self.csch = IcedTeaWeb()
            return
        else:
            raise ex.UnknownJavaVersionException("Unknown platform, java was not identified.")


def testAll():
    return PriorityCheck().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Priority value conventions.")
    return PriorityCheck().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
