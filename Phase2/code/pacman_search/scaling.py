"""
scaling.py
==========
Phase II - extra experiment: what changes when the maze has more pellets?

The three official layouts are small on purpose (1,000 to 10,000 states), so that all nine
algorithms can be run and compared on them. This module builds LARGER instances of the
same problem - one bigger maze with 8, 12, 16, 20 and 24 pellets - and measures on them

    * A* with heuristic h2, which also tells us the optimal cost of every instance;
    * Hill Climbing (with restarts), Simulated Annealing and the Genetic Algorithm, and
      next to them blind random sampling, all with the SAME budget of objective
      evaluations.

The uninformed algorithms are not run here: with 24 pellets the state space has about two
billion states, far too many for a search that has to remember or revisit them.

The pellets are scattered with a fixed seed, and the instances are nested: the maze with
12 pellets contains the 8 pellets of the smaller one, and so on.
"""

import math
import random
import statistics
import time

from .heuristics import MazeMSTHeuristic
from .informed import a_star_search
from .local_search import (
    TourProblem, genetic_algorithm, hill_climbing, random_sampling, simulated_annealing)
from .problem import PacmanProblem

# The bigger maze: 13 x 19 cells, two ghosts, no pellets yet (they are scattered below).
SCALING_MAZE = """
###################
#P                #
# ## ### # ### ## #
#     G           #
# ## # ##### # ## #
#    #       #    #
## # # ## ## # # ##
#                 #
# ## ### # ### ## #
#           G     #
# ## # ##### # ## #
#                 #
###################
"""
PELLET_COUNTS = (8, 12, 16, 20, 24)
SCATTER_SEED = 0


def scatter_pellets(maze_text, pellets, seed=SCATTER_SEED):
    """Return the maze with `pellets` pellets placed on randomly chosen corridor cells.

    The corridor cells are shuffled once with `seed` and the first `pellets` of them are
    used, so a larger number of pellets only ADDS pellets to the smaller instance.
    """
    rows = [list(row) for row in maze_text.strip("\n").split("\n")]
    corridor = [(r, c) for r, row in enumerate(rows) for c, symbol in enumerate(row) if symbol == " "]
    if pellets > len(corridor):
        raise ValueError(f"The maze has only {len(corridor)} corridor cells.")
    random.Random(seed).shuffle(corridor)
    for r, c in corridor[:pellets]:
        rows[r][c] = "."
    return "\n".join("".join(row) for row in rows)


def scaling_problem(pellets):
    """The instance of the scaling experiment with the given number of pellets."""
    return PacmanProblem(scatter_pellets(SCALING_MAZE, pellets), name=f"{pellets} pellets")


def cooling_rate_for(iterations, start_temperature, end_temperature):
    """Cooling rate that makes simulated annealing run for (almost exactly) `iterations`
    iterations: start * rate^iterations = end."""
    return (end_temperature / start_temperature) ** (1.0 / iterations)


def hill_climbing_with_budget(tour, seed, budget):
    """Random-restart hill climbing that keeps restarting until `budget` evaluations are used.

    The number of evaluations of one climb depends on the instance (a maze with k pellets
    has k(k-1)/2 neighbours per step), so a fixed number of restarts would not give the
    same budget on every instance. The last climb is allowed to finish, so the total can
    exceed the budget by less than one climb; the evaluations really used are reported.
    """
    best, used, climbs = None, 0, 0
    while used < budget:
        result = hill_climbing(tour, seed=1000 * seed + climbs, record_history=False)
        used += result.evaluations
        climbs += 1
        if best is None or result.cost < best.cost:
            best = result
    best.algorithm = "Hill Climbing (restarts)"
    best.seed, best.evaluations, best.iterations = seed, used, climbs
    return best


def budget_methods(budget, sa_params, ga_params):
    """{name: function(tour, seed)} - the baseline and the three methods, each set up to use
    about `budget` objective evaluations. All other parameters are the tuned ones."""
    sa = dict(sa_params, cooling_rate=cooling_rate_for(budget, sa_params["start_temperature"],
                                                       sa_params["end_temperature"]))
    population = 100 if budget >= 5000 else ga_params["population_size"]
    ga = dict(ga_params, population_size=population, generations=budget // population - 1)
    return {
        "Random sampling": lambda tour, seed: random_sampling(tour, seed, budget, record_history=False),
        "Hill Climbing (restarts)": lambda tour, seed: hill_climbing_with_budget(tour, seed, budget),
        "Simulated Annealing": lambda tour, seed: simulated_annealing(tour, seed, record_history=False, **sa),
        "Genetic Algorithm": lambda tour, seed: genetic_algorithm(tour, seed, record_history=False, **ga),
    }


def scaling_study(seeds, budget, sa_params, ga_params, pellet_counts=PELLET_COUNTS):
    """Run the experiment. Returns (instance_rows, method_rows).

    instance_rows  one row per maze: its size, the optimal cost and what A* with h2 needed
    method_rows    one row per maze and method: best / mean / worst cost over the seeds,
                   runs that reach the optimum, mean cost above the optimum in percent
    """
    instance_rows, method_rows = [], []
    for pellets in pellet_counts:
        problem = scaling_problem(pellets)
        started = time.perf_counter()
        optimal = a_star_search(problem, MazeMSTHeuristic(problem))
        astar_ms = (time.perf_counter() - started) * 1000.0      # heuristic tables included
        instance_rows.append({
            "pellets": pellets,
            "free_cells": len(problem.free_cells),
            "state_space_upper_bound": len(problem.free_cells) * 2 ** pellets,
            "pellet_orders": math.factorial(pellets),
            "optimal_cost": optimal.path_cost,
            "optimal_steps": optimal.depth,
            "astar_h2_nodes_expanded": optimal.nodes_expanded,
            "astar_h2_max_nodes_in_memory": optimal.max_nodes_in_memory,
            "astar_h2_time_ms": round(astar_ms, 3),
            "layout": problem.render(),
        })
        tour = TourProblem(problem)
        for name, run in budget_methods(budget, sa_params, ga_params).items():
            results = [run(tour, seed) for seed in seeds]
            for result in results:                               # every plan must really work
                states, cost = problem.execute(result.actions)
                assert problem.is_goal(states[-1]) and cost == result.cost >= optimal.path_cost, name
            costs = [result.cost for result in results]
            method_rows.append({
                "pellets": pellets,
                "method": name,
                "runs": len(costs),
                "optimal_cost": optimal.path_cost,
                "best": min(costs),
                "mean": round(statistics.mean(costs), 2),
                "worst": max(costs),
                "optimal_runs": sum(cost == optimal.path_cost for cost in costs),
                "mean_evaluations": round(statistics.mean(result.evaluations for result in results)),
                "mean_percent_above_optimum": round(100.0 * (statistics.mean(costs) / optimal.path_cost - 1), 1),
            })
    return instance_rows, method_rows
