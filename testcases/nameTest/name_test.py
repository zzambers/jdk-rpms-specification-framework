import sys

import config.general_parser
import config.runtime_config
from outputControl import logging_access


def testAll():
    logging_access.LoggingAccess().log("Running name_test")

def main(argv):
    args = config.general_parser.GeneralParser().parser.parse_args(argv)
    canContinue = config.runtime_config.RuntimeConfig().setFromParser(args)
    if canContinue:
        testAll()


if __name__ == "__main__":
    main(sys.argv[1:])