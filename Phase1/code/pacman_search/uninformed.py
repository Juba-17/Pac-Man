"""
uninformed.py
=============
Phase I - the four uninformed (blind) search algorithms, written from scratch:

    breadth_first_search        BFS   FIFO queue,     shallowest node first
    depth_first_search          DFS   LIFO stack,     deepest node first
    uniform_cost_search         UCS   priority queue, cheapest node first
    iterative_deepening_search  IDS   depth-limited DFS repeated with limits 0, 1, 2, ...

All of them use only the problem interface (initial_state, successors, is_goal), so they
know nothing about mazes or pellets, and all return a SearchResult with the solution
path, its cost, the number of nodes generated and expanded, the maximum frontier size and
the running time.

Repeated states. In this problem many different paths lead to the same (position, food)
state, so every algorithm needs some protection against exploring it again and again:

    BFS, DFS, UCS   graph search - a table of visited states (memory grows with the
                    number of states visited)
    IDS             the textbook version: only loops along the CURRENT path are avoided,
                    so memory stays tiny, but the same state can be explored many times.
                    An optional memo table (use_memo=True) trades that memory advantage
                    for speed.

Pass trace=True to also record the order in which nodes were expanded (needed only for
the pictures; it does not change what the algorithm does).
"""

import heapq
from collections import deque

from .search_core import Node, SearchStats


# --------------------------------------------------------------------------------------
# Breadth-First Search
# --------------------------------------------------------------------------------------
def breadth_first_search(problem, trace=False):
    """BFS: always expand the SHALLOWEST node in the frontier.

    frontier   FIFO queue (collections.deque) - nodes leave in the order they arrived
    reached    set of every state that has ever been added to the frontier; a state is
               never queued twice
    goal test  when a node is GENERATED (early goal test). In BFS the first time a state
               is generated is already along a shortest path, so we can stop one level
               earlier than a test at expansion time would.

    Complete: yes (finite state space). Optimal: only in the NUMBER OF STEPS. With unequal
    step costs (danger cells cost 5) the shallowest solution may not be the cheapest, and
    among several shallowest solutions BFS simply returns the first one it meets.
    """
    stats = SearchStats("BFS", trace)
    root = Node(problem.initial_state)
    stats.count_generated()
    if problem.is_goal(root.state):
        return stats.finish(root)

    frontier = deque([root])
    reached = {root.state}
    stats.observe(len(frontier), 0)

    while frontier:
        node = frontier.popleft()                       # oldest node = shallowest node
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in children:
            if child_state in reached:
                continue                                # found earlier by a path at least as short
            child = Node(child_state, node, action, node.path_cost + cost)
            if problem.is_goal(child_state):
                stats.observe(len(frontier), len(reached) - len(frontier))
                return stats.finish(child)
            reached.add(child_state)
            frontier.append(child)
        # states remembered besides the frontier = the ones that were already expanded
        stats.observe(len(frontier), len(reached) - len(frontier))

    return stats.finish(None)                           # frontier empty: no solution


# --------------------------------------------------------------------------------------
# Depth-First Search
# --------------------------------------------------------------------------------------
def depth_first_search(problem, trace=False):
    """DFS: always expand the DEEPEST node in the frontier.

    frontier   LIFO stack (a Python list, push = append, pop = pop)
    explored   set of states that have already been expanded. Without it DFS would walk
               in circles forever in a maze; with it DFS is complete on our finite state
               space.
    goal test  when a node is removed from the stack.

    Complete: yes here (finite space + explored set). Optimal: no - it returns the first
    solution it stumbles on, which is usually far longer and costlier than necessary.
    """
    stats = SearchStats("DFS", trace)
    root = Node(problem.initial_state)
    stats.count_generated()

    frontier = [root]
    explored = set()
    stats.observe(len(frontier), 0)

    while frontier:
        node = frontier.pop()                           # newest node = deepest node
        if node.state in explored:
            continue                                    # already expanded through another branch
        if problem.is_goal(node.state):
            return stats.finish(node)
        explored.add(node.state)
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        # Push the successors in REVERSE order so that the first action (UP) ends up on
        # top of the stack and is the one DFS follows first.
        for action, child_state, cost in reversed(children):
            if child_state not in explored:
                frontier.append(Node(child_state, node, action, node.path_cost + cost))
        stats.observe(len(frontier), len(explored))

    return stats.finish(None)


# --------------------------------------------------------------------------------------
# Uniform-Cost Search
# --------------------------------------------------------------------------------------
def uniform_cost_search(problem, trace=False):
    """UCS: always expand the node with the LOWEST PATH COST g(n).

    frontier   priority queue (binary heap, heapq) ordered by g(n)
    best_cost  cheapest path cost found so far for every reached state. A state is put on
               the frontier again only if a strictly cheaper path to it is discovered.
    goal test  when a node is REMOVED from the frontier (late goal test). This is what
               makes UCS optimal: a goal node that is merely generated might still be
               reachable by a cheaper path that has not been expanded yet.

    Complete: yes (every step has a positive cost). Optimal: yes, in path cost.
    """
    stats = SearchStats("UCS", trace)
    root = Node(problem.initial_state)
    stats.count_generated()

    # Heap entries are (path cost, tie-breaker, node). The tie-breaker is a running
    # counter: equal-cost nodes come out in the order they were inserted, and Python never
    # has to compare two Node objects.
    frontier = [(0, 0, root)]
    best_cost = {root.state: 0}
    counter = 1
    stats.observe(len(frontier), 0)

    while frontier:
        cost_so_far, _, node = heapq.heappop(frontier)   # cheapest node
        if cost_so_far > best_cost[node.state]:
            continue                                    # outdated entry: a cheaper path was found later
        if problem.is_goal(node.state):
            return stats.finish(node)
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in children:
            new_cost = cost_so_far + cost
            if child_state not in best_cost or new_cost < best_cost[child_state]:
                best_cost[child_state] = new_cost
                child = Node(child_state, node, action, new_cost)
                heapq.heappush(frontier, (new_cost, counter, child))
                counter += 1
        # With positive step costs a state is never expanded twice, so the number of
        # expansions is also the number of states that have been expanded.
        stats.observe(len(frontier), stats.expanded)

    return stats.finish(None)


# --------------------------------------------------------------------------------------
# Iterative Deepening Search
# --------------------------------------------------------------------------------------
CUTOFF = "cutoff"      # the depth limit was hit: a larger limit might still find a solution
ABORTED = "aborted"    # the optional expansion budget ran out


def _is_cycle(node):
    """True if the node's state already appears among its ancestors (a loop on the path)."""
    ancestor = node.parent
    while ancestor is not None:
        if ancestor.state == node.state:
            return True
        ancestor = ancestor.parent
    return False


def depth_limited_search(problem, limit, stats, use_memo=False, expansion_limit=None):
    """Depth-first search that never expands a node at depth >= `limit`.

    Returns  a goal Node          a solution with at most `limit` actions was found
             CUTOFF               some node was cut off at the limit (try a bigger limit)
             None                 the whole space was searched without reaching the limit
             ABORTED              the expansion budget was used up

    use_memo=False (default, the textbook version)
        Only loops along the current path are avoided (_is_cycle). The memory needed is
        just the stack: O(branching factor x depth). The price is time: the same state is
        explored again through every different path that reaches it.

    use_memo=True (graph-search variant)
        best_depth remembers the shallowest depth at which each state was visited during
        THIS call. A node is skipped when its state was already visited at the same or a
        smaller depth, because everything reachable from it within the limit is explored
        from that earlier visit. Solutions are still found at their minimum depth and far
        fewer nodes are expanded, but the table needs memory proportional to the number
        of states visited - the memory advantage of IDS is gone.
    """
    root = Node(problem.initial_state)
    stats.count_generated()
    frontier = [root]                                   # LIFO stack, as in DFS
    best_depth = {}
    result = None
    stats.observe(len(frontier), 0)

    while frontier:
        node = frontier.pop()
        if problem.is_goal(node.state):
            return node
        if use_memo:
            if best_depth.get(node.state, limit + 1) <= node.depth:
                continue                                # visited before, at least as shallow
            best_depth[node.state] = node.depth
        elif _is_cycle(node):
            continue
        if node.depth >= limit:
            result = CUTOFF                             # not allowed to go deeper this time
            continue
        if expansion_limit is not None and stats.expanded >= expansion_limit:
            return ABORTED
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in reversed(children):
            frontier.append(Node(child_state, node, action, node.path_cost + cost))
        # memory besides the stack: the memo table, or just the current path of ancestors
        stats.observe(len(frontier), len(best_depth) if use_memo else node.depth + 1)

    return result


def iterative_deepening_search(problem, trace=False, use_memo=False, max_depth=None,
                               expansion_limit=None):
    """IDS: run depth-limited search with limit 0, 1, 2, ... until a solution appears.

    Like BFS it finds a solution with the fewest steps, because limit L is tried only
    after every limit below L has failed. The price is repeated work: the shallow levels
    are searched again in every iteration. All counters are summed over ALL iterations;
    the per-iteration numbers are stored in result.extra["iterations"].

    The loop ends by itself when no solution exists: once the limit is large enough that
    nothing is cut off, depth_limited_search returns None. `max_depth` and
    `expansion_limit` are optional safety limits.

    Complete: yes. Optimal: in the number of steps (like BFS), not in path cost.
    """
    stats = SearchStats("IDS (memo table)" if use_memo else "IDS", trace)
    stats.extra["iterations"] = []          # one record per depth limit
    stats.extra["iteration_starts"] = []    # index into expanded_nodes where each limit begins

    limit = 0
    while max_depth is None or limit <= max_depth:
        expanded_before, generated_before = stats.expanded, stats.generated
        stats.extra["iteration_starts"].append(stats.expanded)
        outcome = depth_limited_search(problem, limit, stats, use_memo, expansion_limit)
        stats.extra["iterations"].append({
            "limit": limit,
            "expanded": stats.expanded - expanded_before,
            "generated": stats.generated - generated_before,
        })
        if outcome is ABORTED:
            stats.extra["aborted"] = True
            return stats.finish(None)
        if outcome is None:
            return stats.finish(None)                   # space exhausted: no solution exists
        if outcome is not CUTOFF:
            return stats.finish(outcome)                # outcome is the goal node
        limit += 1

    stats.extra["depth_limit_reached"] = True           # gave up at max_depth
    return stats.finish(None)


# Name -> function table used by main.py and the experiment scripts.
UNINFORMED_ALGORITHMS = {
    "bfs": breadth_first_search,
    "dfs": depth_first_search,
    "ucs": uniform_cost_search,
    "ids": iterative_deepening_search,
}
