#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import sys

import config.general_parser
import config.runtime_config


def runTasks(args):
    print("Running")


def main(argv):
    args = config.general_parser.GeneralParser().parser.parse_args()
    canContinue = config.runtime_config.RuntimeConfig().setFromParser(args)
    if canContinue:
        runTasks(args)


if __name__ == "__main__":
    main(sys.argv[1:])
