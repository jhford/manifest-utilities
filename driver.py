#!/usr/bin/env python

from diff import diff
from filter import filter
from cleanup import cleanup
import optparse
import os
import sys

def main():
    parser = optparse.OptionParser("%prog - I diff repo manifests")
    parser.add_option("--filter", dest="filters", action="append")
    parser.add_option("--diff", "-d", dest="diff", action="store_false", default=True)
    parser.add_option("--format", dest="out_format", default="report")
    parser.add_option("--output", dest="output", default=None)
    options, args = parser.parse_args()

    if not options.output:
        output = sys.stdout
    else:
        output = options.output
        if os.path.exists(output):
            print >> sys.stderr, "ERROR: Output file already exists"
            exit(1)
    cmd = args[0]
    if len(args) > 1:
        cmd_args = args[1:]
    else:
        cmd_args = None
    if cmd == 'diff':
        if len(cmd_args) != 2:
            print >> sys.stderr, "ERROR: must specify exactly two arguments (left and right)"
            exit(1)
        diff(cmd_args[0], cmd_args[1], output=output, output_format=options.out_format, filters=options.filters)
    elif cmd == 'cleanup':
        if len(cmd_args) != 1:
            print >> sys.stderr, "ERROR: you can only filter one file at a time"
            exit(1)
        cleanup(cmd_args[0], output, options.filters)
    elif cmd == 'filter':
        if len(cmd_args) != 1:
            print >> sys.stderr, "ERROR: you can only filter one file at a time"
            exit(1)
        if options.filters == None:
            print >> sys.stderr, "ERROR: you must specify filters for the filter command"
            exit(1)
        filter(cmd_args[0], output, options.filters)



if __name__ == "__main__":
    main()
