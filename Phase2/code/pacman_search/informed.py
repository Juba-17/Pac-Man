"""
informed.py
===========
Phase II - informed (heuristic) search: Greedy Best-First Search and A*.

Both are best-first graph searches and differ in the evaluation function f(n) that orders
the frontier:

    Greedy Best-First   f(n) = h(n)            "expand the node that LOOKS closest to the goal"
    A*                  f(n) = g(n) + h(n)     "expand the node on the cheapest ESTIMATED
                                                complete solution through n"
    (UCS, from Phase I, is the special case f(n) = g(n).)

g(n) is the path cost from the start to n; h(n) is a heuristic from heuristics.py.

They also differ in how a state that was reached before is treated:

    A*      re-opens it: if a strictly cheaper path to the state is found, the state goes
            back on the frontier (needed for optimality).
    Greedy  never re-opens: a state enters the frontier only the first time it is
            reached. Greedy does not care about path cost at all, so it expands every
            state at most once.

The measurements are the same as in Phase I (see search_core.py).
"""

import heapq

from .search_core import Node, SearchStats


def best_first_search(problem, evaluate, name, trace=False, reopen=True):
    """Best-first graph search: always expand the frontier node with the smallest evaluate(node).

    frontier   priority queue (binary heap) of (f value, tie-breaker, node)
    best_cost  path cost with which each reached state was last put on the frontier
    explored   states that have been expanded (used for the memory statistic)
    reopen     True  - a state is queued again whenever a strictly cheaper path to it is
                       found (A*, UCS)
               False - a state is queued only the first time it is reached (Greedy)
    goal test  when a node is removed from the frontier (late goal test), as in UCS
    """
    stats = SearchStats(name, trace)
    root = Node(problem.initial_state)
    stats.count_generated()

    frontier = [(evaluate(root), 0, root)]
    best_cost = {root.state: 0}
    explored = set()
    counter = 1                     # tie-breaker: among equal f, the older node comes out first
    stats.observe(len(frontier), 0)

    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node.path_cost > best_cost[node.state]:
            continue                                    # outdated entry: a cheaper path was found later
        if problem.is_goal(node.state):
            return stats.finish(node)
        stats.count_expanded(node)
        explored.add(node.state)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in children:
            new_cost = node.path_cost + cost
            known_cost = best_cost.get(child_state)
            if known_cost is None or (reopen and new_cost < known_cost):
                best_cost[child_state] = new_cost
                child = Node(child_state, node, action, new_cost)
                heapq.heappush(frontier, (evaluate(child), counter, child))
                counter += 1
        stats.observe(len(frontier), len(explored))

    return stats.finish(None)


def greedy_best_first_search(problem, heuristic, trace=False):
    """Greedy Best-First Search: f(n) = h(n), no re-opening.

    It ignores the cost already paid completely: the frontier is ordered by h alone and a
    state is never reconsidered when a cheaper path to it turns up. So it rushes towards
    whatever looks closest.
    Complete: yes in this finite state space (every state is expanded at most once).
    Optimal: no.
    """
    return best_first_search(problem, lambda node: heuristic(node.state),
                             f"Greedy ({heuristic.label})", trace, reopen=False)


def a_star_search(problem, heuristic, trace=False):
    """A* search: f(n) = g(n) + h(n), with re-opening.

    Complete: yes. Optimal: yes when h is admissible (it never overestimates) - true for
    h1 and h2. Both are also consistent, which guarantees that the first time a state is
    expanded its cheapest path has already been found, so no state is expanded twice.
    """
    return best_first_search(problem, lambda node: node.path_cost + heuristic(node.state),
                             f"A* ({heuristic.label})", trace, reopen=True)
