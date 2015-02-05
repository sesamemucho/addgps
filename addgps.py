#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
addgps
~~~~~~

This script adds or removes GPS coordinate data from
EXIF data in files.

:copyright: (c) 2015 by Bob Forgey <tools@grumpydogconsulting.com>
:license: GPL v2 or any later version
:bugreports: <tools@grumpydogconsulting.com>

"""
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
from argparse import ArgumentParser, RawDescriptionHelpFormatter

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

LOGGER_NAME = u"addgps"
EPILOG = u"\n\
  :copyright:  (c) 2015 and following by Bob Forgey <tools@grumpydogconsulting.com>\n\
  :license:    GPL v3 or any later version\n\
  :URL:        https://github.com/sesamemucho/addgps\n\
  :bugreports: via github (preferred) or <tools@grumpydogconsulting.com>\n\
  :version:    " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"

# Acquire a logger with default setup, for early use
m_logger = logging.getLogger(LOGGER_NAME)

class GPSxyz(object):
    """Parse and print GPS Latitude or Longitude for exiftool.
    Allowable input is:
    [+-]n[.fffff][NS]
    """
    def __init__(self, value, neg_ref, pos_ref, name, maxval):      #pylint: disable=too-many-arguments
        self.name = name.lower()
        self.title = name.title()

        i = re.search(r'^([+-]?\d+(?:\.\d*)?)([{}{}])?'.format(pos_ref, neg_ref), value)
        if i:
            self.val = float(i.group(1))
            if self.val >= 0:
                if i.group(2) in [None, pos_ref]:
                    self.valref = pos_ref
                else:
                    self.valref = neg_ref
            else:
                if i.group(2) is None:
                    self.val = -self.val
                    self.valref = neg_ref
                else:
                    raise ValueError("Negative value cannot have {}/{} reference".format(
                        pos_ref, neg_ref))
        else:
            raise ValueError("Unrecognized {} value \"{}\"".format(name, value))

        if self.val > maxval:
            raise ValueError("{} value is out of range: {}".format(
                self.title, self.val))

    def value(self):
        """Return numerical value of self.val"""
        return self.val

    def ref(self):
        """Return the GPS reference that goes with the value"""
        return self.valref

    def arguments(self):
        """Return the value and reference as parameters for exiftool"""
        return ["-GPS{}=\"{}\"".format(self.title, self.value()),
                "-GPS{}Ref=\"{}\"".format(self.title, self.ref())]

class GPSLatitude(GPSxyz):
    """Parse and print GPS Latitude for exiftool.
    Allowable input is:
    [+-]n[.fffff][NS]
    """
    def __init__(self, value):
        super(GPSLatitude, self).__init__(value, 'S', 'N', 'latitude', 90)

class GPSLongitude(GPSxyz):
    """Parse and print GPS Longitude for exiftool.
    Allowable input is:
    [+-]n[.fffff][NS]
    """
    def __init__(self, value):
        super(GPSLongitude, self).__init__(value, 'E', 'W', 'longitude', 180)

class GPSAltitude(GPSxyz):
    """Parse and print GPS Altitude for exiftool"""
    def __init__(self, value):
        super(GPSAltitude, self).__init__(
            value,
            'Below sea level',
            'Above sea level',
            'altitude',
            10000000)

        if value is None or value == "":
            self.val = None
            self.valref = ''
        else:
            i = re.search(r'^([+-]?\d+(?:\.\d*)?)(f)?', value)
            if i:
                self.val = float(i.group(1))
                if i.group(2) == 'f':
                    self.val *= 0.304 # feet to meters

                if self.val < 0:
                    self.val = -self.val
                    self.valref = 'Below sea level'
                else:
                    self.valref = 'Above sea level'

            else:
                raise ValueError("Unrecognized {} value \"{}\"".format(self.name, value))

    def arguments(self):
        """Return the value and reference as parameters for exiftool"""
        if self.val is None:
            return []
        else:
            return ["-GPS{}=\"{}\"".format(self.title, self.value()),
                    "-GPS{}Ref=\"{}\"".format(self.title, self.ref())]

class SimpleCompleter(object):
    """Used to complete GPS coordinate aliases.
    Happily stolen from http://pymotw.com/2/readline/
    """

    def __init__(self, options):
        self.options = sorted(options)
        return

    def complete(self, text, state):
        """Perform completion. See readline module for more info."""

        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                matches = [s
                           for s in self.options
                           if s and s.startswith(text)]
                m_logger.debug('%s matches: %s', repr(text), matches)
            else:
                matches = self.options[:]
                m_logger.debug('(empty input) matches: %s', matches)

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = matches[state]
        except IndexError:
            response = None
        m_logger.debug('complete(%s, %s) => %s',
                       repr(text), state, repr(response))
        return response

def handle_arguments(arglist):
    """Command line argument parsing"""

    mydescription = u"FIXXME. Please refer to \n" + \
        "https://github.com/sesamemucho/addgps for more information."

    parser = ArgumentParser(prog=os.path.basename(sys.argv[0]),
                            ## keep line breaks in EPILOG and such
                            formatter_class=RawDescriptionHelpFormatter,
                            epilog=EPILOG,
                            description=mydescription)

    parser.add_argument("-a", "--alias", dest="alias", action='append',
                        default={},
                        help=("define an alias for easier location entry. " +
                              "This argument may be given multiple times."))

    parser.add_argument("-s", "--dryrun", dest="dryrun", action="store_true",
                        help=("enable dryrun mode: just simulate what " +
                              "would happen, do not modify files."))

    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="enable verbose mode")

    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                        help="enable quiet mode")

    parser.add_argument("--logfile", dest="logfile", action="store",
                        help="Name of log file")

    parser.add_argument("-r", "--remove", dest="action", action="store_const",
                        const="remove", default="add",
                        help="Remove GPS information from files.")

    parser.add_argument("-c", "--confirm", dest="confirm", action="store_true",
                        help=("Ask for confirmation before removing GPS " +
                              "info. Default is to not ask."))

    parser.add_argument("--version", action="version",
                        version="%(prog)s " + PROG_VERSION_NUMBER)
    #version="%(prog) " + PROG_VERSION_NUMBER)

    parser.add_argument("filelist", nargs="+")

    args = parser.parse_args(arglist)

    if args.verbose and args.quiet:
        parser.error("please use either verbose (--verbose) or quiet (-q) option")

    return args

def initialize_logging(args):
    """Log handling and configuration"""

    logger = logging.getLogger(LOGGER_NAME)

    # create console handler and set level to debug
    if args.logfile:
        handler = logging.FileHandler(args.logfile)
    else:
        handler = logging.StreamHandler()

    log_format = None
    if args.verbose:
        log_format = "%(levelname)-8s %(asctime)-15s %(message)s"
        handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        log_format = "%(levelname)-8s %(message)s"
        handler.setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)
    else:
        log_format = "%(levelname)-8s %(message)s"
        handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter(log_format)

    # add formatter to handler
    handler.setFormatter(formatter)

    # add console_handler to logger
    logger.addHandler(handler)

    # Make sure warning and error messages always go to console
    if args.logfile:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
        logger.addHandler(console_handler)

    ## omit double output (default handler and my own handler):
    logger.propagate = False

    ## # "application" code
    ## logger.debug("debug message")
    ## logger.info("info message")
    ## logger.warn("warn message")
    ## logger.error("error message")
    ## logger.critical("critical message")

    logger.debug("logging initialized")


def error_exit(errorcode, text):
    """exits with return value of errorcode and prints to stderr"""

    sys.stdout.flush()
    m_logger.error(text)

    sys.exit(errorcode)

def extract_coords_from_argument(argument):
    """
    @param argument: string containing coordinates
    @param return: a list of unicode coords, possibly an alias
    """

    assert argument.__class__ == str or \
        argument.__class__ == unicode

    return [a.strip() for a in argument.split(unicode(BETWEEN_COORD_SEPARATOR))]


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
        m_logger.warning(
            "Skipping directory \"%s\" because this tool only renames proceses file names.",
            filename)
        return True
    elif not os.path.isfile(filename):
        m_logger.error(
            "Skipping \"%s\" because this tool only processes existing file names.",
            filename)
        return True

    return False


def add_gps_to_file(filename, lat, lon, alt, dryrun):
    """
    @param filename: string containing one file name
    @param lat: Latitude, in exiftool-acceptable format
    @param lon: Longitude, in exiftool-acceptable format
    @param alt: Altitude, in exiftool-acceptable format
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """

    if bad_filename(filename, dryrun):
        return
#    import pdb; pdb.set_trace()

    cmdlist = ["exiftool",]
    cmdlist.extend(lat.arguments())
    cmdlist.extend(lon.arguments())
    cmdlist.extend(alt.arguments())
    cmdlist.append(filename)

    m_logger.info(" ")
    m_logger.info("Processing command \"%s\"", cmdlist)

    if not dryrun:
        retcode = subprocess.call(cmdlist, stdout=subprocess.PIPE)
    else:
        retcode = 0

    return retcode

def remove_gps_from_file(filename, dryrun):
    """
    @param filename: string containing one file name
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """
    m_logger.debug("Removing gps info from \"%s\"", filename)
    cmd = ["exiftool",
           "-GPS*=",
           filename]

    m_logger.info(" ")
    m_logger.info("Processing command \"%s\"", cmd)

    if not dryrun:
        retcode = subprocess.call(cmd, stdout=subprocess.PIPE)
    else:
        retcode = 0

    return retcode

def handle_aliases(alias_list):
    """Given a list of alias definitions, make a dictionary from them."""
    m_logger.debug("alias_list is %s", alias_list)
    aliases = dict()
    for alias in alias_list:
        i = re.search(r'^\s*(\w+)\s*=\s*([^\s,]+)\s*,\s*([^\s,]+)\s*,?\s*((?:\d+f?)?)\s*$', alias)
        if i:
            aliases[i.group(1)] = (i.group(2), i.group(3), i.group(4))
        else:
            raise ValueError("Unrecognized alias \"{}\"".format(alias))

    return aliases

def set_up_input_completion(input_list):
    """Do what is necessary and possible to set up tab completion for input"""

    # Register our completer function
    readline.set_completer(SimpleCompleter(input_list).complete)

    # Use the tab key for completion
    readline.parse_and_bind('tab: complete')

def get_lat_lon(files, args):
    """Processes user entry for adding GPS coordinates to files"""

    alias_dict = handle_aliases(args.alias)

    set_up_input_completion(alias_dict.keys())

    while True:
        print("                 ")
        print("    ,---------.  ")
        print("    |  ?     o | ")
        print("    `---------'  ")
        print("                 ")

        print("Please enter latitude and longitude, separated " +
              "by a comma (','):     (abort with Ctrl-C)")
        #entered_coords = sys.stdin.readline().split(',')
        entered_coords = raw_input('Coordinates: ').strip()
        coords = extract_coords_from_argument(entered_coords)

        if len(coords) == 2:
            lat = coords[0]
            lon = coords[1]
            alt = None
        elif len(coords) == 3:
            lat = coords[0]
            lon = coords[1]
            alt = coords[2]
        elif len(coords) == 1:
            shortcut = coords[0].strip()
            m_logger.info("coords[0] is \"%s\"", shortcut)
            if shortcut in alias_dict:
                lat, lon, alt = alias_dict[shortcut]
            else:
                print("\nError: shortcut must be one of: {}".format(
                    ", ".join(sorted(alias_dict.keys()))))
                continue
        else:
            print("\nError: please enter latitude and longitude, separated by a comma")
            continue

        m_logger.debug("Adding coordinates to files ...")
        try:
            latitude = GPSLatitude(lat)
            longitude = GPSLongitude(lon)
            altitude = GPSAltitude(alt)
            for filename in files:
                add_gps_to_file(filename, latitude, longitude, altitude, args.dryrun)
                break
        except ValueError as exception:
            print("Error: {}".format(exception))


    return

def remove_lat_lon(files, args):
    """Processes user entry for adding GPS coordinates to files"""
    while True:
        if args.confirm:
            print("Ok to remove GPS coordinates from files? Y/n:     (abort with Ctrl-C)")

            confirmation = sys.stdin.readline().strip().lower()

            if confirmation in (u'', u'y', u'yes'):
                pass
            elif confirmation in (u'n', u'no'):
                break
            else:
                print("Unrecognized response \"{}\"".format(confirmation))
                continue

        m_logger.debug("Removing coordinates from files ...")
        for filename in files:
            remove_gps_from_file(filename, args.dryrun)
            break

    return

def main(arglist):
    """Main routine"""
    args = handle_arguments(arglist)

    initialize_logging(args)

    files = args.filelist

    m_logger.debug("%d filenames found: [%s]", len(files), '], ['.join(files))

    if args.action == "add":
        get_lat_lon(files, args)
    else:
        remove_lat_lon(files, args)

    m_logger.debug("successfully finished.")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:

        m_logger.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end
