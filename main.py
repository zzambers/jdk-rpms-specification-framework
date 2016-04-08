#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import sys
import config.global_config
import config.general_parser

from outputControl.logging_access import LoggingAccess


def runTasks(args):
    if (True | args.version):
        LoggingAccess().stdout("jdks_specification_framework, version 0.1")
        return


def main(argv):
    args = config.general_parser.GeneralParser().parser.parse_args()
    if len(argv) < 0:
        config.general_parser.GeneralParser().parser.print_help()
    else:
        runTasks(args)


if __name__ == "__main__":
    main(sys.argv[1:])
