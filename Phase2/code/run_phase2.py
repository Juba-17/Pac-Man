"""
run_phase2.py - reproduces every Phase II result: tables, figures and animations.

    python run_phase2.py              full run (about two minutes)
    python run_phase2.py --quick      10 seeds, 3 timing repeats, no landscape analysis, no
                                      tuning study, no scaling experiment, no animations;
                                      results go to results/phase2_quick so a full run is
                                      never overwritten
    python run_phase2.py --out DIR    write the results somewhere else

What it does, for each official layout (small, medium, large)
-------------------------------------------------------------
1. Heuristics   checks h1 and h2 on EVERY reachable state: admissible? consistent? how close
                to the true cost? does h2 dominate h1?
2. Informed     runs Greedy Best-First and A* with both heuristics and records the same
                measurements as in Phase I (the Phase I algorithms are re-run for comparison).
3. Local search runs Hill Climbing, Simulated Annealing and the Genetic Algorithm once for
                every seed in SEEDS and reports best / mean / worst cost; blind random
                sampling with the same number of evaluations is run next to them as a baseline.
4. Landscape    examines all k! pellet orders: how many are optimal, where hill climbing stops.
5. Comparison   builds one table with all algorithms of both phases.
On the main layout it also runs the parameter-sensitivity study for the local-search methods
(300 runs per setting, on seeds that are different from the evaluation seeds), and at the
end the scaling experiment on larger mazes (pacman_search/scaling.py).

Measuring rule, the same for every algorithm: the reported time and memory include
everything the algorithm needs for the given maze - the pre-computed distance tables of
heuristic h2 and of the local-search methods are built inside the measured part. A time is
always the fastest of repeated identical runs (see measure_time); for the randomised
algorithms these per-seed times are then averaged over the seeds, because different seeds
do different amounts of work.

Reproducibility: the random algorithms only use random.Random(seed) with the fixed seeds
below, so every run of this script produces the same costs (only running times and
peak-memory readings change slightly).
"""

import argparse
import gc
import itertools
import math
import os
import statistics
import time

from pacman_search import visualize as viz
from pacman_search import visualize_phase2 as viz2
from pacman_search.experiments import (
    actions_to_string, environment_info, evaluate_search, markdown_table, measure_peak_memory,
    positive_int, save_json, write_csv)
from pacman_search.heuristics import (
    FarthestFoodHeuristic, MazeMSTHeuristic, analyse_heuristic, descent_region, optimal_costs_to_goal)
from pacman_search.informed import a_star_search, greedy_best_first_search
from pacman_search.layouts import DEFAULT_LAYOUT, OFFICIAL_LAYOUTS, load_problem
from pacman_search.local_search import (
    TourProblem, genetic_algorithm, hill_climbing, random_sampling, simulated_annealing)
from pacman_search.scaling import scaling_problem, scaling_study
from pacman_search.uninformed import UNINFORMED_ALGORITHMS

SEEDS = list(range(30))        # fixed seeds: every randomised algorithm is run once per seed
# The parameter-sensitivity study uses 300 OTHER seeds, so that the parameters are not tuned
# on the very runs that are reported as final results.
TUNING_SEEDS = list(range(1000, 1300))

# Parameters of the final local-search experiments (motivated by the sensitivity study).
SA_PARAMS = {"start_temperature": 10.0, "cooling_rate": 0.995, "end_temperature": 0.1}
GA_PARAMS = {"population_size": 30, "generations": 30, "crossover_rate": 0.9,
             "mutation_rate": 0.8, "tournament_size": 2, "elite_count": 0}
HC_RESTARTS = 9                # extra experiment: random-restart hill climbing

# Baseline: blind random sampling with exactly as many evaluations as one simulated-annealing
# run (the start order + one evaluation per iteration; start * rate^iterations <= end).
BASELINE_EVALUATIONS = 1 + math.ceil(math.log(SA_PARAMS["end_temperature"] / SA_PARAMS["start_temperature"])
                                     / math.log(SA_PARAMS["cooling_rate"]))

# Extra experiment on larger mazes (pacman_search/scaling.py): evaluations per run and seeds.
SCALING_BUDGET = 10_000
SCALING_SEEDS = list(range(20))

# The long IDS runs heat the processor, and on our laptop it then ran slower for a moment.
# A short pause before the measurements of each layout keeps this out of the timings.
COOL_DOWN_SECONDS = 3.0

UNINFORMED_LABELS = {"bfs": "BFS", "dfs": "DFS", "ucs": "UCS", "ids": "IDS"}
HC_RESTART_LABEL = f"Hill Climbing ({HC_RESTARTS} restarts)"
BASELINE_LABEL = f"Random sampling ({BASELINE_EVALUATIONS} orders)"

# Theoretical guarantees, used in the comparison table: algorithm -> (complete?, cost-optimal?)
GUARANTEES = {
    "BFS": ("yes", "no (fewest steps only)"),
    "DFS": ("yes (finite space, explored set)", "no"),
    "UCS": ("yes", "yes"),
    "IDS": ("yes", "no (fewest steps only)"),
    "Greedy": ("yes (finite space)", "no"),
    "A*": ("yes", "yes (admissible heuristic)"),
    "local": ("yes (every order is a valid plan)", "no"),
}


def informed_algorithms():
    """{label: search function(problem, trace)}.

    A NEW heuristic object is built for every call, so its caches start empty, and the time
    needed to build it (the pre-computed maze distances of h2) is added to the running time
    of the search. The reported time of Greedy and A* is therefore the full cost of using
    the heuristic.
    """
    def with_fresh_heuristic(search, heuristic_class):
        def run(problem, trace=False):
            started = time.perf_counter()
            heuristic = heuristic_class(problem)
            setup = time.perf_counter() - started
            result = search(problem, heuristic, trace)
            result.runtime_sec += setup
            return result
        return run

    return {
        "Greedy (h1)": with_fresh_heuristic(greedy_best_first_search, FarthestFoodHeuristic),
        "Greedy (h2)": with_fresh_heuristic(greedy_best_first_search, MazeMSTHeuristic),
        "A* (h1)": with_fresh_heuristic(a_star_search, FarthestFoodHeuristic),
        "A* (h2)": with_fresh_heuristic(a_star_search, MazeMSTHeuristic),
    }


def local_algorithms():
    """{label: function(tour, seed, record_history)} with the final parameters.

    The three local-search algorithms, hill climbing with restarts as an extra experiment,
    and blind random sampling as the baseline they are compared with."""
    return {
        "Hill Climbing": lambda tour, seed, record_history=True: hill_climbing(
            tour, seed=seed, record_history=record_history),
        "Simulated Annealing": lambda tour, seed, record_history=True: simulated_annealing(
            tour, seed=seed, record_history=record_history, **SA_PARAMS),
        "Genetic Algorithm": lambda tour, seed, record_history=True: genetic_algorithm(
            tour, seed=seed, record_history=record_history, **GA_PARAMS),
        HC_RESTART_LABEL: lambda tour, seed, record_history=True: hill_climbing(
            tour, seed=seed, restarts=HC_RESTARTS, record_history=record_history),
        BASELINE_LABEL: lambda tour, seed, record_history=True: random_sampling(
            tour, seed=seed, evaluations=BASELINE_EVALUATIONS, record_history=record_history),
    }


def orders_in_memory(label, num_food):
    """How many pellet orders each method holds at the same time (by construction)."""
    if label.startswith("Hill Climbing"):
        return 2 + num_food * (num_food - 1) // 2          # current, best so far, all neighbours
    if label == "Simulated Annealing":
        return 3                                           # current, neighbour, best so far
    if label == BASELINE_LABEL:
        return 2                                           # the order just drawn, best so far
    return 2 * GA_PARAMS["population_size"] + 1            # old and new population, best so far


# --------------------------------------------------------------------------------------
# Measuring
# --------------------------------------------------------------------------------------
def fastest_build_ms(build, repeats=20):
    """Time (ms) of calling build(), fastest of `repeats` calls - used for the tables that are
    computed in advance. Same timing rule as measure_time."""
    times = []
    for _ in range(repeats):
        gc.collect()
        gc.disable()
        try:
            started = time.perf_counter()
            build()
            times.append((time.perf_counter() - started) * 1000.0)
        finally:
            gc.enable()
    return min(times)


def study_heuristics(problem):
    """Exhaustive check of h1 and h2 (admissible / consistent / accuracy / dominance)."""
    true_costs = optimal_costs_to_goal(problem)
    rows, heuristics = [], []
    for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
        setup_ms = fastest_build_ms(lambda: heuristic_class(problem))
        heuristic = heuristic_class(problem)
        row = analyse_heuristic(problem, heuristic, true_costs)
        row["setup_ms"] = round(setup_ms, 3)             # pre-computation time of the heuristic
        # what Greedy has to deal with: few distinct values (ties) and the region it must
        # search before the heuristic rises above its start value again
        row["distinct_values"] = len({heuristic(state) for state in true_costs})
        row["states_below_start_value"], row["goal_below_start_value"] = descent_region(problem, heuristic)
        rows.append(row)
        heuristics.append(heuristic)
    h1, h2 = heuristics
    dominates = all(h2(state) >= h1(state) for state in true_costs)
    strictly = sum(h2(state) > h1(state) for state in true_costs)
    for row in rows:
        row["h2_dominates_h1"] = dominates
        row["states_where_h2_is_larger"] = strictly
    return rows


def run_seed(run, tour, seed, repeats=3):
    """One seed of a local-search algorithm; returns (result, running time in ms).

    The seed is run `repeats` times. Every repetition does exactly the same work and gives
    the same result, so the fastest repetition is the time of this seed with the
    disturbances of the machine filtered out (the same rule as in measure_time).
    """
    times = []
    for _ in range(repeats):
        gc.collect()
        gc.disable()                                     # same timing rule as for the search algorithms
        try:
            result = run(tour, seed)
        finally:
            gc.enable()
        times.append(result.runtime_sec * 1000.0)
    return result, min(times)


def evaluate_local(problem, tour, label, run, seeds, optimum, setup_ms):
    """Run one local-search algorithm for every seed.

    Returns (summary row, one row per run, list of LocalSearchResult). Different seeds do
    different amounts of work, so the running time of the algorithm is the MEAN over the
    seeds (the time of each seed is measured by run_seed).
    """
    results, times = [], []
    for seed in seeds:
        result, time_ms = run_seed(run, tour, seed)
        results.append(result)
        times.append(time_ms)
    run_rows = []
    for result, time_ms in zip(results, times):
        states, replayed_cost = problem.execute(result.actions)    # the plan must really work
        assert problem.is_goal(states[-1]) and replayed_cost == result.cost, f"{label}: invalid plan"
        assert not any(problem.is_goal(state) for state in states[:-1]), f"{label}: plan passes the goal"
        run_rows.append({
            "layout": problem.name, "algorithm": label, "seed": result.seed, "cost": result.cost,
            "optimal": result.cost == optimum, "evaluations": result.evaluations,
            "iterations": result.iterations, "time_ms": round(time_ms, 3),
            "order": " ".join(str(pellet) for pellet in result.order),
            "eating_order": " ".join(str(pellet) for pellet in tour.eating_order(result.order)),
        })
    costs = [result.cost for result in results]
    summary = {
        "layout": problem.name,
        "algorithm": label,
        "runs": len(seeds),
        "best": min(costs),
        "mean": round(statistics.mean(costs), 2),
        "worst": max(costs),
        "std": round(statistics.stdev(costs), 2),
        "optimal_runs": sum(cost == optimum for cost in costs),
        "mean_evaluations": round(statistics.mean(result.evaluations for result in results), 1),
        "mean_iterations": round(statistics.mean(result.iterations for result in results), 1),
        "run_time_ms": round(statistics.mean(times), 3),              # the search itself
        "setup_ms": round(setup_ms, 3),                               # building the distance tables
        "time_ms": round(statistics.mean(times) + setup_ms, 3),       # what the comparison table uses
        "time_std_ms": round(statistics.stdev(times), 3),
        # memory: distance tables + one run, without the history lists kept for the plots
        "peak_memory_kib": round(measure_peak_memory(
            lambda: run(TourProblem(problem), seeds[0], record_history=False)), 1),
        "orders_in_memory": orders_in_memory(label, problem.num_food),
    }
    return summary, run_rows, results


def analyse_landscape(problem, tour, optimum):
    """Exhaustive look at the search landscape of the pellet-ordering problem.

    Feasible because k! is small (at most 8! = 40,320 orders). For every order we follow
    steepest-descent hill climbing to the order where it stops and classify that order:

      global optimum   its cost is the optimal cost
      local optimum    not optimal, and no chain of equal-cost swaps leads to anything better
      shoulder         not optimal, but a chain of equal-cost swaps (a plateau) leads to a
                       better order; the climber stops there only because it refuses
                       sideways moves
    """
    orders = list(itertools.permutations(range(problem.num_food)))
    cost = {order: tour.cost(order) for order in orders}

    def better_neighbour(order):
        best, best_cost = None, cost[order]
        for neighbour in tour.neighbours(order):
            if cost[neighbour] < best_cost:
                best, best_cost = neighbour, cost[neighbour]
        return best

    def kind_of_stop(order):
        if cost[order] == optimum:
            return "global optimum"
        plateau, todo = {order}, [order]                 # flood fill over equal-cost neighbours
        while todo:
            for neighbour in tour.neighbours(todo.pop()):
                if cost[neighbour] < cost[order]:
                    return "shoulder"
                if cost[neighbour] == cost[order] and neighbour not in plateau:
                    plateau.add(neighbour)
                    todo.append(neighbour)
        return "local optimum"

    stops_at = {}                                        # order -> order where the climb ends
    for order in orders:
        path, current = [], order
        while current not in stops_at:
            step = better_neighbour(current)
            if step is None:
                stops_at[current] = current
                break
            path.append(current)
            current = step
        for visited in path:
            stops_at[visited] = stops_at[current]
    kind = {stop: kind_of_stop(stop) for stop in set(stops_at.values())}
    ends = [kind[stops_at[order]] for order in orders]
    uphill = [cost[n] - cost[o] for o in orders for n in tour.neighbours(o) if cost[n] > cost[o]]
    values = sorted(cost.values())
    return {
        "layout": problem.name,
        "orders": len(orders),
        "optimal_orders": values.count(optimum),
        "best_cost": values[0],
        "median_cost": statistics.median(values),
        "worst_cost": values[-1],
        "stop_orders_global_optimum": sum(1 for k in kind.values() if k == "global optimum"),
        "stop_orders_local_optimum": sum(1 for k in kind.values() if k == "local optimum"),
        "stop_orders_shoulder": sum(1 for k in kind.values() if k == "shoulder"),
        "starts_ending_in_global_optimum": ends.count("global optimum"),
        "starts_ending_in_local_optimum": ends.count("local optimum"),
        "starts_ending_on_shoulder": ends.count("shoulder"),
        "hc_success_probability": round(ends.count("global optimum") / len(orders), 4),
        "mean_uphill_swap": round(statistics.mean(uphill), 2),
        "median_uphill_swap": statistics.median(uphill),
    }


def random_sampling_success(optimal_share, evaluations):
    """Exact probability (in percent) that `evaluations` random orders contain an optimal one,
    when the share `optimal_share` of all orders is optimal: 1 - (1 - share)^n."""
    return 100.0 * (1.0 - (1.0 - optimal_share) ** evaluations)


def tuning_study(tour, optimum, seeds, optimal_share, climb_success):
    """Parameter sensitivity of SA, GA and HC on one layout. Returns (sa_rows, ga_rows, other_rows).

    Every row reports the share of runs that reach the optimum AND the number of objective
    evaluations per run, because many parameters change the budget as well. Next to it
    stands the baseline: how often blind random sampling with the same number of
    evaluations would succeed (exact, from the share of optimal orders found by
    analyse_landscape). For hill climbing with restarts the exact success rate is known as
    well - every climb succeeds with probability `climb_success` - and is stored as
    `exact_percent`.
    """
    def score(run):
        results = [run(seed) for seed in seeds]
        costs = [result.cost for result in results]
        evaluations = round(statistics.mean(r.evaluations for r in results))
        return {"hits": sum(cost == optimum for cost in costs), "runs": len(seeds),
                "percent": round(100.0 * sum(cost == optimum for cost in costs) / len(seeds), 1),
                "mean": round(statistics.mean(costs), 2), "worst": max(costs),
                "evaluations": evaluations,
                "random_sampling_percent": round(random_sampling_success(optimal_share, evaluations), 1)}

    def sa(**changes):
        params = dict(SA_PARAMS, **changes)
        return score(lambda seed: simulated_annealing(tour, seed=seed, record_history=False, **params))

    def ga(**changes):
        params = dict(GA_PARAMS, **changes)
        return score(lambda seed: genetic_algorithm(tour, seed=seed, record_history=False, **params))

    sa_rows = [{"start_temperature": start, "cooling_rate": rate, **sa(start_temperature=start, cooling_rate=rate)}
               for start in (1.0, 5.0, 10.0, 20.0) for rate in (0.9, 0.95, 0.99, 0.995, 0.999)]
    ga_rows = [{"population_size": size, "mutation_rate": rate, **ga(population_size=size, mutation_rate=rate)}
               for size in (10, 20, 30, 60) for rate in (0.05, 0.2, 0.5, 0.8)]
    other_rows = []                                # one parameter changed at a time
    variations = (
        [("SA", "end_temperature", value) for value in (2.0, 1.0, 0.5, 0.1)]
        + [("GA", "generations", value) for value in (10, 20, 30, 60)]
        + [("GA", "crossover_rate", value) for value in (0.0, 0.5, 0.9, 1.0)]
        + [("GA", "tournament_size", value) for value in (2, 3, 5)]
        + [("GA", "elite_count", value) for value in (0, 1, 2, 5)]
        + [("HC", "restarts", value) for value in (0, 1, 2, 4, 9)]
        + [("HC", "max_sideways", value) for value in (5, 20, 100)]
    )
    for algorithm, parameter, value in variations:
        if algorithm == "SA":
            result, used = sa(**{parameter: value}), value == SA_PARAMS[parameter]
        elif algorithm == "GA":
            result, used = ga(**{parameter: value}), value == GA_PARAMS[parameter]
        else:                                      # hill climbing: restarts or sideways moves
            result = score(lambda seed: hill_climbing(tour, seed=seed, record_history=False,
                                                      **{parameter: value}))
            used = parameter == "restarts" and value in (0, HC_RESTARTS)
        exact = None
        if parameter == "restarts":                # each of the value + 1 climbs succeeds independently
            exact = round(100.0 * (1.0 - (1.0 - climb_success) ** (value + 1)), 1)
        other_rows.append({"algorithm": algorithm, "parameter": parameter, "value": value,
                           "used_in_final_runs": used, **result, "exact_percent": exact})
    return sa_rows, ga_rows, other_rows


def comparison_table(problem, search_rows, local_summaries, optimum):
    """One table with every algorithm of both phases (also the data of the summary chart)."""
    rows = []
    for row in search_rows:
        name = row["algorithm"]
        complete, optimal = GUARANTEES[name.split(" ")[0]]
        rows.append({
            "layout": problem.name, "algorithm": name,
            "family": "uninformed" if name in UNINFORMED_LABELS.values() else "informed",
            "cost": row["path_cost"], "cost_range": None, "steps": row["steps"],
            "time_ms": row["time_ms"], "peak_memory_kib": row["peak_memory_kib"],
            "memory_items": row["max_nodes_in_memory"], "effort": row["nodes_expanded"],
            "found_optimum": "yes" if row["path_cost"] == optimum else "no",
            "complete": complete, "optimal_guaranteed": optimal,
        })
    complete, optimal = GUARANTEES["local"]
    for summary in local_summaries:
        rows.append({
            "layout": problem.name, "algorithm": summary["algorithm"],
            "family": "baseline" if summary["algorithm"] == BASELINE_LABEL else "local search",
            "cost": summary["mean"], "cost_range": [summary["best"], summary["worst"]], "steps": None,
            "time_ms": summary["time_ms"], "peak_memory_kib": summary["peak_memory_kib"],
            "memory_items": summary["orders_in_memory"], "effort": summary["mean_evaluations"],
            "found_optimum": f"{summary['optimal_runs']}/{summary['runs']} runs",
            "complete": complete, "optimal_guaranteed": optimal,
        })
    return rows


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def main():
    """Measure everything, write the tables, then draw the figures and the animations."""
    parser = argparse.ArgumentParser(description="Run all Phase II experiments.")
    parser.add_argument("--out", help="output folder (default: results/phase2, or results/phase2_quick with --quick)")
    parser.add_argument("--quick", action="store_true",
                        help="fast run: 10 seeds, 3 timing repeats, no landscape analysis, "
                             "no tuning study, no scaling experiment, no animations")
    parser.add_argument("--repeats", type=positive_int, default=20,
                        help="timing repeats per search algorithm (default 20; --quick uses 3)")
    args = parser.parse_args()
    seeds = SEEDS[:10] if args.quick else SEEDS
    repeats = 3 if args.quick else args.repeats
    out = args.out or os.path.join("results", "phase2_quick" if args.quick else "phase2")
    figures = os.path.join(out, "figures")
    animations = os.path.join(out, "animations")
    os.makedirs(figures, exist_ok=True)

    search_rows, heuristic_rows, local_rows, run_rows = [], [], [], []
    comparison, landscapes, solutions = [], [], []
    search_results, tours, local_results, problems, optimum_of = {}, {}, {}, {}, {}

    # ------------------------------------------------------------------ measurements
    # All timings are taken here, before any traced run exists (see evaluate_search).
    for name in OFFICIAL_LAYOUTS:
        problem = load_problem(name)
        problems[name] = problem
        print(f"\n=== {problem.describe()}")
        if not args.quick:
            time.sleep(COOL_DOWN_SECONDS)

        # ---- uninformed (Phase I, re-measured) + informed search ----
        layout_rows, search_results[name] = [], {}
        algorithms = {UNINFORMED_LABELS[key]: search for key, search in UNINFORMED_ALGORITHMS.items()}
        algorithms.update(informed_algorithms())
        for label, search in algorithms.items():
            row, result = evaluate_search(problem, label, search, repeats)
            layout_rows.append(row)
            search_results[name][label] = result
            print("   ", result.summary())
        optimum = next(row["path_cost"] for row in layout_rows if row["algorithm"] == "UCS")
        optimum_of[name] = optimum
        for row in layout_rows:
            row["optimal_cost"] = optimum
            row["cost_optimal"] = row["path_cost"] == optimum
        search_rows += layout_rows

        # ---- heuristics ----
        heuristic_rows += study_heuristics(problem)

        # ---- local search ----
        tour = TourProblem(problem)
        tours[name] = tour
        setup_ms = fastest_build_ms(lambda: TourProblem(problem))  # building the distance tables
        summaries, local_results[name] = [], {}
        for label, run in local_algorithms().items():
            summary, rows, results = evaluate_local(problem, tour, label, run, seeds, optimum, setup_ms)
            summaries.append(summary)
            run_rows += rows
            local_results[name][label] = results
            print(f"    {label}: best {summary['best']} / mean {summary['mean']} / worst {summary['worst']}"
                  f"  - optimum reached in {summary['optimal_runs']} of {summary['runs']} runs")
        local_rows += summaries
        if not args.quick:
            landscapes.append(analyse_landscape(problem, tour, optimum))

        # ---- all algorithms in one table ----
        comparison += comparison_table(problem, layout_rows, summaries, optimum)

        for label, result in search_results[name].items():
            if label not in UNINFORMED_LABELS.values():
                solutions.append(f"[{name}] {label}: cost {result.path_cost}, {result.depth} moves\n"
                                 f"{actions_to_string(result.actions)}\n{problem.render(result.states)}\n")
        for label, results in local_results[name].items():
            best = min(results, key=lambda result: result.cost)
            solutions.append(f"[{name}] {label}: best of {len(results)} runs - cost {best.cost}, "
                             f"{len(best.actions)} moves, pellets eaten in the order "
                             f"{tour.eating_order(best.order)} (seed {best.seed})\n"
                             f"{actions_to_string(best.actions)}\n")

    # ------------------------------------------------------------------ tuning (main layout)
    sa_rows, ga_rows, other_rows = [], [], []
    scaling_instances, scaling_methods = [], []
    if not args.quick:
        print(f"\nParameter-sensitivity study on the main layout ({len(TUNING_SEEDS)} runs per setting) ...")
        main_landscape = next(row for row in landscapes if row["layout"] == DEFAULT_LAYOUT)
        optimal_share = main_landscape["optimal_orders"] / main_landscape["orders"]
        sa_rows, ga_rows, other_rows = tuning_study(
            tours[DEFAULT_LAYOUT], optimum_of[DEFAULT_LAYOUT], TUNING_SEEDS, optimal_share,
            main_landscape["starts_ending_in_global_optimum"] / main_landscape["orders"])
        # ---------------------------------------------------------------- larger mazes
        print(f"Scaling experiment on larger mazes ({SCALING_BUDGET:,} evaluations per run, "
              f"{len(SCALING_SEEDS)} seeds) ...")
        scaling_instances, scaling_methods = scaling_study(SCALING_SEEDS, SCALING_BUDGET, SA_PARAMS, GA_PARAMS)

    # ------------------------------------------------------------------ tables
    search_columns = ["layout", "algorithm", "path_cost", "steps", "nodes_generated", "nodes_expanded",
                      "max_frontier", "max_nodes_in_memory", "time_ms", "time_median_ms", "time_mean_ms",
                      "time_std_ms", "time_runs", "peak_memory_kib", "cost_optimal", "solution"]
    comparison_columns = ["layout", "algorithm", "family", "cost", "cost_range", "steps", "time_ms",
                          "peak_memory_kib", "memory_items", "effort", "found_optimum", "complete",
                          "optimal_guaranteed"]
    write_csv(os.path.join(out, "search_metrics.csv"), search_rows, search_columns)
    write_csv(os.path.join(out, "heuristic_analysis.csv"), heuristic_rows)
    write_csv(os.path.join(out, "local_search_summary.csv"), local_rows)
    write_csv(os.path.join(out, "local_search_runs.csv"), run_rows)
    write_csv(os.path.join(out, "comparison_all.csv"), comparison, comparison_columns)
    write_csv(os.path.join(out, "landscape.csv"), landscapes)
    write_csv(os.path.join(out, "tuning_sa.csv"), sa_rows)
    write_csv(os.path.join(out, "tuning_ga.csv"), ga_rows)
    write_csv(os.path.join(out, "tuning_one_at_a_time.csv"), other_rows)
    if scaling_instances:
        write_csv(os.path.join(out, "scaling_instances.csv"), scaling_instances,
                  [column for column in scaling_instances[0] if column != "layout"])
        write_csv(os.path.join(out, "scaling_methods.csv"), scaling_methods)
    with open(os.path.join(out, "solutions.txt"), "w", encoding="utf-8") as handle:
        handle.write("Solution paths (U = up, R = right, D = down, L = left; '*' = visited cell)\n\n")
        handle.write("\n".join(solutions))
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as handle:
        handle.write("# Phase II results\n\n## Heuristics (checked on every reachable state)\n\n")
        handle.write(markdown_table(heuristic_rows, list(heuristic_rows[0].keys())) + "\n")
        for name in OFFICIAL_LAYOUTS:
            handle.write(f"\n## Layout: {name}\n\n### Search algorithms\n\n")
            handle.write(markdown_table([r for r in search_rows if r["layout"] == name], search_columns[1:-1]) + "\n")
            handle.write(f"\n### Local search ({len(seeds)} seeds)\n\n")
            rows = [r for r in local_rows if r["layout"] == name]
            handle.write(markdown_table(rows, list(rows[0].keys())[1:]) + "\n")
            handle.write("\n### All algorithms\n\n")
            handle.write(markdown_table([r for r in comparison if r["layout"] == name], comparison_columns[1:]) + "\n")
        if scaling_instances:
            handle.write(f"\n## Larger mazes ({SCALING_BUDGET:,} evaluations per run, {len(SCALING_SEEDS)} seeds)\n\n")
            handle.write(markdown_table(scaling_instances,
                                        [c for c in scaling_instances[0] if c != "layout"]) + "\n\n")
            handle.write(markdown_table(scaling_methods, list(scaling_methods[0].keys())) + "\n")
    save_json(os.path.join(out, "results.json"), {
        "environment": environment_info(), "timing_repeats": repeats, "seeds": seeds,
        "tuning_seeds": [TUNING_SEEDS[0], TUNING_SEEDS[-1]], "tuning_runs": len(TUNING_SEEDS),
        "sa_parameters": SA_PARAMS, "ga_parameters": GA_PARAMS, "hc_restarts": HC_RESTARTS,
        "baseline_evaluations": BASELINE_EVALUATIONS, "baseline_label": BASELINE_LABEL,
        "cool_down_seconds": 0 if args.quick else COOL_DOWN_SECONDS,
        "optimum": optimum_of, "search_metrics": search_rows, "heuristic_analysis": heuristic_rows,
        "local_search_summary": local_rows, "local_search_runs": run_rows, "comparison": comparison,
        "landscape": landscapes, "tuning_sa": sa_rows, "tuning_ga": ga_rows,
        "tuning_one_at_a_time": other_rows,
        "scaling_budget": SCALING_BUDGET, "scaling_seeds": len(SCALING_SEEDS),
        "scaling_instances": scaling_instances, "scaling_methods": scaling_methods})

    # ------------------------------------------------------------------ figures and animations
    print("\nDrawing figures ...")
    informed_labels = list(informed_algorithms())
    official_local = ["Hill Climbing", "Simulated Annealing", "Genetic Algorithm"]
    effect_rows = {}
    for name in OFFICIAL_LAYOUTS:
        problem, optimum = problems[name], optimum_of[name]
        # the same informed searches again, this time recording which nodes were expanded
        traced = [search(problem, trace=True) for search in informed_algorithms().values()]
        viz.plot_explored(problem, traced, os.path.join(figures, f"explored_informed_{name}.png"),
                          title=f"Greedy Best-First and A*: explored states and returned path - '{name}' layout")
        if name == DEFAULT_LAYOUT and not args.quick:
            print("Rendering animations ...")
            os.makedirs(animations, exist_ok=True)
            for result in traced:
                file_name = (result.algorithm.lower().replace("*", "star").replace(" ", "_")
                             .replace("(", "").replace(")", ""))
                viz.animate_search(problem, result,
                                   os.path.join(animations, f"{file_name}_{DEFAULT_LAYOUT}.gif"))
        effect_rows[name] = [row for row in search_rows if row["layout"] == name
                             and row["algorithm"] in ["UCS"] + informed_labels]
        viz2.plot_convergence({label: local_results[name][label] for label in official_local}, optimum,
                              os.path.join(figures, f"convergence_{name}.png"),
                              title=f"Local search convergence on the '{name}' layout ({len(seeds)} seeds each)")
        viz2.plot_final_costs(local_results[name], optimum, os.path.join(figures, f"final_costs_{name}.png"),
                              title=f"Final cost of every local-search run - '{name}' layout")
        viz2.plot_summary_all([row for row in comparison if row["layout"] == name],
                              os.path.join(figures, f"summary_all_{name}.png"), optimum,
                              title=f"All algorithms compared on the '{name}' layout", runs=len(seeds))
        # an optimal route (from A*) next to the worst order hill climbing stopped at
        best_search = search_results[name]["A* (h2)"]
        routes = [("Optimal route", f"cost {best_search.path_cost:g}  |  {best_search.depth} moves",
                   best_search.actions)]
        worst_run = max(local_results[name]["Hill Climbing"], key=lambda result: result.cost)
        if worst_run.cost > optimum:
            routes.append(("Where a hill-climbing run stopped",
                           f"cost {worst_run.cost:g}  |  {len(worst_run.actions)} moves  |  "
                           f"priority order {worst_run.order}", worst_run.actions))
        viz2.plot_routes(problem, routes, os.path.join(figures, f"routes_{name}.png"),
                         title=f"Local search on the '{name}' layout")
        viz2.plot_sa_trace(local_results[name]["Simulated Annealing"][0], optimum,
                           os.path.join(figures, f"sa_trace_{name}.png"))
    viz2.plot_heuristic_effect(effect_rows, os.path.join(figures, "heuristic_effect.png"), optimum_of)

    reachable = {name: problems[name].count_reachable_states() for name in OFFICIAL_LAYOUTS}
    points = {label: [(reachable[row["layout"]], row["nodes_expanded"])
                      for row in search_rows if row["algorithm"] == label]
              for label in ["UCS", "A* (h1)", "A* (h2)", "Greedy (h1)", "Greedy (h2)"]}
    viz.plot_scaling(points, os.path.join(figures, "scaling_informed.png"),
                     title="Nodes expanded versus state-space size",
                     layout_names={count: name for name, count in reachable.items()})

    if sa_rows:
        runs = len(TUNING_SEEDS)
        cells = {(row["start_temperature"], row["cooling_rate"]): row for row in sa_rows}
        viz2.plot_tuning_grid(cells, sorted({r["start_temperature"] for r in sa_rows}),
                              sorted({r["cooling_rate"] for r in sa_rows}),
                              "start temperature", "cooling rate", os.path.join(figures, "tuning_sa.png"),
                              f"Simulated annealing on '{DEFAULT_LAYOUT}': start temperature x cooling rate",
                              chosen=(SA_PARAMS["start_temperature"], SA_PARAMS["cooling_rate"]),
                              runs_per_cell=runs)
        cells = {(row["population_size"], row["mutation_rate"]): row for row in ga_rows}
        viz2.plot_tuning_grid(cells, sorted({r["population_size"] for r in ga_rows}),
                              sorted({r["mutation_rate"] for r in ga_rows}),
                              "population size", "mutation rate", os.path.join(figures, "tuning_ga.png"),
                              f"Genetic algorithm on '{DEFAULT_LAYOUT}': population size x mutation rate",
                              chosen=(GA_PARAMS["population_size"], GA_PARAMS["mutation_rate"]),
                              runs_per_cell=runs)
        # reliability against budget: one line per algorithm, one point per setting
        plain_hc = next(r for r in other_rows if r["parameter"] == "restarts" and r["value"] == 0)
        budget = {
            "Hill Climbing, restarts": [
                (r["evaluations"], 100 * r["hits"] / runs, r["value"])
                for r in other_rows if r["parameter"] == "restarts"],
            "Hill Climbing, sideways moves": [
                (r["evaluations"], 100 * r["hits"] / runs, r["value"])
                for r in other_rows + [dict(plain_hc, parameter="max_sideways")]
                if r["parameter"] == "max_sideways"],
            "Simulated Annealing, cooling rate": [
                (r["evaluations"], 100 * r["hits"] / runs, f"{r['cooling_rate']:g}")
                for r in sa_rows if r["start_temperature"] == SA_PARAMS["start_temperature"]],
            "Genetic Algorithm, population": [
                (r["evaluations"], 100 * r["hits"] / runs, r["population_size"])
                for r in ga_rows if r["mutation_rate"] == GA_PARAMS["mutation_rate"]],
        }
        # the baseline, exactly: n random orders contain an optimal one with probability 1 - (1 - p)^n
        lowest = min(x for points in budget.values() for x, _, _ in points)
        highest = max(x for points in budget.values() for x, _, _ in points)
        curve = [(n, random_sampling_success(optimal_share, n))
                 for n in (lowest * (highest / lowest) ** (i / 60) for i in range(61))]
        viz2.plot_budget_vs_success(budget, os.path.join(figures, "budget_vs_success.png"),
                                    title=f"Reliability against budget on the '{DEFAULT_LAYOUT}' layout",
                                    runs=runs, baseline=("Random sampling (exact)", curve))

    if scaling_instances:
        viz2.plot_scaling_local(scaling_methods, scaling_instances, os.path.join(figures, "scaling_local.png"),
                                SCALING_BUDGET, len(SCALING_SEEDS),
                                title="Larger mazes: local search against random sampling, and A*")
        sizes = [scaling_instances[0]["pellets"], scaling_instances[-1]["pellets"]]
        viz.plot_layouts([scaling_problem(pellets) for pellets in sizes],
                         os.path.join(figures, "scaling_mazes.png"))

    print(f"\nDone. Tables are in {out}, figures in {figures}.")


if __name__ == "__main__":
    main()
