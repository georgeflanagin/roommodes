# -*- coding: utf-8 -*-
"""
roommodes is a program to place speakers in rectangular rooms.
"""
import typing
from   typing import *

min_py = (3, 11)

###
# Standard imports, starting with os and sys
###
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
import contextlib
import getpass
import itertools
import logging
import math
from   pprint import pprint
import tomllib

###
# From hpclib
###
import linuxutils
from   sloppytree import SloppyTree
from   urdecorators import trap
from   urlogger import URLogger

###
# Globals
###
logger = None


###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2024'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin'
__email__ = ['gflanagin@richmond.edu', 'me@georgeflanagin.com']
__status__ = 'in progress'
__license__ = 'MIT'


def axial_mode_freq(dimension:float, n:int=4, cs:float=343) -> tuple:
    """
    Generator to provide the axial mode frequency along the 
    dimension given.

    dimension -- in meteres
    n         -- number of modes to consider
    cs        -- in meters / second

    returns   -- tuple of Hz
    """
    return tuple((cs / 2 * i / dimension) for i in range(1,n+1))


def complex_mode_freq(*, 
    length:float=0, width:float=0, height:float=0, cs:float=343) -> float:
    """
    Calculate oblique or tangential mode frequencies.
    """
    mode_number = 0
    while True:
        mode_number += 1
        yield ((speed_of_sound / 2) * 
        math.sqrt((x / length) ** 2 + (y / width) ** 2 + (z / height) ** 2))


def calculate_speaker_position(length:float, width:float, height:float, 
    x_pos:float, y_pos:float, z_pos:float, cs:float, n:int) -> dict:
    """
    Return a dict whose keys are length, width, and height (x, y, z), and whose
    values are tuples of length n. 
    """

    modes_x = axial_mode_freq(length, n, cs)
    modes_y = axial_mode_freq(width, n, cs)
    modes_z = axial_mode_freq(height, n, cs)
    
    print(f"""
        {modes_x=}
        {modes_y=}
        {modes_z=}
        """)

    proximity_x, proximity_y, proximity_z = ([], [], [])

    for i, f in enumerate(modes_x, 1):
        wavelength = cs / f
        node_positions = [(n * wavelength / 2) for n in range(1, int(length / (wavelength / 2)) + 1)]
        distances = [abs(x_pos - node_pos) for node_pos in node_positions]
        proximity_x.append((min(distances), f))

    for i, f in enumerate(modes_y, 1):
        wavelength = cs / f
        node_positions = [(n * wavelength / 2) for n in range(1, int(length / (wavelength / 2)) + 1)]
        distances = [abs(y_pos - node_pos) for node_pos in node_positions]
        proximity_y.append((min(distances), f))

    for i, f in enumerate(modes_z, 1):
        wavelength = cs / f
        node_positions = [(n * wavelength / 2) for n in range(1, int(length / (wavelength / 2)) + 1)]
        distances = [abs(z_pos - node_pos) for node_pos in node_positions]
        proximity_z.append((min(distances), f))

    return {
        'x' : proximity_x,
        'y' : proximity_y,
        'z' : proximity_z
        }


def speed_of_sound(temperature:float, humidity:float) -> float:
    return 331.3 * math.sqrt(1+temperature/273.15) * (1 + 0.0124 * humidity)



@trap
def roommodes_main(myargs:SloppyTree) -> int:
    """
    Calculate room modes and the effects on and by speaker
    position. Speaker is considered to be a point source, and an
    omnidirectional radiator.
    """
    global logger
    config_error = False

    if not all (_ > 0 for _ in (myargs.xpos, myargs.ypos, myargs.zpos)):
        logger.error("x, y, and z should all be non-negative")
        config_error = True

    if not all(_ > 0 for _ in (myargs.height, myargs.length, myargs.width)):
        logger.error("height, width, and length should all be non-negative")
        config_error = True

    if not 0 < myargs.rh < 1.0:
        logger.error(f"RH of {myargs.rh} is outside 0 < rh < 1")
        config_error = True

    if config_error:
        sys.stderr.write('Found a config error. Check {str(logger)}\n')
        sys.exit(os.EX_CONFIG)
    
    cs = speed_of_sound(myargs.temp, myargs.rh)
    logger.info(f"Speed of sound is {cs} m/s")
    answer = calculate_speaker_position(
        myargs.length, myargs.width, myargs.height, 
        myargs.xpos, myargs.ypos, myargs.zpos, cs, myargs.n
        )
    
    pprint(answer)

    return os.EX_OK


if __name__ == '__main__':

    here       = os.getcwd()
    progname   = os.path.basename(__file__)[:-3]
    configfile = f"{here}/{progname}.toml"
    logfile    = f"{here}/{progname}.log"
    lockfile   = f"{here}/{progname}.lock"
    
    parser = argparse.ArgumentParser(prog="roommodes", 
        description="What roommodes does, roommodes does best.")

    parser.add_argument('--loglevel', type=int, 
        choices=range(logging.FATAL, logging.NOTSET, -10), 
        default=logging.DEBUG, 
        help=f"Logging level, defaults to {logging.DEBUG}")

    parser.add_argument('--zap', action='store_true',
        help=f"Remove {logfile} and create a new one.")

    parser.add_argument('-o', '--output', type=str, default=configfile)

    parser.add_argument('--config', type=str, default=configfile,
        help=f"Read the optional configfile, {configfile}")

    myargs = parser.parse_args()
    if myargs.zap:
        try:
            os.unlink(logfile)
        except:
            pass

    logger = URLogger(logfile=logfile, level=myargs.loglevel)

    try:
        with open(myargs.config, 'rb') as f:
            params = tomllib.load(f)
        myargs = SloppyTree({**vars(myargs), **params})
        logger.info(f"{myargs=}")

    except Exception as e:
        logger.error(str(e))
        sys.exit(os.EX_CONFIG)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")


