"""
local_search.py
===============
Phase II - local search: Hill Climbing, Simulated Annealing and a Genetic Algorithm.

COMPLETE-STATE FORMULATION
--------------------------
Local search does not build a path step by step. It starts from a complete candidate
solution and keeps changing it. For the Pac-Man problem a candidate solution is

    a PRIORITY ORDER of the k pellets  =  a permutation of the pellet numbers 0..k-1

It is turned into a plan like this: Pac-Man always walks, along the cheapest path, to the
first pellet of the order that has not been eaten yet. Pellets that happen to lie on the
way are eaten in passing and are simply skipped when their turn comes. The plan ends the
moment the last pellet is eaten. Its quality is measured by the objective function

    cost(order) = total cost of that walk                                (to be MINIMISED)

i.e. the sum of d(a, b) over the legs that are actually walked, where d(a, b) is the
cheapest cost of walking from cell a to cell b (ghost danger included). The table d is
computed once by our own uniform-cost search over the maze cells.

Neighbours of an order: every order obtained by swapping two of its pellets (k(k-1)/2 neighbours).

Why this representation: every order gives a valid solution of the original search
problem, cost(order) is exactly the path cost of that solution in the search model, and
the best order costs exactly the optimal path cost. So the local-search results can be
compared directly with UCS and A*.
(Why the best order is optimal: an optimal path reaches the pellets for the first time in
some order; between two consecutive first visits it cannot be cheaper than d, so that
order costs no more than the optimum - and no order can cost less, because every order is
a real plan.)

All three algorithms are randomised. Each takes a `seed` and uses its own
random.Random(seed) generator, so every run can be reproduced exactly.

random_sampling() at the end of the file is not a fourth algorithm but the baseline the
three are compared with: the best of n orders drawn completely at random.
"""

import heapq
import math
import random
import time
from dataclasses import dataclass, field


# --------------------------------------------------------------------------------------
# The optimisation problem: in which order should Pac-Man go for the pellets?
# --------------------------------------------------------------------------------------
def cheapest_paths_from(problem, source):
    """Uniform-cost search over the maze CELLS, starting from the cell `source`.

    Returns (cost, came_from):
        cost[cell]       cheapest cost of walking from `source` to `cell`
        came_from[cell]  (previous cell, action) on that cheapest path
    """
    cost = {source: 0}
    came_from = {source: None}
    frontier = [(0, source)]
    while frontier:
        cost_so_far, cell = heapq.heappop(frontier)
        if cost_so_far > cost[cell]:
            continue
        for action, nxt, step in problem.neighbors[cell]:
            new_cost = cost_so_far + step
            if nxt not in cost or new_cost < cost[nxt]:
                cost[nxt] = new_cost
                came_from[nxt] = (cell, action)
                heapq.heappush(frontier, (new_cost, nxt))
    return cost, came_from


class TourProblem:
    """The pellet-ordering problem derived from a PacmanProblem.

    points[0] is the start cell and points[i + 1] is pellet i. For every pair of points:
        distance[a][b]   cheapest walking cost from point a to point b
        leg[a][b]        the actions of that cheapest walk
        leg_food[a][b]   bitmask of the pellets that are eaten on that walk (b included)
    """

    def __init__(self, problem):
        started = time.perf_counter()
        self.problem = problem
        self.num_food = problem.num_food
        self.points = [problem.start] + list(problem.food_cells)
        size = len(self.points)
        self.distance = [[0] * size for _ in range(size)]
        self.leg = [[[] for _ in range(size)] for _ in range(size)]
        self.leg_food = [[0] * size for _ in range(size)]
        for a, source in enumerate(self.points):
            cost, came_from = cheapest_paths_from(problem, source)
            for b, target in enumerate(self.points):
                self.distance[a][b] = cost[target]
                actions, eaten = [], 0
                cell = target
                while came_from[cell] is not None:          # walk back to the source
                    eaten |= problem.food_bit.get(cell, 0)  # a pellet in a cell we enter is eaten
                    cell, action = came_from[cell]
                    actions.append(action)
                self.leg[a][b] = actions[::-1]
                self.leg_food[a][b] = eaten
        self.setup_seconds = time.perf_counter() - started

    def walked_legs(self, order):
        """The legs (from point, to point) Pac-Man really walks for this order: a pellet
        that was already eaten on an earlier leg is skipped."""
        legs = []
        here, eaten = 0, 0                                  # start cell, nothing eaten yet
        for pellet in order:
            if eaten >> pellet & 1:
                continue
            legs.append((here, pellet + 1))
            eaten |= self.leg_food[here][pellet + 1]
            here = pellet + 1
        return legs

    def cost(self, order):
        """Objective function: path cost of the plan that this order produces.

        Same loop as walked_legs(), written out because it is called millions of times.
        """
        total, here, eaten = 0, 0, 0
        for pellet in order:
            if eaten >> pellet & 1:
                continue
            target = pellet + 1
            total += self.distance[here][target]
            eaten |= self.leg_food[here][target]
            here = target
        return total

    def to_actions(self, order):
        """Turn an order into the actual list of moves in the maze."""
        actions = []
        for a, b in self.walked_legs(order):
            actions += self.leg[a][b]
        return actions

    def eating_order(self, order):
        """The order in which the pellets are really eaten when this order is followed."""
        state = self.problem.initial_state
        eaten = []
        for action in self.to_actions(order):
            nxt = self.problem.result(state, action)
            if nxt.food != state.food:
                eaten.append(self.problem.food_cells.index(nxt.pos))
            state = nxt
        return tuple(eaten)

    def random_order(self, rng):
        """A random permutation of the pellets (random candidate solution)."""
        order = list(range(self.num_food))
        rng.shuffle(order)
        return tuple(order)

    def neighbours(self, order):
        """All orders that differ from `order` by swapping two pellets."""
        result = []
        for i in range(len(order) - 1):
            for j in range(i + 1, len(order)):
                neighbour = list(order)
                neighbour[i], neighbour[j] = neighbour[j], neighbour[i]
                result.append(tuple(neighbour))
        return result


@dataclass
class LocalSearchResult:
    """What a local-search run returns."""

    algorithm: str
    seed: int
    order: tuple                 # best order found (priority order of the pellets)
    cost: float                  # its cost (value of the objective function)
    actions: list                # the same solution as a list of moves in the maze
    evaluations: int             # how many times the objective function was computed
    iterations: int              # moves made (HC), iterations (SA) or generations (GA)
    history: list                # best cost found so far, after every iteration / generation
    runtime_sec: float
    extra: dict = field(default_factory=dict, repr=False)


def _swap(order, i, j):
    """The order with the pellets at positions i and j exchanged."""
    changed = list(order)
    changed[i], changed[j] = changed[j], changed[i]
    return tuple(changed)


def _finish(name, tour, seed, order, cost, evaluations, iterations, history, started, extra=None):
    """Stop the clock, then turn the best order into a plan and package the result."""
    runtime = time.perf_counter() - started
    return LocalSearchResult(name, seed, order, cost, tour.to_actions(order), evaluations,
                             iterations, history, runtime, extra or {})


# --------------------------------------------------------------------------------------
# Hill Climbing
# --------------------------------------------------------------------------------------
def hill_climbing(tour, seed=0, restarts=0, max_sideways=0, record_history=True):
    """Steepest-ascent hill climbing (here: steepest DESCENT of the cost).

    Start from a random order. In every iteration look at ALL neighbours and move to the
    best one if it is strictly better than the current order. With the default settings
    the climb stops as soon as no neighbour is strictly better: the search is then in a
    local optimum or on a plateau (a flat area where the best neighbours cost the same).
    The order reached may or may not be the global optimum.

    Two standard remedies are available as options:
      restarts > 0      random-restart hill climbing: the climb is repeated from that many
                        additional random orders and the best result is kept
      max_sideways > 0  on a plateau, move to a randomly chosen neighbour of EQUAL cost,
                        at most `max_sideways` times in a row (the allowance is refilled
                        whenever a strictly better order is found)

    The climb always ends: the cost never goes up, strict improvements are finite in
    number, and the sideways moves between two improvements are limited.
    `iterations` in the result counts the moves that were made. record_history=False
    skips the bookkeeping that is only needed for the convergence plots.
    """
    if tour.num_food < 2:                               # only one possible order: nothing to do
        return _single_order_result("Hill Climbing", tour, seed)
    rng = random.Random(seed)
    started = time.perf_counter()
    best_order, best_cost = None, math.inf
    evaluations = moves = 0
    history = []

    for _ in range(restarts + 1):
        current = tour.random_order(rng)
        current_cost = tour.cost(current)
        evaluations += 1
        if current_cost < best_cost:
            best_order, best_cost = current, current_cost
        if record_history:
            history.append(best_cost)

        sideways_left = max_sideways
        while True:
            neighbours = tour.neighbours(current)
            costs = [tour.cost(neighbour) for neighbour in neighbours]
            evaluations += len(neighbours)
            lowest = min(costs)
            if lowest < current_cost:                   # a strictly better neighbour: take the best one
                chosen = neighbours[costs.index(lowest)]
                sideways_left = max_sideways
            elif lowest == current_cost and sideways_left > 0:      # plateau: step sideways
                chosen = rng.choice([n for n, c in zip(neighbours, costs) if c == lowest])
                sideways_left -= 1
            else:
                break                                   # nothing better (and no sideways move left)
            current, current_cost = chosen, lowest
            moves += 1
            if current_cost < best_cost:
                best_order, best_cost = current, current_cost
            if record_history:
                history.append(best_cost)

    name = "Hill Climbing"
    if restarts or max_sideways:
        options = [f"{restarts} restarts"] * bool(restarts) + [f"{max_sideways} sideways"] * bool(max_sideways)
        name += f" ({', '.join(options)})"
    return _finish(name, tour, seed, best_order, best_cost, evaluations, moves, history, started)


# --------------------------------------------------------------------------------------
# Simulated Annealing
# --------------------------------------------------------------------------------------
def simulated_annealing(tour, seed=0, start_temperature=10.0, cooling_rate=0.995,
                        end_temperature=0.1, record_history=True):
    """Simulated annealing with a geometric cooling schedule.

    In every iteration one random neighbour (a random swap) is tried:
      * if it is better or equal, move to it;
      * if it is worse by delta, move to it anyway with probability exp(-delta / T).
    The temperature T starts at `start_temperature` and is multiplied by `cooling_rate`
    after every iteration:  T(n) = start_temperature * cooling_rate^n.
    While T is high, bad moves are often accepted (exploration, escapes local optima and
    plateaus); as T falls the search turns into plain hill climbing (exploitation).
    The run ends when T drops below `end_temperature`; the best order seen is returned.

    The default values are the ones used in the experiments; run_phase2.py contains the
    sensitivity study that motivates them (see the report).
    """
    if not 0 < cooling_rate < 1 or end_temperature <= 0 or start_temperature <= end_temperature:
        raise ValueError("Need 0 < cooling_rate < 1 and start_temperature > end_temperature > 0.")
    if tour.num_food < 2:                               # only one possible order: nothing to do
        return _single_order_result("Simulated Annealing", tour, seed)
    rng = random.Random(seed)
    started = time.perf_counter()
    current = tour.random_order(rng)
    current_cost = tour.cost(current)
    best_order, best_cost = current, current_cost
    evaluations, iterations = 1, 0
    history = [best_cost] if record_history else []
    current_history = [current_cost] if record_history else []   # shows the uphill moves
    temperature = start_temperature

    while temperature > end_temperature:
        i, j = rng.sample(range(tour.num_food), 2)
        neighbour = _swap(current, i, j)
        neighbour_cost = tour.cost(neighbour)
        evaluations += 1
        delta = neighbour_cost - current_cost
        if delta <= 0 or rng.random() < math.exp(-delta / temperature):
            current, current_cost = neighbour, neighbour_cost
            if current_cost < best_cost:
                best_order, best_cost = current, current_cost
        temperature *= cooling_rate                     # geometric cooling
        iterations += 1
        if record_history:
            history.append(best_cost)
            current_history.append(current_cost)

    return _finish("Simulated Annealing", tour, seed, best_order, best_cost, evaluations, iterations,
                   history, started, {"current_history": current_history,
                                      "start_temperature": start_temperature,
                                      "cooling_rate": cooling_rate})


# --------------------------------------------------------------------------------------
# Genetic Algorithm
# --------------------------------------------------------------------------------------
def tournament_selection(population, costs, rng, size):
    """Pick `size` random individuals and return the best (cheapest) of them."""
    contestants = rng.sample(range(len(population)), size)
    winner = min(contestants, key=lambda index: costs[index])
    return population[winner]


def order_crossover(parent_a, parent_b, rng):
    """Order crossover for permutations (a simple variant of Davis's OX).

    A random slice of parent A is copied to the child at the same positions; the remaining
    positions are filled, from left to right, with the missing pellets in the order in
    which they appear in parent B. The child is therefore always a valid permutation.
    (The classic OX fills the positions after the slice first and wraps around, because it
    was designed for round trips. Our routes have a fixed start, so we fill left to right.)
    """
    size = len(parent_a)
    i, j = sorted(rng.sample(range(size), 2))
    child = [None] * size
    child[i:j + 1] = parent_a[i:j + 1]
    kept = set(parent_a[i:j + 1])
    fill = [gene for gene in parent_b if gene not in kept]
    for position in range(size):
        if child[position] is None:
            child[position] = fill.pop(0)
    return tuple(child)


def swap_mutation(order, rng):
    """Mutation: swap two randomly chosen pellets."""
    i, j = rng.sample(range(len(order)), 2)
    return _swap(order, i, j)


def genetic_algorithm(tour, seed=0, population_size=30, generations=30, crossover_rate=0.9,
                      mutation_rate=0.8, tournament_size=2, elite_count=0, record_history=True):
    """Genetic algorithm on pellet orders.

    Representation  a chromosome is an order of the pellets (one gene per pellet)
    Fitness         -cost(order): the cheaper the route, the fitter the individual
    Selection       tournament selection (the best of `tournament_size` random individuals)
    Crossover       order crossover, applied with probability `crossover_rate`
    Mutation        swap of two genes, applied with probability `mutation_rate`
    Elitism         optional: the best `elite_count` individuals are copied unchanged into
                    the next generation. In our sensitivity study elitism did not help
                    and several elites lowered the success rate
                    (tuning_one_at_a_time.csv), so the default is 0.
    The best order ever seen is remembered separately and returned at the end, so nothing
    is lost without elitism.

    The default values are the ones used in the experiments; run_phase2.py contains the
    sensitivity study that motivates them (see the report).
    """
    if tour.num_food < 2:
        return _single_order_result("Genetic Algorithm", tour, seed)
    rng = random.Random(seed)
    started = time.perf_counter()
    population = [tour.random_order(rng) for _ in range(population_size)]
    costs = [tour.cost(individual) for individual in population]
    evaluations = population_size
    best_index = min(range(population_size), key=lambda index: costs[index])
    best_order, best_cost = population[best_index], costs[best_index]
    history = [best_cost] if record_history else []
    mean_history = [sum(costs) / population_size] if record_history else []

    for _ in range(generations):
        ranking = sorted(range(population_size), key=lambda index: costs[index])
        next_population = [population[index] for index in ranking[:elite_count]]
        while len(next_population) < population_size:
            mother = tournament_selection(population, costs, rng, tournament_size)
            father = tournament_selection(population, costs, rng, tournament_size)
            child = order_crossover(mother, father, rng) if rng.random() < crossover_rate else mother
            if rng.random() < mutation_rate:
                child = swap_mutation(child, rng)
            next_population.append(child)
        population = next_population
        costs = [tour.cost(individual) for individual in population]
        evaluations += population_size
        best_index = min(range(population_size), key=lambda index: costs[index])
        if costs[best_index] < best_cost:
            best_order, best_cost = population[best_index], costs[best_index]
        if record_history:
            history.append(best_cost)
            mean_history.append(sum(costs) / population_size)

    return _finish("Genetic Algorithm", tour, seed, best_order, best_cost, evaluations, generations,
                   history, started, {"mean_history": mean_history, "population_size": population_size})


def _single_order_result(name, tour, seed):
    """With fewer than two pellets there is only one possible order - nothing to optimise."""
    order = tuple(range(tour.num_food))
    return _finish(name, tour, seed, order, tour.cost(order), 1, 0, [tour.cost(order)], time.perf_counter())


# --------------------------------------------------------------------------------------
# Baseline: blind random sampling (NOT one of the nine algorithms)
# --------------------------------------------------------------------------------------
def random_sampling(tour, seed=0, evaluations=1000, record_history=True):
    """The best of `evaluations` random orders - a baseline, not a search method.

    Every order is drawn afresh; nothing is learnt from the orders seen before. A
    local-search method is only worth its extra machinery where it does better than this
    with the same number of evaluations, so the experiments report it next to the three
    algorithms.
    """
    rng = random.Random(seed)
    started = time.perf_counter()
    best_order, best_cost = None, math.inf
    history = []
    for _ in range(evaluations):
        order = tour.random_order(rng)
        cost = tour.cost(order)
        if cost < best_cost:
            best_order, best_cost = order, cost
        if record_history:
            history.append(best_cost)
    return _finish("Random Sampling", tour, seed, best_order, best_cost, evaluations, evaluations,
                   history, started)


LOCAL_SEARCH_ALGORITHMS = {
    "hc": hill_climbing,
    "sa": simulated_annealing,
    "ga": genetic_algorithm,
}
