import inspect
import sys
import traceback
import testcases.utils.configuration_specific as cs
from outputControl import logging_access as la
import testcases.utils.test_utils as tu
import config.global_config


def lsort(someList):
    if config.global_config.leSort:
        return sorted(someList)
    return someList


# dont missplace with noarch architecture
NON_ARCH_TEST = "Non_Arch"


class Agregator():
    def __init__(self):
        self.lines = []

    def add(self, arch, method, string):
        la.LoggingAccess().log("for " + method + " on " + arch)
        self.lines.append(string)
        la.LoggingAccess().log("  got: " + string)

    def out(self):
        for l in self.lines:
            la.LoggingAccess().stdout(l)


class BaseTestRunner:
    def __init__(self):
        self.indent = ""
        # configuration specific checks
        self.csch = None
        self.current_arch = None

    def _cleanArchs(self):
        r = self.getTestedArchs()
        if r is None or len(r) == 0:
            return [NON_ARCH_TEST]
        else:
            return r

    def execute_tests(self):
        """Call all test_ prefixed methods in overwritting class"""
        passed = 0
        failed = 0
        self.indent = "  "
        self.log("started tests in suite: " + type(self).__name__ + ":")
        archs = self._cleanArchs()
        methods = lsort(inspect.getmembers(self, predicate=inspect.ismethod))
        for a, b in methods:
            for i, arch in enumerate(archs):
                self.current_arch = arch;
                if str(a).startswith("test_"):
                    self.indent = "    "
                    self.log("Setting configuration-specific-checks")
                    self.setCSCH()
                    self.log("running: " + a + "[" + self.current_arch + "] " + str(i + 1) + "/" + str(len(archs)))
                    self.indent = "      "
                    calllable = self.__class__.__dict__[a]
                    try:
                        self.indent = "        "
                        calllable(self)
                        passed += 1
                        la.LoggingAccess().stdout(
                            tu.result(True) + ": " + type(self).__name__ + "." + a + "[" + arch + "]")
                    except BaseException as ex:
                        m = tu.result(False) + ": " + type(self).__name__ + "." + a + "[" + arch + "]" + " (" + str(
                            ex) + ") from " + \
                            inspect.stack()[1][1]
                        la.LoggingAccess().stdout(m)
                        failed += 1
                        print(m, file=sys.stderr)
                        traceback.print_exc()
                    self.indent = "    "
                    self.log("finished: " + a + "[" + self.current_arch + "] " + str(i + 1) + "/" + str(len(archs)))
        la.LoggingAccess().log(
            "finished testing suite: " + type(self).__name__ +
            " - failed/total: " + str(failed) + "/" + str(failed + passed))
        return passed, failed

    def execute_special_docs(self):
        """Call and document all public methods in csch"""
        documented = 0
        ignored = 0
        failed = 0
        self.indent = "  "
        self.log("started special docs for suite: " + type(self).__name__ + ":")
        archs = self._cleanArchs()
        agregator = Agregator()
        for i, arch in enumerate(archs):
            self.indent = "    "
            self.log("Setting configuration-specific-checks")
            self.setCSCH()
            if self.csch is None:
                self.log("configuration-specific-checks are not set. Nothing to do")
            else:
                # on contrary with execute_tests, this walks methods on csh!!!
                methods = lsort(inspect.getmembers(self.csch, predicate=inspect.ismethod))
                for a, b in methods:
                    self.current_arch = arch;
                    if not str(a).startswith("_"):
                        self.csch.documenting = True
                        self.indent = "      "
                        self.log(
                            "documenting: " + a + "[" + self.current_arch + "] " + str(i + 1) + "/" + str(len(archs)))
                        calllable = self.csch.__class__.__dict__[a]
                        try:
                            self.indent = "        "
                            calllable(self.csch)
                            self.log("Ignored : " + type(self.csch).__name__ + "." + a + "[" + arch + "]")
                            ignored += 1
                        except cs.DocumentationProcessing as doc:
                            agregator.add(arch, a, str(doc))
                            self.log("Processed : " + type(self.csch).__name__ + "." + a + "[" + arch + "]")
                            documented += 1
                        except Exception as ex:
                            m = "Error: " + type(self.csch).__name__ + "." + a + "[" + arch + "]" + " (" + str(
                                ex) + ") from " + \
                                inspect.stack()[1][1]
                            failed += 1
                            self.log(m)
                            print(m, file=sys.stderr)
                            traceback.print_exc()
                        self.indent = "    "
                        self.log("finished: " + a + "[" + self.current_arch + "] " + str(i + 1) + "/" + str(len(archs)))
        agregator.out()
        la.LoggingAccess().log(
            "finished documenting suite: " + type(self).__name__ +
            " - documented/ignored/failed: " + str(documented) + "/" + str(ignored) + "/" + str(failed))
        return documented, ignored, failed

    def log(self, arg):
        la.LoggingAccess().log(self.indent + arg)
