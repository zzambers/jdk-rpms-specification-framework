""""Test that given set of rpms has the right names."""

import sys
import re

import config.general_parser
import config.global_config as gc
import config.runtime_config
import testcases.utils.pkg_name_split as split
import testcases.utils.base_test

CRES_JAVA_REGEXE = re.compile("^java-(1.[5-8].[0-1])|(9)-.*-.*-.*\..*.rpm$")
# java-1.X.0 or just 9-whatever1-whatever2-whatever3.whatever4.rpm
# w1 = vendor, w2 = version
# w3 = release, w4 = arch .rpm


def aInB(a, b):
    return a in b


def aNotNone(a, b):
    return a != None


def aMatchesB(a, b):
    return b.match(a)


def justCopy(a):
    return a


class NameTest(testcases.utils.base_test.BaseTest):
    def checkFilesAgainstValues(self, values, function):
        return self.checkFilesAgainstComparator(values, function, aInB)

    def checkWholeName(self, value):
        return self.checkFilesAgainstComparator(value, justCopy, aMatchesB)

    def checkFilesAgainstNone(self, function):
        return self.checkFilesAgainstComparator(None, function, aNotNone)

    def checkFilesAgainstComparator(self, values, function, comparator):
        rpms = config.runtime_config.RuntimeConfig().getRpmList().getAll()
        failed = 0
        for file in rpms:
            self.log("checking: " + file)
            val = function(file)
            self.log("have: " + val)
            if comparator(val, values):
                self.log("... is ok")
            else:
                self.log("... is BAD")
                failed = failed + 1
        return failed

    def test_prefix(self):
        failed = self.checkFilesAgainstValues([gc.JAVA_STRING], split.get_javaprefix)
        assert failed == 0

    def test_version(self):
        failed = self.checkFilesAgainstValues(gc.LIST_OF_POSSIBLE_VERSIONS, split.get_major_ver)
        assert failed == 0

    def test_vendor(self):
        failed = self.checkFilesAgainstValues(gc.LIST_OF_POSSIBLE_VENDORS, split.get_vendor)
        assert failed == 0

    def test_version(self):
        failed = self.checkFilesAgainstNone(split.get_minor_ver)
        assert failed == 0

    def test_subpackage(self):
        failed = self.checkFilesAgainstNone(split.get_subpackage_only)
        assert failed == 0

    def test_release(self):
        failed = self.checkFilesAgainstNone(split.get_release)
        assert failed == 0

    def test_arches(self):
        failed = self.checkFilesAgainstValues(gc.getAllArchs(), split.get_arch)
        assert failed == 0

    def test_wholeName(self):
        """This is testing whole name by regex. It may sound redundant, but:
        The rest of the test checks validity of individual hunks. Not the order.
        The regex catches at least java->version->dashes->dot->arch->.rpm
        """
        failed = self.checkWholeName(CRES_JAVA_REGEXE)
        assert failed == 0


def testAll():
    return NameTest().execute_tests()


def main(argv):
    testcases.utils.base_test.defaultMain(argv, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
