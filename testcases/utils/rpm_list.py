import ntpath
import testcases.utils.test_utils
from outputControl import logging_access


class RpmList:
    """Class to hold list of file, providing various operations abov themlike get bny arch, get by build (arch+noarch), get srpm and so on"""

    def __init__(self, dir):
        self.files = testcases.utils.test_utils.get_rpms(dir);
        self.topDirs = testcases.utils.test_utils.get_top_dirs(dir);
        self.names = []
        for file in self.files:
            self.names.append(ntpath.basename(file))
        allFiles = testcases.utils.test_utils.get_files(dir);
        logging_access.LoggingAccess().log("Loaded list of " + str(len(self.files)) + " rpms from  directory " + dir)
        if (len(self.files) != len(allFiles)):
            logging_access.LoggingAccess().log("Warning, some files in  " + dir + " - " + str(
                len(allFiles) - len(self.files)) + " are NOT rpms. Ignored")

    def getAllNames(self):
        return self.names

    def getAllFiles(self):
        return self.files

    #thsoe two methods are wierd, but most simpel way to recognize if one build is there, or if bre/koji task was downlaoded
    #single uild form mock have all rpms in singe directory
    #task is stored by archs - each arch is directory and have oe build (with exception of src.rpm and noarch whcih are in "theirs archs"
    def shouldBeBrewDownload(self):
        return len(self.topDirs) != 0

    def shouldBeSingleBuild(self):
        return len(self.topDirs) == 0
