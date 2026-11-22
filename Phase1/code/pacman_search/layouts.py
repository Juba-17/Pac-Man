"""
layouts.py
==========
The maze layouts used in the project, written as ASCII maps.

    #  wall      G  ghost (static)      .  food pellet      P  Pac-Man's start      ' '  corridor

Four layouts are provided. Their state spaces grow from "small enough to draw the whole
search tree" up to the top of the 1,000-10,000 range required by the project:

    name     grid    free cells  pellets  ghosts   reachable states
    tiny      6x7        14         2       1              45      (search-tree drawings only)
    small     7x11       35         5       2           1,016
    medium   11x13       68         6       2           4,160
    large     9x9        38         8       1           8,576      (main instance)

"small / medium / large" refer to the size of the STATE SPACE, not of the grid: the large
layout is a compact maze, but its 8 pellets give 2^8 = 256 food combinations per cell.

The ghosts were placed so that in every layout the plans with the fewest steps are NOT
the cheapest plans: every fewest-step plan has to enter danger cells, and a longer, safer
plan costs less. This is what separates BFS/IDS (fewest steps) from UCS (lowest cost).
run_phase1.py writes the exact numbers to tradeoff.csv (see step_cost_tradeoff in
experiments.py).
"""

from .problem import PacmanProblem

LAYOUTS = {
    # 14 free cells, 2 pellets. The short way to the top-right pellet passes the ghost.
    "tiny": """
#######
#P   .#
# #G# #
#.### #
#     #
#######
""",

    # 35 free cells, 5 pellets. Pac-Man starts in the top-left corner, next to the upper of
    # two ghosts; the direct routes on the left side of the maze are dangerous.
    "small": """
###########
#P  .#   .#
# G # # # #
#         #
# G## # # #
#.   .   .#
###########
""",

    # 68 free cells, 6 pellets, two ghosts guarding the central connectors.
    "medium": """
#############
#P    #    .#
# ### G ### #
#           #
# # ## ## # #
#.#   .   #.#
# # G#### # #
#           #
# ### # ### #
#.    #    .#
#############
""",

    # 38 free cells, 8 pellets. The ghost makes the right-hand passage between the two
    # middle corridors dangerous; the left-hand passage is safe but farther away.
    "large": """
#########
#P .   .#
# # # # #
#   .   #
## ##G ##
#.     .#
# # # # #
#.  .  .#
#########
""",
}

# The three layouts whose state spaces are inside the required 1K-10K range.
OFFICIAL_LAYOUTS = ("small", "medium", "large")
DEFAULT_LAYOUT = "large"


def load_problem(name=DEFAULT_LAYOUT):
    """Build the PacmanProblem for one of the built-in layouts."""
    if name not in LAYOUTS:
        raise KeyError(f"Unknown layout {name!r}. Available: {', '.join(LAYOUTS)}")
    return PacmanProblem(LAYOUTS[name], name)


def load_problem_from_file(path):
    """Build a PacmanProblem from a text file that contains an ASCII map (same symbols).

    'utf-8-sig' also accepts files that start with a byte-order mark (some Windows editors
    write one). Raises OSError / UnicodeError / ValueError if the file cannot be used.
    """
    with open(path, encoding="utf-8-sig") as handle:
        return PacmanProblem(handle.read(), name=str(path))
