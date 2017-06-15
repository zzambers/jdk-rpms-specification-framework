#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import importlib
import os
import sys

import config.general_parser
import config.runtime_config
import utils.test_utils as tu
from outputControl import logging_access as la


def getTestFiles():
    dir = os.path.dirname(os.path.abspath(__file__))
    flist = tu.get_files(dir+"/testcases", "_test.py")
    la.LoggingAccess().log("Found " + str(len(flist))+" files to run.", la.Verbosity.TEST)
    for n, file in enumerate(flist):
        flist[n] = file[len(dir)+1:-3].replace("/",".")
    if config.global_config.leSort:
            return sorted(flist)
    return flist

def header():
    if not config.runtime_config.RuntimeConfig().isHeader():
        return
    rpm = config.runtime_config.RuntimeConfig().getRpmList()
    la.LoggingAccess().stdout("os                 : " +rpm.getOs())
    la.LoggingAccess().stdout("os version major   : " +str(rpm.getOsVersionMajor()))
    la.LoggingAccess().stdout("os version         : " +rpm.getOsVersion())
    la.LoggingAccess().stdout("dist               : " +rpm.getDist())
    la.LoggingAccess().stdout("product            : " +rpm.getJava())
    la.LoggingAccess().stdout("version major      : " +rpm.getMajorVersion())
    la.LoggingAccess().stdout("version simplified : " +rpm.getMajorVersionSimplified())
    la.LoggingAccess().stdout("vendor             : " +rpm.getVendor())
    la.LoggingAccess().stdout("package version    : " +rpm.getVersion())
    la.LoggingAccess().stdout("package release    : " +rpm.getRelease())
    la.LoggingAccess().stdout("contained arches   : " +str(rpm.getAllArches()))


def runDocks():
    header()
    la.LoggingAccess().log("Running documentation", la.Verbosity.TEST)
    dlist = []
    ilist = []
    flist = []
    files = getTestFiles()
    for file in files:
        test_module = importlib.import_module(file)
        func = getattr(test_module, "documentAll")
        passed, ignored, failed = func()
        dlist.append(passed)
        ilist.append(ignored)
        flist.append(failed)
    tu.closeDocSuite(sum(dlist), sum(ilist), sum(flist))


def runTasks():
    header()
    la.LoggingAccess().log("Running all testsuites", la.Verbosity.TEST)
    plist=[]
    flist=[]
    clist = []
    files = getTestFiles()
    for file in files:
        test_module = importlib.import_module(file)
        func = getattr(test_module, "testAll")
        passed, failed, methods = func()
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
