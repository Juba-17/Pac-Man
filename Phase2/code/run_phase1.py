"""
run_phase1.py - reproduces every Phase I result: tables, figures and animations.

    python run_phase1.py              full run (about one minute)
    python run_phase1.py --quick      fewer timing repeats, no animations; results go to
                                      results/phase1_quick so a full run is never overwritten
    python run_phase1.py --out DIR    write the results somewhere else

What it does
------------
1. Runs BFS, DFS, UCS and IDS on the three official layouts (small, medium, large) and
   records: solution path, path cost, nodes generated, nodes expanded, maximum frontier
   size, maximum nodes in memory, running time (fastest of repeated runs) and peak memory.
2. Counts the state space of every layout (upper bound, valid, reachable).
3. Computes exactly how the fewest-steps plans and the cheapest plans differ, and the
   shape of the state graph (states per depth, branching factor) used in the analysis.
4. Compares the two versions of IDS (textbook version and memo-table version).
5. Draws the figures: layouts, explored states + final path, search trees, bar charts,
   frontier growth, IDS iterations, scaling.
6. Saves animated GIFs of the four searches on the main layout (full run only).

Needs Matplotlib (pip install -r requirements.txt). All algorithms are deterministic, so
every run gives the same paths, costs and node counts; only the running times and the
peak-memory readings vary slightly.
"""

import argparse
import os
import time

from pacman_search import visualize as viz
from pacman_search.experiments import (
    actions_to_string, environment_info, evaluate_search, markdown_table, measure_time, positive_int,
    save_json, state_graph_profile, step_cost_tradeoff, write_csv)
from pacman_search.layouts import DEFAULT_LAYOUT, OFFICIAL_LAYOUTS, load_problem
from pacman_search.uninformed import UNINFORMED_ALGORITHMS, iterative_deepening_search

ALGORITHM_LABELS = {"bfs": "BFS", "dfs": "DFS", "ucs": "UCS", "ids": "IDS"}

# The long IDS runs heat the processor, and on our laptop it then ran slower for a moment.
# A short pause before the measurements of each layout keeps this out of the timings.
COOL_DOWN_SECONDS = 3.0


def run_layout(problem, repeats):
    """Measure the four algorithms on one layout. Returns (rows, results)."""
    rows, results = [], {}
    for key, search in UNINFORMED_ALGORITHMS.items():
        label = ALGORITHM_LABELS[key]
        row, result = evaluate_search(problem, label, search, repeats)
        rows.append(row)
        results[label] = result
        print("   ", result.summary())
    # Optimality flags: UCS is cost-optimal and BFS is step-optimal by construction.
    best_cost = next(r["path_cost"] for r in rows if r["algorithm"] == "UCS")
    fewest_steps = next(r["steps"] for r in rows if r["algorithm"] == "BFS")
    for row in rows:
        row["optimal_cost"] = best_cost
        row["cost_optimal"] = row["path_cost"] == best_cost
        row["step_optimal"] = row["steps"] == fewest_steps
    return rows, results


def compare_ids_variants(problem, repeats, textbook_result, textbook_time_ms):
    """The textbook IDS (cycle check on the current path only) versus IDS with a memo table.

    The textbook version is the "IDS" of the main measurements, so its result and its
    running time are taken from there; only the memo-table variant is run and timed here.
    """
    def run_with_memo():
        return iterative_deepening_search(problem, use_memo=True)

    memo_time_ms = measure_time(run_with_memo, repeats).best
    rows = []
    for variant, result, time_ms in (("IDS (textbook)", textbook_result, textbook_time_ms),
                                     ("IDS with memo table", run_with_memo(), memo_time_ms)):
        rows.append({
            "layout": problem.name,
            "variant": variant,
            "deepest_limit": result.extra["iterations"][-1]["limit"],
            "steps": result.depth,
            "path_cost": result.path_cost,
            "nodes_expanded": result.nodes_expanded,
            "nodes_generated": result.nodes_generated,
            "max_frontier": result.max_frontier_size,
            "max_nodes_in_memory": result.max_nodes_in_memory,
            "time_ms": round(time_ms, 3),
        })
    return rows


def main():
    """Measure everything, write the tables, then draw the figures and the animations."""
    parser = argparse.ArgumentParser(description="Run all Phase I experiments.")
    parser.add_argument("--out", help="output folder (default: results/phase1, or results/phase1_quick with --quick)")
    parser.add_argument("--quick", action="store_true", help="fast run: 3 timing repeats, no animations")
    parser.add_argument("--repeats", type=positive_int, default=20,
                        help="timing repeats per algorithm (default 20; --quick uses 3)")
    args = parser.parse_args()
    repeats = 3 if args.quick else args.repeats
    out = args.out or os.path.join("results", "phase1_quick" if args.quick else "phase1")
    figures = os.path.join(out, "figures")
    animations = os.path.join(out, "animations")
    os.makedirs(figures, exist_ok=True)

    all_rows, sizes, tradeoffs, profiles, ids_rows, variant_rows, solutions = [], [], [], [], [], [], []
    problems = {}

    # ------------------------------------------------------------------ measurements
    # All timings are taken here, before any traced run exists (see evaluate_search).
    for name in OFFICIAL_LAYOUTS:
        problem = load_problem(name)
        problems[name] = problem
        print(f"\n=== {problem.describe()}")
        if not args.quick:
            time.sleep(COOL_DOWN_SECONDS)
        rows, results = run_layout(problem, repeats)
        all_rows += rows
        sizes.append({"layout": name, "grid": f"{problem.height}x{problem.width}",
                      "ghosts": len(problem.ghosts), "danger_cells": len(problem.danger_cells),
                      **problem.state_space_report()})
        tradeoffs.append(step_cost_tradeoff(problem))
        profiles.append(state_graph_profile(problem, results["BFS"].depth, results["UCS"].path_cost))
        for iteration in results["IDS"].extra["iterations"]:
            ids_rows.append({"layout": name, **iteration})
        ids_time_ms = next(row["time_ms"] for row in rows if row["algorithm"] == "IDS")
        variant_rows += compare_ids_variants(problem, repeats, results["IDS"], ids_time_ms)
        for label, result in results.items():
            solutions.append(f"[{name}] {label}: cost {result.path_cost}, {result.depth} moves\n"
                             f"{actions_to_string(result.actions)}\n{problem.render(result.states)}\n")

    # ------------------------------------------------------------------ tables
    metric_columns = ["layout", "algorithm", "path_cost", "steps", "nodes_generated", "nodes_expanded",
                      "max_frontier", "max_nodes_in_memory", "time_ms", "time_median_ms", "time_mean_ms",
                      "time_std_ms", "time_runs", "peak_memory_kib", "cost_optimal", "step_optimal",
                      "solution"]
    write_csv(os.path.join(out, "metrics.csv"), all_rows, metric_columns)
    write_csv(os.path.join(out, "state_space.csv"), sizes)
    write_csv(os.path.join(out, "tradeoff.csv"), tradeoffs)
    write_csv(os.path.join(out, "state_graph.csv"), profiles)
    write_csv(os.path.join(out, "ids_iterations.csv"), ids_rows)
    write_csv(os.path.join(out, "ids_variants.csv"), variant_rows)
    with open(os.path.join(out, "solutions.txt"), "w", encoding="utf-8") as handle:
        handle.write("Solution paths (U = up, R = right, D = down, L = left; '*' = visited cell)\n\n")
        handle.write("\n".join(solutions))
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as handle:
        handle.write("# Phase I results\n\n## State-space size\n\n")
        handle.write(markdown_table(sizes, list(sizes[0].keys())) + "\n")
        handle.write("\n## Fewest steps versus lowest cost (exact)\n\n")
        handle.write(markdown_table(tradeoffs, list(tradeoffs[0].keys())) + "\n")
        handle.write("\n## Shape of the state graph\n\n")
        handle.write(markdown_table(profiles, list(profiles[0].keys())[:-1]) + "\n")
        for name in OFFICIAL_LAYOUTS:
            handle.write(f"\n## Layout: {name}\n\n")
            handle.write(markdown_table([r for r in all_rows if r["layout"] == name], metric_columns[1:-1]) + "\n")
        handle.write("\n## IDS: textbook version versus memo table\n\n")
        handle.write(markdown_table(variant_rows, list(variant_rows[0].keys())) + "\n")
    save_json(os.path.join(out, "results.json"), {
        "environment": environment_info(), "timing_repeats": repeats, "state_space": sizes,
        "tradeoff": tradeoffs, "state_graph": profiles, "metrics": all_rows,
        "ids_iterations": ids_rows, "ids_variants": variant_rows})

    # ------------------------------------------------------------------ figures and animations
    print("\nDrawing figures ...")
    tiny = load_problem("tiny")
    viz.plot_layouts([tiny] + [problems[n] for n in OFFICIAL_LAYOUTS], os.path.join(figures, "layouts.png"))
    for name in OFFICIAL_LAYOUTS:
        problem = problems[name]
        rows = [r for r in all_rows if r["layout"] == name]
        # the same searches again, this time recording which nodes were expanded
        traced = [search(problem, trace=True) for search in UNINFORMED_ALGORITHMS.values()]
        viz.plot_explored(problem, traced, os.path.join(figures, f"explored_{name}.png"),
                          title=f"Explored states and returned path - '{name}' layout")
        viz.plot_metric_bars(rows, os.path.join(figures, f"metrics_{name}.png"),
                             title=f"Uninformed search on the '{name}' layout",
                             optimal_cost=rows[0]["optimal_cost"])
        viz.plot_frontier_history(traced, os.path.join(figures, f"frontier_{name}.png"),
                                  title=f"Frontier size during the search - '{name}' layout")
        viz.plot_ids_iterations(traced[-1], os.path.join(figures, f"ids_iterations_{name}.png"))
        if name == DEFAULT_LAYOUT and not args.quick:
            print("Rendering animations ...")
            os.makedirs(animations, exist_ok=True)
            for result in traced:
                viz.animate_search(problem, result, os.path.join(
                    animations, f"{result.algorithm.lower()}_{DEFAULT_LAYOUT}.gif"))
    reachable = {s["layout"]: s["reachable"] for s in sizes}
    points = {label: [(reachable[r["layout"]], r["nodes_expanded"])
                      for r in all_rows if r["algorithm"] == label]
              for label in ALGORITHM_LABELS.values()}
    viz.plot_scaling(points, os.path.join(figures, "scaling.png"),
                     layout_names={s["reachable"]: s["layout"] for s in sizes})

    # search trees on the tiny layout (small enough to draw completely)
    tiny_results = {key: search(tiny, trace=True) for key, search in UNINFORMED_ALGORITHMS.items()}
    for key, result in tiny_results.items():
        viz.plot_search_tree(tiny, result, os.path.join(figures, f"tree_{key}_tiny.png"))
    viz.plot_search_trees(tiny, [tiny_results[key] for key in ("bfs", "dfs", "ucs")],
                          os.path.join(figures, "trees_tiny.png"))
    viz.plot_ids_trees(tiny, tiny_results["ids"], os.path.join(figures, "tree_ids_limits_tiny.png"))

    print(f"\nDone. Tables are in {out}, figures in {figures}.")


if __name__ == "__main__":
    main()
