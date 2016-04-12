""""Test that given set of rpms has the right names."""

import sys
import re

import config.general_parser
import config.global_config as gc
import config.runtime_config
import testcases.utils.pkg_name_split as split
import testcases.utils.base_xtest
from testcases.utils.configuration_specific import JdkConfiguration
from outputControl import logging_access as la

JAVA_REGEX8="^java-(1\.[5-8]\.[0-9])-.*-.*-.*\..*.rpm$"
# java-1.X.0 or just 9-whatever1-whatever2-whatever3.whatever4.rpm
# w1 = vendor, w2 = version
# w3 = release, w4 = arch .rpm
CRES_JAVA_REGEXE8 = re.compile(JAVA_REGEX8)

JAVA_REGEX9="^java-([1-9][0-9]*)-.*-.*-.*\..*.rpm$"
CRES_JAVA_REGEXE9 = re.compile(JAVA_REGEX9)

ITW_REGEX="^icedtea-web-.*-.*\..*.rpm$"
CRES_ITW_REGEXE = re.compile(ITW_REGEX)


def aInB(a, b):
    return a in b


def aNotNone(a, b):
    return a is not None

def justCopy(a):
    return a


class ItwRegexCheck(JdkConfiguration):

    def checkRegex(self, name=None):
        self._document("RPM of ITW must match following regex: "+ITW_REGEX)
        la.LoggingAccess().log("ITW special call for checkRegex")
        return CRES_ITW_REGEXE.match(name)


class Jdk9RegexCheck(JdkConfiguration):

    def checkRegex(self, name=None):
        self._document("RPM of newer then 8 (except itw) must match following regex: "+JAVA_REGEX9)
        la.LoggingAccess().log("JDK 9 special call for checkRegex")
        return CRES_JAVA_REGEXE9.match(name)


class OthersRegexCheck(JdkConfiguration):

    def checkRegex(self, name=None):
        self._document("RPM of jdks older then 9 and except itw must match following regex: "+JAVA_REGEX8)
        la.LoggingAccess().log("non ITW jdk older then 9 call for checkRegex")
        return CRES_ITW_REGEXE.match(name)


class NameTest(testcases.utils.base_xtest.BaseTest):

    def aMatchesB(self, a, b):
            return self.csch.checkRegex(a)

    def checkFilesAgainstValues(self, values, function):
        return self.checkFilesAgainstComparator(values, function, aInB)

    def checkWholeName(self):
        return self.checkFilesAgainstComparator(None, justCopy, self.aMatchesB)

    def checkFilesAgainstNone(self, function):
        return self.checkFilesAgainstComparator(None, function, aNotNone)

    def checkFilesAgainstComparator(self, values, function, comparator):
        rpms = config.runtime_config.RuntimeConfig().getRpmList().getAllNames()
        failed = 0
        for file in rpms:
            self.log("checking: " + file)
            val = function(file)
            self.log("have: " + val)
            if comparator(val, values):
                self.log("... is ok")
            else:
                self.log("... is BAD")
                failed += 1
        return failed

    def test_prefix(self):
        failed = self.checkFilesAgainstValues([gc.JAVA_STRING, gc.ITW], split.get_javaprefix)
        assert failed == 0

    def test_version(self):
        failed = self.checkFilesAgainstValues(gc.LIST_OF_POSSIBLE_VERSIONS, split.get_major_ver)
        assert failed == 0

    def test_vendor(self):
        failed = self.checkFilesAgainstValues(gc.LIST_OF_POSSIBLE_VENDORS, split.get_vendor)
        assert failed == 0

    def test_majorPackage(self):
        failed = self.checkFilesAgainstNone(split.get_major_package_name)
        assert failed == 0

    def test_package(self):
        failed = self.checkFilesAgainstNone(split.get_package_name)
        assert failed == 0

    def test_minorVersion(self):
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

    def test_dist(self):
        failed = self.checkFilesAgainstNone(split.get_dist)
        assert failed == 0

    def test_wholeName(self):
        """This is testing whole name by regex. It may sound redundant, but:
        The rest of the test checks validity of individual hunks. Not the order.
        The regex catches at least java->version->dashes->dot->arch->.rpm
        """
        failed1 = self.checkWholeName()
        assert failed1 == 0

    def setCSCH(self):
        if config.runtime_config.RuntimeConfig().getRpmList().getJava() == gc.ITW:
            self.log("Set ItwRegexCheck")
            self.csch = ItwRegexCheck()
            return
        if int(config.runtime_config.RuntimeConfig().getRpmList().getMajorVersionSimplified()) >= 9:
            self.log("Set Jdk9RegexCheck")
            self.csch = Jdk9RegexCheck()
            return
        self.log("Set OthersRegexCheck")
        self.csch = OthersRegexCheck()



def testAll():
    return NameTest().execute_tests()


def documentAll():
    return NameTest().execute_special_docs()


def main(argv):
    testcases.utils.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
