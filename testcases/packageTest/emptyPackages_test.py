import sys

import utils.pkg_name_split as split

import config.global_config
import config.runtime_config
import utils.core.base_xtest
from outputControl import logging_access as la


class EpmtyPackageTest(utils.core.base_xtest.BaseTest):


    def test_checkNoPacakgeEmpty(self):
        pkgs= config.runtime_config.RuntimeConfig().getRpmList().getAllFiles()
        for pkg in pkgs:
            self.log("checking: " + pkg)
            files = utils.rpmbuild_utils.listFilesInPackage(pkg)
            self.log("got: " + str(len(files)) + " files")
            if split.get_arch(pkg) in config.global_config.getSrcrpmArch():
                assert len(files) > 1
            else:
                assert len(files) > 2



    def getTestedArchs(self):
        return None



def testAll():
    return EpmtyPackageTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Currently all java packages must have at least three files (except srpm which is enough with 2 and more)")
    return EpmtyPackageTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])