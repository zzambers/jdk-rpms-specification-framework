#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import sys
import os
import importlib

import config.general_parser
import config.runtime_config
from outputControl import logging_access
from testcases.nameTest import name_test
from testcases.nameTest import initibuild_test
import testcases.utils.test_utils as tu


def getTestFiles():
    dir = os.path.dirname(os.path.abspath(__file__))
    flist = tu.get_files(dir+"/testcases", "_test.py")
    logging_access.LoggingAccess().log("Found " + str(len(flist))+" files to run.")
    for n, file in enumerate(flist):
        flist[n] = file[len(dir)+1:-3].replace("/",".")
    if config.global_config.leSort:
            return sorted(flist)
    return flist


def runDocks():
    #loop
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
    #loop
    logging_access.LoggingAccess().log("Running all testsuites")
    plist=[]
    flist=[]
    files = getTestFiles();
    for file in files:
        test_module = importlib.import_module(file)
        func = getattr(test_module, "testAll")
        passed,  failed = func()
        plist.append(passed)
        flist.append(failed)
    tu.closeTestSuite(sum(plist), sum(flist))


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
