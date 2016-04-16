import sys
import testcases.utils.core.base_xtest
from outputControl import logging_access as la
import config.runtime_config
import testcases.utils.rpmbuild_utils

class EpmtyPackageTest(testcases.utils.core.base_xtest.BaseTest):


    def test_checkNoPacakgeEmpty(self):
        pkgs= config.runtime_config.RuntimeConfig().getRpmList().getAllFiles()
        for pkg in pkgs:
            self.log("checking: " + pkg)
            files = testcases.utils.rpmbuild_utils.listFilesInPackage(pkg)
            self.log("got: " + str(len(files)) + " files")
            assert len(files) > 2



    def getTestedArchs(self):
        return None



def testAll():
    return EpmtyPackageTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Currently all java packages must have at least three files")
    return EpmtyPackageTest().execute_special_docs()


def main(argv):
    testcases.utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])