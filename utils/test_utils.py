import os
import tempfile
import errno
import sys

import config.global_config
from outputControl import logging_access as la
import config.runtime_config


def closeTestSuite(passed, failed, mtc):
    la.LoggingAccess().stdout("Arch-independet mehtods counted: " + str(mtc))
    la.LoggingAccess().stdout("Passed=" + str(passed))
    la.LoggingAccess().stdout("Failed=" + str(failed))
    la.LoggingAccess().stdout("Total=" + str(failed + passed))
    la.LoggingAccess().stdout("Test suite finished.")
    if failed != 0:
        if config.runtime_config.RuntimeConfig().diewith:
            sys.exit(config.runtime_config.RuntimeConfig().diewith)
        else:
            raise Exception(str(failed) + " tests failed")


# ignored must be taken as a passed test case, since docs are also csch
def closeDocSuite(documented, ignored, failed):
    la.LoggingAccess().log("done - Documented: " + str(documented) + " from total: " + str(documented+ignored+failed),
                           la.Verbosity.TEST)
    if failed != 0:
        if config.runtime_config.RuntimeConfig().diewith:
            sys.exit(config.runtime_config.RuntimeConfig().diewith)
        else:
            raise Exception(str(failed) + " docs failed")


def result(boolval):
    """Return string Passed/FAILED corresponding to boolean True/False."""
    if boolval:
        return 'Passed'
    else:
        return 'FAILED'


def get_rpms(directory, logging=True):
    return get_files(directory, "rpm", logging)


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
    elif subpkg == "slowdebug":
        subpkg = "default-slowdebug"
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
    from config.global_config import get_32b_arch_identifiers_in_scriptlets
    parts = nvra.split(".")
    parts[-1] = get_32b_arch_identifiers_in_scriptlets(parts[-1])
    nvra = ".".join(parts)
    return nvra


# this method expects your testsuite has a "list_of_failed_tests" list, if you do not,
# just use logging_access methods
def log_failed_test(instance, fail):
    instance.failed += 1
    instance.list_of_failed_tests.append(fail)
    la.LoggingAccess().log("        " + fail, la.Verbosity.TEST)
    return


def get_arch(instance):
    from config.global_config import get_32b_arch_identifiers_in_scriptlets
    return get_32b_arch_identifiers_in_scriptlets(instance.getCurrentArch())


# this method is shortcut for getting your passes or fails for the sum-up, give two arguments - instance of object
# (usually self, and a bool-result condition)
def passed_or_failed(instance, bool):
    if bool:
        instance.passed += 1
    else:
        instance.failed += 1
    return bool


# reinit method, sets the counts of passed and failed for zero, used for no-arch tests
def _reinit(instance):
    instance.failed = 0
    instance.passed = 0


def xmltestsuite(errors, failures, passed, tests, skipped, name, hostname, time, timestamp):
    text = "<testsuite errors=\"{}\" failures=\"{}\" passed=\"{}\" tests=\"{}\" ".format(errors, failures, passed, tests)
    text += "skipped=\"{}\" name=\"{}\" hostname=\"{}\" time=\"{}\" timestamp=\"{}\">".format(skipped, name, hostname, time, timestamp)
    return text


#tells whether rpms set has headless pkg
def has_headless_pkg():
    return "headless" in "".join(get_rpms("rpms", False))


#tells whether current rpm is rolling release
def is_rolling(name):
    return "rolling" in name
