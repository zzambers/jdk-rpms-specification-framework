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
import utils.rpmbuild_utils as rbu
import utils.mock.mock_execution_exception


class CommonMethods(JdkConfiguration):
    _fail_list = []
    _success_list = []
    _debug_check_fail_list = []

    # stores a dict of {pkg_name : {master : priority }}
    _pkgPriorities = {}

    rpms = config.runtime_config.RuntimeConfig().getRpmList()

    def __init__(self, length, prefix):
        super(CommonMethods, self).__init__()
        self.length = length
        self.prefix = prefix

    def _get_priority(self, master):
        priority = DefaultMock().get_priority(master)
        if priority is None:
            PriorityCheck.logs.log("Priority not found in output for master " + master + ", output is invalid.")
            return None
        return priority

    def check_length(self, priority):
        self._document("Priority of " + self.rpms.getVendor() + self.rpms.getMajorVersionSimplified() +" is " + str(self.length) + " digit.")
        PriorityCheck.logs.log("Checking priority length.")

        if len(priority) != self.length:
            PriorityCheck.logs.log("Priority should be {}-digit, but is {}.".format(self.length, len(priority)))
            return False

        return True

    def check_prefix(self, priority):
        self._document("Prefix is based on major version, in this case it should be " + self.prefix + ".")
        PriorityCheck.logs.log("Checking priority prefix.")

        if not priority.startswith(self.prefix, 0, len(self.prefix)):
            PriorityCheck.logs.log("Priority prefix not as expected, should be {}.".format(self.prefix))
            return False

        return True

    def check_debug_packages(self, pkg_priorities):
        self._document("Debug package should have lower priority than normal package.")
        pkgs = pkg_priorities.keys()

        for pkg in pkgs:
            if "-debug" in pkg:
                name = pkg.replace("-debug", "")
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
                    if not int(master_and_priority[m]) > int(master_and_priority_debug[m]):
                        self._debug_check_fail_list.append(name + " pkg for master " + master)


class OpenJdkCheck(CommonMethods):
    def _check_priorities(self, pkgs):

        DefaultMock().provideCleanUsefullRoot()
        _default_masters = DefaultMock().get_masters()

        for pkg in pkgs:
            content = utils.rpmbuild_utils.getSrciplet(pkg, rbu.POSTINSTALL)
            ctn = " ".join(content)
            if not ("alternatives" in ctn):
                PriorityCheck.logs.log("Alternatives are not present in postinstall script.")
                continue

            try:
                DefaultMock().install_postscript(pkg)
            except utils.mock.mock_execution_exception.MockExecutionException:
                PriorityCheck.logs.log(rbu.POSTINSTALL + " not found in " + os.path.basename(pkg))
                continue

            pkg_name = utils.pkg_name_split.get_subpackage_only(os.path.basename(pkg))
            self._pkgPriorities[pkg_name] = {}

            masters = DefaultMock().get_masters()
            for m in masters:
                if m in _default_masters:
                    continue

                priority = self._get_priority(m)
                if priority is None:
                    continue

                if (self.check_length(priority) and
                        self.check_prefix(priority)):
                    self._success_list.append(os.path.basename(pkg))
                    PriorityCheck.logs.log("Priority " + priority + " valid for " + os.path.basename(pkg) + "package, master " + m)

                    self._pkgPriorities[pkg_name].update({m : priority})

                else:
                    PriorityCheck.logs.log("Priority " + priority + " invalid for " + os.path.basename(pkg) + " package, master " + m)
                    self._fail_list.append(os.path.basename(pkg) + m)

        PriorityCheck.logs.log("Checking debug packages priorities.")
        self.check_debug_packages(self._pkgPriorities)

        PriorityCheck.logs.log("Successful for: " + str(self._success_list))
        PriorityCheck.logs.log("Failed for: " + str(self._fail_list))
        PriorityCheck.logs.log("Debug package priority check failed for: " + str(self._debug_check_fail_list))

        assert len(self._fail_list) == 0
        assert len(self._debug_check_fail_list) == 0


class OpenJdk6(OpenJdkCheck):
    def __init__(self):
        super(OpenJdk6, self).__init__(5, "160")

    def _check_priorities(self, pkgs):
        return super(OpenJdk6, self)._check_priorities(pkgs)


class OpenJdk7(OpenJdkCheck):
    def __init__(self):
        super(OpenJdk7, self).__init__(7, "170")

    def _check_priorities(self, pkgs):
        return super(OpenJdk7, self)._check_priorities(pkgs)


class OpenJdk8(OpenJdkCheck):
    def __init__(self):
        super(OpenJdk8, self).__init__(7, "180")

    def _check_priorities(self, pkgs):
        return super(OpenJdk8, self)._check_priorities(pkgs)


class PriorityCheck(utils.core.base_xtest.BaseTest):
    logs = None

    def test_priority(self):
        pkgs = self.getBuild()
        self.csch._check_priorities(pkgs)

    def setCSCH(self):
        PriorityCheck.logs = self
        rpms = config.runtime_config.RuntimeConfig().getRpmList()
        self.log("Checking priority for " + rpms.getVendor())

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
            else:
                raise ex.UnknownJavaVersionException("Unknown JDK version.")
        elif rpms.getVendor() == gc.ORACLE:
            return None
        elif rpms.getVendor() == gc.IBM:
            return None
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
