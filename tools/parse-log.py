#!/usr/bin/env python

import argparse
import re


def extract_python_exceptions(log_file):
    """
       Searches a log file for references to Python exceptions
       and returns an array of lines describing the type of
       exception that occurred.
    """
    for line in log_file:
        match = re.match('^(\s+)Traceback', line)
        if match:
            indent = len(match.group(1))
            for line in log_file:
                line_indent = len(re.match('^\s*', line).group(0))
                if line_indent == indent:
                    yield line.strip()
                    break


def main():
    parser = argparse.ArgumentParser(description=
"""Extracts a list of exceptions from Smokey logs.

Given a log file from Smokey, this script parses
out and prints details of exceptions that occurred.
""")
    parser.add_argument('log_file', help="The Smokey log file")
    args = parser.parse_args()

    for exception in extract_python_exceptions(open(args.log_file)):
        print('{}'.format(exception))


if __name__ == '__main__':
    main()
