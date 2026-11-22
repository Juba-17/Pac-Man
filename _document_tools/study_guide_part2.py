"""Study guide, Section 3: the code walkthrough, file by file."""
from study_guide_common import (
    HEUR, IDS_ITER, L, LAND, LOC, M1, MEMO, N_SEEDS, OPT, P1, P2, S2, SA, GA, TEXTBOOK, TRADE, TUNE_RUNS,
    VARIANT, W, excerpt, keep_header_with_first_row, ms, n)

BOX = "FFF4DC"
NAME_W, TEXT_W = 4.7, 12.7        # the name column holds 28 characters of code without breaking a word


def functions(doc, rows):
    keep_header_with_first_row(
        doc.table(["Name", "What it does, and why it is written that way"], rows, widths_cm=[NAME_W, TEXT_W],
                  size=9, stripe=False, keep_together=False))


def examiner(doc, lines):
    doc.callout(["**What an examiner may point at**"] + lines, fill=BOX)


def quote(doc, where, text):
    """An exact excerpt of the code. `where` names the file and the function (identifiers in backticks)."""
    doc.para(where, size=9, italic=True, space_after=1, keep_with_next=True)
    doc.code(text, size=8)


def build(doc):
    reopen = W["reopen"]
    census = W["f_census"][L]
    doc.heading("3. Code walkthrough, file by file", 1, new_page=True)
    doc.para(
        "`Phase1\\code` and `Phase2\\code` contain the same Phase I source files, byte for byte; only `main.py` "
        "was extended in Phase II. So one walkthrough covers both folders. A good reading order is `problem.py`, "
        "`search_core.py`, `uninformed.py`, then `heuristics.py`, `informed.py`, `local_search.py`; the other "
        "files measure, draw or run things.")
    doc.para(
        "One design idea runs through everything: **the search algorithms know nothing about mazes.** They use "
        "only three things of the problem object - `initial_state`, `successors(state)` and `is_goal(state)`. A "
        "unit test runs BFS, DFS, UCS and IDS on a four-state \"line\" problem that has no maze at all to prove it. "
        "This is why the same six search functions would solve any other problem that offers these three things.")

    # ============================================================== Phase I
    doc.heading("Phase I files", 2)

    doc.heading("pacman_search/problem.py - the formal model", 3)
    doc.para(
        "**Purpose:** everything of Section 2 and nothing about searching. **Data structures:** `State` "
        "(NamedTuple); sets `walls` and `danger_cells`; lists `ghosts` and `free_cells`; the tuple `food_cells`; "
        "the dictionary `food_bit` (cell -> 1 << i); the integer `all_food` = 2^{k} - 1; and `neighbors`, a "
        "dictionary cell -> list of (action, next cell, cost of entering it) - the maze as a graph.")
    functions(doc, [
        ["`State`", "A NamedTuple (pos, food). It is immutable and hashable, so states can be stored in sets and "
                    "used as dictionary keys, and two states with the same position and mask are equal whichever "
                    "path produced them. That is what lets a graph search recognise a repeated state."],
        ["`ACTIONS`, `STEP_COST`, `DANGER_COST`, the map symbols",
         "The four moves as (row, col) offsets in the order UP, RIGHT, DOWN, LEFT (a Python dictionary keeps its "
         "insertion order), and the costs 1 and 5. This order is the order of the successors everywhere in the "
         "project, so it decides every tie. `WALL`, `GHOST`, `FOOD`, `START` and `EMPTY` name the five map "
         "symbols `#`, `G`, `.`, `P` and the space."],
        ["`PacmanProblem.__init__`",
         "Reads the ASCII map once and pre-computes everything that never changes: free cells, danger cells, the "
         "bit of every pellet and, for every free cell, its legal moves with their costs (`neighbors`). It refuses "
         "bad input with a ValueError: rows of different length, an unknown symbol, no `P` or several, no pellet, "
         "a cost that is not positive, a pellet that cannot be reached."],
        ["`initial_state`, `is_goal`, `actions`, `result`, `step_cost`, `enter_cost`",
         "The formal model, one small method per row of the table in Section 2. `result` raises ValueError for an "
         "unknown or illegal action. They exist so that the model can be read and tested piece by piece; the "
         "search algorithms call `successors` instead."],
        ["`successors(state)`",
         "The list of (action, next state, step cost) for every legal move, in action order. It gives the same "
         "answer as `actions` + `result` + `step_cost` (a unit test compares them on every reachable state of "
         "every layout) but in one pass over `neighbors`, because it runs once for every expanded node."],
        ["`execute(actions)`, `is_solution(actions)`",
         "Replay a plan from the initial state and return the states it visits and its total cost. This is our "
         "safety net: every plan returned by any of the nine algorithms is replayed here and its cost compared "
         "with the cost the algorithm reported (in `evaluate_search` and `evaluate_local` for all nine, in "
         "`main.py` for the local-search plans, and in the tests)."],
        ["`state_space_report()`, `count_reachable_states()`, `reachable_states()`",
         "The three sizes of Section 2. The reachable states are found by a breadth-first sweep without a goal "
         "test, so the set also contains the states in which Pac-Man keeps walking after the last pellet. The "
         "count is computed once and remembered."],
        ["`render(states)`, `describe()`, `_check_all_food_reachable()`",
         "Text output for `main.py` (`*` marks the cells of a solution), and the breadth-first search over the "
         "maze cells that rejects a maze with a walled-in pellet."],
    ])
    quote(doc, "`problem.py`, `PacmanProblem.successors` (the body of the function)",
          excerpt("pacman_search/problem.py", "children = []", "return children"))
    examiner(doc, [
        "**`state.food & ~self.food_bit.get(cell, 0)`** - `food_bit.get(cell, 0)` is the pellet's bit, or 0 if the "
        "cell holds no pellet. `~bit` has every bit set except that one, so the AND clears exactly this pellet. "
        "For a cell without a pellet, `~0` is all ones and the mask is unchanged. If the pellet was eaten before, "
        "its bit is already 0 and nothing changes.",
        "**Why is the cost stored with the cell that is entered?** `neighbors` stores `self.enter_cost(nxt)`. "
        "Walking into a danger cell costs 5; walking out of it costs 1. So the cost from a to b can differ from "
        "the cost from b to a, and the code never assumes that they are equal (a unit test builds such a maze).",
        "**`if step_cost <= 0 or danger_cost <= 0: raise ValueError`** - UCS and A* are only guaranteed to be "
        "complete and optimal when every step costs more than zero: then the path cost grows with every move.",
        "**Why pre-compute `neighbors`?** Walls and ghosts never change, and `successors` is called for every "
        f"expansion - {n(M1[(L, 'IDS')]['nodes_expanded'])} times in one IDS run on the large layout.",
        "**The formula for the valid states,** `n * 2 ** k - k * 2 ** (k - 1)` - for each of the k pellet cells, "
        "the 2^{k-1} masks in which that pellet is still uneaten are impossible while Pac-Man stands on it.",
        "**Why has `reachable_states()` no goal test?** It measures the state space, not a search. A search stops "
        "at its first goal and never generates most of the food = 0 states.",
    ])

    doc.heading("pacman_search/layouts.py - the four mazes", 3)
    doc.para(
        "`LAYOUTS` is a dictionary name -> ASCII map (`tiny`, `small`, `medium`, `large`); `OFFICIAL_LAYOUTS` are "
        "the three whose state spaces lie in the required 1,000-10,000 range and `DEFAULT_LAYOUT` is `\"large\"`. "
        "`load_problem(name)` builds the `PacmanProblem` (KeyError with the list of names for an unknown name); "
        "`load_problem_from_file(path)` does the same for a text file (`utf-8-sig` also accepts a file that starts "
        "with a byte-order mark).")
    examiner(doc, [
        "**Why is the 9x9 maze \"large\" and the 11x13 maze \"medium\"?** The names refer to the state space, not "
        "the grid: 38 x 2^{8} is more than 68 x 2^{6}. The number of pellets is what counts.",
        "**Why are the ghosts where they are?** They were placed so that on every layout the plans with the "
        "fewest steps have to enter danger cells and a longer, safer plan is cheaper. Without that, BFS and UCS "
        "would return equally good plans and Phase I would show nothing. `step_cost_tradeoff` checks it exactly "
        "(see `experiments.py`).",
    ])

    doc.heading("pacman_search/search_core.py - nodes and counters", 3)
    functions(doc, [
        ["`Node`", "One node of the search tree: `state`, `parent`, `action`, `path_cost` (g) and `depth` (the "
                   "parent's depth + 1). `path()` follows the parent pointers back to the root and reverses the "
                   "list; this is how the solution is rebuilt at the end, so a node never stores a whole path. "
                   "`__slots__` keeps the objects small (no dictionary per object)."],
        ["`SearchResult`", "A dataclass with everything a search returns: `found`, `actions`, `states`, "
                           "`path_cost`, `depth` (the number of steps), the four counters, `runtime_sec`, and "
                           "optional trace data for the pictures (`expanded_nodes`, `frontier_history`, `extra`). "
                           "`summary()` is the one-line text of the tour."],
        ["`SearchStats`", "The bookkeeping object that every search creates in its first line. "
                          "`count_generated(n)`: 1 for the root and, at each expansion, the number of successors "
                          "produced. `count_expanded(node)`: once per expansion. `observe(frontier_size, "
                          "stored_states)`: updates the two maxima. `finish(goal_node)`: stops the clock that "
                          "`__init__` started and builds the `SearchResult`; `finish(None)` means \"no solution\"."],
    ])
    bfs = M1[(L, "BFS")]
    doc.para(
        "**The five measurements, exactly.** __Nodes generated__ = the root plus every successor produced when a "
        "node is expanded, including the ones that are then thrown away as duplicates (IDS counts the root once "
        "per iteration). __Nodes expanded__ = nodes whose successors were produced; a node that is only "
        "goal-tested is not expanded. __Max frontier__ = the largest number of entries waiting in the queue, stack "
        "or heap, looked at when the search starts and after every expansion. __Max nodes in memory__ = the "
        "largest value of frontier + remembered states (table below). __Running time__ = wall-clock time from the "
        "creation of `SearchStats` to `finish()` (`time.perf_counter`).")
    doc.table(
        ["Algorithm", "`frontier_size` passed to `observe`", "`stored_states` passed to `observe`",
         "Max in memory, large layout"],
        [["BFS", "length of the queue", "`len(reached) - len(frontier)` = states already expanded",
          n(bfs["max_nodes_in_memory"])],
         ["DFS", "length of the stack (it may hold the same state several times)", "`len(explored)`",
          n(M1[(L, "DFS")]["max_nodes_in_memory"])],
         ["UCS", "length of the heap, outdated entries included", "`stats.expanded` = states already expanded",
          n(M1[(L, "UCS")]["max_nodes_in_memory"])],
         ["IDS", "length of the stack", "`node.depth + 1` = the current path (or `len(best_depth)` with the memo "
                                        "table)", n(M1[(L, "IDS")]["max_nodes_in_memory"])],
         ["Greedy, A*", "length of the heap, outdated entries included", "`len(explored)`",
          f"{n(S2[(L, 'Greedy (h2)')]['max_nodes_in_memory'])} to {n(S2[(L, 'Greedy (h1)')]['max_nodes_in_memory'])}"]],
        widths_cm=[2.0, 5.3, 6.4, 3.3], size=9, bold_first_col=True, stripe=False)
    examiner(doc, [
        "**Generated versus expanded.** BFS on the large layout expanded "
        f"{n(bfs['nodes_expanded'])} nodes and generated {n(bfs['nodes_generated'])}: about "
        f"{(bfs['nodes_generated'] - 1) / bfs['nodes_expanded']:.2f} successors per expansion, about half of them "
        "duplicates that were thrown away. On the tiny layout every cell has exactly two neighbours, so generated = "
        "1 + 2 x expanded (BFS: 45 = 1 + 2 x 22).",
        "**For BFS, \"max nodes in memory\" is simply the number of states reached so far**, because frontier + "
        "(reached - frontier) = reached.",
        "**Where does the clock start and stop?** In `SearchStats.__init__` and in `finish()`. So `runtime_sec` "
        "covers the search function and nothing else - no printing, no drawing.",
        "**`trace=True`** only stores the expanded nodes and the frontier sizes for the pictures. A unit test "
        "checks that tracing changes neither the path nor the node and memory counts.",
    ])

    doc.heading("pacman_search/uninformed.py - BFS, DFS, UCS, IDS", 3)
    doc.para("The four functions are `breadth_first_search`, `depth_first_search`, `uniform_cost_search` and "
             "`iterative_deepening_search`. Each takes the problem (and `trace=False`) and returns a "
             "`SearchResult`.", space_after=3, keep_with_next=True)
    doc.table(
        ["", "Frontier", "Protection against repeated states", "Goal test", "Returns"],
        [["BFS", "FIFO queue (`deque`, `popleft`)",
          "set `reached` of every state ever queued; a state is queued only once", "when a node is GENERATED "
          "(early)", "a plan with the fewest steps"],
         ["DFS", "LIFO stack (a list, `pop`)",
          "set `explored` of expanded states, checked when a node is popped", "when a node is popped",
          "the first plan it finds"],
         ["UCS", "binary heap (`heapq`) ordered by g",
          "dictionary `best_cost`; a state is queued again only for a strictly cheaper path, and outdated heap "
          "entries are skipped", "when a node is POPPED (late)", "a cheapest plan"],
         ["IDS", "LIFO stack inside `depth_limited_search`; limits 0, 1, 2, ...",
          "only loops on the current path (`_is_cycle`); optional memo table (`use_memo=True`)",
          "when a node is popped", "a plan with the fewest steps"]],
        widths_cm=[1.1, 4.0, 6.0, 3.1, 3.2], size=9, bold_first_col=True, stripe=False)
    functions(doc, [
        ["`depth_limited_search`",
         "Parameters `(problem, limit, stats, use_memo, expansion_limit)`. A depth-first search that never expands "
         "a node at depth >= `limit`. It returns a goal node, or `CUTOFF` (something was cut off at the limit: a "
         "larger limit might help), or `None` (nothing was cut off: the whole space was searched and there is no "
         "solution), or `ABORTED` (the optional expansion budget ran out). It uses an explicit stack, not "
         "recursion, so Python's recursion limit plays no role."],
        ["`_is_cycle(node)`", "Walks up the parent pointers and returns True if the node's state already occurs "
                              "among its ancestors. It needs no extra memory - this is what keeps IDS a tree "
                              "search with a memory of about (branching factor x depth)."],
        ["`iterative_deepening_search`",
         "Calls `depth_limited_search` with limit 0, 1, 2, ... and stops at the first goal, or when a call returns "
         "`None`. All counters are summed over all iterations (one `SearchStats` object is shared); the numbers "
         "per limit are kept in `extra[\"iterations\"]`. Options: `use_memo`, and the safety limits `max_depth` "
         "and `expansion_limit`."],
        ["`UNINFORMED_ALGORITHMS`", "The table name -> function used by `main.py`, the run scripts and the tests."],
    ])
    quote(doc, "`uninformed.py`, `breadth_first_search` (inside the while loop)",
          excerpt("pacman_search/uninformed.py", "node = frontier.popleft()", "frontier.append(child)"))
    quote(doc, "`uninformed.py`, `uniform_cost_search` (inside the while loop)",
          excerpt("pacman_search/uninformed.py", "cost_so_far, _, node = heapq.heappop(frontier)", "counter += 1"))
    quote(doc, "`uninformed.py`, `depth_limited_search` (inside the while loop)",
          excerpt("pacman_search/uninformed.py", "node = frontier.pop()",
                  "frontier.append(Node(child_state, node, action, node.path_cost + cost))",
                  anchor="def depth_limited_search"))
    text_large, memo_large = VARIANT[(L, TEXTBOOK)], VARIANT[(L, MEMO)]
    last_full, final = IDS_ITER[L][-2], IDS_ITER[L][-1]
    goal = W["goal_test"]
    examiner(doc, [
        "**Early goal test in BFS, late goal test in UCS.** BFS creates the states level by level, so the first "
        "time a state is generated it has been reached with the fewest possible steps. The first goal that is "
        "generated is therefore a shallowest goal and BFS can stop at once. Measured: with the test moved to "
        f"expansion time BFS would expand {n(goal['bfs'][L]['late']['expanded'])} nodes instead of "
        f"{n(goal['bfs'][L]['early']['expanded'])}. In UCS a goal that has just been generated may still be "
        "reachable more cheaply through a node that is waiting in the heap. Only when the goal itself is popped is "
        "every waiting node at least as expensive - that is the proof of optimality, and it needs the late test "
        "(Section 5 shows a four-cell maze where the early test returns the wrong plan).",
        "**The counter in `(new_cost, counter, child)`.** Python compares tuples from left to right. With two "
        "equal costs it would go on to compare the `Node` objects and stop with "
        f"`{W['python']['heap_without_counter']}`. The counter is different for every entry, so the comparison "
        "never reaches the node. It also makes equal-cost nodes leave in the order they entered (first in, first "
        "out), so every run gives the same result.",
        "**Why `deque` and `heapq`?** `popleft()` on a `deque` takes constant time; `pop(0)` on a list would move "
        "every remaining element. A binary heap gives the cheapest entry in O(log n) per push and pop. Looking a "
        "state up in a `set` or `dict` takes constant time on average - this is why states must be hashable.",
        "**`if cost_so_far > best_cost[node.state]: continue` (lazy deletion).** `heapq` cannot lower the priority "
        "of an entry that is already in the heap. When a cheaper path to a state is found we push a second entry "
        "and update `best_cost`; the old entry stays behind and is thrown away when it finally comes out. That is "
        "why the frontier size of UCS and A* includes outdated entries.",
        "**`reversed(children)` in DFS and IDS.** A stack returns the last thing pushed. Pushing the successors in "
        "reverse order leaves the FIRST action (UP) on top, so DFS tries the actions in the order UP, RIGHT, DOWN, "
        "LEFT. Without `reversed` it would try LEFT first and return a different path (Section 5).",
        "**`if node.state in explored: continue` in DFS.** The same state can be pushed several times by "
        "different parents before it is expanded, so the test must be repeated when a node is popped. The test "
        "`if child_state not in explored` before the push only saves stack space.",
        "**Why does BFS mark a state when it is generated and DFS when it is expanded?** In BFS the first "
        "generation is already the best one, so later copies can be refused immediately. DFS must be free to "
        "reach a state again along the branch it is following; marking at generation would change the order of "
        "exploration.",
        "**The memo table: `best_depth.get(node.state, limit + 1) <= node.depth`.** A node is skipped if its "
        "state was already visited in THIS iteration at the same or a smaller depth. The depth matters: a state "
        "first met deep in the tree may have had its subtree cut off by the limit; met again nearer the root it "
        "has more depth left and must be searched again. A plain \"visited\" set would be wrong here. The default "
        "`limit + 1` is larger than any possible depth, so a new state is never skipped, and the table is a local "
        "variable, so every iteration starts with an empty one. Measured on the large layout: "
        f"{n(memo_large['nodes_expanded'])} expansions instead of {n(text_large['nodes_expanded'])}, but "
        f"{n(memo_large['max_nodes_in_memory'])} nodes in memory instead of {n(text_large['max_nodes_in_memory'])}.",
        "**The order of the tests in `depth_limited_search`.** Goal test first - so a goal exactly at depth = "
        "limit is still found, and IDS finds a solution of depth d in the iteration with limit d. Then the "
        "duplicate check, then `if node.depth >= limit: result = CUTOFF` (a node at the limit is tested but not "
        "expanded), and only then the expansion.",
        "**Why three different results (goal node, `CUTOFF`, `None`)?** `None` tells IDS that raising the limit "
        "cannot help, so it stops instead of looping forever when no solution exists. On the large layout IDS "
        f"runs {len(IDS_ITER[L])} iterations (limits 0 to {final['limit']}); the last complete one (limit "
        f"{last_full['limit']}) expands {n(last_full['expanded'])} nodes and the final one only "
        f"{n(final['expanded'])}, because it stops at the first goal.",
    ])

    doc.heading("pacman_search/experiments.py - measuring", 3)
    functions(doc, [
        ["`measure_time(run, repeats=20, max_seconds=2.0)`",
         "Calls `run()` up to 20 times and returns a `Timing` (best, median, mean, std, runs) in milliseconds. A "
         "slow algorithm is stopped early: once at least 3 runs were made and they took 2 seconds together, no "
         "further run is started. The garbage collector is switched off during each run. The FASTEST run is the "
         "running time we report; the other values are stored in the result files."],
        ["`measure_peak_memory(run)`", "One extra run under `tracemalloc`; returns the peak memory allocated by "
                                       "Python objects in KiB. It is a separate run because tracing slows the "
                                       "program down."],
        ["`evaluate_search(problem, label, search_fn, repeats)`",
         "One complete measurement of one algorithm on one maze: the timing, the peak memory, one ordinary run "
         "for the counters - and a check: the returned plan is replayed with `problem.execute` and must reach the "
         "goal with exactly the reported cost. Returns the table row and the `SearchResult`."],
        ["`step_cost_tradeoff`",
         "Answers exactly: is the plan with the fewest steps also the cheapest? It runs a uniform-cost search "
         "twice with a two-part key that Python compares from left to right. The key (steps, cost) finds the "
         "fewest steps and, among those plans, the cheapest; the key (cost, steps) finds the lowest cost and, among "
         "those plans, the shortest. `genuine_tradeoff` is True when even the cheapest fewest-step plan costs more "
         "than the optimum."],
        ["`Timing`, `actions_to_string`, `positive_int`, `environment_info`, `write_csv`, `save_json`, "
         "`format_value`, `markdown_table`, `text_table`",
         "Small helpers: the timing record, the `RRDD...` strings, an argparse type, the Python / operating-system "
         "description stored with the results, and the writers for CSV, JSON, Markdown and plain-text tables."],
    ])
    quote(doc, "`experiments.py`, `measure_time` (the timing loop)",
          excerpt("pacman_search/experiments.py", "times_ms = []", "gc.enable()"))
    one, two = M1[(L, "BFS")], S2[(L, "BFS")]
    assert abs(one["time_ms"] - two["time_ms"]) / two["time_ms"] < 0.15
    examiner(doc, [
        "**Why the fastest run and not the mean?** The algorithms are deterministic, so every run does exactly the "
        "same work. Whatever disturbs a run (another program, the operating system moving the process to a slower "
        "core) can only make it slower, never faster. The fastest run is therefore the best estimate of the true "
        "cost; the documentation of Python's `timeit` gives the same advice. Our own evidence: BFS on the large "
        f"layout was timed in two sessions. The fastest runs were {ms(one['time_ms'])} and {ms(two['time_ms'])} "
        f"ms; the means, which include every disturbed run, were {ms(one['time_mean_ms'])} and {ms(two['time_mean_ms'])} ms.",
        "**`if len(times_ms) >= 3 and sum(times_ms) >= max_seconds * 1000.0: break`** - this is why the slow "
        f"algorithms have fewer runs: IDS on the large layout was run {M1[(L, 'IDS')]['time_runs']} times in the "
        f"Phase I session and {S2[(L, 'IDS')]['time_runs']} times in the Phase II session (column `time_runs`).",
        "**`gc.disable()` inside `try ... finally`** - a garbage collection that happens to start in the middle of "
        "a run would be charged to the algorithm. `finally` switches the collector on again even if the run fails.",
        "**`run().runtime_sec`** - the time is the one measured inside the search (`SearchStats`), not a clock "
        "around the call.",
        "**The numbers of `step_cost_tradeoff`** (Table 6 of the Phase I report), small / medium / large: fewest "
        "steps " + " / ".join(str(TRADE[name]["fewest_steps"]) for name in ("small", "medium", "large"))
        + "; cheapest plan with that many steps "
        + " / ".join(str(TRADE[name]["cheapest_cost_with_fewest_steps"]) for name in ("small", "medium", "large"))
        + "; optimal cost " + " / ".join(str(TRADE[name]["optimal_cost"]) for name in ("small", "medium", "large"))
        + ", reached with " + " / ".join(str(TRADE[name]["fewest_steps_at_optimal_cost"])
                                         for name in ("small", "medium", "large"))
        + " steps. BFS returns cost " + " / ".join(str(M1[(name, "BFS")]["path_cost"])
                                                   for name in ("small", "medium", "large"))
        + ": on the medium and large layouts not even the cheapest of the fewest-step plans, just the first one it "
          "meets.",
    ])

    doc.heading("pacman_search/visualize.py - the Phase I pictures", 3)
    functions(doc, [
        ["`apply_style`, `save_figure`, `text_color_on`, `plain_number`, colour constants",
         "One look for all figures. `matplotlib.use(\"Agg\")` draws straight into image files, no window opens. "
         "`text_color_on` chooses black or white text, whichever has the better contrast on a coloured cell."],
        ["`draw_maze`, `draw_path`, `expanded_per_cell`, `symbol_handles`",
         "The building blocks of every maze picture. `expanded_per_cell` counts for each cell the DISTINCT states "
         "that were expanded while Pac-Man stood on it (0 to 2^{k}); this is the blue shading. `draw_path` shifts "
         "every move a little to the right of its direction, so a corridor walked in both directions shows two "
         "lines, and numbers the pellets in the order they are eaten."],
        ["`plot_layouts`, `plot_explored`, `animate_search`",
         "The layouts figure; one panel per algorithm with the shading and the returned path (all panels share "
         "one colour scale); the animated GIF (first the shading grows in the order of expansion, then Pac-Man "
         "walks the solution)."],
        ["`plot_search_tree`, `plot_search_trees`, `plot_ids_trees` (helpers `_layout_tree`, `_draw_tree`)",
         "The search trees on the tiny layout, rebuilt from the parent pointers of the expanded nodes. Leaves are "
         "spread from left to right and a parent sits above the middle of its children. The small number is the "
         "order of expansion, the node colour the number of pellets left. For IDS one tree per depth limit is "
         "drawn; `extra[\"iteration_starts\"]` says where each limit begins in the list of expanded nodes."],
        ["`bar_panel`, `plot_metric_bars`, `plot_frontier_history`, `plot_ids_iterations`, `plot_scaling`",
         "The charts: bars for the six measurements; frontier size against the progress of the run (in percent, "
         "so that runs of very different length fit, logarithmic y axis); the work of IDS per depth limit; nodes "
         "expanded against the size of the state space (both axes logarithmic)."],
    ])
    examiner(doc, [
        "**What does a dark cell in the \"explored states\" figure mean?** Many different states were expanded "
        "with Pac-Man on that cell - up to 256 on the large layout, one for each combination of remaining "
        "pellets. A state that IDS expands a thousand times is still counted once (`seen` set in "
        "`expanded_per_cell`).",
        "**Can a picture change a result?** No. This file contains no search logic; it only reads the "
        "`SearchResult` of a run made with `trace=True`. The measurements are taken from runs without a trace.",
        "**Why are the trees drawn for the tiny layout only?** The tree of the large layout has thousands of "
        "nodes. The tiny maze has 45 states and a tree that fits on a page.",
    ])

    doc.heading("main.py, run_phase1.py and tests/test_phase1.py", 3)
    functions(doc, [
        ["`main.py`", "The command line. `build_parser` defines the options with `argparse`: `-l/--layout`, "
                      "`--layout-file`, `-a/--algorithm` (several names allowed, default all), `--show-path`, "
                      "`--list`. `main` loads the maze, runs the chosen algorithms and prints the table. The "
                      "Phase II version adds the algorithm names `greedy astar hc sa ga`, `--heuristic h1 h2` and "
                      "`--seed`; its helpers `search_row` and `local_row` build the table rows, and `local_row` "
                      "replays a local-search plan and asserts that its cost is right before it is printed."],
        ["`run_phase1.py`", "`run_layout` measures the four algorithms on one layout and adds the flags "
                            "`cost_optimal` (same cost as UCS) and `step_optimal` (same number of steps as BFS). "
                            "`compare_ids_variants` measures IDS with and without the memo table. "
                            "`state_graph_profile` (in `experiments.py`) sweeps the whole state graph once and "
                            "counts the states per depth and per cost: how many are shallower than the solution "
                            "(the most BFS can expand) and how many are cheaper than the optimum (what UCS must "
                            "expand) - the numbers behind Section 6.3 of the report. `main` pauses a few seconds "
                            "before each layout (`COOL_DOWN_SECONDS`, so that a hot processor does not slow the "
                            "next timings), does all "
                            "measurements first, then writes the tables (`metrics.csv`, `state_space.csv`, "
                            "`state_graph.csv`, `tradeoff.csv`, `ids_iterations.csv`, `ids_variants.csv`, "
                            "`solutions.txt`, "
                            "`summary.md`, `results.json`), and only then runs the searches again with a trace to "
                            "draw the figures and the animations."],
        ["`tests/test_phase1.py`", "33 tests: the model (parsing, transition, costs, sizes, bad mazes), the four "
                                   "algorithms, and the measuring helpers. The results are checked against two "
                                   "INDEPENDENT solvers written inside the test file, not against each other: "
                                   "`brute_force_optimum` tries every order of the pellets with its own small "
                                   "Dijkstra, and `fewest_steps_by_sweep` is a plain breadth-first sweep written "
                                   "with `actions` and `result` only."],
    ])
    examiner(doc, [
        "**\"How do you know UCS really returns the optimum?\"** Its cost equals the brute-force minimum over all "
        "pellet orders on all four layouts (`test_ucs_is_cost_optimal`), A* returns the same cost with both "
        "heuristics, and the best of all pellet orders in the local-search formulation costs the same again.",
        "**Why are all timings taken before any traced run?** A trace keeps hundreds of thousands of `Node` "
        "objects alive, and that much data in memory makes whatever is timed next slow and noisy.",
        "**Why does `main.py` show a smaller time for A* than the report?** `main.py` builds the heuristic before "
        "it calls the search. `run_phase2.py` builds a fresh heuristic inside the measured part, so the reported "
        "time includes the preparation of h2.",
    ])

    # ============================================================== Phase II
    doc.heading("Phase II files", 2)

    doc.heading("pacman_search/heuristics.py - h1, h2 and their verification", 3)
    h1r, h2r = HEUR[(L, "h1")], HEUR[(L, "h2")]
    functions(doc, [
        ["`manhattan(a, b)`", "|row difference| + |column difference|: the grid distance when walls are ignored."],
        ["`maze_distances_from`",
         "A breadth-first search over the maze cells from one cell; every step counts 1. It walks "
         "`problem.neighbors`, so walls and ghost cells are respected. Because every move can be reversed, the "
         "distance from A to B equals the distance from B to A."],
        ["`cheapest_step(problem)`", "The smaller of the two step costs (1 with our costs). Both heuristics count "
                                     "STEPS and multiply the count by this factor, so they cannot overestimate "
                                     "whatever the cost settings are."],
        ["`ZeroHeuristic`", "h = 0 everywhere. A* with it is exactly UCS; used as a baseline and in a test."],
        ["`FarthestFoodHeuristic` (h1)",
         "Called like a function: `h1(state)`. It looks at every pellet that is still on the board, takes the "
         "Manhattan distance from Pac-Man to it and returns the largest one (times the cheapest step). No "
         "preparation, one pass over the k pellets per call."],
        ["`MazeMSTHeuristic` (h2)",
         "`__init__` runs one breadth-first search per pellet and stores `steps[i][cell]` (maze distance from "
         "pellet i to every cell) and `between[i][j]` (pellet to pellet). `h2(state)` returns 0 for a goal state, "
         "otherwise (distance to the NEAREST remaining pellet + `mst_weight(food)`) times the cheapest step. "
         "`mst_weight` is the weight of the minimum spanning tree over the remaining pellets (Prim's algorithm)."],
        ["`optimal_costs_to_goal`",
         "h*(s), the true cheapest remaining cost, for EVERY reachable state. It first builds, for every state, "
         "the list of its predecessors, and then runs one uniform-cost search backwards from all goal states at "
         "once. Only possible because the state space is small."],
        ["`analyse_heuristic(problem, heuristic, true_costs)`",
         "The exhaustive check behind Table 3 of the Phase II report. Admissible: h(s) <= h*(s) for every state. "
         "Consistent: h = 0 at every goal state and h(s) <= c + h(s') for every transition. `mean_ratio` is the "
         "average of h(s) / h*(s) over the non-goal states; `worst_overestimate` would show by how much an "
         "inadmissible heuristic is wrong."],
        ["`descent_region(problem, heuristic)`",
         "Explains Greedy. A breadth-first sweep from the start that only steps onto states whose h is SMALLER "
         "than h(start); it returns how many states it reaches and whether a goal is among them. Greedy must "
         "expand all of them before it can expand anything with a larger h. For h1 on the large layout: "
         f"{n(h1r['states_below_start_value'])} states and no goal (a basin); for h2: "
         f"{n(h2r['states_below_start_value'])} states with a goal inside, so Greedy can run downhill and stops "
         "long before it has seen them all."],
        ["`HEURISTICS`", "The table `{\"h1\": ..., \"h2\": ...}` used by `main.py`."],
    ])
    quote(doc, "`heuristics.py`, `FarthestFoodHeuristic.__call__` (h1)",
          excerpt("pacman_search/heuristics.py", "farthest = 0", "return self.unit * farthest"))
    quote(doc, "`heuristics.py`, `MazeMSTHeuristic.__call__` and `MazeMSTHeuristic.mst_weight` (h2)",
          excerpt("pacman_search/heuristics.py", "if state.food == 0:",
                  "return self.unit * (nearest + self.mst_weight(state.food))") + "\n\n"
          + excerpt("pacman_search/heuristics.py", "if food in self._mst_cache:", "return total"))
    cache = reopen[f"{L}/cache"]
    calls = reopen[f"{L}/h2"]["always"]["heuristic_calls"]
    examiner(doc, [
        "**`state.food >> index & 1`** - shift the mask right by `index` places and look at the last bit: is "
        "pellet `index` still there? (`>>` is applied before `&`.)",
        "**`self.unit`** - the cheapest step cost. With the default costs it is 1 and changes nothing. A unit test "
        "runs the costs (0.5, 5), (1, 0.5), (2, 10) and (3, 3): both heuristics stay admissible and consistent and "
        "A* stays optimal.",
        "**Prim's algorithm in `mst_weight`.** Start the tree with the first remaining pellet. `cheapest[j]` is the "
        "cheapest edge from pellet j to the tree built so far. Repeat: take the pellet that is closest to the tree "
        "(`min(cheapest, key=cheapest.get)`), add its edge to the total, and check whether the new tree node "
        "offers the others a cheaper connection. With m pellets this is about m^{2} steps - at most 64.",
        "**Why a cache per food mask?** The spanning tree depends only on WHICH pellets are left, not on where "
        f"Pac-Man is, so there are at most 2^{{k}} = {cache['possible_masks']} different values on the large layout. "
        f"Measured: in one A* run h2 was called {calls} times but needed only {cache['masks_cached']} different "
        "masks.",
        "**`self._mst_cache = {0: 0}` and `if state.food == 0: return 0`** - a goal state must have h = 0 "
        "(consistency needs it), and `min()` over no pellets would fail.",
        "**Why do the heaps here carry no counter?** In `optimal_costs_to_goal` the entries are (cost, state). A "
        "`State` is a tuple of numbers, so Python can compare two of them. `Node` objects cannot be compared; "
        "that is why the search heaps need the counter.",
        f"**The result of the check on the large layout:** {n(h1r['states_checked'])} states and "
        f"{n(h1r['transitions_checked'])} transitions, both heuristics admissible and consistent, h2 >= h1 in every "
        f"state and strictly larger in {n(h1r['states_where_h2_is_larger'])} of them; mean h / h* = "
        f"{h1r['mean_ratio']:.2f} for h1 and {h2r['mean_ratio']:.2f} for h2.",
    ])

    doc.heading("pacman_search/informed.py - Greedy Best-First and A*", 3)
    functions(doc, [
        ["`best_first_search(problem, evaluate, name, trace, reopen)`",
         "ONE best-first graph search for both algorithms. The frontier is a heap of (f, counter, node) where f = "
         "`evaluate(node)`; `best_cost` holds the path cost with which each state was last queued; `explored` is "
         "used only for the memory statistic. The goal test is late, as in UCS, and outdated entries are skipped "
         "in the same way."],
        ["`greedy_best_first_search`",
         "Calls it with `evaluate = lambda node: heuristic(node.state)`, i.e. f = h, and `reopen=False`."],
        ["`a_star_search(problem, heuristic, trace)`",
         "Calls it with `evaluate = lambda node: node.path_cost + heuristic(node.state)`, i.e. f = g + h, and "
         "`reopen=True`."],
    ])
    quote(doc, "`informed.py`, `best_first_search` (inside the while loop)",
          excerpt("pacman_search/informed.py", "_, _, node = heapq.heappop(frontier)", "counter += 1"))
    a1, a2 = reopen[f"{L}/h1"], reopen[f"{L}/h2"]
    assert a1["always"]["requeued_after_expansion"] == a2["always"]["requeued_after_expansion"] == 0
    assert all(reopen[f"{name}/{h}"]["always"]["states_expanded_twice"] == 0
               for name in ("tiny", "small", "medium", "large") for h in ("h1", "h2"))
    examiner(doc, [
        "**`if known_cost is None or (reopen and new_cost < known_cost)`** - the one line in which Greedy and A* "
        "differ besides f. A new state is always queued. A state that was reached before is queued again only by "
        "A*, and only if the new path is strictly cheaper.",
        "**Why does A* need this?** The first path found to a state need not be the cheapest one. Measured on the "
        f"large layout: with h1, A* found a cheaper path to a state that was still waiting in the heap "
        f"{a1['always']['requeued_while_waiting']} times (with h2: {a2['always']['requeued_while_waiting']} times), "
        "and never to a state that had already been expanded. The second fact is what consistency of the "
        "heuristic guarantees: no state is ever expanded twice (also a unit test). So with h1 and h2 the flag is "
        "needed to REPLACE waiting entries, not to expand anything twice.",
        "**Why does Greedy not re-open?** Its f is h alone, and h does not depend on the path. A cheaper path "
        "would not move the state in the queue, and Greedy does not care about cost. Queuing every state only "
        "once also means at most one expansion per state, so Greedy always ends in a finite state space.",
        "**`if node.path_cost > best_cost[node.state]: continue`** - the outdated-entry test compares g, not f, "
        "because `best_cost` stores path costs.",
        "**UCS is the same function with f = g.** A unit test runs A* with the zero heuristic and gets the same "
        "path and the same four counters as `uniform_cost_search`.",
        "**Ties.** Among equal f values the older node leaves first (the counter). On the large layout A* with h2 "
        f"must expand the {census['h2']['f_below_optimum']} states with f < 28 whatever the tie-breaking; it also "
        f"expands all {census['h2']['f_equal_optimum_non_goal']} non-goal states with f = 28, which gives "
        f"{census['h2']['expanded']}. With \"newest first\" we measured {a2['lifo']['expanded']}.",
    ])

    doc.heading("pacman_search/local_search.py - Hill Climbing, Simulated Annealing, Genetic Algorithm", 3)
    dec = W["decoding"][L]
    functions(doc, [
        ["`cheapest_paths_from`",
         "A uniform-cost search over the maze CELLS (not over states) from one cell. Returns `cost[cell]` and "
         "`came_from[cell]` = (previous cell, action), from which the cheapest walk can be read backwards. The "
         "danger costs are included."],
        ["`TourProblem(problem)`",
         "The pellet-ordering problem. `points[0]` is the start cell and `points[i + 1]` is pellet i. For every "
         "pair of points it stores `distance[a][b]` (cheapest walking cost), `leg[a][b]` (the moves of that walk) "
         "and `leg_food[a][b]` (bitmask of the pellets eaten on that walk, b included). Built once with k + 1 "
         "uniform-cost searches."],
        ["`cost(order)`, `walked_legs(order)`, `to_actions(order)`, `eating_order(order)`",
         "The decoder. Go through the order; skip a pellet that has already been eaten; otherwise walk the "
         "cheapest path to it and mark every pellet on that walk as eaten. `cost` adds up the distances (the "
         "objective function), `to_actions` joins the moves into a plan, `eating_order` replays the plan in the "
         "real problem and reports the order in which the pellets are really eaten."],
        ["`random_order(rng)`, `neighbours(order)`",
         "A random permutation (the starting point), and all k(k-1)/2 orders that differ from `order` by swapping "
         f"two pellets ({dec['neighbours']} on the large layout)."],
        ["`hill_climbing(tour, seed, restarts, max_sideways, record_history)`",
         "Steepest descent: from a random order, evaluate ALL neighbours and move to the best one if it is "
         "strictly better; otherwise stop. Options: `restarts` repeats the climb from further random orders and "
         "keeps the best result; `max_sideways` allows that many moves in a row to a random neighbour of EQUAL "
         "cost."],
        ["`simulated_annealing(tour, seed, start_temperature, cooling_rate, end_temperature, record_history)`",
         "Each iteration tries ONE random swap. Better or equal: accept. Worse by delta: accept with probability "
         "exp(-delta / T). Then T is multiplied by the cooling rate. The run ends when T falls to the end "
         "temperature; the best order ever seen is returned."],
        ["`tournament_selection`, `order_crossover`, `swap_mutation`",
         "The three GA operators: the cheapest of `size` randomly drawn individuals; a child that copies a slice "
         "of parent A and fills the other positions with the missing pellets in the order of parent B; a swap of "
         "two random genes."],
        ["`genetic_algorithm(tour, seed, population_size, generations, crossover_rate, mutation_rate, "
         "tournament_size, elite_count, record_history)`",
         "A population of random orders. Each generation: pick two parents by tournament; with probability "
         "`crossover_rate` the child is their crossover, otherwise a copy of the mother; with probability "
         "`mutation_rate` it is mutated; the new population replaces the old one completely (plus optional "
         "elites). The best order ever seen is stored separately."],
        ["`LocalSearchResult`, `_swap`, `_finish`, `_single_order_result`, `LOCAL_SEARCH_ALGORITHMS`",
         "The result record (order, cost, plan, evaluations, iterations, history, time), small helpers, the "
         "special case of a maze with a single pellet, and the name table for `main.py`."],
    ])
    quote(doc, "`local_search.py`, `TourProblem.cost` (the objective function)",
          excerpt("pacman_search/local_search.py", "total, here, eaten = 0, 0, 0", "return total",
                  anchor="def cost(self, order)"))
    quote(doc, "`local_search.py`, `hill_climbing` (inside `while True:`)",
          excerpt("pacman_search/local_search.py", "neighbours = tour.neighbours(current)", "moves += 1",
                  anchor="def hill_climbing"))
    quote(doc, "`local_search.py`, `simulated_annealing` (the main loop)",
          excerpt("pacman_search/local_search.py", "while temperature > end_temperature:", "iterations += 1"))
    quote(doc, "`local_search.py`, `order_crossover`, and the generation loop of `genetic_algorithm`",
          excerpt("pacman_search/local_search.py", "size = len(parent_a)", "return tuple(child)") + "\n\n"
          + excerpt("pacman_search/local_search.py", "ranking = sorted(", "population = next_population"))
    hc = LOC[(L, "Hill Climbing")]
    sa_iter = W["python"]["sa_iterations_formula"]
    assert sa_iter == LOC[(L, "Simulated Annealing")]["mean_iterations"] == 919
    assert LOC[(L, "Genetic Algorithm")]["mean_evaluations"] == GA["population_size"] * (GA["generations"] + 1) == 930
    examiner(doc, [
        "**`if eaten >> pellet & 1: continue` - why are eaten pellets skipped?** A cheapest walk often passes "
        "over other pellets. Without the skip the plan would later walk back to an empty cell, and it could go on "
        "walking after the last pellet was eaten. With the skip, `cost(order)` is exactly the path cost of a plan "
        "that ends the moment the last pellet is eaten (the tests check both). Measured on the large layout: "
        f"{n(dec['orders_with_skips'])} of the {n(dec['orders'])} orders contain at least one pellet that is "
        f"skipped, and the {n(dec['orders'])} orders decode into only {n(dec['distinct_plans'])} different plans.",
        "**`eaten |= self.leg_food[here][target]`** - `leg_food` was filled when the table was built, by walking "
        "back along `came_from` from the target to the source and collecting the bit of every pellet cell that is "
        "entered.",
        "**Is `distance[a][b]` the same as `distance[b][a]`?** Not in general: the cost belongs to the cell that "
        "is entered. The table is computed separately from every point and is never assumed to be symmetric. On "
        "our three layouts it happens to be symmetric, because no pellet and no start cell is a danger cell "
        "(measured).",
        "**`chosen = neighbours[costs.index(lowest)]`** - the best neighbour; if several are equally good, the "
        "first one in the fixed order of `neighbours`. One step costs k(k-1)/2 evaluations. So a run costs 1 + "
        f"28 x (moves + 1) evaluations on the large layout - {n(hc['mean_evaluations'], 1)} on average for "
        f"{hc['mean_iterations']} moves.",
        "**`sideways_left`** is refilled after every strict improvement and counts down on equal-cost moves. The "
        "cost never goes up and the sideways moves between two improvements are limited, so the climb always ends.",
        "**`if delta <= 0 or rng.random() < math.exp(-delta / temperature)`** - the acceptance rule of simulated "
        "annealing. The random number is drawn only when the move is worse. `temperature *= cooling_rate` is the "
        "geometric cooling schedule T(n) = T0 x rate^{n}. The loop condition fixes the length of a run: "
        f"{SA['start_temperature']:g} x {SA['cooling_rate']}^{{n}} falls to {SA['end_temperature']} after "
        f"{sa_iter} iterations, so every run makes {sa_iter + 1} evaluations.",
        "**`child[i:j + 1] = parent_a[i:j + 1]` and `fill.pop(0)`** - the slice from position i to j stays where it "
        "is; the other positions are filled from left to right with the pellets that are not in the slice, in the "
        "order in which parent B has them. Example from the unit test: A = (0,1,2,3,4,5), B = (5,4,3,2,1,0), slice "
        "= positions 2..4 gives the child (5,1,2,3,4,0). Every pellet appears exactly once.",
        "**`ranking[:elite_count]`** - with `elite_count = 0` this list is empty: no elitism. Nothing is lost, "
        "because `best_order` remembers the best individual of all generations. One run evaluates "
        f"{GA['population_size']} x ({GA['generations']} + 1) = {GA['population_size'] * (GA['generations'] + 1)} "
        "orders.",
        "**`rng = random.Random(seed)`** - each run owns a private random generator. The same seed gives the same "
        "run, and nothing else that uses random numbers can disturb it.",
    ])

    doc.heading("pacman_search/visualize_phase2.py - the Phase II charts", 3)
    functions(doc, [
        ["`plot_heuristic_effect`", "Bars for UCS, Greedy and A* on the three layouts: nodes expanded (top) and "
                                    "path cost with the optimal cost as a line (bottom)."],
        ["`plot_convergence`", "One panel per local-search method: the best cost found so far in every run (grey) "
                               "and the average (blue). Runs of different length are padded with their final "
                               "value (`_padded`); long runs get a logarithmic x axis."],
        ["`plot_final_costs`, `plot_sa_trace`", "How many runs ended with each cost (the optimal cost in orange); "
                                                "one annealing run with the cost of the CURRENT order (grey, it "
                                                "goes up and down), the best so far (blue) and the temperature."],
        ["`plot_tuning_grid`, `plot_budget_vs_success`", "The parameter study: a heat map with the share of "
                                                         "optimal runs and the evaluations per run in every cell "
                                                         "(orange frame = the setting we use), and the share of "
                                                         "optimal runs against the evaluations spent, with the "
                                                         "random-sampling curve in grey."],
        ["`plot_scaling_local`", "The larger mazes: mean cost above the optimum of the four budget-matched methods "
                                 "against the number of pellets, next to the expansions of A* with h2."],
        ["`plot_summary_all`, `plot_routes`", "The summary chart of all algorithms (cost, time, memory, effort; "
                                              "colour = family; for local search the bar is the mean and the "
                                              "thin line runs from best to worst), and plans drawn in the maze."],
    ])

    doc.heading("run_phase2.py and tests/test_phase2.py", 3)
    land = LAND[L]
    functions(doc, [
        ["`SEEDS`, `TUNING_SEEDS`, `SA_PARAMS`, `GA_PARAMS`, `HC_RESTARTS`, `GUARANTEES`",
         f"The fixed seeds 0-{N_SEEDS - 1} for the reported runs and {P2['tuning_seeds'][0]}-"
         f"{P2['tuning_seeds'][1]} for the parameter study, the final parameters, and the theoretical properties "
         "printed in the comparison table. `BASELINE_EVALUATIONS`, `SCALING_BUDGET` and `SCALING_SEEDS` set the "
         "size of the random-sampling baseline and of the experiment on larger mazes."],
        ["`informed_algorithms()`, `local_algorithms()`, `fastest_build_ms`",
         "`informed_algorithms` wraps Greedy and A* so that a NEW heuristic object is built for every run and the "
         "time of building it is added to `runtime_sec`: the reported time is the full cost of using the "
         "heuristic. `local_algorithms` returns the three local-search methods with their final parameters, plus "
         "hill climbing with 9 restarts and the baseline `random_sampling` (in `local_search.py`: draw "
         f"{P2['baseline_evaluations']} random orders and keep the best - no search at all). `fastest_build_ms` times a preparation step (a heuristic, the distance "
         "tables) as the fastest of 20 builds."],
        ["`study_heuristics(problem)`", "Runs `analyse_heuristic` for h1 and h2 on one layout and adds the "
                                        "dominance check (h2 >= h1 in every state) and the preparation time."],
        ["`run_seed`, `evaluate_local`",
         "One algorithm, every seed. A seed is run 3 times and the fastest is its time; the time of the algorithm "
         "is the MEAN over the seeds (different seeds do different amounts of work) plus the time to build the "
         "distance tables. Every plan is replayed and must reach the goal, cost exactly what was reported, and "
         "not pass a goal state earlier. The summary row has best / mean / worst / standard deviation and the "
         "number of optimal runs."],
        ["`analyse_landscape(problem, tour, optimum)`",
         "Looks at ALL k! orders. For each one it follows the hill-climbing rule to the order where the climb "
         "stops, and classifies that order: global optimum; \"local optimum\" (no chain of equal-cost swaps leads "
         "to anything cheaper); or \"shoulder\" (such a chain exists - the climber stops only because it refuses "
         "sideways moves)."],
        ["`tuning_study(tour, optimum, seeds, optimal_share, climb_success)`",
         f"The parameter study on the large layout: {TUNE_RUNS} runs per setting. A grid for SA (start temperature "
         "x cooling rate), a grid for GA (population x mutation rate), and one parameter at a time for the rest. "
         "Every row stores the number of optimal runs AND the evaluations per run, because most parameters also "
         "change the budget. It also stores `random_sampling_percent` - the chance that the same number of "
         "random orders contains an optimal one, 1 - (1 - optimal_share)^{n} - and, for the restart rows, "
         "`exact_percent` = 1 - (1 - climb_success)^{climbs}, the exact success rate from the landscape analysis."],
        ["`pacman_search/scaling.py`, `scaling_study`",
         "The experiment beyond the official layouts. `SCALING_MAZE` is a 13x19 maze; `scatter_pellets` places 8 "
         "to 24 pellets on it with a fixed seed; `budget_methods` gives every method the same number of "
         "evaluations (hill climbing restarts until the budget is used and finishes its last climb, "
         "`cooling_rate_for` stretches the annealing schedule to the budget, and the GA gets a population of "
         "100 and 99 generations for the budget of 10,000: `population = 100 if budget >= 5000`). `scaling_study` solves each maze "
         "exactly with A* and h2 and reports how far above that optimum each method ends."],
        ["`comparison_table`, `orders_in_memory`, `main`",
         "The table of all algorithms (the data of the summary chart); how many orders each local-search method "
         "holds at once (HC: current + best + all neighbours = 30 on the large layout; SA: 3; GA: two populations "
         "+ best = 61); and the script that measures, writes the tables and then draws."],
        ["`tests/test_phase2.py`",
         "41 tests. Heuristics: admissible and consistent on every state of every layout, h2 >= h1, still correct "
         "with other step costs, a deliberately bad heuristic is detected. Informed search: A* equals the UCS "
         "cost, A* with h = 0 equals UCS exactly, no state is expanded twice, A* stays optimal with an "
         "inconsistent heuristic, Greedy is valid but not optimal. Local search: every order decodes into a plan "
         "that stops at the goal, the best order costs the optimum, same seed gives the same run, the evaluation "
         "counts, the length of the cooling schedule, the crossover example, a maze with a single pellet (no "
         "swap exists - hill climbing must return at once), the random-sampling baseline, the descent region, "
         "and the scaling mazes."],
    ])
    quote(doc, "`run_phase2.py`, `analyse_landscape` (the inner function `kind_of_stop`)",
          excerpt("run_phase2.py", "def kind_of_stop(order):", "return \"local optimum\""))
    examiner(doc, [
        "**The flood fill in `kind_of_stop`.** Start from the order where the climb stopped and collect every "
        "order that can be reached through swaps of EQUAL cost (the plateau). If any member of the plateau has a "
        "cheaper neighbour, the stop is a shoulder; if the whole plateau has none, it is a true local optimum.",
        f"**What it found on the large layout:** {n(land['orders'])} orders, {land['optimal_orders']} of them "
        f"optimal. The climb reaches an optimum from {n(land['starts_ending_in_global_optimum'])} starting orders "
        f"({land['hc_success_probability'] * 100:.1f}%). It stops at {n(land['stop_orders_shoulder'])} different "
        f"non-optimal orders, and every one of them is a shoulder: there are "
        f"{land['stop_orders_local_optimum']} true local optima, on all three layouts.",
        "**Why separate seeds for tuning?** If the parameters were chosen on the same runs that are reported, the "
        "reported results would look better than they deserve. With 1000-1299 for tuning and 0-29 for the "
        "results, the reported runs are a fair test.",
        "**`result.runtime_sec += setup`** - fairness between algorithms: every method pays for what it prepares. "
        "The time of A* with h2 includes the breadth-first searches from the pellets, and the time of the "
        "local-search methods includes the distance table.",
    ])
    assert OPT[L] == 28 and P1["timing_repeats"] == P2["timing_repeats"] == 20
