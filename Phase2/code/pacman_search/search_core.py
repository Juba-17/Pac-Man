"""
search_core.py
==============
Small building blocks shared by every search algorithm in the project.

Node          a node of the search tree: a state plus how we got there
SearchResult  everything an algorithm reports back (the solution and the measurements)
SearchStats   bookkeeping helper: counts generated / expanded nodes, tracks the frontier
              size, times the run and finally builds the SearchResult

Definitions used for the measurements (the same for all algorithms):

nodes generated   every successor state produced while expanding a node (also the ones that
                  are then discarded as duplicates), plus the root. For IDS the root of
                  every iteration is counted.
nodes expanded    nodes whose successors were generated (a node that is only goal-tested
                  is not counted as expanded)
max frontier      the largest number of nodes waiting in the frontier, observed at the
                  start of the search and after every expansion
max in memory     the largest value of  (frontier size + states remembered by the search);
                  "states remembered" is the explored / reached table of a graph search,
                  the memo table of IDS with use_memo=True, or just the current path for
                  the textbook IDS
running time      wall-clock seconds measured with time.perf_counter()
"""

import time
from dataclasses import dataclass, field


class Node:
    """A node of the search tree.

    state      the state this node represents
    parent     the node this one was generated from (None for the root)
    action     the action applied to the parent to get here
    path_cost  g(n): cost of the path from the root to this node
    depth      number of actions on that path
    """

    __slots__ = ("state", "parent", "action", "path_cost", "depth")

    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.depth = 0 if parent is None else parent.depth + 1

    def path(self):
        """Nodes from the root down to this node (follows the parent pointers back)."""
        nodes = []
        node = self
        while node is not None:
            nodes.append(node)
            node = node.parent
        nodes.reverse()
        return nodes

    def __repr__(self):
        return f"Node(state={self.state}, g={self.path_cost}, depth={self.depth})"


@dataclass
class SearchResult:
    """What a search algorithm returns."""

    algorithm: str
    found: bool                      # was a solution found?
    actions: list                    # the solution: list of action names (empty if not found)
    states: list                     # every state on the solution path, initial state first
    path_cost: float                 # sum of step costs (None if not found)
    depth: int                       # number of actions in the solution (None if not found)
    nodes_generated: int
    nodes_expanded: int
    max_frontier_size: int
    max_nodes_in_memory: int
    runtime_sec: float
    # --- optional trace, only filled when the algorithm was called with trace=True ---
    expanded_nodes: list = field(default_factory=list, repr=False)    # Nodes, in expansion order
    frontier_history: list = field(default_factory=list, repr=False)  # frontier size at every observation
    extra: dict = field(default_factory=dict, repr=False)             # algorithm-specific details

    def summary(self):
        """One-line human-readable summary."""
        if not self.found:
            return f"{self.algorithm}: no solution found ({self.nodes_expanded} nodes expanded)"
        return (
            f"{self.algorithm}: cost={self.path_cost} steps={self.depth} "
            f"generated={self.nodes_generated} expanded={self.nodes_expanded} "
            f"max_frontier={self.max_frontier_size} time={self.runtime_sec * 1000:.2f} ms"
        )


class SearchStats:
    """Collects the measurements of one search run.

    The algorithms call
        count_generated(n)           for the root (n = 1) and, at every expansion, with the
                                     number of successor states that were produced
        count_expanded(node)         when they expand a node
        observe(frontier, stored)    at the start and after each expansion, to track memory use
        finish(goal_node)            at the end, to build the SearchResult
    """

    def __init__(self, algorithm, trace=False):
        self.algorithm = algorithm
        self.trace = trace            # True -> also keep the data needed for the pictures
        self.generated = 0
        self.expanded = 0
        self.max_frontier = 0
        self.max_memory = 0
        self.expanded_nodes = []
        self.frontier_history = []
        self.extra = {}
        self._start_time = time.perf_counter()

    def count_generated(self, how_many=1):
        """Called once for the root and once per expansion with the number of successors."""
        self.generated += how_many

    def count_expanded(self, node):
        """Called when the successors of `node` are about to be generated."""
        self.expanded += 1
        if self.trace:
            self.expanded_nodes.append(node)

    def observe(self, frontier_size, stored_states):
        """Record the current memory use.

        frontier_size  number of nodes waiting in the frontier
        stored_states  number of states the algorithm remembers besides the frontier
                       (explored set / reached table)
        """
        if frontier_size > self.max_frontier:
            self.max_frontier = frontier_size
        if frontier_size + stored_states > self.max_memory:
            self.max_memory = frontier_size + stored_states
        if self.trace:
            self.frontier_history.append(frontier_size)

    def finish(self, goal_node):
        """Stop the clock and package the result. `goal_node` is None when the search failed."""
        runtime = time.perf_counter() - self._start_time
        if goal_node is None:
            actions, states, cost, depth = [], [], None, None
        else:
            path = goal_node.path()
            actions = [node.action for node in path[1:]]     # the root has no action
            states = [node.state for node in path]
            cost = goal_node.path_cost
            depth = goal_node.depth
        if self.trace:
            self.extra["goal_node"] = goal_node          # lets the tree drawing show the goal
        return SearchResult(
            algorithm=self.algorithm,
            found=goal_node is not None,
            actions=actions,
            states=states,
            path_cost=cost,
            depth=depth,
            nodes_generated=self.generated,
            nodes_expanded=self.expanded,
            max_frontier_size=self.max_frontier,
            max_nodes_in_memory=self.max_memory,
            runtime_sec=runtime,
            expanded_nodes=self.expanded_nodes,
            frontier_history=self.frontier_history,
            extra=self.extra,
        )
