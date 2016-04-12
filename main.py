#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import sys

import config.general_parser
import config.runtime_config
from outputControl import logging_access
from testcases.nameTest import name_test
from testcases.nameTest import initibuild_test
import testcases.utils.test_utils as tu


def runDocks():
    logging_access.LoggingAccess().log("Running documentation")
    dlist = []
    ilist = []
    flist = []
    passed, ignored, failed = initibuild_test.documentAll()
    dlist.append(passed)
    ilist.append(ignored)
    flist.append(failed)
    passed, ignored, failed = name_test.documentAll()
    dlist.append(passed)
    ilist.append(ignored)
    flist.append(failed)
    tu.closeDocSuite(sum(dlist), sum(ilist), sum(flist))


def runTasks():
    logging_access.LoggingAccess().log("Running all testsuites")
    plist=[]
    flist=[]
    passed, failed = initibuild_test.testAll()
    plist.append(passed)
    flist.append(failed)
    passed, failed = name_test.testAll()
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
