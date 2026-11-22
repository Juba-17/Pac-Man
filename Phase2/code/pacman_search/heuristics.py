"""
heuristics.py
=============
Phase II - heuristic functions for the Pac-Man food-collection problem.

A heuristic h(state) estimates the cheapest cost of eating all the remaining pellets
starting from `state`. Three are defined here:

    h1  FarthestFoodHeuristic   Manhattan distance to the FARTHEST remaining pellet
    h2  MazeMSTHeuristic        true maze distance to the NEAREST remaining pellet
                                + weight of the minimum spanning tree (MST) that connects
                                  all remaining pellets, measured in true maze distances
    h0  ZeroHeuristic           always 0 - A* with h0 is exactly UCS (baseline only)

Both h1 and h2 count STEPS and multiply the count by the cheapest possible step cost
(1 with the default costs), so they never overestimate whatever the cost settings are.
Both are exact solution costs of a RELAXED (easier) version of the problem:

    h1 relaxation  no walls, no ghost danger, and only the farthest pellet has to be reached
    h2 relaxation  walls are kept, ghost danger is ignored (every step costs the minimum),
                   and after the first pellet the remaining ones only have to be CONNECTED
                   (a tree) instead of being visited one after the other (a path)

Both heuristics are admissible and consistent, and h2 >= h1 in every state (h2 dominates
h1); the arguments are given in the class docstrings. analyse_heuristic() checks
admissibility and consistency on every reachable state; dominance is checked by
run_phase2.py (study_heuristics) and by the unit tests. descent_region() measures how far
Greedy best-first search can get before the heuristic has to rise again.
"""

import heapq
from collections import deque


def manhattan(a, b):
    """Grid distance between two cells when walls are ignored."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def maze_distances_from(problem, source):
    """Number of steps from `source` to every cell, walking around walls and ghosts.

    Plain breadth-first search over the maze cells (every step counts 1). Because moves
    can be reversed, the distance from A to B equals the distance from B to A.
    """
    distance = {source: 0}
    queue = deque([source])
    while queue:
        cell = queue.popleft()
        for _, nxt, _ in problem.neighbors[cell]:
            if nxt not in distance:
                distance[nxt] = distance[cell] + 1
                queue.append(nxt)
    return distance


def cheapest_step(problem):
    """The smallest cost any single move can have (1 with the default costs)."""
    return min(problem.normal_cost, problem.danger_cost)


class ZeroHeuristic:
    """h0(s) = 0. Carries no information; turns A* into uniform-cost search."""

    label = "h0"
    description = "zero heuristic"

    def __init__(self, problem=None):
        pass

    def __call__(self, state):
        return 0


class FarthestFoodHeuristic:
    """h1(s) = (largest Manhattan distance from Pac-Man to a remaining pellet) x cheapest step.

    Why it is reasonable: Pac-Man must at least travel to the pellet that is farthest
    away, and no route can be shorter than the straight grid distance.
    Admissible: one move changes the Manhattan distance to any cell by exactly 1, so
    reaching the farthest pellet needs at least that many moves, each costing at least
    the cheapest step.
    Consistent: one move changes the distance to every pellet by exactly 1, so the
    maximum drops by at most 1 (also when the move eats a pellet, which was at distance
    1); h1 therefore drops by at most one cheapest step, never more than the step cost.
    """

    label = "h1"
    description = "farthest-food Manhattan distance"

    def __init__(self, problem):
        self.food_cells = problem.food_cells
        self.unit = cheapest_step(problem)

    def __call__(self, state):
        farthest = 0
        for index, cell in enumerate(self.food_cells):
            if state.food >> index & 1:                     # pellet `index` is still there
                distance = manhattan(state.pos, cell)
                if distance > farthest:
                    farthest = distance
        return self.unit * farthest


class MazeMSTHeuristic:
    """h2(s) = (maze distance to the nearest remaining pellet + MST over remaining pellets) x cheapest step.

    Distances are true maze distances in steps (walls and ghosts respected); MST(F) is the
    weight of the minimum spanning tree over the set F of remaining pellets.

    Why it is reasonable: any solution first has to reach SOME pellet (at least the
    nearest one) and afterwards has to link all remaining pellets together. The cheapest
    way of linking a set of points is their minimum spanning tree.

    Admissible: a solution reaches the remaining pellets for the first time in some order
    q1, q2, ..., qm. It needs at least d(pos, q1) + d(q1, q2) + ... + d(q(m-1), qm) moves.
    The first term is at least the distance to the nearest pellet; the other terms form a
    path through all pellets, which is one particular spanning tree, so their sum is at
    least MST(F). Every move costs at least the cheapest step.

    Consistent: (a) a move that eats nothing leaves the MST unchanged and changes the
    distance to the nearest pellet by at most 1. (b) a move that eats pellet q: before the
    move h2 <= 1 + MST(F) because q is one step away; and MST(F) <= MST(F without q) +
    (distance from q to its nearest remaining pellet), because hanging q onto the smaller
    tree gives a spanning tree of F. The right-hand side is exactly h2 after the move, so
    h2 drops by at most 1 step.

    Dominates h1: walking to the nearest pellet and then along tree edges to the pellet
    that is farthest in Manhattan distance is a real walk of at most h2 steps, and no walk
    to that pellet can be shorter than its Manhattan distance. Hence h2 >= h1.

    Pre-computation: one breadth-first search from every pellet. The MST weight depends
    only on WHICH pellets are left, so it is cached per food mask (at most 2^k entries).
    """

    label = "h2"
    description = "nearest food + MST (true maze distances)"

    def __init__(self, problem):
        self.num_food = problem.num_food
        self.unit = cheapest_step(problem)
        # steps[i][cell] = maze distance between pellet i and `cell`
        self.steps = [maze_distances_from(problem, cell) for cell in problem.food_cells]
        # between[i][j] = maze distance between pellet i and pellet j
        self.between = [[self.steps[i][cell] for cell in problem.food_cells]
                        for i in range(self.num_food)]
        self._mst_cache = {0: 0}

    def __call__(self, state):
        if state.food == 0:
            return 0
        nearest = min(self.steps[index][state.pos]
                      for index in range(self.num_food) if state.food >> index & 1)
        return self.unit * (nearest + self.mst_weight(state.food))

    def mst_weight(self, food):
        """Weight (in steps) of the minimum spanning tree over the pellets in the mask `food`
        (Prim's algorithm)."""
        if food in self._mst_cache:
            return self._mst_cache[food]
        pellets = [index for index in range(self.num_food) if food >> index & 1]
        first = pellets[0]
        # cheapest[j] = cheapest edge that connects pellet j to the tree built so far
        cheapest = {j: self.between[first][j] for j in pellets[1:]}
        total = 0
        while cheapest:
            nearest = min(cheapest, key=cheapest.get)       # closest pellet outside the tree
            total += cheapest.pop(nearest)
            for j in cheapest:                              # can the new tree node reach j more cheaply?
                if self.between[nearest][j] < cheapest[j]:
                    cheapest[j] = self.between[nearest][j]
        self._mst_cache[food] = total
        return total


HEURISTICS = {
    "h1": FarthestFoodHeuristic,
    "h2": MazeMSTHeuristic,
}


# --------------------------------------------------------------------------------------
# Exhaustive verification of a heuristic
# --------------------------------------------------------------------------------------
def optimal_costs_to_goal(problem):
    """h*(s) for EVERY reachable state s: the true cheapest cost of finishing from s.

    Computed with one backward uniform-cost search (Dijkstra) that starts from all goal
    states at once and follows the transitions in reverse. Only feasible because the state
    space is small (a few thousand states).
    """
    states = problem.reachable_states()
    predecessors = {state: [] for state in states}
    for state in states:
        for _, child, cost in problem.successors(state):
            predecessors[child].append((state, cost))

    best = {state: 0 for state in states if problem.is_goal(state)}
    frontier = [(0, state) for state in best]
    heapq.heapify(frontier)
    while frontier:
        cost, state = heapq.heappop(frontier)
        if cost > best[state]:
            continue
        for previous, step in predecessors[state]:
            new_cost = cost + step
            if previous not in best or new_cost < best[previous]:
                best[previous] = new_cost
                heapq.heappush(frontier, (new_cost, previous))
    return best


def descent_region(problem, heuristic):
    """How far does a search get from the start while the heuristic stays BELOW its start value?

    Returns (states, goal_inside): the number of states - the start included - that can be
    reached through states whose h is smaller than h(start), and whether a goal state is
    among them.

    This explains the behaviour of Greedy best-first search. Greedy always takes the
    frontier node with the smallest h, so it expands a state with h >= h(start) only after
    every state of this region has been expanded. If a goal lies inside the region, Greedy
    can run "downhill" to it. If not, the region is a basin (a local minimum of the
    heuristic): Greedy searches all of it before it climbs out.
    """
    start = problem.initial_state
    limit = heuristic(start)
    seen = {start}
    queue = deque([start])
    goal_inside = problem.is_goal(start)
    while queue:
        state = queue.popleft()
        for _, child, _ in problem.successors(state):
            if child not in seen and heuristic(child) < limit:
                seen.add(child)
                queue.append(child)
                goal_inside = goal_inside or problem.is_goal(child)
    return len(seen), goal_inside


def analyse_heuristic(problem, heuristic, true_costs=None):
    """Check a heuristic on every reachable state and transition of `problem`.

    admissible   h(s) <= h*(s) for every state s
    consistent   h(s) <= c(s, a, s') + h(s') for every transition (and h(goal) = 0)
    mean_ratio   average of h(s) / h*(s) over the non-goal states; 1.0 would be a perfect
                 heuristic, 0.0 an uninformative one
    """
    if true_costs is None:
        true_costs = optimal_costs_to_goal(problem)
    admissible, consistent = True, True
    worst_overestimate = 0
    ratios = []
    transitions = 0
    for state, true_cost in true_costs.items():
        estimate = heuristic(state)
        if estimate > true_cost:
            admissible = False
            worst_overestimate = max(worst_overestimate, estimate - true_cost)
        if problem.is_goal(state):
            if estimate != 0:
                consistent = False
        else:
            ratios.append(estimate / true_cost)
        for _, child, cost in problem.successors(state):
            transitions += 1
            if estimate > cost + heuristic(child):
                consistent = False
    start = problem.initial_state
    return {
        "layout": problem.name,
        "heuristic": heuristic.label,
        "states_checked": len(true_costs),
        "transitions_checked": transitions,
        "admissible": admissible,
        "consistent": consistent,
        "worst_overestimate": worst_overestimate,
        "mean_ratio": round(sum(ratios) / len(ratios), 3),
        "h_start": heuristic(start),
        "true_cost_start": true_costs[start],
    }
