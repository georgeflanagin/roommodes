# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 8)

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
import math
from   pprint import pprint

###
# From hpclib
###
import linuxutils
from   urdecorators import show_exceptions_and_frames as trap

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
def roommodes_main(myargs:argparse.Namespace) -> int:
    """
    Calculate room modes and the effects on and by speaker
    position. Speaker is considered to be a point source, and an
    omnidirectional radiator.
    """
    if not all (_ > 0 for _ in (myargs.xpos, myargs.ypos, myargs.zpos)):
        print("x, y, and z should all be non-negative")
        return os.EX_DATAERR

    if not all(_ > 0 for _ in (myargs.height, myargs.length, myargs.width)):
        print("height, width, and length should all be non-negative")
        return os.EX_DATAERR

    if not 0 < myargs.rh < 1.0:
        print(f"RH of {myargs.rh} is outside 0 < rh < 1")
        return os.EX_DATAERR

    cs = speed_of_sound(myargs.temp, myargs.rh)
    answer = calculate_speaker_position(
        myargs.length, myargs.width, myargs.height, 
        myargs.xpos, myargs.ypos, myargs.zpos, cs, myargs.n
        )
    
    pprint(answer)

    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="roommodes", 
        description="What roommodes does, roommodes does best.")

    parser.add_argument('--temp', type=float, default=23.0,
        help="Temperature in Celcius. Default is 23")
    parser.add_argument('--rh', type=float, default=0.6,
        help="Relative Humidity, 0 < rh < 1.0. Default is 0.6")


    parser.add_argument('-n', type=int, default=4,
        help="Number of axial harmonics to consider. Default is 4.")

    parser.add_argument('-ht', '--height', type=float, default=2.5,
        help="Height of the ceiling in meters. Default is 2.5")
    parser.add_argument('-l', '--length', type=float, default=8.4,
        help="Length of the room in meters.")
    parser.add_argument('-w', '--width', type=float, default=6.1,
        help="Width of the room in meters.")


    parser.add_argument('-x', '--xpos', type=float, default=0,
        help="Initial position of the speaker along the length (x axis) of the room.")
    parser.add_argument('-y', '--ypos', type=float, default=0,
        help="Initial position of the speaker along the width (y axis) of the room.")
    parser.add_argument('-z', '--zpos', type=float, default=0,
        help="Height of the speaker above the floor.")


    parser.add_argument('-o', '--output', type=str, default="")


    myargs = parser.parse_args()

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")


