#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Note:
## This script requires exiftool to be installed.

from __future__ import print_function

import re
import os
import time
import subprocess
import sys
import logging
import readline  # for raw_input() reading from stdin
from optparse import OptionParser

#TODO: Add some Windows readline love, and fail gracefully everywhere
#      if readline is not installed.

PROG_VERSION_NUMBER = u"0.2.0"
PROG_VERSION_DATE = u"2015-01-17"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
BETWEEN_COORD_SEPARATOR = u','

USAGE = u"\n\
    " + sys.argv[0] + u" [<options>] <list of files>\n\
\n\
This tool adds GPS latitude and longitude to files.\n\
\n\
"

class GPSLatitude(object):
    """Parse and print GPS Latitude for exiftool.
    Allowable input is:
    [+-]n[.fffff][NS]
    """
    def __init__(self, value):
       
        m = re.search(r'^([+-]?\d+(?:\.\d*))([NS])?', value)
        if m:
            self.lat = float(m.group(1))
            if self.lat >= 0:
                if m.group(2) in [None, 'N']:
                    self.latref = b'N'
                else:
                    self.latref = b'S'
            else:
                if m.group(2) is None:
                    self.lat = -self.lat
                    self.latref = b'S'
                else:
                    raise ValueError("Negative value cannot have N/S reference")
        else:
            raise ValueError("Unrecognized latitude value \"{}\"".format(value))

        if self.lat > 90.0:
            raise ValueError("Latitude value is out of range: {}".format(self.lat))

    def value(self):
        return self.lat

    def ref(self):
        return self.latref

class SimpleCompleter(object):
    ## happily stolen from http://pymotw.com/2/readline/

    def __init__(self, options):
        self.options = sorted(options)
        return

    def complete(self, text, state):
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s
                                for s in self.options
                                if s and s.startswith(text)]
                logging.debug('%s matches: %s', repr(text), self.matches)
            else:
                self.matches = self.options[:]
                logging.debug('(empty input) matches: %s', self.matches)

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        logging.debug('complete(%s, %s) => %s',
                      repr(text), state, repr(response))
        return response

def handle_arguments(arglist):
    """Command line argument parsing"""
    parser = OptionParser(usage=USAGE)

    parser.add_option("-a", "--alias", dest="alias", action='append',
                      default={},
                      help="define an alias for easier location entry. This argument may be given multiple times.")

    parser.add_option("-s", "--dryrun", dest="dryrun", action="store_true",
                      help="enable dryrun mode: just simulate what would happen, do not modify files.")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="enable verbose mode")

    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="enable quiet mode")

    parser.add_option("--version", dest="version", action="store_true",
                      help="display version and exit")

    parser.add_option("-c", "--confirm", dest="confirm", action="store_true",
                      help="Ask for confirmation before removing GPS info. Default is to not ask.")

    parser.add_option("-r", "--remove", dest="action", action="store_const",
                      const="remove", default="add",
                      help="Remove GPS information from files.")

    (options, args) = parser.parse_args()

    if options.version:
        print(os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_NUMBER + \
            " from " + PROG_VERSION_DATE)
        sys.exit(0)

    if options.verbose and options.quiet:
        error_exit(1, "Options \"--verbose\" and \"--quiet\" found. " +
                   "This does not make any sense, you silly fool :-)")

    return (options, args)

def handle_logging(options):
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

def extract_coords_from_argument(argument):
    """
    @param argument: string containing coordinates
    @param return: a list of unicode coords, possibly an alias
    """

    assert argument.__class__ == str or \
        argument.__class__ == unicode

    return argument.split(unicode(BETWEEN_COORD_SEPARATOR))


def extract_filenames_from_argument(argument):
    """
    @param argument: string containing one or more file names
    @param return: a list of unicode file names
    """

    ## FIXXME: works at my computer without need to convertion but add check later on
    return argument

def bad_filename(filename, dryrun):
    """
    @param filename: string containing one file name
    """
    assert filename.__class__ == str or \
        filename.__class__ == unicode
    if dryrun:
        assert dryrun.__class__ == bool

    if os.path.isdir(filename):
        logging.warning("Skipping directory \"%s\" because this tool only renames proceses file names." % filename)
        return True
    elif not os.path.isfile(filename):
        logging.error("Skipping \"%s\" because this tool only processes existing file names." % filename)
        return True

    return False


def add_gps_to_file(filename, lat, lon, dryrun):
    """
    @param filename: string containing one file name
    @param lat: Latitude, in exiftool-acceptable format
    @param lon: Longitude, in exiftool-acceptable format
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """

    if bad_filename(filename, dryrun):
        return
#    import pdb; pdb.set_trace()

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
        retcode = subprocess.call(cmd, stdout=subprocess.PIPE)
    else:
        retcode = 0

    return retcode

def remove_gps_from_file(filename, dryrun):
    """
    @param filename: string containing one file name
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """
    logging.debug("Removing gps info from \"{}\"".format(filename))
    cmd = ["exiftool",
           "-GPS*=",
           filename]

    logging.info(" ")
    logging.info("Processing command \"%s\"" % cmd)

    if not dryrun:
        retcode = subprocess.call(cmd, stdout=subprocess.PIPE)
    else:
        retcode = 0

    return retcode

def handle_aliases(alias_list):
    logging.debug("alias_list is {}".format(alias_list))
    ad = dict()
    for a in alias_list:
        m = re.search(r'^\s*(\w+)\s*=\s*([^\s,]+)\s*,\s*(\S+?)\s*$', a)
        if m:
            ad[m.group(1)]  = (m.group(2), m.group(3))
        else:
            raise ValueError("Unrecognized alias \"{}\"".format(a))

    return ad

def set_up_input_completion(input_list):
    """Do what is necessary and possible to set up tab completion for input"""

    # Register our completer function
    readline.set_completer(SimpleCompleter(input_list).complete)

    # Use the tab key for completion
    readline.parse_and_bind('tab: complete')

def main(arglist):
    (options, args) = handle_arguments(arglist)

    handle_logging(options)

    alias_dict = handle_aliases(options.alias)

    set_up_input_completion(alias_dict.keys())

    files = extract_filenames_from_argument(args)

    logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))

    next_action = "query user"
    while next_action == "query user":
        print("                 ")
        print("    ,---------.  ")
        print("    |  ?     o | ")
        print("    `---------'  ")
        print("                 ")

        if options.action == "add":
            print("Please enter latitude and longitude, separated by a comma (','):     (abort with Ctrl-C)")
            #entered_coords = sys.stdin.readline().split(',')
            entered_coords = raw_input('Coordinates: ').strip()
            coords = extract_coords_from_argument(entered_coords)

            if len(coords) == 2:
                lat = coords[0]
                lon = coords[1]
                next_action = "OK"
            elif len(coords) == 3:
                lat = coords[0]
                lon = coords[1]
                next_action = "OK"
            elif len(coords) == 1:
                shortcut = coords[0].strip()
                logging.info("coords[0] is \"%s\""%shortcut)
                if shortcut in alias_dict:
                    lat, lon = alias_dict[shortcut]
                    next_action="OK"
                else:
                    print("\nError: shortcut must be one of: {}".format(", ".join(sorted(alias_dict.keys()))));
                    next_action="query user"
            else:
                print("\nError: please enter latitude and longitude, separated by a comma");
                next_action = "query user"

            if next_action == "OK":
                logging.debug("Adding coordinates to files ...")
                for filename in files:
                    add_gps_to_file(filename, lat, lon, options.dryrun)

        else:
            next_action="OK"

            if options.confirm:
                print("Ok to remove GPS coordinates from files? Y/n:     (abort with Ctrl-C)")

                confirmation = sys.stdin.readline().strip().lower()

                if confirmation in (u'', u'y', u'yes'):
                    next_action = "OK"
                elif confirmation in (u'n', u'no'):
                    next_action = "no"
                else:
                    print("Unrecognized response \"{}\"".format(confirmation))
                    next_action = "query user"

            if next_action == "OK":
                logging.debug("Removing coordinates from files ...")
                for filename in files:
                    remove_gps_from_file(filename, options.dryrun)


    logging.debug("successfully finished.")


if __name__ == "__main__":
    #logging.basicConfig(filename="addgps.log", level=logging.DEBUG)
    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end
