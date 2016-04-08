import os

from outputControl import logging_access


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
    logging_access.LoggingAccess().log("Searching in " + directory)
    resList = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(file_suffix) & os.path.isfile(directory + "/" + f):
                resList.append(f)
        for d in dirs:
            if os.path.isdir(directory + "/" + d):
                resList = resList + (get_files(directory + "/" + d, file_suffix))
    return resList
