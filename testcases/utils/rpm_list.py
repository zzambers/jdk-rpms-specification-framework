import testcases.utils.test_utils
from outputControl import logging_access


class RpmList:
    """Class to hold list of file, providing various operations abov themlike get bny arch, get by build (arch+noarch), get srpm and so on"""

    def __init__(self, dir):
        self.files = testcases.utils.test_utils.get_rpms(dir);
        allFiles = testcases.utils.test_utils.get_files(dir);
        logging_access.LoggingAccess().log("Loaded list of " + str(len(self.files)) + " rpms from  directory " + dir)
        if (len(self.files) != len(allFiles)):
            logging_access.LoggingAccess().log("Warning, some files in  " + dir + " - " + str(
                len(allFiles) - len(self.files)) + " are NOT rpms. Ignored")

    def getAll(self):
        return self.files
