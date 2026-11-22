"""Builds Phase1_Report.docx from the Phase I results (results/phase1 of the Phase1 code folder).

Usage: build_phase1_report.py [results folder] [output .docx] [code folder]

Every number in the text is read from results.json (written by run_phase1.py) or, for the
tiny layout and the danger-cell counts, recomputed with the project code; the facts the
prose relies on are asserted, so the report cannot silently drift from the data.
"""
import json
import sys
from pathlib import Path

from docbuilder import Doc
from team import title_page

PROJECT = Path(__file__).resolve().parent.parent
CODE = Path(sys.argv[3]) if len(sys.argv) > 3 else PROJECT / "Phase1" / "code"
RESULTS = Path(sys.argv[1]) if len(sys.argv) > 1 else CODE / "results" / "phase1"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else PROJECT / "Phase1" / "report" / "Phase1_Report.docx"
FIG = RESULTS / "figures"

data = json.loads((RESULTS / "results.json").read_text(encoding="utf-8"))
metrics = {(r["layout"], r["algorithm"]): r for r in data["metrics"]}
sizes = {s["layout"]: s for s in data["state_space"]}
trade = {t["layout"]: t for t in data["tradeoff"]}
graph = {g["layout"]: g for g in data["state_graph"]}
variants = {(r["layout"], r["variant"]): r for r in data["ids_variants"]}
ids_iterations = {name: [r for r in data["ids_iterations"] if r["layout"] == name]
                  for name in ("small", "medium", "large")}
env = data["environment"]
ALGS = ["BFS", "DFS", "UCS", "IDS"]
LAYOUTS = ["small", "medium", "large"]
TEXTBOOK, MEMO = "IDS (textbook)", "IDS with memo table"


def m(layout, algorithm, key):
    return metrics[(layout, algorithm)][key]


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


sys.path.insert(0, str(CODE))
from pacman_search.layouts import load_problem  # noqa: E402
from pacman_search.uninformed import UNINFORMED_ALGORITHMS  # noqa: E402

LETTER = {"U": "UP", "R": "RIGHT", "D": "DOWN", "L": "LEFT"}
PROBLEMS = {name: load_problem(name) for name in LAYOUTS}


def danger_entries(layout, algorithm):
    """How many moves of the returned plan enter a danger cell (replayed in the model)."""
    problem = PROBLEMS[layout]
    states, cost = problem.execute([LETTER[c] for c in m(layout, algorithm, "solution")])
    assert cost == m(layout, algorithm, "path_cost")
    return sum(1 for state in states[1:] if state.pos in problem.danger_cells)


L = "large"
opt = m(L, "UCS", "path_cost")
bfs_cost, dfs_cost = m(L, "BFS", "path_cost"), m(L, "DFS", "path_cost")
reach = sizes[L]["reachable"]
N_L, K_L = sizes[L]["free_cells"], sizes[L]["pellets"]
bfs_danger, ucs_danger = danger_entries(L, "BFS"), danger_entries(L, "UCS")
danger_extra = PROBLEMS[L].danger_cost - 1
same_bfs_ids = all(m(name, "BFS", "solution") == m(name, "IDS", "solution") for name in LAYOUTS)
ids_ratio = m(L, "IDS", "nodes_expanded") / m(L, "BFS", "nodes_expanded")
ids_time_ratio = m(L, "IDS", "time_ms") / m(L, "BFS", "time_ms")
text_large, memo_large = variants[(L, TEXTBOOK)], variants[(L, MEMO)]
share = {name: {a: m(name, a, "nodes_expanded") / sizes[name]["reachable"] for a in ALGS} for name in LAYOUTS}
last_iteration, previous_iteration = ids_iterations[L][-1], ids_iterations[L][-2]
d_large = graph[L]["solution_depth"]
restart_only = graph[L]["restart_only_expansions"]
restart_factor = restart_only / m(L, "BFS", "nodes_expanded")
tree_factor = m(L, "IDS", "nodes_expanded") / restart_only
dfs_ratio = {name: m(name, "DFS", "path_cost") / m(name, "UCS", "path_cost") for name in LAYOUTS}
dfs_off_path = {name: m(name, "DFS", "nodes_expanded") - m(name, "DFS", "steps") for name in LAYOUTS}

# The tiny layout (search trees): run the four algorithms again to describe the pictures.
tiny = load_problem("tiny")
tiny_run = {key: search(tiny) for key, search in UNINFORMED_ALGORITHMS.items()}
tiny_size = tiny.state_space_report()
tiny_limits = sorted({max(1, tiny_run["ids"].depth // 4), max(1, tiny_run["ids"].depth // 2),
                      max(1, 3 * tiny_run["ids"].depth // 4), tiny_run["ids"].depth})

# ---- facts the prose relies on: fail loudly if the experiments ever change them ----
assert all(graph[name]["states"] == sizes[name]["reachable"] for name in LAYOUTS)
assert all(m(name, "UCS", "cost_optimal") for name in LAYOUTS)
assert all(m(name, "UCS", "path_cost") == trade[name]["optimal_cost"] for name in LAYOUTS)
assert all(trade[name]["genuine_tradeoff"] for name in LAYOUTS)
assert all(m(name, a, "steps") == trade[name]["fewest_steps"] for name in LAYOUTS for a in ("BFS", "IDS"))
assert all(m(name, "BFS", "path_cost") > m(name, "UCS", "path_cost") for name in LAYOUTS)
assert same_bfs_ids
assert m(L, "BFS", "steps") + bfs_danger * danger_extra == bfs_cost and ucs_danger == 0
assert sizes[L]["valid"] - sizes[L]["reachable"] == 128 and sizes["small"]["valid"] - sizes["small"]["reachable"] == 24
assert sizes["medium"]["valid"] == sizes["medium"]["reachable"]
assert all(m(name, "DFS", "time_ms") == min(m(name, a, "time_ms") for a in ALGS) for name in LAYOUTS)
assert all(m(name, "DFS", "path_cost") == max(m(name, a, "path_cost") for a in ALGS) for name in LAYOUTS)
assert all(m(name, "DFS", "nodes_expanded") == min(m(name, a, "nodes_expanded") for a in ALGS) for name in LAYOUTS)
assert m(L, "UCS", "nodes_expanded") < m(L, "BFS", "nodes_expanded")
assert all(m(name, "UCS", "nodes_expanded") > m(name, "BFS", "nodes_expanded") for name in ("small", "medium"))
assert graph[L]["states_cheaper_than_optimum"] < 0.6 * graph[L]["states_shallower_than_solution"]
assert graph["small"]["states_cheaper_than_optimum"] > graph["small"]["states_shallower_than_solution"]
assert graph["medium"]["states_cheaper_than_optimum"] < graph["medium"]["states_shallower_than_solution"]
assert all(m(name, "BFS", "nodes_expanded") <= graph[name]["states_shallower_than_solution"] for name in LAYOUTS)
assert all(m(name, "UCS", "nodes_expanded") >= graph[name]["states_cheaper_than_optimum"] for name in LAYOUTS)
assert m("medium", "IDS", "nodes_expanded") > m(L, "IDS", "nodes_expanded") > m("small", "IDS", "nodes_expanded")
assert m("medium", "IDS", "steps") > m(L, "IDS", "steps")
assert all(0.45 < share[name]["BFS"] < 0.56 for name in LAYOUTS)
assert last_iteration["expanded"] < previous_iteration["expanded"]
assert all(variants[(name, TEXTBOOK)]["nodes_expanded"] == m(name, "IDS", "nodes_expanded") for name in LAYOUTS)
assert all(variants[(name, TEXTBOOK)]["time_ms"] == m(name, "IDS", "time_ms") for name in LAYOUTS)
assert all(variants[(name, MEMO)]["path_cost"] == m(name, "IDS", "path_cost") for name in LAYOUTS)
assert memo_large["nodes_expanded"] >= restart_only
assert max(m(L, "DFS", "max_frontier"), m(L, "IDS", "max_frontier")) < 30
assert dfs_ratio["small"] < dfs_ratio["medium"] < dfs_ratio["large"]
assert (tiny_run["bfs"].path_cost, tiny_run["bfs"].depth) == (12, 8)
assert (tiny_run["ucs"].path_cost, tiny_run["ucs"].depth) == (10, 10)
assert (tiny_run["dfs"].path_cost, tiny_run["dfs"].depth) == (16, 12)
assert tiny_run["ids"].actions == tiny_run["bfs"].actions and tiny_limits == [2, 4, 6, 8]
assert tiny_size["reachable"] == 45

doc = Doc()
doc.doc.sections[0].different_first_page_header_footer = True
title_page(doc, "Phase I Report", "Problem Modeling and Uninformed Search (BFS, DFS, UCS, IDS)", "21 November 2026")
doc.page_numbers()


def table(expected, *args, **kwargs):
    doc.table(*args, **kwargs)
    assert doc.table_no == expected, ("table number", doc.table_no, expected)


def figure(expected, *args, **kwargs):
    doc.figure(*args, **kwargs)
    assert doc.figure_no == expected, ("figure number", doc.figure_no, expected)


# numbers used in cross-references
T_MODEL, T_SIZE, T_ALGS, T_RESULTS, T_PATHS, T_TRADE, T_IDS, T_THEORY, T_OTHER_PATHS = range(1, 10)
F_LAYOUTS, F_IDS_ITER, F_SCALING, F_EXPLORED, F_TREES, F_FRONTIER, F_IDS_TREES = range(1, 8)
S_TRADE, S_IDS = "5.2", "5.3"

# ------------------------------------------------------------------------------- summary
doc.heading("Summary", 1)
doc.callout([
    "**Problem.** Pac-Man must eat every food pellet in a maze guarded by stationary ghosts. A state is "
    "Pac-Man's cell together with the set of pellets still uneaten, so the state space is about "
    "(free cells) x 2^{pellets}. Our three official layouts have "
    f"{n(sizes['small']['reachable'])}, {n(sizes['medium']['reachable'])} and {n(sizes['large']['reachable'])} "
    "reachable states - inside the required 1,000-10,000 range.",
    "**Step costs are not uniform.** Entering a cell next to a ghost costs 5 instead of 1. This is what "
    "separates the algorithms: on all three layouts even the best plan with the fewest steps costs more than "
    "the cheapest plan.",
    f"**Main result (large layout).** UCS returns the optimal cost {n(opt)}. BFS and IDS both return a "
    f"{m(L, 'BFS', 'steps')}-step path that costs {n(bfs_cost)} ({(bfs_cost / opt - 1) * 100:.0f}% more), and DFS "
    f"returns a path of cost {n(dfs_cost)} ({dfs_cost / opt:.1f} times the optimum) after expanding only "
    f"{n(m(L, 'DFS', 'nodes_expanded'))} nodes.",
    f"**Cost of each strategy.** BFS expands {n(m(L, 'BFS', 'nodes_expanded'))} nodes and keeps up to "
    f"{n(m(L, 'BFS', 'max_nodes_in_memory'))} nodes in memory. IDS never holds more than "
    f"{n(m(L, 'IDS', 'max_nodes_in_memory'))} nodes, but it repeats its work and expands "
    f"{n(m(L, 'IDS', 'nodes_expanded'))} nodes ({ids_ratio:.0f} times BFS).",
])
doc.toc("1-2")

# ------------------------------------------------------------------------------- 1 problem
doc.heading("1. Problem Description", 1, new_page=True)
doc.para(
    "Our problem is the food-collection task of Pac-Man. Pac-Man moves through a maze, one cell at a time, "
    "and has to eat all the food pellets. Ghosts stand guard in the maze: Pac-Man cannot enter a ghost's cell, "
    "and moving into a cell directly next to a ghost is risky. We want a sequence of moves that eats every "
    "pellet at the lowest total cost. The problem is fully observable, deterministic and has a single agent, "
    "so it can be solved offline by search.", align="justify")
doc.para(
    f"We use four hand-made maze layouts (Figure {F_LAYOUTS}). The tiny layout is only used to draw search "
    "trees. The small, medium and large layouts are the official instances; the large layout is our "
    "main instance. The names refer to the size of the state space, not of the grid: the large layout is a "
    "compact 9x9 maze, but its 8 pellets give 2^{8} = 256 food combinations for every cell.", align="justify")
figure(F_LAYOUTS, FIG / "layouts.png",
       "The four layouts. Numbers next to the pellets are the pellet indices (bit positions in the "
       "food mask). Red frames mark the danger cells next to a ghost; entering them costs 5.",
       width_cm=12.5)

# ------------------------------------------------------------------------------- 2 model
doc.heading("2. Problem Modeling", 1)
doc.heading("2.1 Formal definition", 2)
table(T_MODEL,
      ["Component", "Definition in our model"],
      [
          ["State", "A pair (pos, food). pos = (row, col) is the cell Pac-Man stands on. food is a bitmask with "
                    "one bit per pellet: bit i is 1 while pellet i has not been eaten. Example on the large "
                    "layout: ((1,1), 11111111) is Pac-Man on the start cell with all 8 pellets left."],
          ["Initial state", "(start cell, all k food bits set to 1)."],
          ["Goal test", "food = 0, i.e. every pellet has been eaten. The final position does not matter, so "
                        "there are many goal states."],
          ["Actions", "UP, RIGHT, DOWN, LEFT (always generated in this order). An action is applicable only if "
                      "the target cell is neither a wall nor a ghost."],
          ["Transition model", "RESULT((pos, food), a) = (pos', food'), where pos' is the neighbouring cell in "
                               "direction a, and food' is food with the bit of the pellet in pos' cleared (if "
                               "there is one). The model is deterministic."],
          ["Step cost", "c(s, a, s') = 5 if pos' is a danger cell (directly above, below, left or right of a "
                        "ghost), otherwise 1."],
          ["Path cost", "The sum of the step costs of the path. It is also our measure of solution quality."],
      ],
      widths_cm=[3.0, 13.6], caption="The search problem.", size=9.5, bold_first_col=True)
doc.para(
    "**Why the state must contain the food mask.** Pac-Man's position alone is not a state: standing on the "
    "same cell with different pellets left requires different future moves. With the mask, everything the "
    "future depends on is inside the state, so a search algorithm can safely treat two paths that reach the "
    "same (pos, food) pair as equivalent and keep only one of them.", align="justify")

doc.heading("2.2 Size of the state space", 2)
doc.para(
    "Let N be the number of free cells (cells that are not walls or ghosts) and k the number of pellets. "
    "We estimated the size in three steps, from a rough bound to the exact count:", align="justify")
doc.numbered([
    "**Upper bound: N x 2^{k}.** Every free cell combined with every subset of remaining pellets.",
    "**Valid states: N x 2^{k} - k x 2^{k-1}.** A state in which Pac-Man stands on a pellet that is still "
    "marked uneaten is impossible, because entering the cell eats it. For each of the k pellet cells exactly "
    "half of the 2^{k} masks (those with that pellet's bit set) are impossible, which removes k x 2^{k-1} states.",
    "**Reachable states: exact count.** The function `count_reachable_states()` runs a breadth-first sweep "
    "from the initial state over the whole state graph (without a goal test) and counts the states it finds.",
])
table(T_SIZE,
      ["Layout", "Grid", "Free cells N", "Pellets k", "Ghosts", "Danger cells", "N x 2^{k}", "Valid", "Reachable"],
      [[name, sizes[name]["grid"], n(sizes[name]["free_cells"]), n(sizes[name]["pellets"]), n(sizes[name]["ghosts"]),
        n(sizes[name]["danger_cells"]), n(sizes[name]["upper_bound"]), n(sizes[name]["valid"]),
        n(sizes[name]["reachable"])] for name in LAYOUTS],
      widths_cm=[1.8, 1.6, 2.0, 1.7, 1.5, 2.0, 2.0, 1.8, 2.2], align=["l"] + ["c"] * 8,
      caption="State-space size of the three official layouts. All three counts are between 1,000 and 10,000.")
gap = sizes[L]["valid"] - sizes[L]["reachable"]
doc.para(
    f"For the large layout: {N_L} x {2 ** K_L} = {n(sizes[L]['upper_bound'])}; subtracting {K_L} x "
    f"{2 ** (K_L - 1)} = {n(K_L * 2 ** (K_L - 1))} impossible "
    f"states leaves {n(sizes[L]['valid'])}; the sweep finds {n(sizes[L]['reachable'])} reachable states. The "
    f"missing {n(gap)} states are valid on paper but can never occur: the corridor cells (6,1) and (6,7) each lie "
    "between two pellets and have no other entrance, so Pac-Man cannot stand there while both neighbouring "
    "pellets are still uneaten (2 cells x 2^{6} masks = 128). The same effect removes 24 states in the small "
    "layout (the three cells between pellets 2 and 3 in the bottom corridor, 3 x 2^{3}); in the medium layout "
    "every valid state is reachable. Adding one pellet doubles the state space, while adding one free cell "
    "only adds 2^{k} states - the number of pellets is what makes this problem hard.", align="justify")

doc.heading("2.3 Modeling assumptions", 2)
doc.bullets([
    "The maze is fully known in advance and nothing changes while Pac-Man plans (static, fully observable, "
    "deterministic environment; offline search).",
    "Ghosts do not move. They act as guards: their own cell cannot be entered, and the danger they represent "
    "is modelled as a higher step cost (5 instead of 1) for entering one of the up-to-four cells next to them.",
    "Pac-Man moves one cell per action in the four compass directions; there is no \"stay\" action and no "
    "diagonal move. Cells may be visited any number of times.",
    "A pellet is eaten the moment Pac-Man enters its cell and never reappears. There are no power pellets, "
    "no score and no time limit; the only quantity to minimise is the path cost.",
    "The outer border of every maze is a wall (cells outside the grid are treated as walls in any case), and "
    "every pellet is reachable from the start cell; the code rejects a layout with an unreachable pellet.",
])

# ------------------------------------------------------------------------------- 3 algorithms
doc.heading("3. Uninformed Search Algorithms", 1)
doc.para(
    "All four algorithms follow their textbook descriptions [1, 2] and are written from scratch in "
    "`pacman_search/uninformed.py`. They use only the problem interface (initial state, successors, goal "
    "test); the only library data structures are Python's `deque` (FIFO queue) and `heapq` (binary heap) "
    "[3]. The state graph contains many different paths to the same state, so each algorithm needs a rule "
    f"for repeated states; the rules differ, and so does their price (Table {T_ALGS}).", align="justify")
table(T_ALGS,
      ["Algorithm", "Frontier", "Repeated states", "Goal test", "Expands first"],
      [
          ["BFS", "FIFO queue", "Set of reached states; a state is queued once", "When a node is generated "
           "(early test)", "The shallowest node"],
          ["DFS", "LIFO stack", "Set of expanded states; duplicates on the stack are skipped when popped",
           "When a node is popped", "The deepest node"],
          ["UCS", "Priority queue ordered by path cost g", "Table of the cheapest known cost per state; "
           "outdated queue entries are skipped", "When a node is popped (late test)", "The cheapest node"],
          ["IDS", "LIFO stack, depth-limited", "Only loops on the current path are avoided; nothing else is "
           "remembered (textbook tree search)", "When a node is popped", "The deepest node within the current "
           "limit"],
      ],
      widths_cm=[1.7, 3.0, 5.3, 3.2, 3.4], caption="Implementation of the four algorithms.", size=9,
      bold_first_col=True)
doc.para("**Implementation decisions worth explaining:**", space_after=3)
doc.bullets([
    "**BFS tests the goal early, UCS late.** In BFS the first time a state is generated is already along a "
    "shortest path, so we can stop when a goal is generated. In UCS a goal that is generated may still be "
    "reachable more cheaply through a node that has not been expanded yet, so the test must wait until the "
    "goal is removed from the priority queue - this is what makes UCS optimal.",
    "**DFS has an explored set.** Without any check for repeated states DFS would walk in circles in the "
    "maze forever. We chose an explored set, which makes DFS complete on our finite state space at the price "
    "of remembering every expanded state. (The check on the current path that we use for IDS would also "
    "stop the loops.)",
    "**IDS is kept as a tree search.** It only refuses to step onto a state that is already on its current "
    "path, so it stores nothing but its stack and that path. This keeps the small memory that IDS is known "
    "for; the price is that the same state is explored again through every different path that reaches it. "
    "We also wrote a variant with a memo table (`use_memo=True`) that is much faster but needs as much "
    f"memory as BFS; Section {S_IDS} compares the two.",
    "**Fixed action order.** Successors are always generated in the order UP, RIGHT, DOWN, LEFT and ties are "
    "broken first-in-first-out, so every run gives exactly the same result. For BFS and IDS this order "
    f"also decides which of several equally deep solutions is returned (Section {S_TRADE}); for DFS it decides "
    "the whole path.",
])
doc.para(
    "**Measurements** (identical for all algorithms, defined in `search_core.py`): __nodes generated__ = every "
    "successor produced, including duplicates that are discarded, plus the root (for IDS: the root of every "
    "iteration); __nodes expanded__ = nodes whose successors were generated; __maximum frontier size__ = "
    "largest number of nodes waiting in the frontier; __maximum nodes in memory__ = largest value of frontier "
    "size + remembered states (the reached or explored table, or for IDS the current path); __running time__ "
    "= wall-clock time of the search call.", align="justify")

# ------------------------------------------------------------------------------- 4 setup
doc.heading("4. Experimental Setup", 1)
doc.para(
    f"Experiments were run with Python {env['python']} ({env['implementation']}) on {env['system']} "
    f"({env['machine']}). The script `run_phase1.py` produces every table and figure of this report and the "
    "numbers used in the analysis; they are stored in `results/phase1` (the few values quoted for the tiny "
    "layout come from `python main.py -l tiny`). `README.md` in the code folder explains how to run "
    "everything. The algorithms are deterministic (fixed action order and FIFO tie-breaking), so paths, costs "
    "and all node counts are exactly reproducible. Every returned plan is replayed in the problem model to "
    "confirm that it reaches the goal and that the reported cost is correct, and UCS is checked against an "
    "independent brute-force solver in the unit tests. The figures are drawn with Matplotlib [4].",
    align="justify")
doc.para(
    f"**Running time.** Each algorithm is run up to {data['timing_repeats']} times per layout (a slow "
    "algorithm is stopped after 2 seconds, with at least 3 runs) and the __fastest__ run is reported. "
    "Every run does exactly the same work, and anything that disturbs a run - another program, the "
    "operating system moving the process to a slower processor core, a hot processor - can only make it "
    "slower, so the fastest run is the best estimate; the documentation of Python's `timeit` module gives "
    "the same advice [3]. The garbage collector is switched off during a timed run, all timings are taken "
    "before any search is traced for a picture, the script pauses for a few seconds before each layout, and "
    "Python was pinned to one fast processor core. Even so, times differ by several percent from one session "
    "to the next, so our conclusions rest on the node counts, which are exact.", align="justify")
doc.para(
    "**Memory.** Peak memory is measured in a separate run with `tracemalloc` [3]. The figure in KiB depends "
    "on how Python stores its containers (a `set` reserves memory in large jumps), so we use it only as a "
    "rough indication; __maximum nodes in memory__ is the quantity we compare with the theory.",
    align="justify")

# ------------------------------------------------------------------------------- 5 results
doc.heading("5. Results", 1)
doc.heading("5.1 Measurements on the three layouts", 2)
doc.para(
    f"Table {T_RESULTS} gives all measurements. The pattern is the same on every layout: UCS is the only "
    "algorithm that returns the cheapest path; BFS and IDS return a path with the fewest steps, which is more "
    "expensive because it crosses danger cells; DFS expands the fewest nodes, is the fastest, and returns by "
    "far the worst path. BFS and IDS return exactly the same path on all three layouts.", align="justify")
rows = []
for name in LAYOUTS:
    for a in ALGS:
        rows.append([name if a == "BFS" else "", a, n(m(name, a, "path_cost")), n(m(name, a, "steps")),
                     n(m(name, a, "nodes_generated")), n(m(name, a, "nodes_expanded")),
                     n(m(name, a, "max_frontier")), n(m(name, a, "max_nodes_in_memory")),
                     ms(m(name, a, "time_ms")), n(m(name, a, "peak_memory_kib"), 0),
                     "yes" if m(name, a, "cost_optimal") else "no",
                     "yes" if m(name, a, "step_optimal") else "no"])
table(T_RESULTS,
      ["Layout", "Algorithm", "Path cost", "Steps", "Generated", "Expanded", "Max frontier", "Max in memory",
       "Time (ms)", "Peak memory (KiB)", "Lowest cost", "Fewest steps"],
      rows, widths_cm=[1.3, 1.5, 1.1, 1.0, 1.6, 1.5, 1.3, 1.4, 1.3, 1.5, 1.2, 1.2],
      align=["l", "l"] + ["r"] * 8 + ["c", "c"],
      caption="Results on the three official layouts (the large layout is the main instance; its optimal cost "
              f"is {n(opt)}). The last two columns say whether the returned path has the lowest possible cost "
              "and the fewest possible steps.", stripe=False, size=8, keep_blocks=4)
doc.para(
    f"Table {T_PATHS} lists the paths on the main layout (Figure {F_EXPLORED} in Section 7 draws them in the "
    "maze); the paths on the other two layouts are in the appendix.", align="justify")
table(T_PATHS,
      ["Algorithm", "Solution path"],
      [[a, f"`{m(L, a, 'solution')}`"] for a in ALGS],
      widths_cm=[1.9, 14.7], size=8.5, bold_first_col=True, stripe=False,
      caption="Solution paths on the large layout (U = up, R = right, D = down, L = left).")

doc.heading(f"{S_TRADE} Fewest steps versus lowest cost", 2)
table(T_TRADE,
      ["Layout", "Fewest steps possible", "Cheapest plan with that many steps", "Optimal cost C*",
       "Steps of the cheapest plan", "Returned by BFS and IDS"],
      [[name, n(trade[name]["fewest_steps"]), f"cost {n(trade[name]['cheapest_cost_with_fewest_steps'])}",
        n(trade[name]["optimal_cost"]), n(trade[name]["fewest_steps_at_optimal_cost"]),
        f"{n(m(name, 'BFS', 'steps'))} steps, cost {n(m(name, 'BFS', 'path_cost'))}"] for name in LAYOUTS],
      widths_cm=[1.6, 2.6, 3.4, 2.4, 3.0, 3.6], align=["l"] + ["c"] * 5,
      caption="Fewest steps against lowest cost, computed exactly for each layout.")
lucky = [name for name in LAYOUTS if m(name, "BFS", "path_cost") == trade[name]["cheapest_cost_with_fewest_steps"]]
unlucky = [name for name in LAYOUTS if name not in lucky]
assert lucky == ["small"] and unlucky == ["medium", "large"]
doc.para(
    f"Table {T_TRADE} was computed with a uniform-cost search that uses a two-part cost - first (steps, cost), "
    "then (cost, steps) - in `step_cost_tradeoff()`. On every layout even the best plan among those with the "
    "fewest steps costs more than the optimum ("
    + ", ".join(f"{n(trade[name]['cheapest_cost_with_fewest_steps'])} against {n(trade[name]['optimal_cost'])}"
                for name in LAYOUTS)
    + "), so an algorithm that minimises the number of steps cannot be cost-optimal here. BFS and IDS do "
    "find the fewest steps, but among the plans with that many steps they simply return the first one they "
    "meet, which depends on the action order. On the small layout this happens to be the cheapest of them; "
    f"on the medium and large layouts it is not ({n(m('medium', 'BFS', 'path_cost'))} instead of "
    f"{n(trade['medium']['cheapest_cost_with_fewest_steps'])}, and {n(m(L, 'BFS', 'path_cost'))} instead of "
    f"{n(trade[L]['cheapest_cost_with_fewest_steps'])}).", align="justify")

doc.heading(f"{S_IDS} The two versions of IDS", 2)
table(T_IDS,
      ["Layout", "IDS version", "Nodes expanded", "Max frontier", "Max nodes in memory", "Time (ms)"],
      [[name if v == TEXTBOOK else "", "textbook (reported as IDS)" if v == TEXTBOOK else "with memo table",
        n(variants[(name, v)]["nodes_expanded"]), n(variants[(name, v)]["max_frontier"]),
        n(variants[(name, v)]["max_nodes_in_memory"]), ms(variants[(name, v)]["time_ms"])]
       for name in LAYOUTS for v in (TEXTBOOK, MEMO)],
      widths_cm=[1.8, 4.4, 2.7, 2.3, 3.2, 2.0], align=["l", "l", "r", "r", "r", "r"],
      caption="The textbook IDS, which only avoids loops on the current path, against the variant that "
              "remembers the states visited in the current iteration. Both return the same solution.",
      stripe=False)
doc.para(
    f"On the large layout the memo table cuts the work from {n(text_large['nodes_expanded'])} to "
    f"{n(memo_large['nodes_expanded'])} expansions and the time from {ms(text_large['time_ms'])} to "
    f"{ms(memo_large['time_ms'])} ms, but it stores {n(memo_large['max_nodes_in_memory'])} states - as many as "
    f"BFS ({n(m(L, 'BFS', 'max_nodes_in_memory'))}). The textbook version never holds more than "
    f"{n(text_large['max_nodes_in_memory'])} nodes. This is the time-memory trade-off of IDS, measured. We "
    "report the textbook version as \"IDS\" everywhere else, because its small memory is the reason for "
    "using IDS at all.", align="justify")

# ------------------------------------------------------------------------------- 6 analysis
doc.heading("6. Analysis: Theory versus Measurements", 1)
doc.para(
    "Notation: b = branching factor, d = depth of the shallowest solution, m = maximum depth of the search "
    "tree, C* = optimal path cost, e = smallest step cost, |S| = number of reachable states. In our state "
    f"graph b is small ({graph[L]['average_successors']:.1f} successors per state on average on the large "
    f"layout, at most 4), d = {m(L, 'BFS', 'steps')}, C* = {n(opt)}, e = 1 and |S| = {n(reach)}. The counts of "
    "states per depth and per cost that are quoted below are written to `state_graph.csv` by "
    "`state_graph_profile()`.", align="justify")
table(T_THEORY,
      ["Algorithm", "Complete?", "Optimal?", "Time (theory)", "Space (theory)", "Measured on the large layout"],
      [
          ["BFS", "Yes (b finite)", "Only if all step costs are equal. Here: fewest steps, not cheapest",
           "O(b^{d})", "O(b^{d})",
           f"{n(m(L, 'BFS', 'nodes_expanded'))} expanded, {n(m(L, 'BFS', 'max_nodes_in_memory'))} nodes in memory, "
           f"cost {n(bfs_cost)} (not optimal)"],
          ["DFS", "Tree search: no (loops). Our graph search: yes, the space is finite", "No",
           "O(b^{m})", "Tree search O(b m); our version O(|S|) for the explored set",
           f"{n(m(L, 'DFS', 'nodes_expanded'))} expanded, {n(m(L, 'DFS', 'max_nodes_in_memory'))} nodes in memory, "
           f"cost {n(dfs_cost)}"],
          ["UCS", "Yes (every step costs at least e > 0)", "Yes (cheapest path)",
           "O(b^{1 + floor(C*/e)})", "O(b^{1 + floor(C*/e)})",
           f"{n(m(L, 'UCS', 'nodes_expanded'))} expanded, {n(m(L, 'UCS', 'max_nodes_in_memory'))} nodes in memory, "
           f"cost {n(opt)} (optimal)"],
          ["IDS", "Yes", "Like BFS: fewest steps only", "O(b^{d})", "O(b d)",
           f"{n(m(L, 'IDS', 'nodes_expanded'))} expanded, {n(m(L, 'IDS', 'max_nodes_in_memory'))} nodes in memory, "
           f"cost {n(m(L, 'IDS', 'path_cost'))} (not optimal)"],
      ],
      widths_cm=[1.7, 2.8, 3.0, 2.2, 2.9, 4.0], caption="Properties of the four algorithms in theory [1] and in "
      "our experiment. BFS, DFS and UCS are graph searches on a finite space and expand each state at most "
      "once, so their work is also bounded by |S|. IDS is a tree search and has no such bound.", size=8.5,
      bold_first_col=True)

doc.heading("6.1 Completeness", 2)
doc.para(
    "All four algorithms found a solution on every layout, as theory predicts. BFS is complete whenever the "
    "branching factor is finite; UCS also needs every step to cost at least some e > 0 (here e = 1). A "
    "depth-first search without any check for repeated states is not complete in a maze because it can "
    "follow a loop forever; our explored set removes that problem on a finite state space. IDS is complete "
    "because its depth limit keeps growing until it reaches the shallowest solution; its check for loops on "
    "the current path only saves work.", align="justify")

doc.heading("6.2 Optimality", 2)
doc.para(
    f"Only UCS is optimal. On the large layout the cheapest plan costs {n(opt)} and uses {m(L, 'UCS', 'steps')} "
    f"steps, all of them into safe cells. BFS and IDS minimise the number of steps instead: their plan has "
    f"{m(L, 'BFS', 'steps')} steps, but {bfs_danger} of them enter danger cells (Figure {F_EXPLORED}), so it "
    f"costs {m(L, 'BFS', 'steps')} + {bfs_danger} x {danger_extra} = {n(bfs_cost)}. This is a direct demonstration of "
    f"the textbook statement that BFS is optimal only when all step costs are equal [1], and Table {T_TRADE} "
    "shows that it is not an accident of tie-breaking. DFS returns the first "
    f"solution it reaches: {m(L, 'DFS', 'steps')} steps at cost {n(dfs_cost)}. Its result depends on the order in "
    "which the actions are tried, not on any notion of quality.", align="justify")

doc.heading("6.3 Time", 2)
g_large, g_small, g_medium = graph[L], graph["small"], graph["medium"]
doc.para(
    f"BFS expanded {n(m(L, 'BFS', 'nodes_expanded'))} nodes, {share[L]['BFS'] * 100:.0f}% of "
    f"all reachable states, before the first goal was generated; UCS expanded {n(m(L, 'UCS', 'nodes_expanded'))} "
    f"({share[L]['UCS'] * 100:.0f}%). The two algorithms search different regions of the state graph. BFS "
    "expands states in order of depth and stops as soon as a goal is generated, so it expands at most the "
    f"states that are shallower than the solution depth d ({n(g_large['states_shallower_than_solution'])} on the "
    "large layout). UCS expands states in order of cost: all the states that can be reached for less than "
    f"C* ({n(g_large['states_cheaper_than_optimum'])}), and those with cost exactly C* that leave the queue "
    "before a goal does. On the large layout the UCS region is much smaller, because states whose short "
    "routes pass danger cells are far away in cost. On the small layout it is larger "
    f"({n(g_small['states_cheaper_than_optimum'])} states are cheaper than C* = {n(g_small['optimal_cost'])}, "
    f"{n(g_small['states_shallower_than_solution'])} are shallower than d = {g_small['solution_depth']}), and UCS "
    f"expands more nodes than BFS ({n(m('small', 'UCS', 'nodes_expanded'))} against "
    f"{n(m('small', 'BFS', 'nodes_expanded'))}). On the medium layout it is slightly smaller "
    f"({n(g_medium['states_cheaper_than_optimum'])} against {n(g_medium['states_shallower_than_solution'])}), but "
    f"UCS still needs a few more expansions ({n(m('medium', 'UCS', 'nodes_expanded'))} against "
    f"{n(m('medium', 'BFS', 'nodes_expanded'))}), because it cannot stop when a goal is merely generated and "
    "first has to work through states that cost exactly C*.", align="justify")
doc.para(
    f"DFS expanded only {n(m(L, 'DFS', 'nodes_expanded'))} nodes for a path of {m(L, 'DFS', 'steps')} steps. "
    "That is not a general strength of DFS but a property of this problem: there is no state from which the "
    "remaining pellets can no longer be eaten, so DFS never has to give up a whole branch and its "
    f"backtracking stays short. On the large layout only {dfs_off_path[L]} of its expanded states are not on "
    f"the returned path ({dfs_off_path['medium']} of {n(m('medium', 'DFS', 'nodes_expanded'))} on the medium "
    f"layout, {dfs_off_path['small']} of {n(m('small', 'DFS', 'nodes_expanded'))} on the small one).",
    align="justify")
doc.para(
    f"IDS expanded {n(m(L, 'IDS', 'nodes_expanded'))} nodes, {ids_ratio:.0f} times as many as BFS, and needed "
    f"about {ids_time_ratio:.0f} times as long. There are two reasons. First, every iteration starts again "
    f"from the root (Figure {F_IDS_ITER}): expanding every state within the limit exactly once in each of the "
    f"{d_large} unsuccessful iterations would already take {n(restart_only)} expansions, {restart_factor:.1f} "
    "times those of BFS. In a tree whose levels grow by a factor b these repeated iterations would only cost "
    "about 1/(b-1) of one breadth-first search; our state graph does not grow like that - the number of new "
    f"states per depth level rises slowly and never exceeds {n(g_large['largest_level'])} - so the shallow "
    "levels are a large part of the total and repeating them is expensive. Second, and more important here, "
    "IDS is a tree search: it does not notice when it reaches a state that it has already explored along "
    "another path, and a maze offers very many paths to the same state. This accounts for the rest, a "
    f"further factor of about {tree_factor:.0f}. The memo-table variant of Section {S_IDS} removes most of "
    f"this second effect and needs {n(memo_large['nodes_expanded'])} expansions.", align="justify")
figure(F_IDS_ITER, FIG / "ids_iterations_large.png",
       "Nodes expanded by IDS at each depth limit on the large layout. The last iteration is short "
       "because it stops at the first goal.", width_cm=11.5)
doc.para(
    f"Figure {F_SCALING} puts the three layouts side by side. BFS expands about half of the reachable states on "
    f"every layout ({', '.join(f'{share[name]['BFS'] * 100:.0f}%' for name in LAYOUTS)}), so its work grows in "
    "proportion to the size of the state space. UCS expands between "
    f"{min(share[name]['UCS'] for name in LAYOUTS) * 100:.0f}% and "
    f"{max(share[name]['UCS'] for name in LAYOUTS) * 100:.0f}%, depending on how far C* lies above d. The work "
    "of IDS does not follow the number of states at all: it is largest on the medium layout, which has fewer "
    f"states than the large one but the deepest solution (d = {m('medium', 'IDS', 'steps')} against "
    f"{m(L, 'IDS', 'steps')}) - the cost of a tree search grows with the depth, as O(b^{{d}}) says. DFS stays "
    f"between {min(m(name, 'DFS', 'nodes_expanded') for name in LAYOUTS)} and "
    f"{max(m(name, 'DFS', 'nodes_expanded') for name in LAYOUTS)} expansions, but its answers get worse "
    f"relative to the optimum ({', '.join(f'{dfs_ratio[name]:.1f}' for name in LAYOUTS[:-1])} and "
    f"{dfs_ratio[L]:.1f} times the optimal cost).", align="justify")
figure(F_SCALING, FIG / "scaling.png",
       "Nodes expanded by each algorithm on the three layouts (both axes logarithmic).", width_cm=11.5)

doc.heading("6.4 Memory", 2)
doc.para(
    f"BFS and UCS keep a wide frontier ({n(m(L, 'BFS', 'max_frontier'))} and {n(m(L, 'UCS', 'max_frontier'))} "
    f"nodes) and remember every reached state ({n(m(L, 'BFS', 'max_nodes_in_memory'))} and "
    f"{n(m(L, 'UCS', 'max_nodes_in_memory'))} nodes in memory), which is the exponential space of the theory "
    "(O(b^{d}) for BFS, O(b^{1 + floor(C*/e)}) for UCS). DFS and IDS keep a frontier of fewer than 30 nodes at "
    f"all times (Figure {F_FRONTIER} in Section 7), the linear behaviour expected from a stack (O(b m) for DFS, "
    "O(b d) for IDS). DFS also stores its explored set; that set stays small "
    f"({n(m(L, 'DFS', 'max_nodes_in_memory'))} nodes in total) only because DFS stops early, and in the worst "
    f"case it would grow to |S|. IDS stores nothing besides its stack and the current path: at most "
    f"{n(m(L, 'IDS', 'max_nodes_in_memory'))} nodes, about "
    f"{m(L, 'IDS', 'max_nodes_in_memory') / m(L, 'BFS', 'max_nodes_in_memory') * 100:.0f}% of what BFS needs, "
    "and this number depends on the depth of the solution only, not on the size of the state space. The "
    f"`tracemalloc` readings in Table {T_RESULTS} give the same order. The price of the small memory of IDS is "
    f"the running time of Section 6.3. With IDS we could not have both: the tree-search version has linear "
    f"memory but needs {n(text_large['nodes_expanded'])} expansions, and the memo-table version is fast but "
    f"stores as many states as BFS (Table {T_IDS}).", align="justify")

# ------------------------------------------------------------------------------- 7 visualization
doc.heading("7. Visualization of the Search", 1)
doc.para(
    f"Figure {F_EXPLORED} shows the explored states and the final path of every algorithm on the main layout. "
    "The same figure for the other two layouts is in the results folder, together with animated GIFs of the "
    "four searches.", align="justify")
figure(F_EXPLORED, FIG / "explored_large.png",
       "Explored states and returned path on the large layout. The darker a cell, the more of its 256 "
       f"food combinations were expanded while Pac-Man stood there. BFS and IDS enter danger cells "
       f"{bfs_danger} times; UCS walks back along the top row and uses the left passage, so it never comes "
       "near the ghost.", width_cm=13.0)
doc.para(
    "A search tree of the large layout has thousands of nodes, so the trees themselves "
    f"are drawn on the tiny layout ({tiny_size['reachable']} states), where they fit on a page (Figure "
    f"{F_TREES} for BFS, DFS and UCS, Figure {F_IDS_TREES} for IDS). The trees show the four strategies "
    "directly. BFS grows level by level; its "
    "solution eats the pellet below the start, comes back and then crosses the danger cell next to the ghost "
    f"({tiny_run['bfs'].depth} steps, cost {n(tiny_run['bfs'].path_cost)}). UCS postpones the expensive node "
    "and, after the first pellet, walks around the bottom of the maze instead "
    f"({tiny_run['ucs'].depth} steps, cost {n(tiny_run['ucs'].path_cost)}). DFS follows a single branch to the "
    f"end ({tiny_run['dfs'].depth} steps, cost {n(tiny_run['dfs'].path_cost)}). IDS rebuilds the tree for every "
    "depth limit and ends with the same plan as BFS.", align="justify")
figure(F_TREES, FIG / "trees_tiny.png",
       "Search trees of BFS, DFS and UCS on the tiny layout. A node shows Pac-Man's (row,col); the "
       "small number is the order of expansion; edge letters are the actions; the orange branch is the "
       "returned solution. Only expanded nodes and the goal node are drawn; nodes that were generated but "
       "never expanded are left out.", width_cm=12.5)
doc.para(
    f"Figure {F_FRONTIER} follows the size of the frontier while the four searches run on the large layout. The "
    "two stack-based algorithms stay below 30 nodes from start to finish; the queues of BFS and UCS grow to "
    "several hundred nodes.", align="justify")
figure(F_FRONTIER, FIG / "frontier_large.png",
       "Frontier size during the search on the large layout (logarithmic axis).", width_cm=12.0)
figure(F_IDS_TREES, FIG / "tree_ids_limits_tiny.png",
       f"The trees searched by IDS on the tiny layout at depth limits {', '.join(str(x) for x in tiny_limits[:-1])} "
       f"and {tiny_limits[-1]}. Every iteration starts again from the root. Only expanded nodes are drawn, so "
       "the tree for limit L reaches depth L - 1: the nodes at depth L are cut off, not expanded.",
       width_cm=15.5)

# ------------------------------------------------------------------------------- 8 reflections
doc.heading("8. Reflections", 1)
doc.bullets([
    "**The model decides everything.** A state made of Pac-Man's position alone cannot express the goal "
    "\"all food eaten\". Putting the food mask into the state makes the model correct, and it also shows "
    "where the difficulty of the problem comes from (2^{k}).",
    "**Step costs change which algorithm is \"best\".** With uniform costs BFS would have been optimal and "
    "UCS unnecessary. The ghost danger cost is a small modelling detail, but it is the reason the four "
    "algorithms give three different answers. We check this for every layout exactly instead of assuming "
    f"it (Section {S_TRADE}): in a different maze a plan with the fewest steps can also be the cheapest, and "
    "then BFS and UCS would look the same.",
    "**Textbook properties assume a tree.** IDS is described as needing little memory, and it does - but on "
    f"a graph with many paths to the same state the tree search repeats an enormous amount of work "
    f"({ids_ratio:.0f} times BFS here). Every algorithm needs some protection against repeated states, and "
    "each choice has its price: the explored set we gave DFS costs memory, the path check we gave IDS costs "
    "time. We measured both choices for IDS.",
    "**Measurements need definitions.** \"Nodes generated\" or \"memory\" only mean something once it is "
    "fixed what is counted; we wrote the definitions down once and used the same counters in every algorithm. "
    "Timing needed the same care: on our laptop identical runs differed by a factor of two to three, so we "
    "report the fastest of several runs and keep the process on one processor core.",
    f"**Next phase.** UCS still expands {share[L]['UCS'] * 100:.0f}% of the state space. In Phase II we will "
    "add heuristics to reduce this - the model admits at least two, the Manhattan distance to the farthest "
    "pellet and the maze distance to the nearest pellet plus a minimum spanning tree over the others - and "
    "local search as a different way of attacking the same problem, with the path cost as the measure of "
    "solution quality.",
])

# ------------------------------------------------------------------------------- 9 conclusion
doc.heading("9. Conclusion", 1)
doc.para(
    "We modelled Pac-Man's food-collection task as a search problem with a clearly defined state (position "
    "and food mask), initial state, goal test, actions, transition model and non-uniform step costs, and "
    f"showed that the state space of our three official layouts has between {n(sizes['small']['reachable'])} "
    f"and {n(sizes['large']['reachable'])} reachable states. BFS, DFS, UCS and IDS were implemented from "
    "scratch and measured. The measurements agree with the theory: UCS is the only cost-optimal algorithm; "
    "BFS and IDS are optimal in steps only; DFS is complete here but returns poor solutions; BFS and UCS pay "
    "with memory, IDS with repeated work. For this problem UCS is the right uninformed algorithm, and its "
    "cost in expanded nodes is the baseline that the informed methods of Phase II have to beat.",
    align="justify")

# ------------------------------------------------------------------------------- references
doc.heading("References", 1)
doc.numbered([
    "S. Russell and P. Norvig, __Artificial Intelligence: A Modern Approach__, 4th edition, Pearson, 2021 - "
    "Chapter 3 (Solving Problems by Searching).",
    "CSAI 301 lecture material on uninformed search.",
    "Python Software Foundation, The Python Standard Library documentation: `collections.deque`, `heapq`, "
    "`timeit`, `tracemalloc`. https://docs.python.org/3/library/",
    "J. D. Hunter, \"Matplotlib: A 2D Graphics Environment\", Computing in Science & Engineering, 9(3), 2007 "
    "(used for the figures only).",
], size=10)
doc.heading("Use of AI tools", 1)
doc.para(
    "In line with the course policy on outside sources, we state that an AI assistant (Claude, by Anthropic) "
    "was used in this project: it helped to write and test the code, to produce the figures and to draft "
    "this report. No ready-made search library is used; every algorithm is implemented in the submitted "
    "code. The team reviewed the code and the results and is responsible for the whole submission.",
    size=10, align="justify")

# ------------------------------------------------------------------------------- appendix
doc.heading("Appendix. Solution Paths on the Other Layouts", 1)
table(T_OTHER_PATHS,
      ["Layout", "Algorithm", "Cost", "Solution path"],
      [[name if a == "BFS" else "", a, n(m(name, a, "path_cost")), f"`{m(name, a, 'solution')}`"]
       for name in ("small", "medium") for a in ALGS],
      widths_cm=[1.5, 1.7, 1.1, 12.3], size=8, stripe=False,
      caption="Solution paths on the small and medium layouts.")

assert doc.figure_no == F_IDS_TREES and doc.table_no == T_OTHER_PATHS, (doc.figure_no, doc.table_no)
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("written", OUT)
