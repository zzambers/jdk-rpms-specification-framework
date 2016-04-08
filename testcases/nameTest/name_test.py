""""Test that given set of rpms has the right names."""

import sys

import config.general_parser
import config.global_config as gc
import config.runtime_config
import testcases.utils.pkg_name_split as split
import testcases.utils.test_utils as tu
from outputControl import logging_access as la


def testAll():
    la.LoggingAccess().log("name_test:")
    testArches()


def testArches():
    la.LoggingAccess().log("testArches:")
    rpms = config.runtime_config.RuntimeConfig().getRpmList().getAll()
    arches = gc.getAllArchs();
    failed = 0;
    for file in rpms:
        la.LoggingAccess().log("checking: " + file)
        arch = split.get_arch(file);
        la.LoggingAccess().log("have: " + arch)
        if arch in arches:
            la.LoggingAccess().log("... is known")
        else:
            la.LoggingAccess().log("... is unknown")
            failed = failed + 1
    la.LoggingAccess().stdout(tu.result(failed == 0) + ": testArches")


def main(argv):
    args = config.general_parser.GeneralParser().parser.parse_args(argv)
    canContinue = config.runtime_config.RuntimeConfig().setFromParser(args)
    if canContinue:
        testAll()


if __name__ == "__main__":
    main(sys.argv[1:])
