"""Study guide, Sections 1 and 2: how to use the guide, the hands-on tour, the model on one page."""
import re

from study_guide_common import (
    CODE1, CODE2, HEUR, L, LAND, LAYOUTS, LOC, M1, N_SEEDS, OPT, S2, SIZE, TRADE, W, WORK, n, run_command,
    run_session, transcript_text)

BOX = "FFF4DC"          # "What an examiner may point at"
NOTE = "EEF3FA"         # other boxes


def lines_between(text, first, last=None, keep=None):
    """The part of a command's output from the line containing `first` to the line containing `last`."""
    lines = text.rstrip("\n").split("\n")
    begin = next(i for i, line in enumerate(lines) if first in line)
    end = len(lines) - 1 if last is None else next(i for i in range(begin, len(lines)) if last in lines[i])
    chosen = lines[begin:end + 1]
    if keep is not None:
        chosen = [line for line in chosen if keep(line)]
    return "\n".join(line.rstrip() for line in chosen)


def build(doc):
    # ------------------------------------------------------------------ 1. how to use
    doc.heading("1. How to use this guide", 1, new_page=True)
    doc.para(
        "The oral discussion is held with each of us alone. The project description says that each student "
        "\"must be able to explain every part of the code, including 'what if' questions, and the theory behind "
        "the algorithms\" (uninformed, heuristic and local search). The grade of a student who cannot answer is "
        "reduced by 10%, and by 5% for a student who answers only some of the questions.")
    doc.para(
        "Our code was developed with the help of an AI assistant, and both reports say so. The project "
        "description accepts outside sources only together with understanding: it counts material taken from AI "
        "tools \"without understanding and citing\" as plagiarism. The citing is done in the reports. The "
        "understanding is what the discussion tests, and it is what this guide is for. If you are asked how the "
        "code was written, say exactly that: an AI assistant helped to write and test it; the team reviewed it, "
        "ran every experiment and can explain every part.")
    doc.para("**How to study with it.**", space_after=2, keep_with_next=True)
    doc.numbered([
        "Do the 15-minute tour below with a terminal open. Seeing the program run makes everything else easier.",
        "Learn Section 2 (the model) until you can write it on paper from memory. Every other answer builds on it.",
        "Read Section 3 with the source file open next to it. Before you read our explanation of a function, say "
        "aloud what you think it does. The boxes \"What an examiner may point at\" are the lines that are most "
        "likely to be asked about.",
        "Sections 4 and 5: cover the answer, answer aloud in your own words, then compare. A good answer gives "
        "the reason and, where we have one, the number.",
        "Read Section 6 (the numbers) again on the morning of the discussion.",
        "Section 7: practise the demo of your own area, then the demo of one other member.",
    ])
    doc.callout([
        "**Conventions.** **Measured** means: the number is in the submitted result files (`results.json`, the "
        "CSV files) or comes from an experiment that we ran for this guide with the project code; the command to "
        "repeat it is given. **Theory** means: it follows from the textbook and the lectures and was not measured. "
        "Keep the two apart in your own answers as well (\"we measured 4,458 expansions\" - \"theory says "
        "O(b^{d})\").",
        "\"The large layout\" is the main instance; numbers without a layout name refer to it. Positions are "
        "(row, col) with row 0 at the top. Costs and node counts are exact and repeat on every run; running times "
        "change by several percent between sessions, so never argue from a small time difference.",
        "**Work on a copy of the project folder.** Running Python creates `__pycache__` folders, and the "
        "`--quick` runs write new result folders; neither belongs in the folder we submit. The file "
        "`whatif_experiments.py` next to this guide repeats every experiment of Section 5 "
        "(`python whatif_experiments.py --list`).",
    ], fill=NOTE)

    # ------------------------------------------------------------------ 1.1 tour
    doc.heading("1.1 A 15-minute hands-on tour", 2)
    doc.para(
        "Open a terminal in (a copy of) `Phase2\\code`. Every command below was run on the final code and the "
        "output is real; `...` marks lines we left out. Your costs and node counts must be identical; your times "
        "will differ a little.")

    listing = run_command([CODE2 / "main.py", "--list"])["stdout"]
    doc.para("**Step 1 - the mazes (1 minute).**  `python main.py --list`  prints the four layouts; the last one "
             "is the main instance:", space_after=2, keep_with_next=True)
    doc.code(lines_between(listing, "Layout 'large'", None, keep=lambda line: line.strip()))
    assert "38 free cells, 8 pellets" in listing and "reachable 8,576" in listing
    doc.para("Notice N = 38 free cells and k = 8 pellets: 38 x 2^{8} = 9,728 is the upper bound of Section 2. "
             "`P` is the start, `.` a pellet, `G` the ghost, `#` a wall.")

    everything = run_command([CODE2 / "main.py"])["stdout"]
    doc.para("**Step 2 - all nine algorithms (3 minutes).**  `python main.py`  runs everything on the large "
             "layout:", space_after=2, keep_with_next=True)
    doc.code(lines_between(everything, "Search algorithms", "Genetic Algorithm"))
    for label, cost, expanded in (("BFS", 38, "4,458"), ("UCS", 28, "2,841"), ("A* (h2)", 28, "108")):
        assert S2[(L, label)]["path_cost"] == cost and n(S2[(L, label)]["nodes_expanded"]) == expanded
        assert re.search(rf"{re.escape(label)}\s+{cost}\s", everything), label
    doc.para(
        "Notice: the four uninformed algorithms return three different costs (38, 116, 28, 38); A* returns the "
        "same cost as UCS with 108 expansions instead of 2,841; a local-search \"solution\" is an order of the "
        "pellets, shown here as the order in which they are really eaten. In this table the time of Greedy and A* "
        "does not include building the heuristic (`main.py` builds it before the call); in the reports it does.")

    tiny = run_command([CODE2 / "main.py", "-l", "tiny", "-a", "bfs", "ucs", "--show-path"])["stdout"]
    doc.para("**Step 3 - fewest steps is not lowest cost (2 minutes).**  "
             "`python main.py -l tiny -a bfs ucs --show-path`", space_after=2, keep_with_next=True)
    doc.code(lines_between(tiny, "BFS solution", None, keep=lambda line: line.strip()))
    assert "BFS solution (8 moves, cost 12)" in tiny and "UCS solution (10 moves, cost 10)" in tiny
    doc.para(
        "BFS needs 8 moves but pays 12: its path enters the cell next to the ghost once (8 + 4). UCS walks around "
        "the bottom: 10 moves, cost 10. This is the whole Phase I story in one small maze. Try the same with "
        "`-a dfs ids`.")

    seed2 = run_command([CODE2 / "main.py", "-a", "hc", "sa", "ga", "--seed", "2"])["stdout"]
    seed7 = run_command([CODE2 / "main.py", "-a", "hc", "sa", "ga", "--seed", "7"])["stdout"]
    doc.para("**Step 4 - random algorithms and seeds (2 minutes).**  `python main.py -a hc sa ga --seed 2`  and "
             "then the same with  `--seed 7`:", space_after=2, keep_with_next=True)
    doc.code(lines_between(seed2, "algorithm  ", "Genetic Algorithm") + "\n"
             + "... and the Hill Climbing line of the run with --seed 7:\n"
             + lines_between(seed7, "Hill Climbing", "Hill Climbing"))
    hc_costs = W["local"]["hc_costs_by_seed"]
    assert hc_costs[2] == 33 and hc_costs[7] == 28
    assert re.search(r"Hill Climbing\s+2\s+33\s", seed2) and re.search(r"Hill Climbing\s+7\s+28\s", seed7)
    doc.para(
        "With seed 2 hill climbing starts on an order that no swap improves and stops at once with cost 33 "
        "(0 iterations, 29 evaluations = the start and its 28 neighbours). With seed 7 it reaches the optimum 28. "
        "Run a command twice: the same seed always gives exactly the same line.")

    tests2 = run_command(["-m", "unittest", "discover", "-s", "tests"], cwd=CODE2)["stderr"]
    tests1 = run_command(["-m", "unittest", "discover", "-s", "tests"], cwd=CODE1)["stderr"]
    assert "Ran 74 tests" in tests2 and "Ran 33 tests" in tests1 and tests2.strip().endswith("OK") \
        and tests1.strip().endswith("OK")
    doc.para(
        "**Step 5 - the unit tests (1 minute).**  `python -m unittest discover -s tests`  ends with "
        "`Ran 74 tests` and `OK` (33 tests of Phase I and 41 of Phase II; in `Phase1\\code` the same command runs "
        "the 33). Add `-v` to see the name of every test - the names read like a list of the facts we checked.")

    quick = run_command([CODE2 / "run_phase2.py", "--quick", "--out", WORK / "p2_quick"])["stdout"]
    doc.para("**Step 6 - reproduce the experiments (3 minutes).**  `python run_phase2.py --quick`  takes about "
             "20 seconds. It prints one block per layout and writes the tables and figures to "
             "`results\\phase2_quick`. The block of the large layout:", space_after=2, keep_with_next=True)
    large_block = lines_between(quick, "=== Layout 'large'", "Hill Climbing (9 restarts)").split("\n")
    shown = large_block[:2] + ["    ...   (the eight search algorithms, with the same numbers as in Step 2)"] \
        + large_block[-4:]
    assert len(large_block) == 14 and large_block[-4].lstrip().startswith("Hill Climbing: best 28 / mean 29.7")
    assert "A* (h2): cost=28 steps=28 generated=253 expanded=108 max_frontier=59" in quick
    assert "BFS: cost=38 steps=26 generated=10554 expanded=4458 max_frontier=675" in quick
    doc.code("\n".join(shown))
    assert "Hill Climbing: best 28 / mean 29.7 / worst 33  - optimum reached in 5 of 10 runs" in quick
    doc.para(
        f"The quick mode uses 10 seeds and 3 timing repeats; the full "
        f"run (`python run_phase2.py`, about a minute and a half) uses {N_SEEDS} seeds - there Hill Climbing reaches "
        f"the optimum in {LOC[(L, 'Hill Climbing')]['optimal_runs']} of {N_SEEDS} runs - and adds the landscape "
        "analysis, the parameter study and the animations. `python run_phase1.py --quick` does the same for "
        "Phase I. Open the `figures` folder and look at `explored_informed_large.png` and `summary_all_large.png`.")

    session = run_session("tour", [["tour", [
        "from pacman_search.layouts import load_problem",
        "p = load_problem(\"large\")",
        "s = p.initial_state; s",
        "p.successors(s)",
        "t = p.result(p.result(s, \"RIGHT\"), \"RIGHT\"); t, bin(t.food)",
        "p.enter_cost((3, 5)), p.enter_cost((3, 4)), p.is_goal(t)",
        "p.state_space_report()",
        "from pacman_search.heuristics import FarthestFoodHeuristic, MazeMSTHeuristic",
        "FarthestFoodHeuristic(p)(s), MazeMSTHeuristic(p)(s)",
    ]]])["tour"]
    text = transcript_text(session)
    assert "State(pos=(1, 3), food=254), '0b11111110'" in text and "(12, 24)" in text and "(5, 1, False)" in text
    doc.para("**Step 7 - talk to the model directly (3 minutes).**  Start `python` in the code folder and type:",
             space_after=2, keep_with_next=True)
    doc.code(text)
    doc.para(
        "Pellet 0 lies at (1, 3) and is bit 0 of the mask, so after two moves to the right the mask is 11111110. "
        f"(3, 5) is next to the ghost and costs 5 to enter. The two heuristics estimate {HEUR[(L, 'h1')]['h_start']} "
        f"and {HEUR[(L, 'h2')]['h_start']} for the start state; the true cost is {OPT[L]}.")
    doc.figure(CODE1 / "results" / "phase1" / "figures" / "layouts.png",
               "The four layouts as pictures (Figure 1 of the Phase I report). The small numbers next to the "
               "pellets are the pellet indices = bit positions in the food mask; red frames are the danger cells. "
               "Keep this picture at hand for Sections 2 to 5.", width_cm=10.0)

    # ------------------------------------------------------------------ 2. the model
    doc.heading("2. The model on one page", 1, new_page=True)
    model = W["model"]
    large = model[L]
    assert large["goal_states"] == large["free_cells"] == 38
    assert large["danger_cell_list"] == [[3, 5], [4, 6], [5, 5]] and W["tour"]["ghosts"] == [[4, 5]]
    assert not any(model[name]["pellet_on_danger_cell"] for name in model)
    doc.table(
        ["Component", "Definition (this is what you write on the board)", "In `problem.py`"],
        [
            ["State", "A pair (pos, food). pos = (row, col) of Pac-Man; row 0 is the top row. food = a bitmask with "
                      "one bit per pellet: bit i is 1 while pellet i is still uneaten. Pellets are numbered in "
                      "reading order (row by row, left to right).", "`State` (a NamedTuple)"],
            ["Initial state", "(start cell, all k bits set). Large layout: ((1, 1), 255), i.e. mask 11111111.",
             "`initial_state`"],
            ["Goal test", "food = 0: every pellet has been eaten. The final position does not matter, so there is "
                          f"one goal state per free cell ({large['goal_states']} on the large layout).", "`is_goal`"],
            ["Actions", "UP, RIGHT, DOWN, LEFT, always generated in this order. An action is legal only if the "
                        "target cell is neither a wall nor a ghost. There is no \"stay\" and no diagonal move.",
             "`ACTIONS`, `actions`"],
            ["Transition", "Pac-Man moves one cell; if the new cell holds a pellet, that pellet's bit is cleared. "
                           "Deterministic.", "`result`, `successors`"],
            ["Step cost", "The cost of ENTERING the target cell: 5 if it is a danger cell, otherwise 1. Leaving a "
                          "danger cell costs nothing extra. Path cost = sum of the step costs.",
             "`enter_cost`, `step_cost`"],
            ["Danger cells", "The free cells directly above, below, left or right of a ghost (not diagonal). Large "
                             "layout: (3, 5), (4, 6) and (5, 5), around the ghost at (4, 5) - see Figure 1.",
             "`danger_cells`"],
        ],
        widths_cm=[2.2, 11.8, 3.4], size=9, bold_first_col=True, stripe=False, keep_together=False)
    doc.para(
        "**Why the food mask is part of the state.** (1) The goal \"all pellets eaten\" cannot be expressed with "
        "the position alone. (2) A state must contain everything the future depends on: on the same cell, "
        "different pellets left call for different moves. With the mask in the state, two paths that reach the "
        "same (pos, food) pair really are interchangeable, so a graph search may keep only one of them. The "
        "price: the state space is multiplied by 2^{k}.")
    doc.para("**Size of the state space** (N = free cells, k = pellets) - three counts, from rough to exact:",
             space_after=2, keep_with_next=True)
    doc.numbered([
        "**Upper bound N x 2^{k}**: every free cell with every subset of pellets.",
        "**Valid states N x 2^{k} - k x 2^{k-1}**: Pac-Man cannot stand on a pellet that is still uneaten "
        "(entering the cell eats it). For each of the k pellet cells, half of the 2^{k} masks are impossible.",
        "**Reachable states**: counted exactly by `reachable_states()`, a breadth-first sweep over the whole "
        "state graph without a goal test.",
    ])
    rows = []
    for name in ("tiny", "small", "medium", "large"):
        m = model[name]
        rows.append([name, m["grid"], n(m["free_cells"]), n(m["pellets"]), n(m["ghosts"]), n(m["danger_cells"]),
                     n(m["upper_bound"]), n(m["valid"]), n(m["reachable"]),
                     n(OPT[name]) if name in OPT else n(W["goal_test"]["ucs"]["tiny"]["late"]["cost"]),
                     n(TRADE[name]["fewest_steps"]) if name in TRADE else n(W["goal_test"]["bfs"]["tiny"]["early"]["steps"])])
    doc.table(["Layout", "Grid", "N", "k", "Ghosts", "Danger cells", "N x 2^{k}", "Valid", "Reachable",
               "Optimal cost C*", "Fewest steps d"],
              rows, widths_cm=[1.5, 1.4, 1.0, 0.9, 1.4, 1.5, 1.8, 1.5, 1.9, 2.0, 2.1], align=["l"] + ["c"] * 10,
              size=9, bold_first_col=True)
    gap_large = large["valid"] - large["reachable"]
    gap_small = model["small"]["valid"] - model["small"]["reachable"]
    assert large["valid_but_unreachable"] == {"6,1": 64, "6,7": 64} and gap_large == 128
    assert model["small"]["valid_but_unreachable"] == {"5,2": 8, "5,3": 8, "5,4": 8} and gap_small == 24
    assert model["medium"]["valid"] == model["medium"]["reachable"]
    doc.para(
        f"Large layout: 38 x 256 = {n(large['upper_bound'])}; minus 8 x 128 = 1,024 gives {n(large['valid'])} valid "
        f"states; {n(large['reachable'])} of them are reachable. The missing {gap_large} are valid on paper but can "
        "never occur: the cells (6, 1) and (6, 7) each lie between two pellets and have no other entrance, so "
        "Pac-Man cannot stand there while both neighbouring pellets are uneaten (2 cells x 2^{6} masks). The same "
        f"effect removes {gap_small} states in the small layout (the cells (5, 2), (5, 3), (5, 4) between pellets 2 "
        "and 3: 3 x 2^{3}); in the medium layout every valid state is reachable. One more pellet doubles the "
        "state space; one more free cell adds only 2^{k} states.")
    doc.para("**Modeling assumptions.**", space_after=2, keep_with_next=True)
    doc.bullets([
        "The maze is fully known and nothing changes while Pac-Man plans (static, fully observable, "
        "deterministic, one agent), so the problem can be solved offline by search.",
        "Ghosts do not move. Their own cell cannot be entered; their danger is modelled as a higher cost (5 "
        "instead of 1) for entering a cell next to them.",
        "One cell per action in the four compass directions; cells may be visited any number of times. A pellet "
        "is eaten the moment its cell is entered and never comes back.",
        "No power pellets, score, lives or time limit: only the path cost counts. The outer border of our mazes "
        "is a wall. Every pellet can be reached and every step cost is positive - the code refuses a maze or a "
        "cost where this is not true.",
    ])
    assert M1[(L, "UCS")]["path_cost"] == OPT[L] and LAND[L]["orders"] == 40320 and doc.figure_no == 1
