import os

from outputControl import logging_access

def closeTestSuite(passed, failed):
    logging_access.LoggingAccess().stdout("done - Passed: " + str(passed) + " from total: " + str(passed + failed))
    if failed != 0:
        raise Exception(str(failed) + " tests failed")

def closeDocSuite(documented, ignored, failed):
    logging_access.LoggingAccess().log("done - Documented: " + str(documented) + " from total: " + str(documented+ignored+failed))
    if (failed+ignored) != 0:
        raise Exception(str(failed+ignored) + " docs failed")


def result(boolval):
    """Return string Passed/FAILED corresponding to boolean True/False."""
    if boolval:
        return 'Passed'
    else:
        return 'FAILED'


def get_rpms(directory):
    return get_files(directory, "rpm")


def get_files(directory, file_suffix=""):
    """Walk `directory' and get a list of all rpms names in it."""
    logging_access.LoggingAccess().log("Searching in " + directory + " for: *" + file_suffix)
    resList = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(file_suffix) & os.path.isfile(directory + "/" + f):
                resList.append(directory + "/" + f)
        for d in dirs:
            if os.path.isdir(directory + "/" + d):
                resList = resList + (get_files(directory + "/" + d, file_suffix))
    return resList

def get_top_dirs(directory):
    """Walk `directory' and get a list of all top directory names in it."""
    logging_access.LoggingAccess().log("Searching in " + directory + " for: top dirs")
    resList = []
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            if os.path.isdir(directory + "/" + d):
                resList.append(d)
    return resList
