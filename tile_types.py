from typing import Tuple

import numpy as np

graphic_dt = np.dtype(
    [
        ("ch", np.int32),
        ("fg", "3B"),
        ("bg", "3B"),
    ]
)

tile_dt = np.dtype(
    [
        ("walkable", np.bool), # True if this tile can be walked over
        ("transparent", np.bool), # True if this tile doesn't block FOV
        ("dark", graphic_dt), # graphics for when the tile is not in FOV
        ("light", graphic_dt), # graphics for when the tile is in FOV
    ]
)

def new_tile(
    *,
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype = graphic_dt)

floor_dark: Tuple = (46, 46, 35)
floor_light: Tuple = (173, 159, 64)

floor = new_tile(
    walkable = True, 
    transparent = True, 
    dark = (ord(" "), (255, 255, 255), floor_dark),
    light = (ord(" "), (255, 255, 255), floor_light),
)

wall = new_tile(
    walkable = False, 
    transparent = False, 
    dark = (ord("░"), (0, 0, 0), (36, 35, 27)),
    light = (ord("░"), (0, 0, 0), (94, 82, 44)),
)

down_stairs = new_tile(
    walkable = True,
    transparent = True,
    dark = (ord(">"), (255, 255, 255), floor_dark),
    light = (ord(">"), (255, 255, 255), floor_light)
)