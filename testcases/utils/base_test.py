from outputControl import logging_access as la
import traceback
import inspect
import testcases.utils.test_utils as tu
import config.general_parser
import config.runtime_config


def defaultMain(argv, run):
    args = config.general_parser.GeneralParser().parser.parse_args(argv)
    canContinue = config.runtime_config.RuntimeConfig().setFromParser(args)
    if canContinue:
        passed, failed = run()
        tu.closeSuite(passed, failed);


class BaseTest:
    def __init__(self):
        self.indent = "";
        self.passed = 0;
        self.failed = 0;

    def execute_tests(self):
        self.indent = "  "
        self.log("started suite: " + type(self).__name__ + ":")
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for a, b in methods:
            if str(a).startswith("test_"):
                self.indent = "    "
                self.log("started: " + a + ":")
                callable = self.__class__.__dict__[a]
                try:
                    self.indent = "      "
                    callable(self)
                    self.passed += 1
                    la.LoggingAccess().stdout(tu.result(True) + ": " + type(self).__name__ + "." + a)
                except BaseException as ex:
                    la.LoggingAccess().stdout(
                        tu.result(False) + ": " + type(self).__name__ + "." + a + " ("+str(ex)+") from " + inspect.stack()[1][1])
                    self.failed += 1
                    traceback.print_exc()
        la.LoggingAccess().log(
            "finished suite: " + type(self).__name__ + " - failed/total: " + str(self.failed) + "/" + str(
                self.failed + self.passed))
        return self.passed, self.failed

    def log(self, arg):
        la.LoggingAccess().log(self.indent + arg)
