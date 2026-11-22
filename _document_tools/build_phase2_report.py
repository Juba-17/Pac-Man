"""Builds Phase2_Report.docx from the Phase II results (results/phase2 of the Phase2 code folder).

Every number in the text is read from results.json or recomputed from the project code, and
the facts the prose relies on are asserted, so the report cannot silently drift from the data.
"""
import json
import math
import sys
from pathlib import Path

from docbuilder import Doc
from team import title_page

PROJECT = Path(__file__).resolve().parent.parent
CODE = PROJECT / "Phase2" / "code"
RESULTS = Path(sys.argv[1]) if len(sys.argv) > 1 else CODE / "results" / "phase2"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else CODE.parent / "report" / "Phase2_Report.docx"
FIG = RESULTS / "figures"
PHASE1 = PROJECT / "Phase1" / "code" / "results" / "phase1" / "results.json"

sys.path.insert(0, str(CODE))
from pacman_search.layouts import load_problem  # noqa: E402

data = json.loads((RESULTS / "results.json").read_text(encoding="utf-8"))
phase1 = json.loads(PHASE1.read_text(encoding="utf-8"))
env = data["environment"]
LAYOUTS = ["small", "medium", "large"]
L = "large"
SEARCH = {(r["layout"], r["algorithm"]): r for r in data["search_metrics"]}
LOCAL = {(r["layout"], r["algorithm"]): r for r in data["local_search_summary"]}
HEUR = {(r["layout"], r["heuristic"]): r for r in data["heuristic_analysis"]}
LAND = {r["layout"]: r for r in data["landscape"]}
COMP = {name: [r for r in data["comparison"] if r["layout"] == name] for name in LAYOUTS}
OPT = data["optimum"]
SA, GA = data["sa_parameters"], data["ga_parameters"]
RUNS = len(data["seeds"])
TUNE_RUNS = data["tuning_runs"]
ONE = data["tuning_one_at_a_time"]
INFORMED = ["Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)"]
UNINFORMED = ["BFS", "DFS", "UCS", "IDS"]
LOCALS = ["Hill Climbing", "Simulated Annealing", "Genetic Algorithm"]
HC_RR = f"Hill Climbing ({data['hc_restarts']} restarts)"
BASE = data["baseline_label"]
BASE_N = data["baseline_evaluations"]
SCALE_I = {r["pellets"]: r for r in data["scaling_instances"]}
SCALE_M = {(r["pellets"], r["method"]): r for r in data["scaling_methods"]}
PELLETS = sorted(SCALE_I)
SCALE_METHODS = ["Random sampling", "Hill Climbing (restarts)", "Simulated Annealing", "Genetic Algorithm"]
PROBLEMS = {name: load_problem(name) for name in LAYOUTS}
REACH = {name: PROBLEMS[name].count_reachable_states() for name in LAYOUTS}
LETTER = {"U": "UP", "R": "RIGHT", "D": "DOWN", "L": "LEFT"}


def s(layout, algorithm, key):
    return SEARCH[(layout, algorithm)][key]


def ls(layout, algorithm, key):
    return LOCAL[(layout, algorithm)][key]


def n(value, digits=0):
    if value is None:
        return "-"
    if isinstance(value, float) and digits:
        return f"{value:,.{digits}f}"
    return f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)


def ms(value):
    """A running time in milliseconds with about three significant digits."""
    if value < 1:
        return f"{value:.3f}"
    if value < 10:
        return f"{value:.2f}"
    if value < 100:
        return f"{value:.1f}"
    return f"{value:,.0f}"


def danger_entries(layout, algorithm):
    problem = PROBLEMS[layout]
    states, cost = problem.execute([LETTER[c] for c in s(layout, algorithm, "solution")])
    assert cost == s(layout, algorithm, "path_cost")
    return sum(1 for state in states[1:] if state.pos in problem.danger_cells)


def effective_branching_factor(generated, depth):
    """b* such that 1 + b* + b*^2 + ... + b*^depth = generated + 1 (bisection)."""
    low, high = 1.0000001, 4.0
    for _ in range(80):
        mid = (low + high) / 2
        total = (mid ** (depth + 1) - 1) / (mid - 1)
        if total < generated + 1:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def pct(row):
    """Share of the tuning runs that reached the optimum, in percent (one decimal)."""
    return round(100 * row["hits"] / row["runs"], 1)


def random_share(evaluations, layout=L):
    """Probability (percent) that `evaluations` random orders contain an optimal one."""
    share = LAND[layout]["optimal_orders"] / LAND[layout]["orders"]
    return 100 * (1 - (1 - share) ** evaluations)


def above(pellets, method):
    return SCALE_M[(pellets, method)]["mean_percent_above_optimum"]


def big(value):
    """A large count: with thousands separators up to a billion, else as m x 10^e."""
    if value < 10 ** 9:
        return f"{value:,}"
    exponent = len(str(value)) - 1
    return f"{value / 10 ** exponent:.1f} x 10^{{{exponent}}}"


def tune(algorithm, parameter):
    """Rows of the one-parameter-at-a-time study, in the order they were run."""
    return [r for r in ONE if r["algorithm"] == algorithm and r["parameter"] == parameter]


def pct_list(rows, key="value"):
    """'82% (2), 92% (1), ...' - share of optimal runs with the parameter value in brackets."""
    return ", ".join(f"{pct(r):.0f}% ({r[key]:g})" for r in rows)


def grid(rows, fixed_key, fixed_value, vary_key):
    return sorted((r for r in rows if r[fixed_key] == fixed_value), key=lambda r: r[vary_key])


opt = OPT[L]
ucs_exp, a1_exp, a2_exp = (s(L, a, "nodes_expanded") for a in ("UCS", "A* (h1)", "A* (h2)"))
g1, g2 = SEARCH[(L, "Greedy (h1)")], SEARCH[(L, "Greedy (h2)")]
a2 = SEARCH[(L, "A* (h2)")]
hc, sa, ga, rr = (LOCAL[(L, a)] for a in LOCALS + [HC_RR])
base = LOCAL[(L, BASE)]
h1L, h2L = HEUR[(L, "h1")], HEUR[(L, "h2")]
uphill = round(LAND[L]["mean_uphill_swap"], 1)
land = LAND[L]
k_large = PROBLEMS[L].num_food
g1_danger, g2_danger = danger_entries(L, "Greedy (h1)"), danger_entries(L, "Greedy (h2)")
sa_grid_cool = grid(data["tuning_sa"], "start_temperature", SA["start_temperature"], "cooling_rate")
sa_grid_temp = grid(data["tuning_sa"], "cooling_rate", SA["cooling_rate"], "start_temperature")
ga_grid_pop = grid(data["tuning_ga"], "mutation_rate", GA["mutation_rate"], "population_size")
ga_grid_mut = grid(data["tuning_ga"], "population_size", GA["population_size"], "mutation_rate")
sa_used = next(r for r in sa_grid_cool if r["cooling_rate"] == SA["cooling_rate"])
ga_used = next(r for r in ga_grid_pop if r["population_size"] == GA["population_size"])
sa_slowest = sa_grid_cool[-1]
restarts = tune("HC", "restarts")
sideways = tune("HC", "max_sideways")
rr_tuned = next(r for r in restarts if r["value"] == data["hc_restarts"])
hc_tuned = next(r for r in restarts if r["value"] == 0)
hc_runs = [r for r in data["local_search_runs"] if r["layout"] == L and r["algorithm"] == "Hill Climbing"]
hc_worst_run = max(hc_runs, key=lambda r: r["cost"])
hc_error = 100 * math.sqrt(land["hc_success_probability"] * (1 - land["hc_success_probability"]) / RUNS)

# ---- Phase I results: the same algorithms measured in the Phase I session ----
P1 = {(r["layout"], r["algorithm"]): r for r in phase1["metrics"]}
time_gap, time_gap_row = 0.0, None
for key, row in P1.items():
    again = SEARCH[key]
    for field in ("path_cost", "steps", "nodes_generated", "nodes_expanded", "max_frontier",
                  "max_nodes_in_memory", "solution"):
        assert row[field] == again[field], (key, field)
    gap = abs(again["time_ms"] / row["time_ms"] - 1)
    if gap > time_gap:
        time_gap, time_gap_row = gap, key

# ---- facts the prose relies on: fail loudly if the experiments ever change them ----
for name in LAYOUTS:
    for h in ("h1", "h2"):
        assert HEUR[(name, h)]["admissible"] and HEUR[(name, h)]["consistent"], (name, h)
    assert HEUR[(name, "h1")]["h2_dominates_h1"]
    assert s(name, "A* (h1)", "path_cost") == s(name, "A* (h2)", "path_cost") == OPT[name]
    assert s(name, "A* (h2)", "nodes_expanded") < s(name, "A* (h1)", "nodes_expanded") < s(name, "UCS", "nodes_expanded")
    assert all(s(name, g, "path_cost") > OPT[name] for g in ("Greedy (h1)", "Greedy (h2)"))
    assert s(name, "Greedy (h2)", "steps") == s(name, "BFS", "steps")
    assert all(ls(name, a, "best") == OPT[name] for a in LOCALS)
    assert ls(name, "Simulated Annealing", "optimal_runs") == ls(name, "Genetic Algorithm", "optimal_runs") == RUNS
    assert LAND[name]["stop_orders_local_optimum"] == 0 and LAND[name]["starts_ending_in_local_optimum"] == 0
    assert ls(name, "Hill Climbing", "optimal_runs") < RUNS
assert g2["nodes_expanded"] < a2_exp < a1_exp < g1["nodes_expanded"] < ucs_exp
assert g2["nodes_expanded"] <= 1.2 * g2["steps"] and g1["nodes_expanded"] > 2 * a1_exp
assert 0.4 < land["hc_success_probability"] < 0.5
assert abs(hc["optimal_runs"] / RUNS - land["hc_success_probability"]) < 2 * hc_error / 100
assert ga["run_time_ms"] > 2 * sa["run_time_ms"]
assert RUNS - 1 <= rr["optimal_runs"] <= RUNS and pct(rr_tuned) >= 99
assert 95 <= pct(sa_used) < 100 and 95 <= pct(ga_used) < 100
assert pct(sa_used) < random_share(sa_used["evaluations"]) and pct(ga_used) < random_share(ga_used["evaluations"])
assert all(LOCAL[(name, BASE)]["optimal_runs"] == RUNS for name in LAYOUTS)
assert pct(hc_tuned) > random_share(hc_tuned["evaluations"])
for name in LAYOUTS:
    assert not HEUR[(name, "h1")]["goal_below_start_value"] and HEUR[(name, "h2")]["goal_below_start_value"]
for k in PELLETS[1:]:
    assert above(k, "Hill Climbing (restarts)") < above(k, "Genetic Algorithm") < above(k, "Random sampling")
    assert above(k, "Simulated Annealing") < above(k, "Genetic Algorithm")
assert all(above(PELLETS[0], m) == 0 for m in SCALE_METHODS[1:])
assert above(PELLETS[-1], "Simulated Annealing") < above(PELLETS[-1], "Hill Climbing (restarts)")
assert SCALE_I[PELLETS[-1]]["astar_h2_time_ms"] < 200
# "a population of 100 for 99 generations": 100 x (99 + 1) evaluations, exactly the budget
assert data["scaling_budget"] == 10_000
assert all(SCALE_M[(k, "Genetic Algorithm")]["mean_evaluations"] == data["scaling_budget"] for k in PELLETS)
assert [r["value"] for r in tune("GA", "crossover_rate")] == [0.0, 0.5, 0.9, 1.0]
assert max(pct(r) for r in tune("GA", "crossover_rate")) - min(pct(r) for r in tune("GA", "crossover_rate")) <= 3
assert pct(tune("GA", "elite_count")[0]) >= max(pct(r) for r in tune("GA", "elite_count"))
assert pct(tune("GA", "elite_count")[0]) - pct(tune("GA", "elite_count")[-1]) > 5
assert pct(tune("GA", "tournament_size")[0]) > pct(tune("GA", "tournament_size")[-1])
assert pct(sideways[-1]) < pct(rr_tuned) and sideways[-1]["evaluations"] > 3 * rr_tuned["evaluations"]
assert s(L, "DFS", "time_ms") < g2["time_ms"] < hc["time_ms"] < a2["time_ms"] < sa["time_ms"] < ga["time_ms"]
assert s("small", "Greedy (h1)", "path_cost") > 1.7 * OPT["small"] and s("medium", "Greedy (h1)", "path_cost") > 2 * OPT["medium"]
assert all(s(name, "DFS", "path_cost") > OPT[name] for name in LAYOUTS)
assert 4.5 < sa_slowest["evaluations"] / sa_used["evaluations"] < 5.5
assert rr_tuned["evaluations"] < sa_used["evaluations"] <= ga_used["evaluations"]

doc = Doc()
doc.doc.sections[0].different_first_page_header_footer = True
title_page(doc, "Phase II Report", "Heuristic Search, Local Search and Comparison of All Methods",
           "December 2026")
doc.page_numbers()


def table(expected, *args, **kwargs):
    doc.table(*args, **kwargs)
    assert doc.table_no == expected, ("table number", doc.table_no, expected)


def figure(expected, *args, **kwargs):
    doc.figure(*args, **kwargs)
    assert doc.figure_no == expected, ("figure number", doc.figure_no, expected)


# numbers used in cross-references
(T_CHANGES, T_HEUR, T_VERIFY, T_INF_LARGE, T_INF_OTHER, T_FORM, T_LAND, T_PARAMS, T_LOCAL, T_SCALE_I,
 T_SCALE_M, T_ALL, T_ALL_SMALL, T_ALL_MEDIUM, T_PATHS) = range(1, 16)
(F_EFFECT, F_EXPLORED, F_SCALING, F_ROUTES, F_TUNE_SA, F_TUNE_GA, F_BUDGET, F_CONV, F_FINAL, F_TRACE,
 F_MAZES, F_SCALE_LOCAL, F_SUMMARY) = range(1, 14)

# =============================================================================== summary
doc.heading("Summary", 1)
doc.callout([
    "**Same problem, same model.** Pac-Man must eat all pellets in a ghost-guarded maze; a state is "
    "(position, food mask); entering a cell next to a ghost costs 5 instead of 1. The Phase I model is "
    "unchanged.",
    "**Two heuristics.** h1 = Manhattan distance to the farthest pellet; h2 = maze distance to the nearest "
    "pellet + minimum spanning tree over the remaining pellets. Both are admissible and consistent (proved, "
    f"and checked on every reachable state); h2 dominates h1 and reaches "
    f"{HEUR[(L, 'h2')]['mean_ratio'] * 100:.0f}% of the true remaining cost on average (h1: "
    f"{HEUR[(L, 'h1')]['mean_ratio'] * 100:.0f}%).",
    f"**Informed search (large layout).** A* returns the optimal cost {n(opt)} with both heuristics. It expands "
    f"{n(a1_exp)} nodes with h1 and only {n(a2_exp)} with h2, against {n(ucs_exp)} for UCS "
    f"({ucs_exp / a2_exp:.0f} times fewer). Greedy Best-First is not optimal (cost {n(g1['path_cost'])} and "
    f"{n(g2['path_cost'])}).",
    f"**Local search (large layout, {RUNS} seeds).** A solution is a priority order of the pellets. "
    f"Hill Climbing reaches the optimum in {hc['optimal_runs']} of {RUNS} runs; it "
    "stops on plateaus, not in true local optima. Simulated Annealing and the Genetic Algorithm reach the "
    f"optimum in all {RUNS} runs with about {n(round(sa['mean_evaluations'], -2))} evaluations each - but so "
    f"does drawing {n(BASE_N)} random orders; only the larger mazes of Section 4.6 show what these two "
    "methods add.",
    "**Best method for this problem:** A* with h2 - optimal, complete, and the fastest method that guarantees "
    "the optimum.",
])
doc.toc("1-2")

# =============================================================================== 1 intro
doc.heading("1. Problem Recap and Changes since Phase I", 1, new_page=True)
doc.heading("1.1 The problem model", 2)
doc.para(
    "We use exactly the search problem of Phase I. A state is a pair (pos, food): Pac-Man's cell and a "
    "bitmask of the pellets that are still uneaten. The initial state has all k bits set; the goal test is "
    "food = 0. The actions are UP, RIGHT, DOWN and LEFT (walls and ghost cells cannot be entered); moving "
    "into a pellet's cell clears its bit. A step costs 5 if it enters a cell directly next to a ghost and 1 "
    "otherwise. The three official layouts have "
    f"{n(REACH['small'])}, {n(REACH['medium'])} and {n(REACH['large'])} reachable states; the large layout "
    "(9x9 grid, 8 pellets) is the main instance.", align="justify")
doc.heading("1.2 Changes since Phase I", 2)
table(T_CHANGES,
      ["Item", "Change"],
      [
          ["Problem model", "None. State, initial state, goal test, actions, transition model and step costs "
                            "are unchanged."],
          ["Layouts", "None. The same tiny, small, medium and large layouts are used."],
          ["Phase I code", "Unchanged: `problem.py`, `layouts.py`, `search_core.py`, `uninformed.py`, "
                           "`experiments.py`, `visualize.py` and `run_phase1.py` are the files of the Phase I "
                           "submission."],
          ["Phase I results", "BFS, DFS, UCS and IDS were run again in the Phase II session, so that all the "
                              "running times in this report were measured together. Their paths, costs and "
                              "node counts are identical to the Phase I report; their running times differ "
                              f"from it by up to {time_gap * 100:.0f}% ({time_gap_row[1]} on the "
                              f"{time_gap_row[0]} layout), which is the normal variation between two sessions."],
          ["New code", "`heuristics.py` (h1, h2 and their exhaustive verification), `informed.py` (Greedy "
                       "Best-First, A*), `local_search.py` (Hill Climbing, Simulated Annealing, Genetic "
                       "Algorithm, and random sampling as a baseline), `scaling.py` (larger mazes for Section "
                       "4.6), `visualize_phase2.py`, `run_phase2.py`, `tests/test_phase2.py`; `main.py` now "
                       "offers all nine algorithms."],
          ["Measurements", "Same definitions as in Phase I: the running time of a search algorithm is the "
                           f"fastest of up to {data['timing_repeats']} identical runs [6], with the garbage "
                           "collector switched off and the process kept on one processor core. The time and "
                           "memory of an algorithm include what it prepares in advance: the distance tables "
                           "of h2 and of the local-search methods. A local-search run depends on its seed, so "
                           "every seeded run is timed separately (fastest of 3 identical repetitions) and the "
                           f"reported time is the mean over the {RUNS} seeds plus the preparation. Local search "
                           "is measured in objective-function evaluations instead of node expansions."],
          ["Environment", f"Python {env['python']} ({env['implementation']}) on {env['system']} "
                          f"({env['machine']}); `run_phase2.py` produces every table and figure of this "
                          "report."],
      ],
      widths_cm=[3.0, 13.6], caption="Changes since Phase I.", size=9.5, bold_first_col=True, stripe=False)

# =============================================================================== 2 heuristics
doc.heading("2. Heuristic Design", 1)
doc.para(
    "A heuristic h(s) estimates the cheapest cost of eating all the remaining pellets from state s. Below, "
    "F is the set of remaining pellets in s, Manhattan(a, b) is the grid distance between two cells without "
    "walls, d(a, b) is the true maze distance in steps (walls and ghosts respected), h*(s) is the true "
    "optimal remaining cost, and c is the cost of a step (1 or 5). Both heuristics count steps. The code "
    "multiplies the count by the cheapest step cost of the maze, which is 1 in our model, so that the "
    "heuristics would stay admissible if the costs were changed; we leave this factor out of the formulas. "
    "The definitions of admissibility, consistency and dominance are those of the textbook [1, 2].",
    align="justify")
doc.heading("2.1 The two heuristics", 2)
table(T_HEUR,
      ["", "h1: farthest-food Manhattan distance", "h2: nearest food + minimum spanning tree"],
      [
          ["Definition", "h1(s) = largest Manhattan(pos, p) over the pellets p in F; 0 when F is empty.",
           "h2(s) = smallest d(pos, p) over the pellets p in F  +  MST(F); 0 when F is empty. MST(F) is the "
           "weight of the minimum spanning tree that connects the pellets of F, with d as edge weight."],
          ["Idea", "Pac-Man must at least travel to the pellet that is farthest away.",
           "Pac-Man must first reach some pellet (at least the nearest one) and then link all remaining "
           "pellets together; the cheapest way to link a set of points is their MST."],
          ["Relaxed problem it solves exactly", "No walls, no ghost danger, and only the farthest pellet has to "
           "be reached.",
           "Walls are kept; ghost danger is ignored (every step costs 1); after the first pellet the others "
           "only have to be connected by a tree instead of visited along one path."],
          ["Cost of computing it", "No preparation; one pass over the k pellets per call.",
           "One breadth-first search from every pellet before the search starts; the MST (Prim's algorithm) is "
           "computed once per food mask and cached, so a call is again one pass over the pellets."],
          ["Start state of the large layout",
           f"h1 = {HEUR[(L, 'h1')]['h_start']}  (true cost {HEUR[(L, 'h1')]['true_cost_start']})",
           f"h2 = {HEUR[(L, 'h2')]['h_start']}  (true cost {HEUR[(L, 'h2')]['true_cost_start']})"],
      ],
      widths_cm=[3.0, 6.3, 7.3], caption="The two heuristic functions.", size=9, bold_first_col=True,
      stripe=False)
doc.para(
    "The two heuristics are deliberately different in kind: h1 is cheap and uses no knowledge of the maze, "
    "h2 uses the real maze distances and looks at all remaining pellets instead of one. Both are exact costs "
    "of a relaxed (easier) problem, which is the standard way of obtaining admissible heuristics [1].",
    align="justify")

doc.heading("2.2 Admissibility", 2)
doc.para("A heuristic is admissible if it never overestimates: h(s) ≤ h*(s) for every state s.", space_after=3)
doc.para(
    "**h1 is admissible.** Let p be the farthest remaining pellet. Every solution must enter the cell of p. "
    "One move changes Pac-Man's Manhattan distance to p by exactly 1, so at least Manhattan(pos, p) moves are "
    "needed, and every move costs at least 1. Therefore h*(s) ≥ Manhattan(pos, p) = h1(s).", align="justify")
doc.para(
    "**h2 is admissible.** Take any solution from s and let q1, q2, ..., qm be the remaining pellets in the "
    "order in which this solution first reaches them. Its cost is at least its number of moves, which is at "
    "least d(pos, q1) + d(q1, q2) + ... + d(q(m-1), qm), because d is the smallest possible number of moves "
    "between two cells. The first term is at least the distance to the nearest pellet. The remaining terms "
    "are the edges of a path through all pellets of F; a path is one particular spanning tree, so their sum "
    "is at least MST(F). Therefore h*(s) ≥ h2(s).", align="justify")

doc.heading("2.3 Consistency", 2)
doc.para(
    "A heuristic is consistent if h(s) ≤ c(s, a, s') + h(s') for every transition, and h = 0 at goal states. "
    "Consistency implies admissibility and guarantees that A* never has to expand a state twice.",
    align="justify")
doc.para(
    "**h1 is consistent.** A move changes the Manhattan distance to every pellet by exactly 1. If no pellet "
    "is eaten, the maximum over the pellets can drop by at most 1. If the move eats a pellet q, then q was at "
    "distance 1, and the distances to all other pellets again change by at most 1. In both cases "
    "h1(s) - h1(s') ≤ 1 ≤ c.", align="justify")
doc.para(
    "**h2 is consistent.** Case A - no pellet is eaten: MST(F) is unchanged and, by the triangle inequality "
    "of d, the distance to the nearest pellet changes by at most 1, so h2(s) - h2(s') ≤ 1 ≤ c. Case B - the "
    "move eats pellet q, so before the move d(pos, q) = 1 and h2(s) ≤ d(pos, q) + MST(F) = 1 + MST(F). Let "
    "F' be F without q. Connecting q to the minimum spanning tree of F' through q's nearest "
    "pellet gives a spanning tree of F, hence MST(F) ≤ MST(F') + (distance from q to its nearest pellet in "
    "F') = h2(s'), because after the move Pac-Man stands on q. Together: h2(s) ≤ 1 + h2(s') ≤ c + h2(s'). "
    "If q was the last pellet, h2(s) = 1 and h2(s') = 0, and the inequality also holds.", align="justify")

doc.heading("2.4 Dominance: h2 is never smaller than h1", 2)
doc.para(
    "Let f be the pellet that is farthest in Manhattan distance and e the pellet that is nearest in maze "
    "distance. Walking from pos to e and then along the tree edges of the MST from e to f is a walk from "
    "pos to f of length at most d(pos, e) + MST(F) = h2(s). No walk from pos to f can be shorter than "
    "Manhattan(pos, f) = h1(s). Hence h1(s) ≤ h2(s) ≤ h*(s) in every state: h2 dominates h1. A* with h2 "
    "therefore expands no node that A* with h1 can avoid, apart from ties among nodes whose f value equals "
    "the optimal cost.", align="justify")

doc.heading("2.5 Exhaustive verification", 2)
doc.para(
    "Because the state space is small, we do not have to rely on the proofs alone. `analyse_heuristic()` "
    "computes the true remaining cost h* of every reachable state with one backward uniform-cost search from "
    "the goal states and then checks h(s) ≤ h*(s) for every state and h(s) ≤ c + h(s') for every "
    f"transition (Table {T_VERIFY}). Table {T_HEUR} above gives the definitions.", align="justify")
table(T_VERIFY,
      ["Layout", "Heuristic", "States checked", "Transitions checked", "Admissible", "Consistent",
       "Mean h / h*", "h(start)", "h*(start)", "Setup (ms)"],
      [[name if h == "h1" else "", h, n(HEUR[(name, h)]["states_checked"]), n(HEUR[(name, h)]["transitions_checked"]),
        "yes" if HEUR[(name, h)]["admissible"] else "NO", "yes" if HEUR[(name, h)]["consistent"] else "NO",
        f"{HEUR[(name, h)]['mean_ratio']:.2f}", n(HEUR[(name, h)]["h_start"]), n(HEUR[(name, h)]["true_cost_start"]),
        f"{HEUR[(name, h)]['setup_ms']:.3f}"] for name in LAYOUTS for h in ("h1", "h2")],
      widths_cm=[1.5, 1.6, 1.7, 2.0, 1.8, 1.8, 1.6, 1.4, 1.5, 1.7], align=["l", "l"] + ["r"] * 2 + ["c"] * 2 + ["r"] * 4,
      caption="Both heuristics checked on every reachable state and transition. \"Mean h / h*\" is the average "
              "ratio between the estimate and the true remaining cost over all non-goal states (1.00 would be a "
              "perfect heuristic). \"Setup\" is the time needed to build the heuristic before the search. In "
              "every layout h2 ≥ h1 holds in all states.", stripe=False)
doc.para(
    f"On the large layout h2 is strictly larger than h1 in {n(HEUR[(L, 'h1')]['states_where_h2_is_larger'])} of "
    f"the {n(HEUR[(L, 'h1')]['states_checked'])} states. h1 captures about half of the true cost because it "
    "ignores every pellet except one; h2 is closer because it accounts for all pellets and for the walls. What "
    "h2 still misses is the ghost danger cost and the fact that a real route is a path, not a tree. Its "
    f"preparation costs less than a tenth of a millisecond.", align="justify")
assert max(HEUR[(name, "h2")]["setup_ms"] for name in LAYOUTS) < 0.1

# =============================================================================== 3 informed search
doc.heading("3. Informed Search: Greedy Best-First and A*", 1)
doc.heading("3.1 Implementation", 2)
doc.para(
    "Greedy Best-First and A* [1, 3] are the same best-first graph search (`best_first_search` in "
    "`informed.py`) and differ "
    "in two points. The first is the evaluation function that orders the priority queue: Greedy uses "
    "f(n) = h(n), A* uses f(n) = g(n) + h(n), where g(n) is the path cost so far. UCS from Phase I is the "
    "special case f(n) = g(n); the unit tests confirm that A* with h = 0 expands the same number of nodes and "
    "returns the same path as our UCS. The second point is what happens when a state is reached again: A* "
    "puts it back on the frontier if the new path is strictly cheaper (needed for optimality), while Greedy, "
    "to which path cost means nothing, queues every state only once. In both, the goal test is applied when a "
    "node is removed from the queue, outdated queue entries are skipped, and ties are broken "
    "first-in-first-out. The same measurements as in Phase I are recorded; the running time includes building "
    "the heuristic.", align="justify")

doc.heading("3.2 Results", 2)
doc.para(
    f"Table {T_INF_LARGE} gives the measurements on the main layout and Table {T_INF_OTHER} those on the other "
    f"two; Figure {F_EFFECT} shows the expansions and the path costs side by side.", align="justify")
ROWS_L = ["UCS"] + INFORMED
table(T_INF_LARGE,
      ["Algorithm", "Path cost", "Steps", "Nodes generated", "Nodes expanded", "Max frontier",
       "Max nodes in memory", "Time (ms)", "Optimal"],
      [[a, n(s(L, a, "path_cost")), n(s(L, a, "steps")), n(s(L, a, "nodes_generated")), n(s(L, a, "nodes_expanded")),
        n(s(L, a, "max_frontier")), n(s(L, a, "max_nodes_in_memory")), ms(s(L, a, "time_ms")),
        "yes" if s(L, a, "cost_optimal") else "no"] for a in ROWS_L],
      widths_cm=[2.4, 1.5, 1.3, 2.1, 2.0, 1.8, 2.3, 1.7, 1.5], align=["l"] + ["r"] * 7 + ["c"],
      caption=f"Informed search on the large layout, with UCS as the uninformed baseline. Optimal cost = {n(opt)}.",
      bold_first_col=True)
table(T_INF_OTHER,
      ["Layout", "Algorithm", "Path cost", "Steps", "Nodes generated", "Nodes expanded", "Max frontier",
       "Time (ms)", "Optimal"],
      [[name if a == "UCS" else "", a, n(s(name, a, "path_cost")), n(s(name, a, "steps")),
        n(s(name, a, "nodes_generated")), n(s(name, a, "nodes_expanded")), n(s(name, a, "max_frontier")),
        ms(s(name, a, "time_ms")), "yes" if s(name, a, "cost_optimal") else "no"]
       for name in ("small", "medium") for a in ROWS_L],
      widths_cm=[1.7, 2.4, 1.6, 1.4, 2.4, 2.3, 2.0, 1.7, 1.5], align=["l", "l"] + ["r"] * 6 + ["c"],
      caption="The same comparison on the small and medium layouts.", stripe=False)
figure(F_EFFECT, FIG / "heuristic_effect.png",
       "Nodes expanded (top) and path cost (bottom) of UCS, Greedy and A* on the three layouts. "
       "The black line marks the optimal cost.")

doc.heading("3.3 Effect of each heuristic", 2)
bstar = {a: effective_branching_factor(s(L, a, "nodes_generated"), s(L, a, "steps"))
         for a in ("UCS", "A* (h1)", "A* (h2)")}
doc.para(
    f"**A*.** With either heuristic A* returns the optimal cost on all three layouts, as the theory promises "
    f"for an admissible heuristic. The heuristics only change how much work that takes. On the large layout "
    f"UCS expands {n(ucs_exp)} nodes; A* with h1 expands {n(a1_exp)} ({ucs_exp / a1_exp:.1f} times fewer) and A* "
    f"with h2 only {n(a2_exp)} ({ucs_exp / a2_exp:.0f} times fewer than UCS, {a1_exp / a2_exp:.1f} times fewer than "
    f"h1). The maximum frontier shrinks in the same way, from {n(s(L, 'UCS', 'max_frontier'))} to "
    f"{n(s(L, 'A* (h1)', 'max_frontier'))} and {n(s(L, 'A* (h2)', 'max_frontier'))} nodes, and the running time "
    f"from {ms(s(L, 'UCS', 'time_ms'))} ms to {ms(a2['time_ms'])} ms even though h2 is the more "
    "expensive function to evaluate. The effective branching factor b* (the branching factor of a uniform "
    f"tree with the same depth and number of generated nodes) falls from {bstar['UCS']:.2f} for UCS to "
    f"{bstar['A* (h1)']:.2f} with h1 and {bstar['A* (h2)']:.2f} with h2. This is the dominance result of "
    "Section 2.4 in numbers: the better informed heuristic prunes more.", align="justify")
doc.para(
    f"**Greedy Best-First.** Greedy ignores the cost already paid, so it is not optimal: it returns cost "
    f"{n(g1['path_cost'])} with h1 and {n(g2['path_cost'])} with h2 instead of {n(opt)}. With h2 it is extremely "
    f"fast - {n(g2['nodes_expanded'])} expansions for a path of {g2['steps']} steps - because h2 "
    "decreases almost every time Pac-Man moves towards the nearest pellet, so the search runs straight "
    f"ahead. The price is that h2 counts steps and not danger: its path enters danger cells {g2_danger} "
    f"{'time' if g2_danger == 1 else 'times'}. "
    "On all three layouts Greedy with h2 returns a path with the fewest possible steps, like BFS, and never "
    f"the cheapest one. With h1 Greedy does badly in a different way: it expands {n(g1['nodes_expanded'])} "
    f"nodes, nearly as many as UCS and {g1['nodes_expanded'] / a1_exp:.1f} times as many as A* with the same "
    "heuristic. The reason is a basin of the heuristic, not missing guidance. Greedy always expands the "
    "frontier node with the smallest h, so it cannot expand a state whose h is at least h(start) before it "
    "has expanded every state that can be reached through smaller values. For h1 this region contains "
    f"{n(h1L['states_below_start_value'])} of the {n(h1L['states_checked'])} states and no goal state "
    "(`descent_region()` in `heuristics.py`): walking towards the farthest pellet lowers h1, but once that "
    "pellet is eaten another pellet becomes the farthest and h1 jumps up again. Greedy therefore searches "
    "the whole basin before it climbs out of it. For h2 the corresponding region does contain a goal on all "
    "three layouts, so Greedy can run downhill all the way. On the small and medium layouts the returned "
    f"path of Greedy with h1 costs {s('small', 'Greedy (h1)', 'path_cost') / OPT['small']:.1f} and "
    f"{s('medium', 'Greedy (h1)', 'path_cost') / OPT['medium']:.1f} times the optimum "
    f"({n(s('small', 'Greedy (h1)', 'path_cost'))} instead of {n(OPT['small'])}, and "
    f"{n(s('medium', 'Greedy (h1)', 'path_cost'))} instead of {n(OPT['medium'])}).", align="justify")
doc.para(f"Figure {F_EXPLORED} shows where the four searches spend their expansions.", align="justify")
figure(F_EXPLORED, FIG / "explored_informed_large.png",
       "Explored states and returned path of Greedy and A* with both heuristics on the large layout "
       f"(same colour scale in all four panels). The darker a cell, the more of its {2 ** k_large} food "
       f"combinations were expanded there. A* with h2 expands {n(a2_exp)} nodes and Greedy with h2 "
       f"{n(g2['nodes_expanded'])}, so their cells stay pale; Greedy with h1 expands {n(g1['nodes_expanded'])} "
       f"and A* with h1 {n(a1_exp)}.", width_cm=14.0)
doc.para(
    f"Figure {F_SCALING} shows the three layouts together. The work of UCS grows with the state space, while "
    f"A* with h2 needs about a hundred expansions on every layout "
    f"({', '.join(n(s(name, 'A* (h2)', 'nodes_expanded')) for name in LAYOUTS)}). A* only has to expand the "
    "states whose f = g + h is below the optimal cost, plus some of those where it is equal [1]; h2 is so "
    "close to the true cost that few states qualify, and how many depends on the accuracy of the heuristic, "
    "not on the number of states.", align="justify")
figure(F_SCALING, FIG / "scaling_informed.png",
       "Nodes expanded on the three layouts (both axes logarithmic).", width_cm=12.5)

# =============================================================================== 4 local search
doc.heading("4. Local Search", 1)
doc.heading("4.1 Formulation", 2)
doc.para(
    "Local search [1, 2] does not build a path step by step: it keeps one complete candidate solution (or a "
    f"population of them) and improves it. Table {T_FORM} defines what a candidate is in our problem.",
    align="justify")
table(T_FORM,
      ["Element", "Our definition"],
      [
          ["Solution representation", "A complete candidate solution is a priority order of the k pellets: a "
                                      "permutation of the pellet numbers 0..k-1."],
          ["From an order to a plan", "Pac-Man repeatedly walks, along the cheapest path, to the first pellet of "
                                      "the order that is still uneaten. Pellets that lie on the way are eaten in "
                                      "passing and skipped when their turn comes. The plan ends the moment the "
                                      "last pellet is eaten, so every order gives a valid plan of the Phase I "
                                      "model."],
          ["Objective (minimise)", "cost(order) = path cost of that plan = the sum of D(a, b) over the legs that "
                                   "are walked, where D(a, b) is the cheapest walking cost from a to b including "
                                   "the ghost danger cost. The table D is computed once by our own uniform-cost "
                                   "search over the maze cells (`cheapest_paths_from`). The GA uses fitness = "
                                   "-cost."],
          ["Neighbours", "All orders obtained by swapping two pellets of the current order: k(k-1)/2 neighbours "
                         f"({k_large * (k_large - 1) // 2} on the large layout)."],
          ["Link to the search problem", "cost(order) is exactly the path cost of the plan in the search model "
                                         "(the code replays every returned plan to confirm it), and the best of "
                                         "the k! orders costs exactly the optimal path cost."],
      ],
      widths_cm=[3.4, 13.2], caption="Local-search formulation of the Pac-Man problem.", size=9.5,
      bold_first_col=True, stripe=False)
doc.para(
    "**Why the best order is the optimal solution.** Every order is a real plan, so no order can cost less "
    "than the optimum. In the other direction, take an optimal path and write down the pellets in the order "
    "in which it first reaches them. Between two consecutive first visits the path cannot be cheaper than D, "
    "so the sum of D along this order is at most the optimal cost; and when our plan skips a pellet that was "
    "already eaten it can only get cheaper, because going straight to the next pellet never costs more than "
    "going through the skipped one (triangle inequality of D). We chose this representation instead of a "
    "sequence of single moves because every candidate is feasible, the neighbourhood is small and "
    "meaningful, and the result can be compared directly with UCS and A*.", align="justify")

doc.heading("4.2 The search landscape", 2)
doc.para(
    "With at most 8 pellets the landscape can be examined completely (`analyse_landscape` in `run_phase2.py`). "
    "This is only possible because the instance is small; it tells us what to expect from the algorithms "
    f"(Table {T_LAND}). For every order we follow the hill-climbing rule of Section 4.3 to the order where it "
    "stops, and we classify that order: it is a global optimum, a true local optimum (no chain of equal-cost "
    "swaps leads to anything cheaper), or a point on a plateau from which such a chain exists - a "
    "\"shoulder\".", align="justify")
table(T_LAND,
      ["Layout", "Orders (k!)", "Optimal orders", "Best / median / worst cost",
       "Orders where the climb stops: optimal / shoulder / local optimum",
       "Starts from which the climb reaches an optimum", "Mean size of an uphill swap"],
      [[name, n(LAND[name]["orders"]), n(LAND[name]["optimal_orders"]),
        f"{n(LAND[name]['best_cost'])} / {n(LAND[name]['median_cost'])} / {n(LAND[name]['worst_cost'])}",
        f"{n(LAND[name]['stop_orders_global_optimum'])} / {n(LAND[name]['stop_orders_shoulder'])} / "
        f"{n(LAND[name]['stop_orders_local_optimum'])}",
        f"{n(LAND[name]['starts_ending_in_global_optimum'])} ({LAND[name]['hc_success_probability'] * 100:.1f}%)",
        f"{LAND[name]['mean_uphill_swap']:.1f}"] for name in LAYOUTS],
      widths_cm=[1.5, 1.8, 1.7, 2.9, 3.6, 3.1, 2.0], align=["l", "r", "r", "c", "c", "r", "r"],
      caption="Exhaustive analysis of the pellet-ordering landscape.")
doc.para(
    f"On the large layout only {land['optimal_orders']} of the {n(land['orders'])} orders are optimal. The climb "
    f"reaches one of them from {land['hc_success_probability'] * 100:.1f}% of the possible starting orders; from "
    f"all the others it stops in one of {n(land['stop_orders_shoulder'])} non-optimal orders. None of these is a "
    "true local optimum: every one of them lies on a plateau that has a way down. The plain climber stops "
    "there only because it accepts strict improvements only. So on this problem hill climbing does not fail "
    "because of local optima but because of plateaus, on all three layouts - which also tells us what can "
    f"repair it (Section 4.5). Figure {F_ROUTES} shows one such stopping point.", align="justify")
figure(F_ROUTES, FIG / "routes_large.png",
       f"Left: an optimal plan. Right: the plan at which one hill-climbing run stopped (cost "
       f"{n(hc_worst_run['cost'])}): no swap of two pellets in its priority order "
       f"({', '.join(hc_worst_run['order'].split())}) is cheaper. Small numbers next to the pellets are the "
       "pellet indices; numbers in circles give the order in which the pellets are actually eaten.",
       width_cm=14.5)

doc.heading("4.3 The three algorithms", 2)
doc.bullets([
    "**Hill Climbing** (steepest descent of the cost): start from a random order; evaluate all neighbours; "
    "move to the best one if it is strictly better; stop when no neighbour is better. It has no parameters "
    "besides the random start. Two standard remedies are implemented as options: random restarts and a "
    "limited number of sideways moves on a plateau.",
    "**Simulated Annealing** [4]: start from a random order; in each iteration try one random swap; accept it if "
    "it is not worse, otherwise accept it with probability exp(-delta / T), where delta is the increase in "
    "cost. Cooling schedule (geometric): T(n) = T0 x a^{n}, i.e. the temperature is multiplied by the cooling "
    "rate a after every iteration; the run stops when T falls below the end temperature. The best order seen "
    "is returned.",
    "**Genetic Algorithm:** a chromosome is an order (one gene per pellet); fitness = -cost; parents are "
    "chosen by tournament selection; with the crossover probability two parents produce a child by a "
    "simple variant of Davis's order crossover [5] (a slice of one parent is copied, the remaining positions "
    "are filled from left to right in the order of the other parent, so a child is always a valid "
    "permutation), otherwise the child is a copy of the first parent; with the mutation probability two "
    "genes of the child are swapped (at most one swap per child); optionally the best individuals are copied unchanged into the "
    "next generation (elitism). The best order ever seen is stored separately and returned.",
])

doc.heading("4.4 Parameter values and their justification", 2)
doc.para(
    f"The values were chosen with a sensitivity study on the large layout: {TUNE_RUNS} runs per setting, on "
    f"seeds {data['tuning_seeds'][0]}-{data['tuning_seeds'][1]}, which are different from the {RUNS} seeds used "
    "for the final results, so that the parameters are not tuned on the reported runs. For every setting we "
    "record the share of runs that reach the optimal cost and the number of objective evaluations per run, "
    f"because most parameters also change the budget. With {TUNE_RUNS} runs the sampling error of a share "
    f"near 97% is about one percentage point, so differences of two or three points are within the noise "
    f"(Table {T_PARAMS}, Figures {F_TUNE_SA} and {F_TUNE_GA}).", align="justify")
sa_iter = round(sa["mean_iterations"])
table(T_PARAMS,
      ["Algorithm", "Parameter", "Value", "Justification"],
      [
          ["SA", "Start temperature T0", f"{SA['start_temperature']:g}",
           f"An uphill swap increases the cost by {uphill:.1f} on average. With T0 = "
           f"{SA['start_temperature']:g} such a move is accepted with probability "
           f"exp(-{uphill:.1f}/{SA['start_temperature']:g}) = "
           f"{math.exp(-uphill / SA['start_temperature']):.2f} at the start, so the search moves "
           f"freely at first. {pct_list(sa_grid_temp, 'start_temperature')} of the runs are optimal for the start "
           "temperatures in brackets: 1 freezes too early, and from 5 upwards the differences are within the noise."],
          ["SA", "Cooling rate a", f"{SA['cooling_rate']:g}",
           f"The most important parameter, because it fixes the number of iterations: "
           f"{pct_list(sa_grid_cool, 'cooling_rate')}, for {n(sa_grid_cool[0]['evaluations'])} to "
           f"{n(sa_slowest['evaluations'])} evaluations. {SA['cooling_rate']:g} gives {pct(sa_used):.0f}% with "
           f"{n(sa_used['evaluations'])} evaluations ({n(sa_iter)} iterations); {sa_slowest['cooling_rate']:g} "
           f"gains {pct(sa_slowest) - pct(sa_used):.0f} points for five times the work."],
          ["SA", "End temperature", f"{SA['end_temperature']:g}",
           "At T = 0.1 even the smallest uphill move (+1) is accepted with probability e^{-10}, about 0.00005: "
           f"the search is frozen, and cooling further would only cost evaluations. Stopping earlier loses "
           f"reliability: {pct_list(tune('SA', 'end_temperature'))}."],
          ["GA", "Population size", f"{GA['population_size']}",
           f"{pct_list(ga_grid_pop, 'population_size')}. Larger populations are more reliable but cost "
           f"proportionally more evaluations. {GA['population_size']} individuals for {GA['generations']} "
           f"generations give the GA a budget of {n(ga['mean_evaluations'])} evaluations, the same as SA "
           f"({n(sa['mean_evaluations'])}), so that the two can be compared fairly."],
          ["GA", "Generations", f"{GA['generations']}",
           f"{pct_list(tune('GA', 'generations'))}: most of the progress is made early; more generations buy "
           "the last few points."],
          ["GA", "Mutation rate", f"{GA['mutation_rate']:g}",
           f"{pct_list(ga_grid_mut, 'mutation_rate')}. A chromosome has only {k_large} genes and the population "
           "is small, so it becomes uniform quickly; frequent mutation keeps it diverse. This is far above the "
           "small rates usually quoted for GAs, and it is what the measurements ask for on this problem."],
          ["GA", "Crossover rate", f"{GA['crossover_rate']:g}",
           f"{pct_list(tune('GA', 'crossover_rate'))}: no measurable effect - the differences are within the "
           "noise, and the GA does as well without any crossover. We keep the usual value 0.9."],
          ["GA", "Tournament size", f"{GA['tournament_size']}",
           f"{pct_list(tune('GA', 'tournament_size'))}: weaker selection pressure protects diversity. Size 2 "
           "is the weakest selection we tested."],
          ["GA", "Elite count", f"{GA['elite_count']}",
           f"{pct_list(tune('GA', 'elite_count'))}: elitism does not help and more elites hurt, because copies "
           "of the best order take over the small population. Nothing is lost without it: the best order ever "
           "seen is stored separately."],
          ["HC", "Restarts (extra experiment)", f"{data['hc_restarts']}",
           f"{pct_list(restarts)}. The exact values, from the {land['hc_success_probability'] * 100:.1f}% of "
           f"Table {T_LAND}, are {', '.join(format(r['exact_percent'], '.0f') + '%' for r in restarts)}. "
           f"{data['hc_restarts']} restarts ({data['hc_restarts'] + 1} climbs, about "
           f"{n(rr_tuned['evaluations'])} evaluations) bring hill climbing close to the budget of SA and the GA. "
           "The plain algorithm (0 restarts) is the one reported as \"Hill Climbing\"."],
      ],
      widths_cm=[1.7, 3.0, 1.2, 10.7], align=["l", "l", "c", "l"],
      caption=f"Parameter values used in the final experiments. Percentages are the share of {TUNE_RUNS} tuning "
              "runs that reached the optimum, with the tested parameter value in brackets.", size=9,
      stripe=False, keep_together=False)
figure(F_TUNE_SA, FIG / "tuning_sa.png",
       "Simulated annealing: start temperature against cooling rate. Each cell shows the share of optimal "
       "runs and the evaluations per run.", width_cm=11.5)
figure(F_TUNE_GA, FIG / "tuning_ga.png",
       "Genetic algorithm: population size against mutation rate.", width_cm=10.5)
doc.para(
    f"**Reliability is bought with evaluations.** Figure {F_BUDGET} plots the share of optimal runs against "
    "the evaluations spent, for the settings that change the budget. Hill climbing with restarts, simulated "
    "annealing and the genetic algorithm lie on similar curves: with "
    f"{n(rr_tuned['evaluations'])} to {n(ga_used['evaluations'])} evaluations per run all three reach the "
    f"optimum in {min(pct(sa_used), pct(ga_used)):.0f}% of the runs or more. Sideways moves are the exception: "
    f"they use the budget badly ({pct(sideways[-1]):.0f}% for {n(sideways[-1]['evaluations'])} evaluations). "
    "The parameter choice is therefore mainly a choice of budget, and we gave the three methods a similar "
    "one.", align="justify")
doc.para(
    f"**The baseline: random sampling.** The grey curve of Figure {F_BUDGET} is not an algorithm at all: it "
    "is the probability that n orders drawn at random contain an optimal one. On the large layout "
    f"{land['optimal_orders']} of the {n(land['orders'])} orders are optimal (Table {T_LAND}), one in "
    f"{land['orders'] / land['optimal_orders']:.0f}, so this probability is 1 - (1 - 1/"
    f"{land['orders'] / land['optimal_orders']:.0f})^n: {random_share(hc_tuned['evaluations']):.0f}% for "
    f"{n(hc_tuned['evaluations'])} orders and {random_share(BASE_N):.1f}% for {n(BASE_N)}. Simulated annealing "
    f"({pct(sa_used):.0f}%) and the genetic algorithm ({pct(ga_used):.0f}%) with the chosen settings are "
    "therefore not better than drawing the same number of random orders; they are slightly worse, because "
    "they spend part of their budget on orders close to ones they have already seen. On this layout our "
    "parameter study measures the budget more than the algorithms, and the best GA settings are the most "
    "random ones we tested (frequent mutation, weakest selection, no elitism). Hill climbing is the "
    f"exception: one climb succeeds from {land['hc_success_probability'] * 100:.1f}% of the starts with about "
    f"{n(hc_tuned['evaluations'])} evaluations, against {random_share(hc_tuned['evaluations']):.0f}% for the "
    "same number of random orders. Section 4.6 repeats the comparison on larger mazes, where the picture "
    "changes.", align="justify")
figure(F_BUDGET, FIG / "budget_vs_success.png",
       f"Share of {TUNE_RUNS} runs that reach the optimum against the evaluations spent per run, for the "
       "settings of the sensitivity study that change the budget. Grey curve: random sampling of the same "
       "number of orders.", width_cm=11.5)

doc.heading("4.5 Results", 2)
doc.para(
    f"Each algorithm was run {RUNS} times per layout with the seeds 0 to {RUNS - 1}; every run uses its own "
    f"`random.Random(seed)` generator, so each run is reproducible (Table {T_LOCAL}). The last row of each "
    f"layout is the baseline: the best of {n(BASE_N)} random orders.", align="justify")
table(T_LOCAL,
      ["Layout", "Algorithm", "Best", "Mean", "Worst", "Std. dev.", f"Optimal runs (of {RUNS})",
       "Mean evaluations", "Mean time (ms)"],
      [[name if a == LOCALS[0] else "", a, n(ls(name, a, "best")), f"{ls(name, a, 'mean'):.2f}", n(ls(name, a, "worst")),
        f"{ls(name, a, 'std'):.2f}", n(ls(name, a, "optimal_runs")), n(ls(name, a, "mean_evaluations")),
        ms(ls(name, a, "time_ms"))] for name in LAYOUTS for a in LOCALS + [HC_RR, BASE]],
      widths_cm=[1.4, 4.0, 1.1, 1.3, 1.2, 1.5, 2.2, 2.0, 1.9], align=["l", "l"] + ["r"] * 7,
      caption="Local search: cost of the returned solution over the seeded runs. The optimal costs are "
              f"{OPT['small']}, {OPT['medium']} and {OPT['large']}. The time includes building the distance "
              "table.", stripe=False)
doc.para(
    f"**Hill Climbing** converges after only {hc['mean_iterations']:.1f} moves on average "
    f"({n(hc['mean_evaluations'])} evaluations) and is by far the cheapest method, but on the large layout it ends "
    f"in an optimum in only {hc['optimal_runs']} of {RUNS} runs. That agrees with the "
    f"{land['hc_success_probability'] * 100:.0f}% predicted by the landscape analysis (with {RUNS} runs the "
    f"sampling error is about {hc_error:.0f} points; the {TUNE_RUNS} tuning runs gave {pct(hc_tuned):.0f}%). Its "
    f"worst run costs {hc['worst']}, {(hc['worst'] / opt - 1) * 100:.0f}% above the optimum. **Simulated "
    f"Annealing** accepts sideways and uphill moves, so plateaus do not stop it: all {RUNS} runs are optimal "
    f"on all three layouts. The **Genetic Algorithm** achieves the same with almost the same number of "
    f"evaluations, but it does more bookkeeping per evaluation (selection, crossover, sorting), so a run takes "
    f"{ga['time_ms'] / sa['time_ms']:.1f} times as long. Neither result is a guarantee: on the tuning "
    f"seeds the same settings reached the optimum in {pct(sa_used):.0f}% and {pct(ga_used):.0f}% of the runs. "
    f"Nor is it evidence of clever search: the baseline row finds the optimum in all {RUNS} runs as well, and "
    f"on the small and medium layouts {n(BASE_N)} evaluations are more than the "
    f"{n(LAND['small']['orders'])} and {n(LAND['medium']['orders'])} orders that exist. "
    f"Figures {F_CONV} to {F_TRACE} show how the runs proceed.", align="justify")
figure(F_CONV, FIG / "convergence_large.png",
       f"Convergence on the large layout: best cost found so far for each of the {RUNS} runs (grey) and "
       "their average (blue). Hill Climbing stops after a few iterations, often above the optimum; "
       "Simulated Annealing and the Genetic Algorithm keep improving.")
figure(F_FINAL, FIG / "final_costs_large.png",
       "Distribution of the final costs on the large layout: number of runs that ended with each cost.")
figure(F_TRACE, FIG / "sa_trace_large.png",
       "One simulated-annealing run. While the temperature is high the current order (grey) moves up and "
       "down freely; as it cools the search settles. The best order found (blue) is kept separately.",
       width_cm=12.5)
doc.para(
    f"**Repairing hill climbing.** Since the climber stops on plateaus, two remedies suggest themselves. "
    f"Random restarts work well: with {data['hc_restarts']} restarts ({n(rr['mean_evaluations'])} evaluations in "
    f"total) the optimum was found in {rr['optimal_runs']} of {RUNS} runs, and in {rr_tuned['hits']} of the "
    f"{TUNE_RUNS} tuning runs (the exact success probability is {rr_tuned['exact_percent']:.1f}%). "
    f"Sideways moves help less than expected: allowing up to {', '.join(str(r['value']) for r in sideways[:-1])} "
    f"or {sideways[-1]['value']} equal-cost moves raises the success rate from {pct(hc_tuned):.0f}% to "
    f"{', '.join(format(pct(r), '.0f') + '%' for r in sideways[:-1])} and {pct(sideways[-1]):.0f}%, at a much higher price in "
    f"evaluations: every sideways step costs a full look at the {k_large * (k_large - 1) // 2} neighbours, and a "
    "random walk over a plateau needs many steps before it reaches an order that has a way down.",
    align="justify")

doc.heading("4.6 Beyond the official layouts: larger mazes", 2)
kmax = PELLETS[-1]
doc.para(
    "The official layouts have to stay below 10,000 states, and Section 4.4 showed that at this size random "
    "sampling is as good as simulated annealing or the genetic algorithm. To see what the methods are worth "
    "when sampling stops working, we ran one extra experiment outside the official range (`scaling.py`): a "
    f"13x19 maze with {SCALE_I[kmax]['free_cells']} free cells and two ghosts, with "
    f"{', '.join(str(k) for k in PELLETS[:-1])} and {kmax} pellets (Figure {F_MAZES}). The number of pellet "
    f"orders grows from {n(SCALE_I[PELLETS[0]]['pellet_orders'])} to about "
    f"{big(SCALE_I[kmax]['pellet_orders'])}, and the state space from at most "
    f"{n(SCALE_I[PELLETS[0]]['state_space_upper_bound'])} to at most "
    f"{n(SCALE_I[kmax]['state_space_upper_bound'])} states. Every method gets the same budget of "
    f"{n(data['scaling_budget'])} evaluations per run and {data['scaling_seeds']} seeded runs: hill climbing "
    "restarts until the budget is used, simulated annealing keeps T0 and the end temperature and stretches "
    "its cooling rate to the budget, and the genetic algorithm uses a population of 100 for 99 generations "
    f"({n(data['scaling_budget'])} evaluations). Hill climbing finishes its last climb, so it used "
    f"{n(min(SCALE_M[(k, 'Hill Climbing (restarts)')]['mean_evaluations'] for k in PELLETS))} to "
    f"{n(max(SCALE_M[(k, 'Hill Climbing (restarts)')]['mean_evaluations'] for k in PELLETS))} evaluations on "
    "average. All other settings are those of Table "
    f"{T_PARAMS}; they were not tuned again. A* with h2 supplies the optimal cost of every instance "
    f"(Tables {T_SCALE_I} and {T_SCALE_M}, Figure {F_SCALE_LOCAL}).", align="justify")
figure(F_MAZES, FIG / "scaling_mazes.png",
       f"The mazes of the scaling experiment, from {PELLETS[0]} to {kmax} pellets. They are not official "
       "instances of the project.", width_cm=15.5)
table(T_SCALE_I,
      ["Pellets", "States (upper bound)", "Pellet orders (k!)", "Optimal cost", "A* (h2): nodes expanded",
       "A* (h2): max nodes in memory", "A* (h2): time (ms)"],
      [[n(k), n(SCALE_I[k]["state_space_upper_bound"]),
        big(SCALE_I[k]["pellet_orders"]),
        n(SCALE_I[k]["optimal_cost"]), n(SCALE_I[k]["astar_h2_nodes_expanded"]),
        n(SCALE_I[k]["astar_h2_max_nodes_in_memory"]), ms(SCALE_I[k]["astar_h2_time_ms"])] for k in PELLETS],
      widths_cm=[1.6, 3.0, 2.8, 2.0, 2.6, 2.6, 2.0], align=["r"] * 7,
      caption="The instances of the scaling experiment and what A* with h2 needs to solve them exactly.")
table(T_SCALE_M,
      ["Pellets", "Optimal cost"] + [f"{m}: mean cost (optimal runs)" for m in SCALE_METHODS],
      [[n(k), n(SCALE_I[k]["optimal_cost"])] +
       [f"{SCALE_M[(k, m)]['mean']:.1f} (+{above(k, m):.1f}%; {SCALE_M[(k, m)]['optimal_runs']}/"
        f"{SCALE_M[(k, m)]['runs']})" for m in SCALE_METHODS] for k in PELLETS],
      widths_cm=[1.4, 1.6, 3.4, 3.4, 3.4, 3.4], align=["r", "r", "c", "c", "c", "c"],
      caption=f"Local search on the larger mazes: mean cost over {data['scaling_seeds']} runs of about "
              f"{n(data['scaling_budget'])} evaluations, its distance from the optimum, and the number of runs "
              "that found the optimum.", size=9)
figure(F_SCALE_LOCAL, FIG / "scaling_local.png",
       f"Mean cost above the optimum for the four methods as the number of pellets grows "
       f"({n(data['scaling_budget'])} evaluations per run).", width_cm=15.5)
doc.para(
    f"With {PELLETS[0]} pellets the three algorithms find the optimum in every run and random sampling in "
    f"{SCALE_M[(PELLETS[0], 'Random sampling')]['optimal_runs']} of {data['scaling_seeds']}. From {PELLETS[1]} "
    "pellets on, random sampling never finds it again and falls further behind with every step "
    f"(+{above(PELLETS[1], 'Random sampling'):.1f}% to +{above(kmax, 'Random sampling'):.1f}%). Hill "
    f"climbing with restarts and simulated annealing stay much closer (+{above(kmax, 'Hill Climbing (restarts)'):.1f}% "
    f"and +{above(kmax, 'Simulated Annealing'):.1f}% with {kmax} pellets), and simulated annealing is the best "
    f"method on the largest instance. The genetic algorithm lies between them and random sampling "
    f"(+{above(kmax, 'Genetic Algorithm'):.1f}%); its mutation, crossover and selection settings were chosen "
    "on a problem where randomness was all that mattered, and we did not retune them. So the local-search methods do search better than chance; "
    "the official layouts are simply too small to show it. The experiment also has a second result, which we "
    f"did not expect: A* with h2 solves even the {kmax}-pellet maze exactly, with "
    f"{n(SCALE_I[kmax]['astar_h2_nodes_expanded'])} expansions in {ms(SCALE_I[kmax]['astar_h2_time_ms'])} ms, "
    f"while no local-search method reaches the optimum reliably there. These are single instances per size "
    f"and {data['scaling_seeds']} runs, so the figures show a trend, not precise rates.", align="justify")

# =============================================================================== 5 comparison
doc.heading("5. Comparison of All Nine Algorithms", 1)
doc.para(
    f"Table {T_ALL} and Figure {F_SUMMARY} compare all algorithms of both phases on the main layout; Greedy "
    "and A* appear once per heuristic, and hill climbing with restarts and the random-sampling baseline are "
    "added as extra rows. \"Complete\" means that the method always returns a solution when one exists - for "
    "local search this holds because every order is a valid plan - and \"optimal\" that the returned "
    "solution is guaranteed to have the lowest cost. The same measurements for the other two layouts are "
    "in Appendix B (completeness and optimality are as in this table). Time is the running time as defined "
    "in Section 1.2. Memory is given twice: the peak memory allocated during a run (`tracemalloc`) and the "
    "number of items held at the same time - search nodes for the search algorithms, pellet orders for local "
    "search. Effort is the number of nodes expanded for the search algorithms and of objective evaluations "
    "for local search; the two are not the same unit and should only be compared within a family. For the "
    f"randomised methods the cost is given as mean (best-worst) over {RUNS} seeds, and their time includes "
    f"the {ms(hc['setup_ms'])} ms needed to build the distance table.", align="justify")
rows = []
for r in COMP[L]:
    cost = n(r["cost"]) if not r["cost_range"] else f"{r['cost']:.1f} ({r['cost_range'][0]}-{r['cost_range'][1]})"
    rows.append([r["algorithm"], cost, r["found_optimum"], ms(r["time_ms"]), n(r["peak_memory_kib"]),
                 n(r["memory_items"]), n(r["effort"]), r["complete"], r["optimal_guaranteed"]])
table(T_ALL,
      ["Algorithm", "Solution cost", "Optimum found", "Time (ms)", "Memory (KiB)", "Items in memory", "Effort",
       "Complete?", "Optimal (guaranteed)?"],
      rows, widths_cm=[2.4, 1.9, 1.6, 1.1, 1.4, 1.4, 1.4, 2.9, 2.5],
      align=["l", "r", "c", "r", "r", "r", "r", "l", "l"],
      caption=f"All algorithms on the large layout ({n(REACH[L])} reachable states, optimal cost {n(opt)}).",
      size=8, bold_first_col=True)
figure(F_SUMMARY, FIG / "summary_all_large.png",
       "Summary chart: solution cost, running time, peak memory and search effort of all algorithms on "
       "the large layout (time and effort on logarithmic axes). Colours mark the three families; "
       "the baseline is grey.", width_cm=15.5)

doc.heading("5.1 Which algorithm suits this problem best?", 2)
doc.para(
    f"**A* with h2.** It is complete and guaranteed optimal, like UCS, but it expands {n(a2_exp)} nodes "
    f"instead of {n(ucs_exp)}, runs in {ms(a2['time_ms'])} ms instead of {ms(s(L, 'UCS', 'time_ms'))} ms and "
    f"holds {n(a2['max_nodes_in_memory'])} nodes instead of {n(s(L, 'UCS', 'max_nodes_in_memory'))}. No other "
    "method that guarantees the optimum comes close. The only methods that are faster (DFS, Greedy with h2, "
    "a single Hill Climbing run) do not guarantee the optimum: DFS and Greedy miss it on every layout and "
    f"Hill Climbing misses it in {RUNS - hc['optimal_runs']} of {RUNS} runs on the main layout. Simulated "
    f"Annealing and the Genetic Algorithm did find the optimum in every run, but they take "
    f"{sa['time_ms'] / a2['time_ms']:.0f} and {ga['time_ms'] / a2['time_ms']:.0f} times as long as A*, do no "
    "better than random sampling at this size, and cannot tell that what they found is optimal. "
    "The reason A* fits so well is that the problem has a good admissible heuristic: the structure of the "
    f"task (reach a pellet, then connect the rest) is captured well by h2 ({h2L['mean_ratio'] * 100:.0f}% of the "
    "true remaining cost on average), and the state space is small enough for A*'s memory use to be "
    "irrelevant.", align="justify")
doc.para(
    "What if the number of pellets grows? The state space doubles with every pellet, so the uninformed "
    "searches, which expand a fixed share of it, become impossible first. In theory A* is also exponential, "
    f"and its frontier has to be kept in memory. In our scaling experiment (Section 4.6), however, A* with h2 "
    f"was still the best method at {kmax} pellets: {n(SCALE_I[kmax]['astar_h2_nodes_expanded'])} expansions "
    f"for a state space of up to {SCALE_I[kmax]['state_space_upper_bound'] / 1e9:.1f} billion states, with "
    "the guarantee of optimality, while the local-search methods ended "
    f"{above(kmax, 'Simulated Annealing'):.0f}% to {above(kmax, 'Genetic Algorithm'):.0f}% above the optimum. "
    "Its work did grow quickly, though (by a factor of "
    f"{SCALE_I[kmax]['astar_h2_nodes_expanded'] / SCALE_I[PELLETS[0]]['astar_h2_nodes_expanded']:.0f} from "
    f"{PELLETS[0]} to {kmax} pellets), whereas local search needs a handful of orders in memory and k table "
    "look-ups per evaluation whatever the size. We therefore expect - but did not test - that for much "
    "larger instances Simulated Annealing or random-restart Hill Climbing on the pellet order becomes the "
    "practical choice, at the price of losing the optimality guarantee.", align="justify")

doc.heading("5.2 Where each algorithm fails or struggles", 2)
doc.bullets([
    f"**BFS** - finds the fewest steps, not the lowest cost: {n(s(L, 'BFS', 'path_cost'))} instead of {n(opt)}, "
    f"because it walks through danger cells. It also has the largest memory footprint "
    f"({n(s(L, 'BFS', 'max_nodes_in_memory'))} nodes, {n(s(L, 'BFS', 'peak_memory_kib'))} KiB).",
    f"**DFS** - the fastest of all ({n(s(L, 'DFS', 'nodes_expanded'))} expansions) but returns "
    f"{'an' if str(s(L, 'DFS', 'steps'))[0] == '8' else 'a'} {s(L, 'DFS', 'steps')}-step path of cost {n(s(L, 'DFS', 'path_cost'))}, {s(L, 'DFS', 'path_cost') / opt:.1f} "
    "times the optimum. Without the explored set it would not even terminate.",
    f"**UCS** - optimal, but blind: it expands {n(ucs_exp)} nodes, "
    f"{ucs_exp / REACH[L] * 100:.0f}% of the state space, in all directions before it reaches the goal.",
    f"**IDS** - the same solution as BFS with almost no memory ({n(s(L, 'IDS', 'max_nodes_in_memory'))} nodes), "
    f"paid for with {n(s(L, 'IDS', 'nodes_expanded'))} expansions, "
    f"{s(L, 'IDS', 'nodes_expanded') / s(L, 'BFS', 'nodes_expanded'):.0f} times those of BFS: it restarts from the "
    "root for every depth limit and, being a tree search, explores the same states again and again. It is by "
    f"far the slowest method ({ms(s(L, 'IDS', 'time_ms'))} ms): on larger instances it would run out of time "
    "long before it ran out of memory.",
    f"**Greedy Best-First** - not optimal ({n(g1['path_cost'])} and {n(g2['path_cost'])}), and its behaviour "
    f"depends completely on the heuristic: {n(g2['nodes_expanded'])} expansions with h2 but "
    f"{n(g1['nodes_expanded'])} with h1, which leads it into a basin that it has to search completely "
    "(Section 3.3). It is fast only with h2.",
    f"**A*** - no weakness with h2 on these layouts. With the weaker heuristic h1 it still expands "
    f"{n(a1_exp)} nodes on the large layout ({a1_exp / a2_exp:.0f} times as many as with h2), which shows "
    "that its efficiency is entirely the heuristic's. Its memory grows with the frontier, which would become "
    "the limit on much larger instances.",
    f"**Hill Climbing** - stops on the first plateau it cannot leave by a strict improvement: on the main "
    f"layout {RUNS - hc['optimal_runs']} of {RUNS} runs are not optimal, and the result varies between "
    f"{hc['best']} and {hc['worst']} depending on the random start.",
    f"**Simulated Annealing** - reliable only when it is given enough iterations: with fast cooling "
    f"({sa_grid_cool[0]['cooling_rate']:g}) it reaches the optimum in {pct(sa_grid_cool[0]):.0f}% of the runs, fewer "
    f"than plain hill climbing. It has three parameters to set and gives no guarantee, and on the official "
    f"layouts it is no better than {n(BASE_N)} random orders; its advantage only shows on larger mazes "
    "(Section 4.6).",
    f"**Genetic Algorithm** - the slowest local-search method ({ms(ga['time_ms'])} ms per run) and the one with "
    "the most parameters; small populations and strong selection make it converge too early, crossover "
    "brought no measurable benefit, and on the larger mazes it was the weakest of the three methods.",
    "**All local-search methods** - they can never prove that their answer is optimal. We only know that "
    "they found the optimum because A* and UCS told us what it is.",
])
assert pct(sa_grid_cool[0]) < pct(hc_tuned)

# =============================================================================== 6 conclusion
doc.heading("6. Conclusions", 1)
doc.bullets([
    "Two admissible and consistent heuristics were designed from relaxed problems, proved correct and "
    "verified on every state. The more informed one (h2) cuts the work of A* by a factor of "
    f"{ucs_exp / a2_exp:.0f} compared with UCS on the main layout.",
    "A* with h2 is the best algorithm for this problem: optimal, complete and the fastest optimal method, "
    f"also on mazes far beyond the official size (Section 4.6). "
    "Greedy Best-First shows that a heuristic alone, without the path cost, gives fast but unreliable answers.",
    "Recasting the problem as \"choose a priority order of the pellets\" made local search applicable. "
    f"On the main layout Hill Climbing stops on a plateau in about half of its runs; Simulated Annealing and "
    f"the Genetic Algorithm found the optimum in all {RUNS} runs once their budget was large enough; random "
    "restarts are the cheapest remedy on a landscape this small.",
    "The parameter study showed that, for all three local-search methods, reliability is mostly a matter of "
    "how many evaluations are spent, and that two textbook ingredients of the GA - crossover and elitism - "
    "did not help here. Comparing with random sampling was essential: on the official layouts it does as "
    "well as simulated annealing and the genetic algorithm, and only the larger mazes showed that the "
    "methods really search (there, random sampling ends "
    f"{above(kmax, 'Random sampling'):.0f}% above the optimum and simulated annealing "
    f"{above(kmax, 'Simulated Annealing'):.0f}%).",
    "The comparison of all nine algorithms shows the general trade-off: guarantees (UCS, A*) cost memory, "
    "speed without guarantees (DFS, Greedy, Hill Climbing) costs solution quality, and knowledge about the "
    "problem - a heuristic or a good representation - is what improves both at once.",
])

# =============================================================================== references
doc.heading("References", 1)
doc.numbered([
    "S. Russell and P. Norvig, __Artificial Intelligence: A Modern Approach__, 4th edition, Pearson, 2021 - "
    "Chapter 3 (informed search, heuristic functions, relaxed problems) and Chapter 4 (local search).",
    "CSAI 301 lecture material on heuristic search and local search.",
    "P. E. Hart, N. J. Nilsson and B. Raphael, \"A Formal Basis for the Heuristic Determination of Minimum "
    "Cost Paths\", IEEE Transactions on Systems Science and Cybernetics, 4(2), 1968 (A*).",
    "S. Kirkpatrick, C. D. Gelatt and M. P. Vecchi, \"Optimization by Simulated Annealing\", Science, "
    "220(4598), 1983.",
    "L. Davis, \"Applying Adaptive Algorithms to Epistatic Domains\", Proc. IJCAI, 1985 (order crossover).",
    "Python Software Foundation, The Python Standard Library documentation: `heapq`, `random`, `timeit`, "
    "`tracemalloc`. https://docs.python.org/3/library/",
    "J. D. Hunter, \"Matplotlib: A 2D Graphics Environment\", Computing in Science & Engineering, 9(3), 2007 "
    "(used for the figures only).",
], size=10)
doc.heading("Use of AI tools", 1)
doc.para(
    "In line with the course policy on outside sources, we state that an AI assistant (Claude, by Anthropic) "
    "was used in this project: it helped to write and test the code, to produce the figures and to draft "
    "this report. No ready-made search or optimisation library is used; every algorithm is implemented in "
    "the submitted code. The team reviewed the code and the results and is responsible for the whole "
    "submission.", size=10, align="justify")

# =============================================================================== appendices
doc.heading("Appendix A. How to Run the Code", 1)
doc.para("From the `code` folder (Python 3; Matplotlib is needed only for the figures):", space_after=3,
         keep_with_next=True)
doc.code(
    "pip install -r requirements.txt               # only needed for run_phase1.py / run_phase2.py\n"
    "python main.py                                # all nine algorithms on the large layout\n"
    "python main.py -a astar --heuristic h2        # A* with the MST heuristic\n"
    "python main.py -a hc sa ga --seed 7           # local search with seed 7\n"
    "python run_phase2.py                          # all Phase II tables and figures -> results/phase2\n"
    "python run_phase2.py --quick                  # fast check: no parameter or scaling study\n"
    "python run_phase1.py                          # the Phase I experiments (unchanged)\n"
    "python -m unittest discover -s tests -v       # unit tests of both phases")
doc.heading("Appendix B. All Algorithms on the Small and Medium Layouts", 1)
for name, expected in (("small", T_ALL_SMALL), ("medium", T_ALL_MEDIUM)):
    rows = []
    for r in COMP[name]:
        cost = n(r["cost"]) if not r["cost_range"] else f"{r['cost']:.1f} ({r['cost_range'][0]}-{r['cost_range'][1]})"
        rows.append([r["algorithm"], cost, r["found_optimum"], ms(r["time_ms"]), n(r["peak_memory_kib"]),
                     n(r["memory_items"]), n(r["effort"])])
    table(expected,
          ["Algorithm", "Solution cost", "Optimum found", "Time (ms)", "Memory (KiB)", "Items in memory", "Effort"],
          rows, widths_cm=[4.0, 2.6, 2.4, 1.9, 2.0, 2.0, 1.7], align=["l", "r", "c", "r", "r", "r", "r"],
          caption=f"All algorithms on the {name} layout ({n(REACH[name])} reachable "
                  f"states, optimal cost {OPT[name]}).", size=9, bold_first_col=True)
doc.heading("Appendix C. Solution Paths on the Large Layout", 1)
table(T_PATHS,
      ["Algorithm", "Cost", "Solution path (U = up, R = right, D = down, L = left)"],
      [[a, n(s(L, a, "path_cost")), f"`{s(L, a, 'solution')}`"] for a in UNINFORMED + INFORMED],
      widths_cm=[2.4, 1.1, 13.1], caption="Solution paths of the eight search runs on the large layout.",
      size=8, stripe=False)

assert doc.figure_no == F_SUMMARY and doc.table_no == T_PATHS, (doc.figure_no, doc.table_no)
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("written", OUT)
