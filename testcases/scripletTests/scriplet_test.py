import ntpath
import sys

import utils.core.base_xtest
import utils.rpmbuild_utils
from outputControl import logging_access as la
from utils.mock.mock_executor import DefaultMock
from utils.rpmbuild_utils import ScripletStarterFinisher


class TestTest(utils.core.base_xtest.BaseTest):
    def __init__(self):
        super().__init__()
        self.passed = 0
        self.failed = 0

    # this test has no asserts, therefore it is not working properly, must be fixed, now gives 0 passes, 0 fails
    def test_allScripletsPresentedAsExpected(self):
        pkgs = self.getBuild()
        for pkg in pkgs:
            for scriplet in ScripletStarterFinisher.allScriplets:
                self.log("searching for " + scriplet + " in " + ntpath.basename(pkg))
                content = utils.rpmbuild_utils.getSrciplet(pkg, scriplet)
                if len(content) == 0:
                    self.log("is " + str(len(content)) + " lines long")
                    self.log("not found?")
                    # todo add asserts
                else:
                    self.log("is " + str(len(content)) + " lines long")
                    # todo add asserts
        return self.passed, self.failed

    # this test is currently disabled
    def allScripletsPReturnsZero(self):
        pkgs = self.getBuild()
        failures=[]
        passes=[]
        skippes=[]
        for pkg in pkgs:
            DefaultMock().importRpm(pkg)
            # now applying scriplets in order
            for scriplet in ScripletStarterFinisher.allScriplets:
                self.log("searching for " + scriplet + " in " + ntpath.basename(pkg))
                content = utils.rpmbuild_utils.getSrciplet(pkg, scriplet)
                if len(content) == 0:
                    self.log(scriplet + " not found in " + ntpath.basename(pkg))
                    skippes.append(scriplet + " - " + ntpath.basename(pkg))
                else:
                    self.log("is " + str(len(content)) + " lines long")
                    self.log("executing " + scriplet + " in " + ntpath.basename(pkg))
                    o, r = DefaultMock().executeScriptlet(pkg, scriplet)
                    self.log(scriplet + "returned " + str(r) + " of " + ntpath.basename(pkg))
                    if r == 0:
                        passes.append(scriplet + " - " + ntpath.basename(pkg))
                    else:
                        failures.append(scriplet + " - " + ntpath.basename(pkg))
        for s in skippes:
            self.log("skipped: " + s)
        for s in skippes:
            self.log("passed : " + s)
        for s in skippes:
            self.log("failed : " + s)
        assert len(failures) == 0

    def setCSCH(self):
        self.csch = None


def testAll():
    return TestTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Basic tests on scriplets")
    la.LoggingAccess().stdout(" - All existing scriplets retuns zero")
    return TestTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
