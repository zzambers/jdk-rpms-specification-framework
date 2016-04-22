#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import importlib
import os
import sys

import config.general_parser
import config.runtime_config
import utils.test_utils as tu
from outputControl import logging_access


def getTestFiles():
    dir = os.path.dirname(os.path.abspath(__file__))
    flist = tu.get_files(dir+"/testcases", "_test.py")
    logging_access.LoggingAccess().log("Found " + str(len(flist))+" files to run.")
    for n, file in enumerate(flist):
        flist[n] = file[len(dir)+1:-3].replace("/",".")
    if config.global_config.leSort:
            return sorted(flist)
    return flist

def header():
    if  not config.runtime_config.RuntimeConfig().isHeader():
        return
    rpm = config.runtime_config.RuntimeConfig().getRpmList()
    logging_access.LoggingAccess().stdout("os                 : " +rpm.getOs())
    logging_access.LoggingAccess().stdout("os version major   : " +str(rpm.getOsVersionMajor()))
    logging_access.LoggingAccess().stdout("os version         : " +rpm.getOsVersion())
    logging_access.LoggingAccess().stdout("dist               : " +rpm.getDist())
    logging_access.LoggingAccess().stdout("product            : " +rpm.getJava())
    logging_access.LoggingAccess().stdout("version major      : " +rpm.getMajorVersion())
    logging_access.LoggingAccess().stdout("version simplified : " +rpm.getMajorVersionSimplified())
    logging_access.LoggingAccess().stdout("vendor             : " +rpm.getVendor())
    logging_access.LoggingAccess().stdout("package version    : " +rpm.getVersion())
    logging_access.LoggingAccess().stdout("package release    : " +rpm.getRelease())
    logging_access.LoggingAccess().stdout("contained arches   : " +str(rpm.getAllArches()))


def runDocks():
    header();
    logging_access.LoggingAccess().log("Running documentation")
    dlist = []
    ilist = []
    flist = []
    files = getTestFiles();
    for file in files:
        test_module = importlib.import_module(file)
        func = getattr(test_module, "documentAll")
        passed, ignored, failed = func()
        dlist.append(passed)
        ilist.append(ignored)
        flist.append(failed)
    tu.closeDocSuite(sum(dlist), sum(ilist), sum(flist))


def runTasks():
    header();
    logging_access.LoggingAccess().log("Running all testsuites")
    plist=[]
    flist=[]
    clist = []
    files = getTestFiles();
    for file in files:
        test_module = importlib.import_module(file)
        func = getattr(test_module, "testAll")
        passed,  failed, methods = func()
        plist.append(passed)
        flist.append(failed)
        clist.append(methods)
    tu.closeTestSuite(sum(plist), sum(flist), sum(clist))


def main(argv):
    args = config.general_parser.GeneralParser().parser.parse_args(argv)
    canContinue = config.runtime_config.RuntimeConfig().setFromParser(args)
    if canContinue:
        if config.runtime_config.RuntimeConfig().getDocs():
            runDocks()
        else:
            runTasks()


if __name__ == "__main__":
    main(sys.argv[1:])
