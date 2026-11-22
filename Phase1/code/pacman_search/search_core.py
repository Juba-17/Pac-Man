
import time
from dataclasses import dataclass, field


class Node:

    __slots__ = ("state", "parent", "action", "path_cost", "depth")

    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.depth = 0 if parent is None else parent.depth + 1

    def path(self):
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

    algorithm: str
    found: bool                      
    actions: list                  
    states: list                   
    path_cost: float                
    depth: int                      
    nodes_generated: int
    nodes_expanded: int
    max_frontier_size: int
    max_nodes_in_memory: int
    runtime_sec: float
    expanded_nodes: list = field(default_factory=list, repr=False)   
    frontier_history: list = field(default_factory=list, repr=False) 
    extra: dict = field(default_factory=dict, repr=False)

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


    def __init__(self, algorithm, trace=False):
        self.algorithm = algorithm
        self.trace = trace            
        self.generated = 0
        self.expanded = 0
        self.max_frontier = 0
        self.max_memory = 0
        self.expanded_nodes = []
        self.frontier_history = []
        self.extra = {}
        self._start_time = time.perf_counter()

    def count_generated(self, how_many=1):
        self.generated += how_many

    def count_expanded(self, node):
        self.expanded += 1
        if self.trace:
            self.expanded_nodes.append(node)

    def observe(self, frontier_size, stored_states):

        if frontier_size > self.max_frontier:
            self.max_frontier = frontier_size
        if frontier_size + stored_states > self.max_memory:
            self.max_memory = frontier_size + stored_states
        if self.trace:
            self.frontier_history.append(frontier_size)

    def finish(self, goal_node):
        runtime = time.perf_counter() - self._start_time
        if goal_node is None:
            actions, states, cost, depth = [], [], None, None
        else:
            path = goal_node.path()
            actions = [node.action for node in path[1:]]     
            states = [node.state for node in path]
            cost = goal_node.path_cost
            depth = goal_node.depth
        if self.trace:
            self.extra["goal_node"] = goal_node          
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
