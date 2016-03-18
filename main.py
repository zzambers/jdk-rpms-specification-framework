#!/usr/bin/env python3

"""Main entry point to jdks_specification_framework."""

import sys
import argparse

def createParser():
    parser = argparse.ArgumentParser()

    parser.add_argument( "-v", "--version",
        help="display the version of the framework",
        action="store_true" )

    return parser

def runTasks( args ):
    if( args.version ):
        print( "jdks_specification_framework, version 0.1" )
        return

def main( argv ):
    parser = createParser()
    args = parser.parse_args()
    if( len( argv ) < 1 ):
        parser.print_help()
    else:
        runTasks( args )

if __name__ == "__main__":
    main(sys.argv[1:])


