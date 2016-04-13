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


class BaseTestRunner:
    def __init__(self):
        self.indent = ""
        # configuration specific checks
        self.csch = None

    def execute_tests(self):
        """Call all test_ prefixed methods in overwritting class"""
        passed = 0
        failed = 0
        self.indent = "  "
        self.log("started tests in suite: " + type(self).__name__ + ":")
        self.indent = "    "
        self.log("Setting configuration-specific-checks")
        self.setCSCH()
        methods = lsort(inspect.getmembers(self, predicate=inspect.ismethod))
        for a, b in methods:
            #support per arch!
            if str(a).startswith("test_"):
                self.indent = "      "
                self.log("started: " + a + ":")
                calllable = self.__class__.__dict__[a]
                try:
                    self.indent = "        "
                    calllable(self)
                    passed += 1
                    la.LoggingAccess().stdout(tu.result(True) + ": " + type(self).__name__ + "." + a)
                except BaseException as ex:
                    m = tu.result(False) + ": " + type(self).__name__ + "." + a + " (" + str(ex) + ") from " + \
                        inspect.stack()[1][1]
                    la.LoggingAccess().stdout(m)
                    failed += 1
                    print(m, file=sys.stderr)
                    traceback.print_exc()
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
        self.indent = "    "
        self.log("Setting configuration-specific-checks")
        self.setCSCH()
        if self.csch is None:
            self.log("configuration-specific-checks are not set. Nothing to do")
        else:
            self.csch.documenting = True
            methods = lsort(inspect.getmembers(self.csch, predicate=inspect.ismethod))
            for a, b in methods:
                # support per arch!
                if not str(a).startswith("_"):
                    self.indent = "      "
                    self.log("documenting: " + a + ":")
                    calllable = self.csch.__class__.__dict__[a]
                    try:
                        self.indent = "        "
                        calllable(self.csch)
                        self.log("Ignored : " + type(self.csch).__name__ + "." + a)
                        ignored += 1
                    except cs.DocumentationProcessing as doc:
                        la.LoggingAccess().stdout(str(doc))
                        self.log("Processed : " + type(self.csch).__name__ + "." + a)
                        documented += 1
                    except Exception as ex:
                        m = "Error: " + type(self.csch).__name__ + "." + a + " (" + str(ex) + ") from " + inspect.stack()[1][1]
                        failed += 1
                        self.log(m)
                        print(m, file=sys.stderr)
                        traceback.print_exc()
        la.LoggingAccess().log(
            "finished documenting suite: " + type(self).__name__ +
            " - documented/ignored/failed: " + str(documented) + "/" + str(ignored)+"/" + str(failed))
        return documented, ignored, failed

    def log(self, arg):
        la.LoggingAccess().log(self.indent + arg)
