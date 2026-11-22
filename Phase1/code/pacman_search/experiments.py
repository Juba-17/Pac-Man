"""
experiments.py
==============
Helpers for measuring the algorithms and for writing the result tables.

Every number in the report comes from these functions:

measure_time         running time: the fastest of several repeated runs
measure_peak_memory  peak amount of memory allocated during one run (tracemalloc)
evaluate_search      one complete measurement of one search algorithm on one maze
step_cost_tradeoff   exact answer to "is the plan with the fewest steps also the cheapest?"
state_graph_profile  shape of the state graph (states per depth, branching factor, ...)
write_csv / markdown_table / save_json   output helpers
"""

import argparse
import csv
import gc
import heapq
from collections import deque
import json
import platform
import statistics
import sys
import tracemalloc
from typing import NamedTuple

# Short letters used to print a solution path compactly, e.g. "RRDDLU".
ACTION_LETTER = {"UP": "U", "RIGHT": "R", "DOWN": "D", "LEFT": "L"}


class Timing(NamedTuple):
    """Result of measure_time(); every time is in milliseconds."""
    best: float        # fastest run - the value reported as "running time"
    median: float
    mean: float
    std: float         # sample standard deviation of the runs
    runs: int          # how many runs were made


def actions_to_string(actions):
    """['RIGHT', 'RIGHT', 'DOWN'] -> 'RRD'."""
    return "".join(ACTION_LETTER[action] for action in actions)


def positive_int(text):
    """argparse type: an integer that is at least 1."""
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def measure_time(run, repeats=20, max_seconds=2.0):
    """Call run() repeatedly and return a Timing (best, median, mean, std, runs) in milliseconds.

    `run` must return an object with a `runtime_sec` attribute (SearchResult does). It is
    called `repeats` times, but a slow algorithm is stopped early: once the runs have
    taken `max_seconds` in total, no further run is started (this early stop never happens
    before 3 runs have been made). The algorithms are deterministic, so every run does
    exactly the same work.

    The FASTEST run is the value we report. Whatever disturbs a run - another program,
    the operating system moving the process to a slower CPU core, a hot processor slowing
    itself down - can only make it slower, never faster, so the fastest run is the one
    that is closest to the true cost of the algorithm. (On our laptop identical runs of
    BFS took anything between 4.7 and 13 ms, a factor of almost three.) The documentation
    of Python's `timeit` module gives the same advice. The median, the mean and the
    standard deviation are returned as well and are stored in the result tables.

    Python's garbage collector is switched off while a run is being timed (`timeit` does
    the same), otherwise a collection that happens to start in the middle of a run would
    be charged to the algorithm.
    """
    times_ms = []
    while len(times_ms) < repeats:
        if len(times_ms) >= 3 and sum(times_ms) >= max_seconds * 1000.0:
            break
        gc.collect()                       # start every run from a clean heap
        gc.disable()
        try:
            times_ms.append(run().runtime_sec * 1000.0)
        finally:
            gc.enable()
    spread = statistics.stdev(times_ms) if len(times_ms) > 1 else 0.0
    return Timing(min(times_ms), statistics.median(times_ms), statistics.mean(times_ms), spread,
                  len(times_ms))


def measure_peak_memory(run):
    """Peak memory allocated by Python objects while run() executes, in KiB.

    tracemalloc slows the program down, so this is done in a separate run and never
    during the timing runs. Note that the figure depends on how Python stores things (a
    `set` reserves memory in big jumps), so it is a rough indication; "max nodes in
    memory" is the measure that can be compared with the theory.
    """
    gc.collect()
    tracemalloc.start()
    try:
        run()
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak_bytes / 1024.0


def evaluate_search(problem, label, search_fn, repeats=20):
    """Measure one search algorithm on one problem.

    Returns (row, result):
      row     dictionary with every measurement (one line of the result tables)
      result  the SearchResult of one ordinary run (solution path, counters)

    No trace is recorded here. The traced runs needed for the pictures are made later by
    the run scripts, after all timings: a trace keeps hundreds of thousands of nodes alive,
    and that much data in memory makes the timings of whatever runs next slow and noisy.
    """
    timing = measure_time(lambda: search_fn(problem), repeats)
    peak_kib = measure_peak_memory(lambda: search_fn(problem))
    result = search_fn(problem)

    # Safety net: replay the returned plan in the problem model and compare the cost.
    if result.found:
        states, replayed_cost = problem.execute(result.actions)
        assert problem.is_goal(states[-1]), f"{label}: returned plan does not reach the goal"
        assert replayed_cost == result.path_cost, f"{label}: reported cost differs from replayed cost"

    row = {
        "layout": problem.name,
        "algorithm": label,
        "found": result.found,
        "path_cost": result.path_cost,
        "steps": result.depth,
        "nodes_generated": result.nodes_generated,
        "nodes_expanded": result.nodes_expanded,
        "max_frontier": result.max_frontier_size,
        "max_nodes_in_memory": result.max_nodes_in_memory,
        "time_ms": round(timing.best, 3),              # the reported running time (fastest run)
        "time_median_ms": round(timing.median, 3),
        "time_mean_ms": round(timing.mean, 3),
        "time_std_ms": round(timing.std, 3),
        "time_runs": timing.runs,
        "peak_memory_kib": round(peak_kib, 1),
        "solution": actions_to_string(result.actions),
    }
    return row, result


def step_cost_tradeoff(problem):
    """Is the plan with the fewest steps also the cheapest one? An exact answer.

    Runs a uniform-cost search over the full state space twice, with a two-part cost:
      (steps, cost)  -> the fewest steps, and among all plans with that many steps the cheapest
      (cost, steps)  -> the lowest cost, and among all plans with that cost the shortest
    The trade-off is genuine when even the cheapest fewest-step plan costs more than the
    optimum.
    """
    def best(steps_first):
        start = problem.initial_state
        best_key = {start: (0, 0)}
        frontier = [((0, 0), 0, start)]
        counter = 1
        while frontier:
            key, _, state = heapq.heappop(frontier)
            if key > best_key[state]:
                continue
            if problem.is_goal(state):
                return key
            for _, child, cost in problem.successors(state):
                new_key = (key[0] + 1, key[1] + cost) if steps_first else (key[0] + cost, key[1] + 1)
                if child not in best_key or new_key < best_key[child]:
                    best_key[child] = new_key
                    heapq.heappush(frontier, (new_key, counter, child))
                    counter += 1
        return None

    fewest_steps, cost_of_shortest = best(steps_first=True)
    optimal_cost, steps_of_cheapest = best(steps_first=False)
    return {
        "layout": problem.name,
        "fewest_steps": fewest_steps,
        "cheapest_cost_with_fewest_steps": cost_of_shortest,
        "optimal_cost": optimal_cost,
        "fewest_steps_at_optimal_cost": steps_of_cheapest,
        "genuine_tradeoff": cost_of_shortest > optimal_cost,
    }


def state_graph_profile(problem, solution_depth, optimal_cost):
    """Shape of the reachable state graph - the numbers the analysis of the report uses to
    explain how much work the algorithms do.

    One breadth-first sweep (no goal test) gives the depth of every state, i.e. the fewest
    steps needed to reach it; one uniform-cost sweep gives its cheapest cost.

      states_per_depth                 number of states at depth 0, 1, 2, ...
      average_successors               average number of successors per state (branching factor b)
      states_shallower_than_solution   states of depth < solution_depth: BFS expands at most these
      states_cheaper_than_optimum      states that can be reached for less than optimal_cost:
                                       UCS has to expand all of these
      restart_only_expansions          work of an ideal iterative deepening search that expands
                                       every state within the limit exactly ONCE per iteration:
                                       in the iteration with limit L it expands the states of
                                       depth < L, for L = 0 .. solution_depth-1 (the iterations
                                       that find no goal). Whatever IDS expands beyond this
                                       comes from reaching the same state along different paths.
    """
    start = problem.initial_state
    depth = {start: 0}
    queue = deque([start])
    successor_count = 0
    while queue:
        state = queue.popleft()
        children = problem.successors(state)
        successor_count += len(children)
        for _, child, _ in children:
            if child not in depth:
                depth[child] = depth[state] + 1
                queue.append(child)

    cheapest = {start: 0}                       # uniform-cost sweep over the same states
    frontier = [(0, 0, start)]
    counter = 1
    while frontier:
        cost, _, state = heapq.heappop(frontier)
        if cost > cheapest[state]:
            continue
        for _, child, step in problem.successors(state):
            if child not in cheapest or cost + step < cheapest[child]:
                cheapest[child] = cost + step
                heapq.heappush(frontier, (cost + step, counter, child))
                counter += 1

    levels = [0] * (max(depth.values()) + 1)
    for value in depth.values():
        levels[value] += 1
    return {
        "layout": problem.name,
        "states": len(depth),
        "average_successors": round(successor_count / len(depth), 3),
        "deepest_level": len(levels) - 1,
        "largest_level": max(levels),
        "solution_depth": solution_depth,
        "optimal_cost": optimal_cost,
        "states_shallower_than_solution": sum(levels[:solution_depth]),
        "states_cheaper_than_optimum": sum(1 for cost in cheapest.values() if cost < optimal_cost),
        "restart_only_expansions": sum(sum(levels[:limit]) for limit in range(solution_depth)),
        "states_per_depth": " ".join(str(count) for count in levels),
    }


def environment_info():
    """Where the experiments were run (stored next to the results for the report)."""
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "system": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def write_csv(path, rows, columns=None):
    """Write a list of dictionaries as a CSV file (columns default to the keys of the first row).
    Nothing is written when there are no rows."""
    if not rows:
        return
    columns = columns or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_json(path, data):
    """Write `data` (dictionaries, lists, numbers, strings) as an indented JSON file."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def format_value(value):
    """Readable formatting for table cells."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def markdown_table(rows, columns, headers=None):
    """Build a Markdown table from a list of dictionaries."""
    headers = headers or columns
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(format_value(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)


def text_table(rows, columns, headers=None):
    """Plain-text table with aligned columns (printed in the terminal by main.py)."""
    headers = headers or columns
    cells = [[format_value(row.get(col)) for col in columns] for row in rows]
    widths = [max([len(headers[i])] + [len(line[i]) for line in cells]) for i in range(len(columns))]
    out = ["  ".join(headers[i].ljust(widths[i]) for i in range(len(columns)))]
    out.append("  ".join("-" * widths[i] for i in range(len(columns))))
    for line in cells:
        out.append("  ".join(line[i].rjust(widths[i]) for i in range(len(columns))))
    return "\n".join(out)
