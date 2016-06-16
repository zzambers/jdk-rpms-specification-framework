import sys
import  ntpath
import utils.core.base_xtest
from outputControl import logging_access as la
from utils.rpmbuild_utils import ScripletStarterFinisher
import utils.rpmbuild_utils
from utils.mock.mock_executor import DefaultMock


class TestTest(utils.core.base_xtest.BaseTest):

    def test_allScripletsPresentedAsExpected(self):
        pkgs = self.getBuild()
        for pkg in pkgs:
            for scriplet in ScripletStarterFinisher.allScriplets:
                self.log("searching for "+scriplet+" in "+ntpath.basename(pkg))
                content = utils.rpmbuild_utils.getSrciplet(pkg, scriplet)
                if len(content) == 0:
                    self.log("not found")
                else:
                    self.log("is " + str(len(content))+ " lines long")
                # todo add asserts

    def test_allScripletsPReturnsZero(self):
        pkgs = self.getBuild()
        for pkg in pkgs:
            for scriplet in ScripletStarterFinisher.allScriplets:
                self.log("searching for " + scriplet + " in " + ntpath.basename(pkg))
                content = utils.rpmbuild_utils.getSrciplet(pkg, scriplet)
                if len(content) == 0:
                    self.log("not found")
                else:
                    self.log("is " + str(len(content)) + " lines long")
                    self.log("executing " + scriplet + " in " + ntpath.basename(pkg))
                    DefaultMock().provideCleanUsefullRoot()
                    DefaultMock().importUnpackedRpm(pkg)
                    o, r = DefaultMock().executeScriptlet(pkg, scriplet)
                    assert r ==0




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
