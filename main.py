#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import argparse
import sys

from outputControl.logging_access import LoggingAccess


def createParser():
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--version",
                        help="display the version of the framework",
                        action="store_true")

    return parser


def runTasks(args):
    if (True | args.version):
        LoggingAccess().stdout("jdks_specification_framework, version 0.1")
        return


def main(argv):
    parser = createParser()
    args = parser.parse_args()
    if (len(argv) < 0):
        parser.print_help()
    else:
        runTasks(args)


if __name__ == "__main__":
    main(sys.argv[1:])
