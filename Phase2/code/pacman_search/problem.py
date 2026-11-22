"""
problem.py
==========
Formal model of the Pac-Man food-collection problem (used unchanged in both phases).

The world is a rectangular grid maze described by a small ASCII map:

    #   wall          Pac-Man can never enter it
    G   ghost         stands still; its cell cannot be entered
    .   food pellet   eaten the moment Pac-Man enters the cell
    P   Pac-Man's starting cell
        (space)       empty corridor

THE SEARCH PROBLEM
------------------
State          (pos, food)
                   pos  = (row, col) of the cell Pac-Man is standing on
                   food = bitmask of the pellets that are still on the board;
                          bit i is 1 while pellet i has not been eaten yet
Initial state  (start cell, all k food bits set to 1)
Goal test      food == 0   -> every pellet has been eaten (the final cell does not matter)
Actions        UP, RIGHT, DOWN, LEFT, restricted to moves whose target cell is neither a
               wall nor a ghost
Transition     Pac-Man moves one cell in the chosen direction; if that cell holds a pellet
               the pellet's bit is cleared
Step cost      1 for entering a normal cell,
               DANGER_COST (5) for entering a cell directly next to a ghost
Path cost      the sum of the step costs along the path

Because the state has to remember WHICH pellets are left (not only where Pac-Man is), the
state space has about  (free cells) x 2^(pellets)  states - see state_space_report().
"""

from collections import deque
from typing import NamedTuple

# --------------------------------------------------------------------------------------
# Layout symbols
# --------------------------------------------------------------------------------------
WALL = "#"
GHOST = "G"
FOOD = "."
START = "P"
EMPTY = " "

# --------------------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------------------
# Each action moves Pac-Man by a (row, col) offset. Row 0 is the TOP row of the maze, so
# UP decreases the row. The order of this dictionary is the order in which successors are
# generated everywhere in the project; it only matters for tie-breaking (for example,
# which branch DFS dives into first).
ACTIONS = {
    "UP": (-1, 0),
    "RIGHT": (0, 1),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
}

STEP_COST = 1      # cost of entering an ordinary cell
DANGER_COST = 5    # cost of entering a cell that is next to a ghost


class State(NamedTuple):
    """One state of the search problem (immutable and hashable, so it can live in sets)."""

    pos: tuple   # (row, col) of Pac-Man
    food: int    # bitmask of the pellets still on the board


class PacmanProblem:
    """The Pac-Man food-collection problem for one maze layout.

    The class answers the five questions that define a search problem:
    initial_state, actions(), result(), step_cost() and is_goal().
    successors() bundles actions/result/step_cost for the search algorithms.
    """

    def __init__(self, layout_text, name="custom", step_cost=STEP_COST, danger_cost=DANGER_COST):
        if step_cost <= 0 or danger_cost <= 0:
            # UCS and A* are only complete and optimal when every step has a positive cost.
            raise ValueError("Step costs must be positive.")
        self.name = name
        self.normal_cost = step_cost
        self.danger_cost = danger_cost

        # ---- 1. read the ASCII map -------------------------------------------------
        self.rows = [line for line in layout_text.strip("\n").split("\n")]
        self.height = len(self.rows)
        self.width = len(self.rows[0])
        if any(len(row) != self.width for row in self.rows):
            raise ValueError("Every row of the layout must have the same length.")

        self.walls = set()
        self.ghosts = []
        food = []
        self.start = None
        for r, row in enumerate(self.rows):
            for c, symbol in enumerate(row):
                cell = (r, c)
                if symbol == WALL:
                    self.walls.add(cell)
                elif symbol == GHOST:
                    self.ghosts.append(cell)
                elif symbol == FOOD:
                    food.append(cell)
                elif symbol == START:
                    if self.start is not None:
                        raise ValueError("The layout must contain exactly one 'P'.")
                    self.start = cell
                elif symbol != EMPTY:
                    raise ValueError(f"Unknown layout symbol {symbol!r} at {cell}.")
        if self.start is None:
            raise ValueError("The layout must contain a start cell 'P'.")
        if not food:
            raise ValueError("The layout must contain at least one food pellet '.'.")

        # ---- 2. cells Pac-Man may stand on -----------------------------------------
        blocked = self.walls | set(self.ghosts)
        self.free_cells = [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in blocked
        ]
        free = set(self.free_cells)

        # ---- 3. danger zone: free cells directly next to a ghost --------------------
        self.danger_cells = set()
        for gr, gc in self.ghosts:
            for dr, dc in ACTIONS.values():
                cell = (gr + dr, gc + dc)
                if cell in free:
                    self.danger_cells.add(cell)

        # ---- 4. pellets: pellet i (reading order) is represented by bit i ----------
        self.food_cells = tuple(food)
        self.num_food = len(food)
        self.food_bit = {cell: 1 << i for i, cell in enumerate(self.food_cells)}
        self.all_food = (1 << self.num_food) - 1

        # ---- 5. the maze graph: for every cell, the moves that are possible --------
        # neighbors[cell] = [(action, next_cell, cost of entering next_cell), ...]
        self.neighbors = {}
        for r, c in self.free_cells:
            moves = []
            for action, (dr, dc) in ACTIONS.items():
                nxt = (r + dr, c + dc)
                if nxt in free:
                    moves.append((action, nxt, self.enter_cost(nxt)))
            self.neighbors[(r, c)] = moves

        self._check_all_food_reachable()
        self._reachable_count = None   # filled lazily by count_reachable_states()

    # ----------------------------------------------------------------------------------
    # The formal problem definition
    # ----------------------------------------------------------------------------------
    @property
    def initial_state(self):
        """Pac-Man on the start cell, every pellet still on the board."""
        return State(self.start, self.all_food)

    def is_goal(self, state):
        """Goal test: no pellet is left."""
        return state.food == 0

    def actions(self, state):
        """Names of the actions that are legal in `state` (no walls, no ghosts)."""
        return [action for action, _, _ in self.neighbors[state.pos]]

    def result(self, state, action):
        """Transition model: the state reached by doing `action` in `state`."""
        if action not in ACTIONS:
            raise ValueError(f"Unknown action {action!r}.")
        dr, dc = ACTIONS[action]
        cell = (state.pos[0] + dr, state.pos[1] + dc)
        if cell not in self.neighbors:
            raise ValueError(f"Action {action} is not legal in state {state}.")
        # Entering a pellet cell eats the pellet: clear its bit (no effect on empty cells).
        return State(cell, state.food & ~self.food_bit.get(cell, 0))

    def step_cost(self, state, action, next_state):
        """Cost of one move = cost of entering the cell we arrive in."""
        return self.enter_cost(next_state.pos)

    def enter_cost(self, cell):
        """1 for a normal cell, DANGER_COST for a cell next to a ghost."""
        return self.danger_cost if cell in self.danger_cells else self.normal_cost

    def successors(self, state):
        """All (action, next_state, step_cost) triples for `state`.

        Equivalent to calling actions(), result() and step_cost() for each legal action,
        but done in one pass over the pre-computed maze graph because the search
        algorithms call it once for every node they expand.
        """
        children = []
        for action, cell, cost in self.neighbors[state.pos]:
            food_left = state.food & ~self.food_bit.get(cell, 0)
            children.append((action, State(cell, food_left), cost))
        return children

    # ----------------------------------------------------------------------------------
    # Checking and replaying solutions
    # ----------------------------------------------------------------------------------
    def execute(self, actions):
        """Replay a list of actions from the initial state.

        Returns (states, total_cost) where `states` contains every state on the way,
        including the initial one. Raises ValueError if an action is illegal. Used by the
        tests and by the experiment code to make sure a plan really is a solution.
        """
        state = self.initial_state
        states = [state]
        total = 0
        for action in actions:
            nxt = self.result(state, action)
            total += self.step_cost(state, action, nxt)
            state = nxt
            states.append(state)
        return states, total

    def is_solution(self, actions):
        """True if `actions` is a legal plan that eats every pellet."""
        try:
            states, _ = self.execute(actions)
        except ValueError:
            return False
        return self.is_goal(states[-1])

    # ----------------------------------------------------------------------------------
    # State-space size
    # ----------------------------------------------------------------------------------
    def state_space_report(self, count_reachable=True):
        """Three counts of the state space, from loosest to exact.

        upper_bound : N * 2^k        every cell combined with every subset of pellets
        valid       : N*2^k - k*2^(k-1)
                      a state in which Pac-Man stands ON a pellet that is still "uneaten"
                      is impossible (entering the cell eats it). For each of the k
                      pellets there are 2^(k-1) such impossible combinations.
        reachable   : states that can actually be reached from the initial state,
                      counted by exhaustive enumeration (see reachable_states()).
                      Pass count_reachable=False to skip this (it is None then).
        """
        n = len(self.free_cells)
        k = self.num_food
        return {
            "free_cells": n,
            "pellets": k,
            "upper_bound": n * 2 ** k,
            "valid": n * 2 ** k - k * 2 ** (k - 1),
            "reachable": self.count_reachable_states() if count_reachable else None,
        }

    def count_reachable_states(self):
        """Count the states reachable from the initial state (exhaustive breadth-first sweep)."""
        if self._reachable_count is None:
            self._reachable_count = len(self.reachable_states())
        return self._reachable_count

    def reachable_states(self):
        """Set of every state reachable from the initial state by any sequence of actions.

        This is the state space in the textbook sense: the sweep has no goal test, so it
        also contains the states in which Pac-Man keeps walking after the last pellet was
        eaten (food == 0 on any free cell). A search never generates most of those,
        because it stops at the first goal state it finds.
        """
        start = self.initial_state
        seen = {start}
        queue = deque([start])
        while queue:
            state = queue.popleft()
            for _, child, _ in self.successors(state):
                if child not in seen:
                    seen.add(child)
                    queue.append(child)
        return seen

    # ----------------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------------
    def _check_all_food_reachable(self):
        """Refuse layouts in which some pellet is walled off from the start cell."""
        seen = {self.start}
        queue = deque([self.start])
        while queue:
            cell = queue.popleft()
            for _, nxt, _ in self.neighbors[cell]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        unreachable = [cell for cell in self.food_cells if cell not in seen]
        if unreachable:
            raise ValueError(f"Pellets at {unreachable} cannot be reached from the start cell.")

    def render(self, states=None):
        """ASCII picture of the maze. If a solution's states are given, the cells it
        visits are marked with '*' (the start cell keeps its 'P')."""
        visited = {s.pos for s in states} if states else set()
        lines = []
        for r, row in enumerate(self.rows):
            line = ""
            for c, symbol in enumerate(row):
                if (r, c) in visited and symbol in (EMPTY, FOOD):
                    line += "*"
                else:
                    line += symbol
            lines.append(line)
        return "\n".join(lines)

    def describe(self, enumerate_up_to=1_000_000):
        """One-paragraph summary of the instance (printed by main.py).

        The exact number of reachable states needs a sweep over the whole state space, so
        it is only computed when the upper bound is at most `enumerate_up_to` states.
        """
        small_enough = len(self.free_cells) * 2 ** self.num_food <= enumerate_up_to
        size = self.state_space_report(count_reachable=small_enough)
        reachable = f"{size['reachable']:,}" if small_enough else "not counted (too many)"
        return (
            f"Layout '{self.name}': {self.height}x{self.width} grid, "
            f"{size['free_cells']} free cells, {size['pellets']} pellets, "
            f"{len(self.ghosts)} ghost(s), {len(self.danger_cells)} danger cells\n"
            f"State space: upper bound {size['upper_bound']:,} | valid {size['valid']:,} | "
            f"reachable {reachable} states"
        )
