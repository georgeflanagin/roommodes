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
import math

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


def speed_of_sound(temperature:float, humidity:float) -> float:
    return 331.3 * math.sqrt(1+temperature/273.15) * (1 + 0.0124 * humidity)


def calculate_room_modes(length:float, width:float, height:float, 
    x:float, y:float, z:float, 
    speed_of_sound=343) -> float:
    # Calculate the frequency of the room mode
    return ((speed_of_sound / 2) * 
        math.sqrt((x / length) ** 2 + (y / width) ** 2 + (z / height) ** 2))

def calculate_speaker_position(length:float, width:float, height:float, 
    x_pos:float, y_pos:float, z_pos:float, cs:float, n:int) -> dict:
    """
    Return a dict whose keys are length, width, and height (x, y, z), and whose
    values are tuples of length n. 
    """
    
    # Generator expressions to invoke calculate_room_modes.
    modes_x = (calculate_room_modes(length, width, height, i, 0, 0, cs) for i in range(1, n+1))
    modes_y = (calculate_room_modes(length, width, height, 0, i, 0, cs) for i in range(1, n+1))
    modes_z = (calculate_room_modes(length, width, height, 0, 0, 1, cs) for i in range(1, n+1))
    
    # Check how close the speaker is to these modes
    proximity_x = tuple((abs(x_pos - (i * length / 2)) for i in modes_x))
    proximity_y = tuple((abs(y_pos - (i * width / 2)) for i in modes_y))
    proximity_z = tuple((abs(z_pos - (i * height / 2)) for i in modes_z))
    
    return {
        'x' : proximity_x,
        'y' : proximity_y,
        'z' : proximity_z
        }



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

    cs = speed_of_sound(myargs.temp, myargs.rh)
    answer = calculate_speaker_position(
        myargs.length, myargs.width, myargs.height, 
        x_pos, y_pos, z_pos, cs, myargs.n
        )
    
    print(f"{answer=}")

    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="roommodes", 
        description="What roommodes does, roommodes does best.")

    parser.add_argument('--temp', type=float, default=23.0,
        help="Temperature in Celcius. Default is 23")
    parser.add_argument('--rh', type=float, default=0.6,
        help="Relative Humidity, 0 < rh < 1.0. Default is 0.6")


    parser.add_argument('-n', type=int, default=4,
        help="Number of harmonics to consider. Default is 4.")

    parser.add_argument('-ht', '--height', type=float, default=2.5,
        help="Height of the ceiling in meters. Default is 2.5")
    parser.add_argument('-l', '--length', type=float, default=0,
        help="Length of the room in meters.")
    parser.add_argument('-w', '--width', type=float, default=0,
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


