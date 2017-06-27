import os
import tempfile
import errno

import config.global_config
from outputControl import logging_access as la
import config.runtime_config


def closeTestSuite(passed, failed, mtc):
    la.LoggingAccess().stdout("Arch-independet mehtods counted: " + str(mtc))
    la.LoggingAccess().stdout("done - Passed: " + str(passed) + " from total: " + str(passed + failed))
    if failed != 0:
        if config.runtime_config.RuntimeConfig().diewith:
            return config.runtime_config.RuntimeConfig().diewith
        else:
            raise Exception(str(failed) + " tests failed")


# ignored must be taken as a passed test case, since docs are also csch
def closeDocSuite(documented, ignored, failed):
    la.LoggingAccess().log("done - Documented: " + str(documented) + " from total: " + str(documented+ignored+failed),
                           la.Verbosity.TEST)
    if failed != 0:
        if config.runtime_config.RuntimeConfig().diewith:
            return config.runtime_config.RuntimeConfig().diewith
        else:
            raise Exception(str(failed) + " docs failed")


def result(boolval):
    """Return string Passed/FAILED corresponding to boolean True/False."""
    if boolval:
        return 'Passed'
    else:
        return 'FAILED'


def get_rpms(directory):
    return get_files(directory, "rpm")


def get_files(directory, file_suffix="", logging = True):
    files, dirs = get_files_and_dirs(directory, file_suffix, logging)
    return files


def get_dirs(directory, file_suffix="", logging = True):
    files, dirs = get_files_and_dirs(directory, file_suffix, logging)
    return dirs


def get_files_and_dirs(directory, file_suffix="", logging = True):
    """Walk `directory' and get a list of all filenames/dirs in it."""
    if logging:
        la.LoggingAccess().log("Searching in " + directory + " for: *" + file_suffix, la.Verbosity.TEST)
    resList = []
    dirList = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(file_suffix) & os.path.isfile(directory + "/" + f):
                resList.append(directory + "/" + f)
        for d in dirs:
            if os.path.isdir(directory + "/" + d):
                dirList.append(directory + "/" + d)
                nwFiles, nwDirs = (get_files_and_dirs(directory + "/" + d, file_suffix))
                resList = resList + nwFiles
                dirList = dirList + nwDirs
    return resList, dirList


def get_top_dirs(directory):
    """Walk `directory' and get a list of all top directory names in it."""
    la.LoggingAccess().log("Searching in " + directory + " for: top dirs", la.Verbosity.TEST)
    resList = []
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            if os.path.isdir(directory + "/" + d):
                resList.append(d)
    return resList


def get_top_dirs_and_files(directory):
    """Walk `directory' and get a list of all top directory names in it."""
    la.LoggingAccess().log("Searching in " + directory + " for: top dirs and files", la.Verbosity.TEST)
    resList = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if os.path.isfile(directory + "/" + f):
                resList.append(directory + "/" + f)
        for d in dirs:
            if os.path.isdir(directory + "/" + d):
                resList.append(d)
    return resList


def removeNoarchSrpmArch(arches):
    nwList = list(arches)
    if config.global_config.getSrcrpmArch()[0] in nwList:
        nwList.remove(config.global_config.getSrcrpmArch()[0])
    if config.global_config.getNoarch()[0] in nwList:
        nwList.remove(config.global_config.getNoarch()[0])
    return nwList


def saveStringsAsTmpFile(strings, suffix):
    tf = tempfile.NamedTemporaryFile(mode="wt", suffix=suffix, delete=False)
    for item in strings:
        tf.file.write(str(item + "\n"))
    tf.flush()
    tf.close()
    return tf.name


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def rename_default_subpkg(subpkg):
    if subpkg == "":
        subpkg = "default"
    elif subpkg == "debug":
        subpkg = "default-debug"
    return subpkg


# expects a list, not a string, othervise, strange behaviour appears
def replace_archs_with_general_arch(names, arch):
    clean_names = []
    for name in names:
        if arch in name:
            name = name.replace(arch, "ARCH")
        clean_names.append(name)
    return clean_names


def two_lists_diff(desired_list, elements_to_remove):
    diff = list(set(desired_list) - set(elements_to_remove))
    return diff


def get_32bit_id_in_nvra(nvra):
    from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
    parts = nvra.split(".")
    parts[-1] = get_id(parts[-1])
    nvra = ".".join(parts)
    return nvra


# this method expects your testsuite has a "failed" list, if you do not, just use logging_access methods
def log_failed_test(instance, fail):
    instance.failed.append(fail)
    la.LoggingAccess().log("        " + fail, la.Verbosity.TEST)
    return
