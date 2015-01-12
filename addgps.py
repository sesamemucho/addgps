#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Note:
## This script requires exiftool to be installed.

from __future__ import print_function
import os
import time
import subprocess
import sys
import logging
from optparse import OptionParser

PROG_VERSION_NUMBER = "0.1"
PROG_VERSION_DATE = "2014-12-31"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

USAGE = "\n\
    " + sys.argv[0] + " [<options>] <list of files>\n\
\n\
This tool adds GPS latitude and longitude to files.\n\
\n\
"

parser = OptionParser(usage=USAGE)

parser.add_option("-s", "--dryrun", dest="dryrun", action="store_true",
                  help="enable dryrun mode: just simulate what would happen, do not modify files")

parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")

parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="enable quiet mode")

parser.add_option("--version", dest="version", action="store_true",
                  help="display version and exit")

(options, args) = parser.parse_args()


def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.ERROR, format=FORMAT)
    else:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)


def error_exit(errorcode, text):
    """exits with return value of errorcode and prints to stderr"""

    sys.stdout.flush()
    logging.error(text)

    sys.exit(errorcode)

def extract_filenames_from_argument(argument):
    """
    @param argument: string containing one or more file names
    @param return: a list of unicode file names
    """

    ## FIXXME: works at my computer without need to convertion but add check later on
    return argument


def handle_file(filename, lat, lon, dryrun):
    """
    @param filename: string containing one file name
    @param lat: Latitude, in exiftool-acceptable format
    @param lon: Longitude, in exiftool-acceptable format
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """

#    import pdb; pdb.set_trace()

    assert filename.__class__ == str or \
        filename.__class__ == unicode
    if dryrun:
        assert dryrun.__class__ == bool

    if os.path.isdir(filename):
        logging.warning("Skipping directory \"%s\" because this tool only renames proceses file names." % filename)
        return
    elif not os.path.isfile(filename):
        logging.error("Skipping \"%s\" because this tool only processes existing file names." % filename)
        return

    lat = float(lat)
    if lat > 0:
        latref = b'N'
    else:
        lat = -lat
        latref = b'S'

    lon = float(lon)
    if lon > 0:
        lonref = b'E'
    else:
        lon = -lon
        lonref = b'W'

    cmd = ["exiftool",
           "-GPSLatitude=\"%s\""%lat,
           "-GPSLatitudeRef=%s"%latref,
           "-GPSLongitude=\"%s\""%lon,
           "-GPSLongitudeRef=%s"%lonref,
           filename]

    logging.info(" ")
    logging.info("Processing command \"%s\"" % cmd)
    logging.info("exiftool -GPSLatitude=\"%s\" -GPSLatitudeRef=%s -GPSLongitude=\"%s\" -GPSLongitudeRef=%s" % (lat, latref, lon, lonref))
    if not dryrun:
        retcode = subprocess.call(cmd)

def main():
    if options.version:
        print(os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_NUMBER + \
            " from " + PROG_VERSION_DATE)
        sys.exit(0)

    if options.verbose and options.quiet:
        error_exit(1, "Options \"--verbose\" and \"--quiet\" found. " +
                   "This does not make any sense, you silly fool :-)")

    handle_logging()

    print("                 ")
    print("    ,---------.  ")
    print("    |  ?     o | ")
    print("    `---------'  ")
    print("                 ")

    print("Please enter latitude and longitude, separated by a comma (','):     (abort with Ctrl-C)")
    entered_coords = sys.stdin.readline().split(',')
    if len(entered_coords) == 2:
        lat = entered_coords[0]
        lon = entered_coords[1]
    elif len(entered_coords) == 1:
        shortcut = entered_coords[0].strip()
        logging.info("entered_coords[0] is \"%s\""%shortcut)
        if shortcut == "here":
            lat = "0.0"
            lon = "0.0"
        elif shortcut == "there":
            lat = "51.524370"
            lon = "117.025049"
        else:
            error_exit(5, "Shortcut must be one of: here there");
    else:
        error_exit(5, "Please enter latitude and longitude, separated by a comma");

    files = extract_filenames_from_argument(args)

    logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))

    logging.debug("iterate over files ...")
    for filename in files:
        handle_file(filename, lat, lon, options.dryrun)

    logging.debug("successfully finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end
