"""whatif_experiments.py - the "what if" experiments quoted in the oral-discussion study guide.

Study aid only - NOT part of the submission. Nothing in the project folders is changed: the
script only IMPORTS the Phase II code and runs it with other settings, or runs small VARIANTS of
the project's algorithms that are written out below (each variant is a copy of the project
function with one clearly marked change).

    python whatif_experiments.py                 run every experiment and print a readable summary
    python whatif_experiments.py goal_test dfs   run only the named experiments
    python whatif_experiments.py --list          list the experiment names
    python whatif_experiments.py --json FILE     also save the raw numbers as JSON

The script looks for the code in ..\\Phase2\\code (it is meant to sit in the Study_Guide folder
next to Phase1 and Phase2). Everything is deterministic (fixed seeds), so the numbers printed
are the numbers in the guide; a full run takes well under a minute.
"""
import sys

sys.dont_write_bytecode = True          # never create __pycache__ inside the project folders

import heapq  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import statistics  # noqa: E402
import time  # noqa: E402
from collections import deque  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
CODE = next((folder for folder in (HERE.parent / "Phase2" / "code",
                                   Path(r"C:\Users\moata\Downloads\CSAI301_PacMan_Project\Phase2\code"))
             if (folder / "pacman_search").is_dir()), None)
if CODE is None:
    sys.exit("Cannot find Phase2/code - put this script in the Study_Guide folder next to Phase1 and Phase2.")
sys.path.insert(0, str(CODE))

import pacman_search.problem as problem_module  # noqa: E402
from pacman_search.experiments import actions_to_string, step_cost_tradeoff  # noqa: E402
from pacman_search.heuristics import (  # noqa: E402
    FarthestFoodHeuristic, MazeMSTHeuristic, ZeroHeuristic, analyse_heuristic, cheapest_step, manhattan,
    optimal_costs_to_goal)
from pacman_search.informed import a_star_search, best_first_search, greedy_best_first_search  # noqa: E402
from pacman_search.layouts import LAYOUTS, load_problem  # noqa: E402
from pacman_search.local_search import (  # noqa: E402
    TourProblem, genetic_algorithm, hill_climbing, simulated_annealing)
from pacman_search.problem import PacmanProblem, State  # noqa: E402
from pacman_search.search_core import Node, SearchStats  # noqa: E402
from pacman_search.uninformed import (  # noqa: E402
    CUTOFF, breadth_first_search, depth_first_search, depth_limited_search, iterative_deepening_search,
    uniform_cost_search)

OFFICIAL = ("small", "medium", "large")
EVAL_SEEDS = list(range(30))                 # the seeds of the reported results
TUNING_SEEDS = list(range(1000, 1300))       # the seeds of the sensitivity study
SA_PARAMS = {"start_temperature": 10.0, "cooling_rate": 0.995, "end_temperature": 0.1}
GA_PARAMS = {"population_size": 30, "generations": 30, "crossover_rate": 0.9,
             "mutation_rate": 0.8, "tournament_size": 2, "elite_count": 0}


def brief(result):
    """The numbers of a SearchResult that the guide quotes."""
    return {"found": result.found, "cost": result.path_cost, "steps": result.depth,
            "expanded": result.nodes_expanded, "generated": result.nodes_generated,
            "max_frontier": result.max_frontier_size, "max_memory": result.max_nodes_in_memory,
            "solution": actions_to_string(result.actions)}


def danger_entries(problem, actions):
    """How many moves of a plan enter a danger cell."""
    states, _ = problem.execute(actions)
    return sum(1 for state in states[1:] if state.pos in problem.danger_cells)


# --------------------------------------------------------------------------------------
# Variants of the project's algorithms (one marked change each)
# --------------------------------------------------------------------------------------
def bfs_late_goal_test(problem):
    """The project's BFS with ONE change: the goal is tested when a node is taken from the queue."""
    stats = SearchStats("BFS (goal test at expansion)")
    root = Node(problem.initial_state)
    stats.count_generated()
    frontier = deque([root])
    reached = {root.state}
    stats.observe(len(frontier), 0)
    while frontier:
        node = frontier.popleft()
        if problem.is_goal(node.state):                 # <-- CHANGE: late goal test
            return stats.finish(node)
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in children:
            if child_state in reached:
                continue
            reached.add(child_state)
            frontier.append(Node(child_state, node, action, node.path_cost + cost))
        stats.observe(len(frontier), len(reached) - len(frontier))
    return stats.finish(None)


def ucs_early_goal_test(problem):
    """The project's UCS with ONE change: the goal is tested when a node is generated."""
    stats = SearchStats("UCS (goal test at generation)")
    root = Node(problem.initial_state)
    stats.count_generated()
    if problem.is_goal(root.state):
        return stats.finish(root)
    frontier = [(0, 0, root)]
    best_cost = {root.state: 0}
    counter = 1
    stats.observe(len(frontier), 0)
    while frontier:
        cost_so_far, _, node = heapq.heappop(frontier)
        if cost_so_far > best_cost[node.state]:
            continue
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in children:
            new_cost = cost_so_far + cost
            if child_state not in best_cost or new_cost < best_cost[child_state]:
                best_cost[child_state] = new_cost
                child = Node(child_state, node, action, new_cost)
                if problem.is_goal(child_state):        # <-- CHANGE: early goal test
                    return stats.finish(child)
                heapq.heappush(frontier, (new_cost, counter, child))
                counter += 1
        stats.observe(len(frontier), stats.expanded)
    return stats.finish(None)


def dfs_without_explored_set(problem, max_expansions=100_000):
    """The project's DFS with the explored set REMOVED (pure tree search, no loop check at all).

    It never ends in a maze, so it is stopped after `max_expansions` expansions."""
    root = Node(problem.initial_state)
    frontier = [root]
    expanded = 0
    recent = deque(maxlen=6)
    node = root
    while frontier:
        node = frontier.pop()
        if problem.is_goal(node.state):
            return {"found": True, "expanded": expanded, "steps": node.depth, "cost": node.path_cost}
        if expanded >= max_expansions:
            break
        expanded += 1
        recent.append(node.state.pos)
        for action, child_state, cost in reversed(problem.successors(node.state)):
            frontier.append(Node(child_state, node, action, node.path_cost + cost))
    return {"found": False, "expanded": expanded, "depth_reached": node.depth, "stack_size": len(frontier),
            "last_cells": [list(cell) for cell in recent],
            "pellets_left": bin(node.state.food).count("1")}


def dfs_without_reversed(problem):
    """The project's DFS with ONE change: the successors are pushed in their natural order."""
    stats = SearchStats("DFS (children not reversed)")
    root = Node(problem.initial_state)
    stats.count_generated()
    frontier = [root]
    explored = set()
    stats.observe(len(frontier), 0)
    while frontier:
        node = frontier.pop()
        if node.state in explored:
            continue
        if problem.is_goal(node.state):
            return stats.finish(node)
        explored.add(node.state)
        stats.count_expanded(node)
        children = problem.successors(node.state)
        stats.count_generated(len(children))
        for action, child_state, cost in children:      # <-- CHANGE: no reversed()
            if child_state not in explored:
                frontier.append(Node(child_state, node, action, node.path_cost + cost))
        stats.observe(len(frontier), len(explored))
    return stats.finish(None)


def ids_with_step(problem, step, expansion_limit=3_000_000):
    """The project's IDS loop, but the depth limit grows by `step` instead of 1."""
    stats = SearchStats(f"IDS (limit += {step})")
    limit = 0
    while True:
        outcome = depth_limited_search(problem, limit, stats, False, expansion_limit)
        if isinstance(outcome, Node):
            return stats.finish(outcome), limit
        if outcome is not CUTOFF:                        # None (space exhausted) or aborted
            return stats.finish(None), limit
        limit += step


def best_first_instrumented(problem, evaluate, reopen="always", lifo_ties=False):
    """Copy of informed.best_first_search with counters and two extra switches.

    reopen = "always"         the project's A*: a state is queued again whenever a strictly cheaper path is found
             "never"          the project's Greedy rule: a state is queued only the first time it is reached
             "frontier-only"  textbook graph search: a cheaper path replaces a WAITING state, but a state that
                              has already been expanded is closed for good
    lifo_ties = True          among equal f values the NEWEST node comes out first (the project: oldest first)
    """
    root = Node(problem.initial_state)
    frontier = [(evaluate(root), 0, root)]
    best_cost = {root.state: 0}
    explored = set()
    counter = 1
    out = {"expanded": 0, "generated": 1, "requeued_while_waiting": 0, "requeued_after_expansion": 0,
           "states_expanded_twice": 0, "heuristic_calls": 1}
    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node.path_cost > best_cost[node.state]:
            continue
        if problem.is_goal(node.state):
            out.update(found=True, cost=node.path_cost, steps=node.depth,
                       solution=actions_to_string([n.action for n in node.path()[1:]]))
            return out
        if node.state in explored:
            out["states_expanded_twice"] += 1
        out["expanded"] += 1
        explored.add(node.state)
        children = problem.successors(node.state)
        out["generated"] += len(children)
        for action, child_state, cost in children:
            new_cost = node.path_cost + cost
            known_cost = best_cost.get(child_state)
            if known_cost is None:
                push = True
            elif new_cost < known_cost:
                was_expanded = child_state in explored
                push = reopen == "always" or (reopen == "frontier-only" and not was_expanded)
                if push:
                    out["requeued_after_expansion" if was_expanded else "requeued_while_waiting"] += 1
            else:
                push = False
            if push:
                best_cost[child_state] = new_cost
                child = Node(child_state, node, action, new_cost)
                heapq.heappush(frontier, (evaluate(child), -counter if lifo_ties else counter, child))
                out["heuristic_calls"] += 1
                counter += 1
    out.update(found=False, cost=None, steps=None, solution="")
    return out


class Weighted:
    """w x h: not admissible for w > 1 (weighted A*)."""

    def __init__(self, heuristic, weight):
        self.heuristic, self.weight = heuristic, weight
        self.label = f"{weight:g} x {heuristic.label}"

    def __call__(self, state):
        return self.weight * self.heuristic(state)


class SumOfBoth:
    """h1 + h2: NOT admissible (the two estimates count the same moves twice)."""
    label = "h1 + h2"

    def __init__(self, problem):
        self.h1, self.h2 = FarthestFoodHeuristic(problem), MazeMSTHeuristic(problem)

    def __call__(self, state):
        return self.h1(state) + self.h2(state)


class Patchy:
    """Admissible but NOT consistent: h2 on every second cell, 0 elsewhere (same idea as in the unit test)."""
    label = "patchy h2"

    def __init__(self, problem):
        self.h2 = MazeMSTHeuristic(problem)

    def __call__(self, state):
        return self.h2(state) if (state.pos[0] + state.pos[1]) % 2 else 0


class ManhattanMST(MazeMSTHeuristic):
    """h2 with Manhattan distances in place of the true maze distances (nearest pellet + MST)."""
    label = "h2 (Manhattan)"

    def __init__(self, problem):
        self.num_food = problem.num_food
        self.unit = cheapest_step(problem)
        self.steps = [{cell: manhattan(food, cell) for cell in problem.free_cells} for food in problem.food_cells]
        self.between = [[self.steps[i][cell] for cell in problem.food_cells] for i in range(self.num_food)]
        self._mst_cache = {0: 0}


class UncheckedProblem(PacmanProblem):
    """PacmanProblem with the "every pellet must be reachable" check switched off."""

    def _check_all_food_reachable(self):
        pass


def problem_with_action_order(layout, order):
    """A PacmanProblem whose successors are generated in a different action order.

    The module constant ACTIONS is replaced only while the problem object is being built."""
    original = problem_module.ACTIONS
    problem_module.ACTIONS = {name: original[name] for name in order}
    try:
        return PacmanProblem(LAYOUTS[layout], layout)
    finally:
        problem_module.ACTIONS = original


def score(run, seeds, optimum):
    """Run a local-search function once per seed and summarise the costs."""
    results = [run(seed) for seed in seeds]
    costs = [result.cost for result in results]
    return {"hits": sum(cost == optimum for cost in costs), "runs": len(seeds), "best": min(costs),
            "mean": round(statistics.mean(costs), 2), "worst": max(costs),
            "evaluations": round(statistics.mean(result.evaluations for result in results), 1),
            "iterations": round(statistics.mean(result.iterations for result in results), 1)}


# --------------------------------------------------------------------------------------
# The experiments
# --------------------------------------------------------------------------------------
def exp_tour():
    """The first steps of the hands-on tour: states, actions, successors, heuristics."""
    problem = load_problem("large")
    start = problem.initial_state
    after = problem.result(problem.result(start, "RIGHT"), "RIGHT")
    return {
        "start": repr(start), "actions": problem.actions(start),
        "successors": [[a, repr(s), c] for a, s, c in problem.successors(start)],
        "after_RR": repr(after), "after_RR_mask": f"{after.food:08b}",
        "food_cells": [list(cell) for cell in problem.food_cells],
        "danger_cells": sorted(list(cell) for cell in problem.danger_cells),
        "ghosts": [list(cell) for cell in problem.ghosts],
        "h1_start": FarthestFoodHeuristic(problem)(start), "h2_start": MazeMSTHeuristic(problem)(start),
    }


def exp_model():
    """State-space details: sizes, valid-but-unreachable states, branching factor, depth levels."""
    out = {}
    for name in LAYOUTS:
        problem = load_problem(name)
        report = problem.state_space_report()
        reachable = problem.reachable_states()
        missing = {}
        for cell in problem.free_cells:
            for mask in range(2 ** problem.num_food):
                if mask & problem.food_bit.get(cell, 0):
                    continue                              # Pac-Man on an uneaten pellet: not a valid state
                if State(cell, mask) not in reachable:
                    missing[cell] = missing.get(cell, 0) + 1
        transitions = sum(len(problem.successors(state)) for state in reachable)
        depth = {problem.initial_state: 0}
        queue = deque([problem.initial_state])
        while queue:
            state = queue.popleft()
            for _, child, _ in problem.successors(state):
                if child not in depth:
                    depth[child] = depth[state] + 1
                    queue.append(child)
        levels = {}
        for value in depth.values():
            levels[value] = levels.get(value, 0) + 1
        # Iterative deepening that expanded every state within the limit exactly ONCE per iteration:
        # with limit L it expands the states of depth < L. Summed over the unsuccessful limits 0 .. d-1.
        fewest_steps = breadth_first_search(problem).depth
        restart_only = sum(sum(count for level, count in levels.items() if level < limit)
                           for limit in range(fewest_steps))
        out[name] = {**report, "grid": f"{problem.height}x{problem.width}", "ghosts": len(problem.ghosts),
                     "fewest_steps": fewest_steps, "restart_only_expansions": restart_only,
                     "danger_cells": len(problem.danger_cells),
                     "valid_but_unreachable": {f"{cell[0]},{cell[1]}": count for cell, count in missing.items()},
                     "transitions": transitions, "mean_branching": round(transitions / len(reachable), 3),
                     "max_branching": max(len(problem.successors(state)) for state in reachable),
                     "goal_states": sum(1 for state in reachable if problem.is_goal(state)),
                     "deepest_level": max(levels), "largest_level": max(levels.values()),
                     "food_cells": [list(cell) for cell in problem.food_cells],
                     "danger_cell_list": sorted(list(cell) for cell in problem.danger_cells),
                     "pellet_on_danger_cell": any(cell in problem.danger_cells for cell in problem.food_cells)}
    return out


def exp_paths():
    """How often does each returned plan enter a danger cell? (cost = steps + 4 x entries)"""
    out = {}
    for name in OFFICIAL:
        problem = load_problem(name)
        searches = {
            "BFS": breadth_first_search, "DFS": depth_first_search, "UCS": uniform_cost_search,
            "IDS": iterative_deepening_search,
            "Greedy (h1)": lambda p: greedy_best_first_search(p, FarthestFoodHeuristic(p)),
            "Greedy (h2)": lambda p: greedy_best_first_search(p, MazeMSTHeuristic(p)),
            "A* (h1)": lambda p: a_star_search(p, FarthestFoodHeuristic(p)),
            "A* (h2)": lambda p: a_star_search(p, MazeMSTHeuristic(p)),
        }
        row = {}
        for label, search in searches.items():
            result = search(problem)
            entries = danger_entries(problem, result.actions)
            assert result.path_cost == result.depth + (problem.danger_cost - 1) * entries
            row[label] = {"cost": result.path_cost, "steps": result.depth, "danger_entries": entries}
        out[name] = row
    return out


def exp_danger_cost():
    """What if entering a danger cell cost 1 (uniform costs), 10, or less than a normal step?"""
    out = {}
    for danger in (1, 5, 10):
        for name in OFFICIAL:
            problem = PacmanProblem(LAYOUTS[name], name, danger_cost=danger)
            bfs, ucs = breadth_first_search(problem), uniform_cost_search(problem)
            astar = a_star_search(problem, MazeMSTHeuristic(problem))
            trade = step_cost_tradeoff(problem)
            out[f"{danger}/{name}"] = {
                "bfs": brief(bfs), "ucs": brief(ucs), "astar_h2": brief(astar),
                "bfs_danger_entries": danger_entries(problem, bfs.actions),
                "ucs_danger_entries": danger_entries(problem, ucs.actions),
                "genuine_tradeoff": trade["genuine_tradeoff"],
                "cheapest_cost_with_fewest_steps": trade["cheapest_cost_with_fewest_steps"],
                "fewest_steps": trade["fewest_steps"],
            }
    # danger cheaper than a normal step: the heuristics are scaled by the cheapest step
    problem = PacmanProblem(LAYOUTS["large"], "large", step_cost=1, danger_cost=0.5)
    true_costs = optimal_costs_to_goal(problem)
    row = {"ucs": brief(uniform_cost_search(problem)), "unit": cheapest_step(problem)}
    for cls in (FarthestFoodHeuristic, MazeMSTHeuristic):
        report = analyse_heuristic(problem, cls(problem), true_costs)
        row[cls.label] = {"admissible": report["admissible"], "consistent": report["consistent"],
                          "h_start": report["h_start"], "astar": brief(a_star_search(problem, cls(problem)))}
    out["half/large"] = row
    try:
        PacmanProblem(LAYOUTS["large"], "large", danger_cost=0)
        out["zero_cost_error"] = None
    except ValueError as error:
        out["zero_cost_error"] = str(error)
    return out


def exp_action_order():
    """What if the actions were generated in the reverse order (LEFT, DOWN, RIGHT, UP)?"""
    out = {}
    reverse = ("LEFT", "DOWN", "RIGHT", "UP")
    for name in OFFICIAL:
        row = {}
        for label, problem in (("original", load_problem(name)), ("reversed", problem_with_action_order(name, reverse))):
            row[label] = {
                "first_successors": [a for a, _, _ in problem.successors(problem.initial_state)],
                "BFS": brief(breadth_first_search(problem)), "DFS": brief(depth_first_search(problem)),
                "UCS": brief(uniform_cost_search(problem)), "IDS": brief(iterative_deepening_search(problem)),
                "Greedy (h2)": brief(greedy_best_first_search(problem, MazeMSTHeuristic(problem))),
                "A* (h2)": brief(a_star_search(problem, MazeMSTHeuristic(problem))),
                "A* (h1)": brief(a_star_search(problem, FarthestFoodHeuristic(problem))),
            }
        # DFS without reversed(children) explores exactly like DFS with the reversed action order
        no_reverse = dfs_without_reversed(load_problem(name))
        row["dfs_without_reversed"] = brief(no_reverse)
        assert brief(no_reverse) == row["reversed"]["DFS"], name
        out[name] = row
    return out


def exp_goal_test():
    """BFS with a late goal test, UCS with an early goal test (and a maze on which that goes wrong)."""
    out = {"bfs": {}, "ucs": {}}
    for name in LAYOUTS:
        problem = load_problem(name)
        early, late = breadth_first_search(problem), bfs_late_goal_test(problem)
        greedy_h0 = greedy_best_first_search(problem, ZeroHeuristic(problem))
        astar_h0 = a_star_search(problem, ZeroHeuristic(problem))
        proper, hasty = uniform_cost_search(problem), ucs_early_goal_test(problem)
        out["bfs"][name] = {"early": brief(early), "late": brief(late), "greedy_h0": brief(greedy_h0)}
        out["ucs"][name] = {"late": brief(proper), "early": brief(hasty), "astar_h0": brief(astar_h0)}
    # a four-cell maze on which the early test in UCS returns a plan that is NOT the cheapest
    maze = "######\n#. P.#\n####G#\n######"
    problem = PacmanProblem(maze, "four cells")
    proper, hasty = uniform_cost_search(problem), ucs_early_goal_test(problem)
    out["counterexample"] = {"maze": maze, "danger_cells": sorted(list(c) for c in problem.danger_cells),
                             "food_cells": [list(c) for c in problem.food_cells],
                             "late": brief(proper), "early": brief(hasty),
                             "bfs": brief(breadth_first_search(problem)),
                             "astar_h2": brief(a_star_search(problem, MazeMSTHeuristic(problem)))}
    return out


def exp_dfs_variants():
    """DFS without its explored set, and DFS as a tree search that only checks the current path."""
    out = {}
    for name in OFFICIAL:
        problem = load_problem(name)
        stats = SearchStats("DFS (tree search, loop check on the current path)")
        outcome = depth_limited_search(problem, 10 ** 9, stats, False, 2_000_000)
        if isinstance(outcome, Node):
            tree = brief(stats.finish(outcome))
        else:
            tree = {"found": False, "outcome": str(outcome), "expanded": stats.expanded}
        out[name] = {"project": brief(depth_first_search(problem)),
                     "no_explored_set": dfs_without_explored_set(problem),
                     "path_check_only": tree}
    return out


def exp_ids():
    """IDS with a depth limit that grows by more than 1."""
    out = {}
    for name, steps in (("small", (1, 5)), ("large", (1, 4))):
        problem = load_problem(name)
        for step in steps:
            result, limit = ids_with_step(problem, step)
            out[f"{name}/{step}"] = {**brief(result), "final_limit": limit}
    return out


def exp_extra_pellet():
    """What if the large maze had one more pellet (9 instead of 8)?"""
    rows = LAYOUTS["large"].strip("\n").split("\n")
    assert rows[5][4] == " "
    rows[5] = rows[5][:4] + "." + rows[5][5:]              # new pellet in the middle of the lower corridor
    problem = PacmanProblem("\n".join(rows), "large + 1 pellet")
    base = load_problem("large")
    out = {"cell": [5, 4], "size": problem.state_space_report(), "base_size": base.state_space_report(),
           "maze": "\n".join(rows)}
    searches = {
        "BFS": breadth_first_search, "DFS": depth_first_search, "UCS": uniform_cost_search,
        "IDS": lambda p: iterative_deepening_search(p, expansion_limit=20_000_000),
        "Greedy (h1)": lambda p: greedy_best_first_search(p, FarthestFoodHeuristic(p)),
        "Greedy (h2)": lambda p: greedy_best_first_search(p, MazeMSTHeuristic(p)),
        "A* (h1)": lambda p: a_star_search(p, FarthestFoodHeuristic(p)),
        "A* (h2)": lambda p: a_star_search(p, MazeMSTHeuristic(p)),
    }
    out["search"] = {label: {"new": brief(search(problem)), "old": brief(search(base))}
                     for label, search in searches.items()}
    optimum = out["search"]["UCS"]["new"]["cost"]
    old_optimum = out["search"]["UCS"]["old"]["cost"]
    out["orders"] = math.factorial(problem.num_food)
    out["neighbours"] = problem.num_food * (problem.num_food - 1) // 2
    for key, tour, best in (("local", TourProblem(problem), optimum), ("local_old", TourProblem(base), old_optimum)):
        out[key] = {
            "Hill Climbing": score(lambda seed: hill_climbing(tour, seed=seed), EVAL_SEEDS, best),
            "Simulated Annealing": score(lambda seed: simulated_annealing(tour, seed=seed, **SA_PARAMS),
                                         EVAL_SEEDS, best),
            "Genetic Algorithm": score(lambda seed: genetic_algorithm(tour, seed=seed, **GA_PARAMS),
                                       EVAL_SEEDS, best),
            "Hill Climbing (9 restarts)": score(lambda seed: hill_climbing(tour, seed=seed, restarts=9),
                                                EVAL_SEEDS, best),
        }
    return out


def exp_unreachable():
    """What if a pellet could not be reached?"""
    out = {}
    walled = "#####\n#P#.#\n#####"
    try:
        PacmanProblem(walled)
    except ValueError as error:
        out["constructor_error"] = str(error)
    maze = "#######\n#P   .#\n###G# #\n#.### #\n##    #\n#######"
    problem = UncheckedProblem(maze, "tiny with a walled-in pellet")
    out["maze"] = maze
    out["reachable_states"] = len(problem.reachable_states())
    searches = {
        "BFS": breadth_first_search, "DFS": depth_first_search, "UCS": uniform_cost_search,
        "IDS": lambda p: iterative_deepening_search(p, expansion_limit=5_000_000),
        "Greedy (h1)": lambda p: greedy_best_first_search(p, FarthestFoodHeuristic(p)),
        "A* (h1)": lambda p: a_star_search(p, FarthestFoodHeuristic(p)),
    }
    out["search"] = {}
    for label, search in searches.items():
        result = search(problem)
        out["search"][label] = {"found": result.found, "expanded": result.nodes_expanded,
                                "aborted": bool(result.extra.get("aborted", False)),
                                "iterations": len(result.extra.get("iterations", []))}
    for label, build in (("h2", lambda: MazeMSTHeuristic(problem)), ("TourProblem", lambda: TourProblem(problem))):
        try:
            build()
            out[f"{label}_error"] = None
        except Exception as error:                        # noqa: BLE001 - we want to report whatever happens
            out[f"{label}_error"] = f"{type(error).__name__}: {error}"
    return out


def exp_weighted():
    """What if the heuristic were multiplied by 1.5, 2, 3 or 5 (weighted A*), or h1 + h2 were used?"""
    out = {}
    for name in OFFICIAL:
        problem = load_problem(name)
        optimum = uniform_cost_search(problem).path_cost
        true_costs = optimal_costs_to_goal(problem)
        for cls in (FarthestFoodHeuristic, MazeMSTHeuristic):
            for weight in (1, 1.5, 2, 3, 5):
                heuristic = Weighted(cls(problem), weight)
                result = a_star_search(problem, heuristic)
                report = analyse_heuristic(problem, heuristic, true_costs)
                out[f"{name}/{cls.label}/{weight:g}"] = {
                    "cost": result.path_cost, "steps": result.depth, "expanded": result.nodes_expanded,
                    "optimal": result.path_cost == optimum, "admissible": report["admissible"],
                    "worst_overestimate": report["worst_overestimate"],
                    "within_bound": result.path_cost <= weight * optimum}
        heuristic = SumOfBoth(problem)
        result = a_star_search(problem, heuristic)
        report = analyse_heuristic(problem, heuristic, true_costs)
        out[f"{name}/sum"] = {"cost": result.path_cost, "expanded": result.nodes_expanded,
                              "optimal": result.path_cost == optimum, "admissible": report["admissible"],
                              "worst_overestimate": report["worst_overestimate"],
                              "h_start": heuristic(problem.initial_state), "optimum": optimum}
    return out


def exp_reopen():
    """What if A* did not re-open states? How often is a state queued again? Inconsistent heuristic, tie-breaking."""
    out = {}
    for name in LAYOUTS:
        problem = load_problem(name)
        optimum = uniform_cost_search(problem).path_cost
        for cls in (FarthestFoodHeuristic, MazeMSTHeuristic, Patchy):
            heuristic = cls(problem)

            def f(node, heuristic=heuristic):
                return node.path_cost + heuristic(node.state)

            project = a_star_search(problem, heuristic)
            always = best_first_instrumented(problem, f, "always")
            # the instrumented copy must behave exactly like the project's A*
            assert (always["cost"], always["expanded"], always["generated"]) == (
                project.path_cost, project.nodes_expanded, project.nodes_generated), (name, cls.label)
            never_project = best_first_search(problem, f, "A* without re-opening", reopen=False)
            never = best_first_instrumented(problem, f, "never")
            assert (never["cost"], never["expanded"]) == (never_project.path_cost, never_project.nodes_expanded)
            report = analyse_heuristic(problem, heuristic)
            out[f"{name}/{cls.label}"] = {
                "optimum": optimum, "admissible": report["admissible"], "consistent": report["consistent"],
                "always": always, "never": never,
                "frontier_only": best_first_instrumented(problem, f, "frontier-only"),
                "lifo": best_first_instrumented(problem, f, "always", lifo_ties=True)}
        # MST cache of h2: how many different food masks did one A* run ask for?
        fresh = MazeMSTHeuristic(problem)
        a_star_search(problem, fresh)
        out[f"{name}/cache"] = {"masks_cached": len(fresh._mst_cache) - 1,
                                "possible_masks": 2 ** problem.num_food}
    return out


def exp_f_census():
    """Which states MUST a search expand? States counted by f = g* + h against the optimal cost C*."""
    out = {}
    for name in OFFICIAL:
        problem = load_problem(name)
        start = problem.initial_state
        best = {start: 0}                                  # g*: cheapest cost from the start to every state
        heap = [(0, start)]
        while heap:
            cost, state = heapq.heappop(heap)
            if cost > best[state]:
                continue
            for _, child, step in problem.successors(state):
                if child not in best or cost + step < best[child]:
                    best[child] = cost + step
                    heapq.heappush(heap, (cost + step, child))
        optimum = min(cost for state, cost in best.items() if problem.is_goal(state))
        row = {"optimum": optimum, "states": len(best)}
        for cls in (ZeroHeuristic, FarthestFoodHeuristic, MazeMSTHeuristic):
            heuristic = cls(problem)
            below = sum(1 for state, cost in best.items() if cost + heuristic(state) < optimum)
            equal = sum(1 for state, cost in best.items()
                        if cost + heuristic(state) == optimum and not problem.is_goal(state))
            actual = a_star_search(problem, cls(problem)).nodes_expanded
            row[cls.label] = {"f_below_optimum": below, "f_equal_optimum_non_goal": equal, "expanded": actual}
        depth = {start: 0}                                 # BFS: states by depth
        queue = deque([start])
        while queue:
            state = queue.popleft()
            for _, child, _ in problem.successors(state):
                if child not in depth:
                    depth[child] = depth[state] + 1
                    queue.append(child)
        bfs = breadth_first_search(problem)
        row["bfs"] = {"d": bfs.depth,
                      "states_up_to_d_minus_2": sum(1 for v in depth.values() if v <= bfs.depth - 2),
                      "states_at_d_minus_1": sum(1 for v in depth.values() if v == bfs.depth - 1),
                      "expanded": bfs.nodes_expanded}
        out[name] = row
    return out


def exp_heuristic_variants():
    """h2 with Manhattan distances instead of maze distances; how many different values each heuristic takes."""
    out = {}
    for name in OFFICIAL:
        problem = load_problem(name)
        true_costs = optimal_costs_to_goal(problem)
        row = {}
        for cls in (FarthestFoodHeuristic, ManhattanMST, MazeMSTHeuristic):
            heuristic = cls(problem)
            report = analyse_heuristic(problem, heuristic, true_costs)
            result = a_star_search(problem, cls(problem))
            greedy = greedy_best_first_search(problem, cls(problem))
            row[cls.label] = {"admissible": report["admissible"], "consistent": report["consistent"],
                              "mean_ratio": report["mean_ratio"], "h_start": report["h_start"],
                              "distinct_values": len({heuristic(state) for state in true_costs}),
                              "astar_expanded": result.nodes_expanded, "astar_cost": result.path_cost,
                              "greedy_expanded": greedy.nodes_expanded, "greedy_cost": greedy.path_cost}
        out[name] = row
    return out


def exp_local_search():
    """SA / GA / HC variants on the main layout, on the evaluation seeds and on the tuning seeds."""
    problem = load_problem("large")
    tour = TourProblem(problem)
    optimum = uniform_cost_search(problem).path_cost
    out = {"optimum": optimum}

    def sa(**changes):
        params = dict(SA_PARAMS, **changes)
        return lambda seed: simulated_annealing(tour, seed=seed, record_history=False, **params)

    def ga(**changes):
        params = dict(GA_PARAMS, **changes)
        return lambda seed: genetic_algorithm(tour, seed=seed, record_history=False, **params)

    def hc(**options):
        return lambda seed: hill_climbing(tour, seed=seed, record_history=False, **options)

    variants = {
        "SA final": sa(),
        "SA cooling 0.9": sa(cooling_rate=0.9),
        "SA cooling 0.95": sa(cooling_rate=0.95),
        "SA cooling 0.999": sa(cooling_rate=0.999),
        "SA start 1": sa(start_temperature=1.0),
        "SA start 100": sa(start_temperature=100.0),
        "SA frozen": sa(start_temperature=0.001, end_temperature=0.00001),   # same 919 iterations, T ~ 0
        "GA final": ga(),
        "GA no mutation": ga(mutation_rate=0.0),
        "GA no crossover": ga(crossover_rate=0.0),
        "GA no mutation, no crossover": ga(mutation_rate=0.0, crossover_rate=0.0),
        "GA elite 2": ga(elite_count=2),
        "GA population 10": ga(population_size=10),
        "HC plain": hc(),
        "HC sideways 5": hc(max_sideways=5),
        "HC sideways 20": hc(max_sideways=20),
        "HC sideways 100": hc(max_sideways=100),
        "HC 9 restarts": hc(restarts=9),
    }
    for label, run in variants.items():
        out[label] = {"eval": score(run, EVAL_SEEDS, optimum), "tuning": score(run, TUNING_SEEDS, optimum)}
    for name in ("small", "medium"):                       # sideways moves on the other layouts
        other = TourProblem(load_problem(name))
        best = uniform_cost_search(load_problem(name)).path_cost
        out[f"HC plain/{name}"] = score(lambda seed: hill_climbing(other, seed=seed), EVAL_SEEDS, best)
        out[f"HC sideways 20/{name}"] = score(lambda seed: hill_climbing(other, seed=seed, max_sideways=20),
                                              EVAL_SEEDS, best)
    first, second = hill_climbing(tour, seed=5), hill_climbing(tour, seed=5)
    out["same_seed_same_result"] = (first.order, first.cost, first.history) == (second.order, second.cost, second.history)
    out["hc_costs_by_seed"] = [hill_climbing(tour, seed=seed).cost for seed in EVAL_SEEDS]
    out["hc_start_costs_by_seed"] = [hill_climbing(tour, seed=seed).history[0] for seed in EVAL_SEEDS]
    return out


def exp_restarts():
    """Random-restart hill climbing against the formula 1 - (1 - p)^(r + 1), on 5,000 other seeds."""
    problem = load_problem("large")
    tour = TourProblem(problem)
    optimum = uniform_cost_search(problem).path_cost
    orders = list(itertools.permutations(range(problem.num_food)))
    cost = {order: tour.cost(order) for order in orders}
    stops = {}

    def stop_cost(order):                                  # cost at which plain hill climbing stops
        path = []
        while order not in stops:
            best, best_cost = None, cost[order]
            for neighbour in tour.neighbours(order):
                if cost[neighbour] < best_cost:
                    best, best_cost = neighbour, cost[neighbour]
            if best is None:
                stops[order] = cost[order]
                break
            path.append(order)
            order = best
        for visited in path:
            stops[visited] = stops[order]
        return stops[order]

    p = sum(stop_cost(order) == optimum for order in orders) / len(orders)
    seeds = range(20000, 25000)
    out = {"p_single_climb": round(p, 4), "seeds": len(seeds), "optimal_orders": sum(c == optimum for c in cost.values()),
           "orders": len(orders)}
    for restarts in (0, 1, 2, 4, 9):
        hits = sum(hill_climbing(tour, seed=seed, restarts=restarts, record_history=False).cost == optimum
                   for seed in seeds)
        out[str(restarts)] = {"measured": round(hits / len(seeds), 4),
                              "predicted": round(1 - (1 - p) ** (restarts + 1), 4)}
    # a GA without crossover and mutation can only return the best of its 30 random starting orders
    out["chance_optimal_order_in_30"] = round(1 - (1 - out["optimal_orders"] / len(orders)) ** 30, 4)
    return out


def exp_decoding():
    """The order -> plan decoding: orders that eat a pellet "in passing", number of different plans."""
    out = {}
    for name in OFFICIAL:
        problem = load_problem(name)
        tour = TourProblem(problem)
        orders = list(itertools.permutations(range(problem.num_food)))
        costs = {order: tour.cost(order) for order in orders}

        def naive(order):                      # walk to every pellet of the order, eaten or not
            total, here = 0, 0
            for pellet in order:
                total += tour.distance[here][pellet + 1]
                here = pellet + 1
            return total

        naive_costs = {order: naive(order) for order in orders}
        optimum = min(costs.values())
        best_orders = [order for order in orders if costs[order] == optimum]
        out[name] = {
            "orders": len(orders), "optimum": optimum, "naive_minimum": min(naive_costs.values()),
            "orders_with_skips": sum(1 for order in orders if len(tour.walked_legs(order)) < problem.num_food),
            "orders_where_naive_costs_more": sum(1 for order in orders if naive_costs[order] > costs[order]),
            "distinct_plans": len({tuple(tour.to_actions(order)) for order in orders}),
            "distinct_costs": len(set(costs.values())),
            "optimal_orders": len(best_orders),
            "optimal_plans": len({tuple(tour.to_actions(order)) for order in best_orders}),
            "optimal_eating_order": list(tour.eating_order(best_orders[0])),
            "distance_table_symmetric": all(tour.distance[a][b] == tour.distance[b][a]
                                            for a in range(len(tour.points)) for b in range(len(tour.points))),
            "neighbours": problem.num_food * (problem.num_food - 1) // 2,
        }
        if name == "large":
            order = (5, 3, 4, 1, 2, 6, 7, 0)             # where hill climbing stopped with seed 2
            assert hill_climbing(tour, seed=2).order == order
            out["large_example"] = {
                "order": list(order), "cost": costs[order], "eating_order": list(tour.eating_order(order)),
                "walked_targets": [b - 1 for _, b in tour.walked_legs(order)],
                "equal_neighbours": sum(1 for n in tour.neighbours(order) if costs[n] == costs[order]),
                "better_neighbours": sum(1 for n in tour.neighbours(order) if costs[n] < costs[order]),
                "steps": len(tour.to_actions(order)),
                "danger_entries": danger_entries(problem, tour.to_actions(order)),
            }
    return out


def exp_python_details():
    """Small facts about the code: heap entries without a tie-breaker, the length of an SA run."""
    out = {}
    a, b = Node("x"), Node("y")
    try:
        heapq.heappush([(3, a)], (3, b))                  # equal costs and no tie-breaker: Nodes get compared
        out["heap_without_counter"] = "no error"
    except TypeError as error:
        out["heap_without_counter"] = f"TypeError: {error}"
    start, rate, end = (SA_PARAMS[key] for key in ("start_temperature", "cooling_rate", "end_temperature"))
    out["sa_iterations_formula"] = math.ceil(math.log(end / start) / math.log(rate))
    out["sa_halving_iterations"] = round(math.log(0.5) / math.log(rate), 1)
    out["sa_iterations_until_T1"] = math.ceil(math.log(1.0 / start) / math.log(rate))
    return out


EXPERIMENTS = {
    "tour": exp_tour, "model": exp_model, "paths": exp_paths, "danger_cost": exp_danger_cost,
    "action_order": exp_action_order, "goal_test": exp_goal_test, "dfs": exp_dfs_variants, "ids": exp_ids,
    "extra_pellet": exp_extra_pellet, "unreachable": exp_unreachable, "weighted": exp_weighted,
    "reopen": exp_reopen, "f_census": exp_f_census, "heuristic_variants": exp_heuristic_variants,
    "local": exp_local_search, "restarts": exp_restarts, "decoding": exp_decoding, "python": exp_python_details,
}


def run_all(only=None, quiet=False):
    """Run the experiments (all, or the named ones) and return {name: results}."""
    results = {}
    for key, experiment in EXPERIMENTS.items():
        if only and key not in only:
            continue
        started = time.perf_counter()
        results[key] = experiment()
        if not quiet:
            print(f"[{key}: {time.perf_counter() - started:.1f} s]", file=sys.stderr)
    return results


# --------------------------------------------------------------------------------------
# Readable output
# --------------------------------------------------------------------------------------
def show(value, indent=0, key=None):
    """Print nested results compactly: one line per group of plain values."""
    pad = " " * indent
    if isinstance(value, dict):
        plain = {k: v for k, v in value.items() if not isinstance(v, dict)}
        nested = {k: v for k, v in value.items() if isinstance(v, dict)}
        if key is not None and not nested:
            print(f"{pad}{key}: " + ", ".join(f"{k}={v}" for k, v in plain.items()))
            return
        if key is not None:
            print(f"{pad}{key}:")
        for k, v in plain.items():
            text = str(v)
            if "\n" in text:
                print(f"{pad}  {k}:")
                for line in text.split("\n"):
                    print(f"{pad}      {line}")
            else:
                print(f"{pad}  {k} = {text}")
        for k, v in nested.items():
            show(v, indent + 2, k)
    else:
        print(f"{pad}{key} = {value}")


def main():
    arguments = sys.argv[1:]
    if "--list" in arguments:
        for key, experiment in EXPERIMENTS.items():
            print(f"{key:20s} {experiment.__doc__.strip().splitlines()[0]}")
        return
    json_file = None
    if "--json" in arguments:
        position = arguments.index("--json")
        json_file = arguments[position + 1]
        del arguments[position:position + 2]
    unknown = [name for name in arguments if name not in EXPERIMENTS]
    if unknown:
        sys.exit(f"Unknown experiment(s): {', '.join(unknown)}. Use --list.")
    results = run_all(arguments or None)
    for key, value in results.items():
        print("=" * 100)
        print(f"{key}: {EXPERIMENTS[key].__doc__.strip().splitlines()[0]}")
        print("=" * 100)
        show(value)
        print()
    if json_file:
        Path(json_file).write_text(json.dumps(results, indent=1), encoding="utf-8")
        print(f"Raw numbers written to {json_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
