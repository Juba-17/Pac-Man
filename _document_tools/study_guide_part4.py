"""Study guide, Sections 5-7: "what if" questions, the cheat sheet, who should be able to demo what."""
from study_guide_common import (
    GA, HC_RR, HEUR, L, LAND, LOC, M1, MEMO, N_SEEDS, ONE, OPT, P2, S2, SA, SIZE, TEXTBOOK, TGA, TRADE,
    TUNE_RUNS, VARIANT, W, ms, n, run_session, transcript_text)

NOTE = "EEF3FA"

# The questions of Section 5 in their order; ref("name") gives the number of a question.
ORDER = ["danger1", "danger10", "cheap", "order", "pellet", "unreachable", "ghosts", "diagonal", "twenty",
         "bfs_late", "ucs_early", "dfs_noset", "dfs_norev", "ids_memo", "ids_step",
         "weighted", "sum", "noreopen", "inconsistent", "ties", "zero", "manhattan", "cache",
         "sa_fast", "sa_cold", "ga_ops", "ga_more", "sideways", "restarts", "seeds", "noskip", "meantime"]


def ref(key):
    return f"W{ORDER.index(key) + 1}"


SETUP = [
    "from pacman_search.layouts import LAYOUTS, load_problem",
    "from pacman_search.problem import PacmanProblem",
    "from pacman_search.uninformed import breadth_first_search, depth_first_search",
    "from pacman_search.uninformed import uniform_cost_search, iterative_deepening_search",
    "from pacman_search.heuristics import FarthestFoodHeuristic, MazeMSTHeuristic, ZeroHeuristic",
    "from pacman_search.informed import a_star_search, greedy_best_first_search, best_first_search",
    "from pacman_search.local_search import TourProblem, hill_climbing",
    "from pacman_search.local_search import simulated_annealing, genetic_algorithm",
    "p = load_problem(\"large\"); tour = TourProblem(p)",
    "h1 = FarthestFoodHeuristic(p); h2 = MazeMSTHeuristic(p)",
]
BLOCKS = [
    ["setup", SETUP],
    ["danger1", [
        "q = PacmanProblem(LAYOUTS[\"large\"], \"large\", danger_cost=1)",
        "print(breadth_first_search(q).summary()); print(uniform_cost_search(q).summary())"]],
    ["danger10", [
        "q = PacmanProblem(LAYOUTS[\"large\"], \"large\", danger_cost=10)",
        "print(breadth_first_search(q).summary()); print(uniform_cost_search(q).summary())"]],
    ["memo", ["print(iterative_deepening_search(p, use_memo=True).summary())"]],
    ["pellet", [
        "rows = LAYOUTS[\"large\"].strip(\"\\n\").split(\"\\n\"); rows[5] = \"#.  .  .#\"",
        "q = PacmanProblem(\"\\n\".join(rows), \"nine pellets\"); print(q.describe())",
        "print(uniform_cost_search(q).summary()); print(a_star_search(q, MazeMSTHeuristic(q)).summary())"]],
    ["unreachable", ["PacmanProblem(\"#####\\n#P#.#\\n#####\")"]],
    ["weighted", [
        "class Times:",
        "    def __init__(self, h, w): self.h, self.w, self.label = h, w, f\"{w} x {h.label}\"",
        "    def __call__(self, state): return self.w * self.h(state)",
        "",
        "for w in (1, 2, 5): print(a_star_search(p, Times(h2, w)).summary())",
        ""]],
    ["reopen", [
        "f = lambda node: node.path_cost + h1(node.state)",
        "print(best_first_search(p, f, \"A* (h1), no re-opening\", reopen=False).summary())"]],
    ["zero", [
        "print(a_star_search(p, ZeroHeuristic()).summary())",
        "print(greedy_best_first_search(p, ZeroHeuristic()).summary())"]],
    ["sa", [
        "def hits(run): return sum(run(seed).cost == 28 for seed in range(30))",
        "",
        "hits(lambda s: simulated_annealing(tour, seed=s))",
        "hits(lambda s: simulated_annealing(tour, seed=s, cooling_rate=0.9))",
        "hits(lambda s: simulated_annealing(tour, seed=s, start_temperature=1.0))"]],
    ["ga", [
        "hits(lambda s: genetic_algorithm(tour, seed=s, mutation_rate=0.0))",
        "hits(lambda s: genetic_algorithm(tour, seed=s, crossover_rate=0.0))"]],
    ["sideways", ["[hits(lambda s: hill_climbing(tour, seed=s, max_sideways=m)) for m in (0, 5, 20, 100)]"]],
    ["seeds", ["[hill_climbing(tour, seed=s).cost for s in range(10)]",
               "hill_climbing(tour, seed=2).order == hill_climbing(tour, seed=2).order"]],
]


def printed(transcript):
    """Only what Python printed in a session (the lines without a prompt)."""
    return [line for line in transcript.split("\n") if not line.startswith((">>>", "..."))]


def build(doc, question_refs):
    session = run_session("whatif", BLOCKS)
    text = {name: transcript_text(session[name]) for name, _ in BLOCKS}
    asked = []

    def what_if(key, question, *paragraphs, transcript=None, repeat=None):
        asked.append(key)
        assert ORDER[len(asked) - 1] == key, (key, "is not at its place in ORDER")
        doc.para(f"**{ref(key)}. {question}**", space_before=6, space_after=2, keep_with_next=True)
        for index, paragraph in enumerate(paragraphs):
            last = index == len(paragraphs) - 1
            doc.para(paragraph, space_after=3, keep_with_next=last and bool(transcript or repeat))
        if repeat:
            doc.para(f"__Repeat it:__ {repeat}", size=9, space_after=2 if transcript else 4,
                     keep_with_next=bool(transcript))
        if transcript:
            doc.code(text[transcript])

    opt, d = OPT[L], M1[(L, "BFS")]["steps"]
    danger, act, goal = W["danger_cost"], W["action_order"], W["goal_test"]
    bfs, dfs, ucs, ids = (M1[(L, a)] for a in ("BFS", "DFS", "UCS", "IDS"))
    a1, a2 = S2[(L, "A* (h1)")], S2[(L, "A* (h2)")]
    local, land = W["local"], LAND[L]

    doc.heading("5. \"What if\" questions with answers", 1)
    doc.para(
        "Every answer says what was **measured** and what is **theory**. \"Measured\" numbers come from the result "
        "files or from runs that we made for this guide with the unchanged project code. There are two ways to "
        "repeat them:")
    doc.bullets([
        "`python whatif_experiments.py NAME` - the file lies next to this guide, and `--list` shows the names. It "
        "imports the code from `Phase2\\code` and changes nothing there. Where an answer needs a changed "
        "algorithm (for example BFS with a late goal test), the changed copy is written out in that file with the "
        "one changed line marked.",
        "Short experiments are given as a Python session. Start `python` in a copy of `Phase2\\code`, type the ten "
        "set-up lines below once, and then the lines of the question. The sessions printed here were run for this "
        "guide; we only cut the `time=...` part off the `summary()` lines.",
    ])
    doc.code(text["setup"])
    assert len(SETUP) == 10 and not printed(text["setup"])

    # ------------------------------------------------------------------ the model
    doc.heading("5.1 Changing the model", 2)
    d1 = {name: danger[f"1/{name}"] for name in ("small", "medium", "large")}
    for name, row in d1.items():
        assert row["bfs"]["cost"] == row["ucs"]["cost"] == row["bfs"]["steps"] == TRADE[name]["fewest_steps"]
        assert not row["genuine_tradeoff"]
        assert row["ucs"]["expanded"] == goal["bfs"][name]["late"]["expanded"]
    assert "BFS: cost=26 steps=26" in text["danger1"] and "UCS: cost=26 steps=26" in text["danger1"]
    what_if("danger1", "What if entering a danger cell cost 1, like any other cell?",
            "**Measured.** All step costs are then equal and BFS becomes optimal: on all three layouts BFS and UCS "
            "return the same cost, which is the fewest number of steps ("
            + " / ".join(str(d1[name]["bfs"]["cost"]) for name in ("small", "medium", "large"))
            + "), and `step_cost_tradeoff` reports no trade-off. UCS now does MORE work than BFS "
            f"({n(d1[L]['ucs']['expanded'])} expansions against {n(d1[L]['bfs']['expanded'])}) because it tests the "
            f"goal late: with equal costs UCS is exactly BFS with a late goal test ({ref('bfs_late')} gives the "
            "same number).",
            "**Take-away.** The danger cost is the only reason why BFS and UCS disagree in Phase I.",
            transcript="danger1")
    d10 = {name: danger[f"10/{name}"] for name in ("small", "medium", "large")}
    assert d10[L]["ucs"]["cost"] == opt and d10[L]["bfs"]["cost"] == d + 3 * 9 and d10[L]["bfs_danger_entries"] == 3
    assert d10["small"]["ucs"]["cost"] == d10["small"]["ucs"]["steps"] + 9 * d10["small"]["ucs_danger_entries"]
    assert d10["small"]["ucs_danger_entries"] == 3 and d10["medium"]["ucs"]["cost"] == OPT["medium"]
    what_if("danger10", "What if it cost 10?",
            f"**Measured.** On the large layout the optimal cost stays {opt}, because the best plan never enters a "
            f"danger cell. BFS returns the same {d}-step path as before, which now costs {d} + 3 x 9 = "
            f"{d10[L]['bfs']['cost']}. UCS expands fewer nodes ({n(d10[L]['ucs']['expanded'])} instead of "
            f"{n(ucs['nodes_expanded'])}): the dangerous short cuts have moved further away in cost. On the small "
            f"layout the optimum rises from {OPT['small']} to {d10['small']['ucs']['cost']}, because its best plan "
            f"cannot avoid entering danger cells 3 times ({d10['small']['ucs']['steps']} steps + 3 x 9); the medium "
            f"layout stays at {OPT['medium']}.",
            transcript="danger10")
    half = danger["half/large"]
    assert half["ucs"]["cost"] == 24.5 and half["ucs"]["solution"] == bfs["solution"] and half["unit"] == 0.5
    assert all(half[h]["admissible"] and half[h]["consistent"] and half[h]["astar"]["cost"] == 24.5 for h in ("h1", "h2"))
    what_if("cheap", "What if a danger cell were cheaper than a normal cell - or free?",
            "**Measured.** With a danger cost of 0.5 on the large layout the cheapest step is 0.5, and both "
            f"heuristics are multiplied by it (`cheapest_step`): h1(start) = {half['h1']['h_start']:g}, h2(start) = "
            f"{half['h2']['h_start']:g}. They stay admissible and consistent on every state, and A* stays optimal: "
            f"cost {half['ucs']['cost']} (the {d}-step path of BFS is now the cheapest plan: 23 normal steps + 3 x "
            "0.5). But the heuristics are weak now, because they must assume that every step costs only 0.5: A* with "
            f"h2 needs {n(half['h2']['astar']['expanded'])} expansions. A cost of 0 or less is refused by the "
            f"constructor: \"{danger['zero_cost_error']}\"",
            "**Theory.** The textbook guarantee for UCS assumes that every step costs at least some e > 0: then the "
            "path cost grows with every step, and the search cannot wander for ever along free moves. With negative "
            "costs a longer walk could be cheaper than a shorter one, and the argument \"the first goal taken from "
            "the queue is the cheapest\" breaks down. That is why the code accepts positive costs only.",
            repeat="`python whatif_experiments.py danger_cost`")
    rev, orig = act[L]["reversed"], act[L]["original"]
    assert rev["BFS"]["steps"] == rev["IDS"]["steps"] == d and rev["UCS"]["cost"] == rev["A* (h2)"]["cost"] == opt
    assert rev["A* (h2)"]["expanded"] == a2["nodes_expanded"] and rev["A* (h1)"]["expanded"] == a1["nodes_expanded"]
    assert orig["first_successors"] == ["RIGHT", "DOWN"] and rev["first_successors"] == ["DOWN", "RIGHT"]
    med = act["medium"]["reversed"]
    what_if("order", "What if the actions were generated in the opposite order (LEFT, DOWN, RIGHT, UP)?",
            f"**Measured (large layout).** What is guaranteed does not change: BFS and IDS still need {d} steps, UCS "
            f"and A* still cost {opt}, and A* expands exactly as many nodes as before ({n(a2['nodes_expanded'])} "
            f"with h2, {n(a1['nodes_expanded'])} with h1). What depends on ties does change. BFS and IDS return a "
            f"different {d}-step path, which costs {rev['BFS']['cost']} instead of {bfs['path_cost']} (medium "
            f"layout: {med['BFS']['cost']} instead of {M1[('medium', 'BFS')]['path_cost']}). DFS returns a "
            f"completely different plan ({rev['DFS']['steps']} steps, cost {rev['DFS']['cost']}, instead of "
            f"{dfs['steps']} steps, cost {dfs['path_cost']}). Greedy with h2 returns cost "
            f"{rev['Greedy (h2)']['cost']} instead of {S2[(L, 'Greedy (h2)')]['path_cost']}. The amount of work "
            f"shifts too: BFS {n(rev['BFS']['expanded'])} expansions instead of {n(bfs['nodes_expanded'])}, IDS "
            f"{n(rev['IDS']['expanded'])} instead of {n(ids['nodes_expanded'])}.",
            "**Take-away.** The answers of BFS, IDS, DFS and Greedy are \"one of several possible\", and the action "
            "order picks which. The guarantees (fewest steps, lowest cost) are not touched.",
            repeat="`python whatif_experiments.py action_order` (the function `problem_with_action_order` swaps "
                   "the order only while the problem object is being built)")
    extra = W["extra_pellet"]
    size9 = extra["size"]
    new = {k: v["new"] for k, v in extra["search"].items()}
    old = {k: v["old"] for k, v in extra["search"].items()}
    assert extra["cell"] == [5, 4] and size9["upper_bound"] == 38 * 512 and size9["pellets"] == 9
    assert old["UCS"]["expanded"] == ucs["nodes_expanded"] and old["A* (h2)"]["expanded"] == a2["nodes_expanded"]
    lo_new, lo_old = extra["local"], extra["local_old"]
    assert all(lo_old[a]["hits"] == LOC[(L, a)]["optimal_runs"] for a in lo_old)
    assert f"reachable {size9['reachable']:,}" in text["pellet"] and f"UCS: cost={new['UCS']['cost']} " in text["pellet"]
    growth = [new[a]["expanded"] / old[a]["expanded"] for a in ("BFS", "UCS", "IDS", "A* (h1)", "A* (h2)")]
    assert 2 <= min(growth) and max(growth) <= 5
    what_if("pellet", "What if the maze had one more pellet?",
            "**Measured.** We put a ninth pellet on the cell (5, 4) of the large layout. The state space roughly "
            f"doubles: upper bound {n(size9['upper_bound'])}, valid {n(size9['valid'])}, reachable "
            f"{n(size9['reachable'])} (before: {n(SIZE[L]['upper_bound'])} / {n(SIZE[L]['valid'])} / "
            f"{n(SIZE[L]['reachable'])}). That is above the \"about 1,000 to 10,000 states\" that the project "
            f"description asks for - the reason why we stopped at 8 pellets. The optimal cost becomes "
            f"{new['UCS']['cost']}. Expansions: BFS "
            f"{n(new['BFS']['expanded'])} (before {n(old['BFS']['expanded'])}), UCS {n(new['UCS']['expanded'])} "
            f"({n(old['UCS']['expanded'])}), IDS {n(new['IDS']['expanded'])} ({n(old['IDS']['expanded'])}), A* with "
            f"h1 {n(new['A* (h1)']['expanded'])} ({n(old['A* (h1)']['expanded'])}), A* with h2 "
            f"{n(new['A* (h2)']['expanded'])} ({n(old['A* (h2)']['expanded'])}).",
            f"Local search now has 9! = {n(extra['orders'])} orders and {extra['neighbours']} neighbours. With the "
            f"SAME parameters, optimal runs out of {N_SEEDS}: Hill Climbing {lo_new['Hill Climbing']['hits']} "
            f"(before {lo_old['Hill Climbing']['hits']}), Simulated Annealing "
            f"{lo_new['Simulated Annealing']['hits']} ({lo_old['Simulated Annealing']['hits']}), Genetic Algorithm "
            f"{lo_new['Genetic Algorithm']['hits']} ({lo_old['Genetic Algorithm']['hits']}), Hill Climbing with 9 "
            f"restarts {lo_new[HC_RR]['hits']} ({lo_old[HC_RR]['hits']}).",
            "**Take-away.** One pellet doubles the states and multiplies the work of the systematic searches by two "
            "to five. And parameters belong to an instance: the settings tuned for 8 pellets are no longer enough "
            "for 9.",
            repeat="the session below - or save the maze in a text file and run "
                   "`python main.py --layout-file my_maze.txt`",
            transcript="pellet")
    unreach = W["unreachable"]
    assert unreach["constructor_error"] in text["unreachable"]
    assert all(not row["found"] for row in unreach["search"].values())
    assert all(unreach["search"][a]["expanded"] == unreach["reachable_states"]
               for a in ("BFS", "DFS", "UCS", "Greedy (h1)", "A* (h1)"))
    assert unreach["h2_error"].startswith("KeyError") and unreach["TourProblem_error"].startswith("KeyError")
    what_if("unreachable", "What if a pellet could not be reached?",
            "**Measured.** `PacmanProblem` refuses such a maze (session below). If the check is switched off (a "
            "small subclass in `whatif_experiments.py`) and one pellet of the tiny maze is walled in, then BFS, DFS, "
            f"UCS, Greedy and A* expand all {unreach['reachable_states']} reachable states and return `found = "
            f"False`. IDS stops after {unreach['search']['IDS']['iterations']} iterations "
            f"({unreach['search']['IDS']['expanded']} expansions), because `depth_limited_search` returns `None` as "
            "soon as nothing was cut off by the limit. h2 and the distance table of local search cannot even be "
            "built (KeyError): they need a distance to every pellet.",
            "**Theory.** A complete algorithm reports failure on a finite state space; it does not loop.",
            repeat="`python whatif_experiments.py unreachable`; the refusal itself:",
            transcript="unreachable")
    what_if("ghosts", "What if the ghosts moved?",
            "**Theory - not implemented and not measured.** If the ghosts walked a fixed, known round, the state "
            "would need the time as well: (pos, food, time step within the round). That multiplies the number of "
            "states by the length of the round, the danger cells would depend on the time, and a \"wait\" action "
            "would become useful. The six search algorithms would run unchanged, because they use only "
            "`initial_state`, `successors` and `is_goal`. h1 would stay admissible. h2 would have to measure its "
            "maze distances without the ghosts, because a ghost that walks away opens a shorter way. The distance "
            "table of local search would depend on the time of departure, so `TourProblem` would have to be "
            "redesigned.",
            "If the ghosts chased Pac-Man or moved at random, this would no longer be a classical search problem: "
            "the world would not be deterministic, and a fixed plan could fail. It would need adversarial search "
            "(minimax, expectimax) or planning again after every move. That is why \"ghosts do not move\" is one of "
            "our modeling assumptions.")
    what_if("diagonal", "What if diagonal moves were allowed?",
            "**Theory.** A state would have up to 8 successors. h1 would no longer be admissible: one diagonal step "
            "reduces the Manhattan distance by 2. The right distance would be the larger of the row difference and "
            "the column difference. h2 computes its distances by breadth-first search over `problem.neighbors`, so "
            "it would adapt by itself and stay admissible. The search algorithms themselves would not change.")
    what_if("twenty", "What if there were 20 pellets?",
            "**Theory, and one measured step.** The state space would be N x 2^{20}, about a million states for "
            "every free cell. BFS and UCS could not store it. The measured trend from 8 to 9 pellets: "
            f"{size9['reachable'] / SIZE[L]['reachable']:.1f} times the states, "
            f"{new['UCS']['expanded'] / old['UCS']['expanded']:.1f} times the expansions of UCS, "
            f"{new['A* (h2)']['expanded'] / old['A* (h2)']['expanded']:.1f} times those of A* with h2. Local search "
            "would still need only a 21 x 21 distance table and a few orders - but there would be 20! (about 2.4 x "
            "10^{18}) orders, no exhaustive look at the landscape, no way of knowing the optimum, and the "
            "parameters would have to be tuned again.")

    # ------------------------------------------------------------------ uninformed
    doc.heading("5.2 Changing the uninformed algorithms", 2)
    late, early = goal["bfs"][L]["late"], goal["bfs"][L]["early"]
    assert late["solution"] == early["solution"] == bfs["solution"] and early["expanded"] == bfs["nodes_expanded"]
    assert goal["bfs"][L]["greedy_h0"]["expanded"] == late["expanded"]
    what_if("bfs_late", "What if BFS tested the goal when a node is expanded (late), as UCS does?",
            f"**Measured.** The same path and cost, but more work: {n(late['expanded'])} expansions instead of "
            f"{n(early['expanded'])} (+{(late['expanded'] / early['expanded'] - 1) * 100:.0f}%) and "
            f"{n(late['max_memory'])} states in memory instead of {n(early['max_memory'])}.",
            "**Theory.** With the late test BFS must finish level d - 1 and expand the nodes of level d that stand "
            "in front of the goal before the goal reaches the head of the queue: O(b^{d+1}) instead of O(b^{d}). "
            "Cross-checks: Greedy with h = 0 and UCS with a danger cost of 1 are both \"BFS with a late goal test\", "
            f"and both expand the same {n(late['expanded'])} nodes.",
            repeat="`python whatif_experiments.py goal_test` (the function `bfs_late_goal_test`)")
    hasty, proper, ce = goal["ucs"][L]["early"], goal["ucs"][L]["late"], goal["counterexample"]
    assert all(goal["ucs"][name]["early"]["cost"] == goal["ucs"][name]["late"]["cost"] for name in goal["ucs"])
    assert not any(W["model"][name]["pellet_on_danger_cell"] for name in W["model"])
    assert (ce["late"]["cost"], ce["late"]["solution"], ce["early"]["cost"], ce["early"]["solution"]) == (
        8, "RLLL", 9, "LLRRR")
    assert ce["maze"] == "######\n#. P.#\n####G#\n######" and ce["danger_cells"] == [[1, 4]]
    what_if("ucs_early", "What if UCS tested the goal when a node is generated (early), as BFS does?",
            f"**Measured.** On our four layouts nothing visible happens: the cost is still optimal ({opt} on the "
            f"large layout) with fewer expansions ({n(hasty['expanded'])} instead of {n(proper['expanded'])}). But "
            "that is a property of our mazes, not of the algorithm: no pellet lies on a danger cell, so the last "
            "step of every plan costs 1, and then the first goal that is generated is also a cheapest one. As soon "
            "as the last pellet can be entered at cost 5, the early test goes wrong. A maze with four free cells:")
    doc.code("######\n"
             "#. P.#     pellets at (1, 1) and (1, 4); the ghost below makes the cell (1, 4) a danger cell\n"
             "####G#\n"
             "######")
    doc.para(
        f"The real UCS returns `{ce['late']['solution']}`, cost {ce['late']['cost']}: step right onto the dangerous "
        "pellet first (5), then three steps left (3). UCS with the early test returns "
        f"`{ce['early']['solution']}`, cost {ce['early']['cost']}. It expands the node \"left pellet eaten, back on "
        "the start cell\" (g = 4), generates a goal of cost 4 + 5 = 9 and stops - although the node \"right pellet "
        "eaten\" (g = 5) is still waiting in the heap and leads to a goal of cost 8.", space_after=3)
    doc.para("**Theory.** This is exactly why UCS and A* must test the goal at expansion time.", space_after=3,
             keep_with_next=True)
    doc.para("__Repeat it:__ `python whatif_experiments.py goal_test` (the function `ucs_early_goal_test`)", size=9,
             space_after=4)
    no_set, tree = W["dfs"][L]["no_explored_set"], W["dfs"][L]["path_check_only"]
    assert not no_set["found"] and no_set["last_cells"][-2:] == [[1, 7], [2, 7]] and no_set["pellets_left"] == 6
    assert (tree["cost"], tree["steps"], tree["expanded"]) == (dfs["path_cost"], dfs["steps"], dfs["nodes_expanded"])
    what_if("dfs_noset", "What if DFS had no explored set?",
            f"**Measured.** It never finishes. On the large layout, after {n(no_set['expanded'])} expansions the "
            f"path was {n(no_set['depth_reached'])} moves long and Pac-Man was bouncing between the cells (1, 7) "
            f"and (2, 7), with {no_set['pellets_left']} pellets still on the board. From (2, 7) the first legal "
            "action is UP, back to (1, 7); from there the first legal action is DOWN again - the same two states "
            "for ever.",
            "**Theory.** DFS as a tree search is not complete in a state space with loops. A middle way: with only "
            "a loop check on the current path (`depth_limited_search` with a huge limit) DFS does finish here and "
            f"returns the same {tree['steps']}-step plan after {tree['expanded']} expansions, with only the path in "
            "memory - but in general such a tree search can explore the same states exponentially often.",
            repeat="`python whatif_experiments.py dfs`")
    no_rev = act[L]["dfs_without_reversed"]
    assert no_rev == rev["DFS"]
    what_if("dfs_norev", "What if `reversed(children)` were removed from DFS?",
            "**Measured.** DFS would then try the actions in the order LEFT, DOWN, RIGHT, UP. It behaves exactly "
            f"like DFS with the reversed action order of {ref('order')}: {no_rev['steps']} steps, cost "
            f"{no_rev['cost']}, {no_rev['expanded']} expansions on the large layout (instead of {dfs['steps']} / "
            f"{dfs['path_cost']} / {dfs['nodes_expanded']}). It is still a correct DFS - just a different one.",
            repeat="`python whatif_experiments.py action_order` (the function `dfs_without_reversed`)")
    textbook, memo = VARIANT[(L, TEXTBOOK)], VARIANT[(L, MEMO)]
    assert f"expanded={memo['nodes_expanded']} " in text["memo"] and "cost=38 steps=26" in text["memo"]
    what_if("ids_memo", "What if IDS used the memo table?",
            f"**Measured (result files, Table 7 of the Phase I report).** {n(memo['nodes_expanded'])} expansions "
            f"instead of {n(textbook['nodes_expanded'])} and {ms(memo['time_ms'])} ms instead of "
            f"{ms(ids['time_ms'])} ms, with the same path - but {n(memo['max_nodes_in_memory'])} states in memory "
            "instead of "
            f"{textbook['max_nodes_in_memory']}, as many as BFS ({n(bfs['max_nodes_in_memory'])}).",
            "**Theory.** The memo table turns every iteration into a graph search. The small memory, the only "
            "reason to use IDS, is gone.",
            transcript="memo")
    step4, step5 = W["ids"]["large/4"], W["ids"]["small/5"]
    assert step4["steps"] == d + 1 and step4["final_limit"] == 28 and step5["steps"] == TRADE["small"]["fewest_steps"]
    what_if("ids_step", "What if the depth limit of IDS grew by 4 instead of by 1?",
            f"**Measured.** On the large layout the limits are 0, 4, 8, ..., {step4['final_limit']}, and the search "
            f"returns a plan with {step4['steps']} steps (cost {step4['cost']}) after {n(step4['expanded'])} "
            f"expansions. That is less work than before, but {step4['steps']} is not the minimum of {d}: a limit of "
            f"{step4['final_limit']} also admits plans that are longer than necessary, and depth-first order "
            "returns the first one it meets. (On the small layout with steps of 5 it happens to find the shortest "
            "plan.)",
            "**Theory.** IDS returns a plan with the fewest steps only because limit L is tried after every smaller "
            "limit has failed.",
            repeat="`python whatif_experiments.py ids`")

    # ------------------------------------------------------------------ informed
    doc.heading("5.3 Changing the heuristics and the informed algorithms", 2)
    wt = W["weighted"]

    def weighted(layout, h, w):
        return wt[f"{layout}/{h}/{w:g}"]

    assert all(row["within_bound"] for key, row in wt.items() if not key.endswith("/sum"))
    assert weighted(L, "h2", 1)["cost"] == opt < weighted(L, "h2", 2)["cost"] and not weighted(L, "h2", 2)["admissible"]
    for w in (1, 2, 5):
        row = weighted(L, "h2", w)
        assert f"A* ({w} x h2): cost={row['cost']} steps={row['steps']} " in text["weighted"]
        assert f"expanded={row['expanded']} " in text["weighted"]
    what_if("weighted", "What if the heuristic were multiplied by 2 or by 5?",
            f"**Measured (A*, large layout).** 2 x h2: cost {weighted(L, 'h2', 2)['cost']} after "
            f"{weighted(L, 'h2', 2)['expanded']} expansions; 5 x h2: cost {weighted(L, 'h2', 5)['cost']} after "
            f"{weighted(L, 'h2', 5)['expanded']} (plain h2: cost {opt} after {a2['nodes_expanded']}). With h1: 2 x h1 "
            f"gives cost {weighted(L, 'h1', 2)['cost']} after {weighted(L, 'h1', 2)['expanded']} expansions, 5 x h1 "
            f"cost {weighted(L, 'h1', 5)['cost']} after {weighted(L, 'h1', 5)['expanded']}. On the medium layout "
            f"2 x h2 returns {weighted('medium', 'h2', 2)['cost']} instead of {OPT['medium']}. The heuristic is no "
            f"longer admissible (2 x h2 overestimates by up to {weighted(L, 'h2', 2)['worst_overestimate']}), so A* "
            "loses its guarantee and gains speed: it behaves more and more like Greedy.",
            "**Theory.** Weighted A* with weight w returns a solution that costs at most w x C*. All our results "
            f"are inside that bound (for example {weighted(L, 'h2', 2)['cost']} <= 2 x {opt}).",
            transcript="weighted")
    total = {name: wt[f"{name}/sum"] for name in ("small", "medium", "large")}
    assert total[L]["h_start"] == HEUR[(L, "h1")]["h_start"] + HEUR[(L, "h2")]["h_start"] > opt
    assert not total[L]["admissible"] and total[L]["cost"] > opt and total["medium"]["cost"] > OPT["medium"]
    assert total["small"]["cost"] == OPT["small"]
    what_if("sum", "What if we used h1 + h2, or the larger of h1 and h2?",
            f"**Measured.** h1 + h2 is not admissible: for the start state it gives {HEUR[(L, 'h1')]['h_start']} + "
            f"{HEUR[(L, 'h2')]['h_start']} = {total[L]['h_start']}, more than the true cost {opt}. A* with it "
            f"returns {total[L]['cost']} on the large layout and {total['medium']['cost']} on the medium one (on the "
            f"small layout {total['small']['cost']}, optimal by luck). The larger of the two is admissible but "
            "useless here: h2 >= h1 in every state, so the maximum is simply h2.",
            "**Theory.** The maximum of two admissible heuristics is admissible and dominates both. The sum is not "
            "admissible in general, because both estimates count the same moves.",
            repeat="`python whatif_experiments.py weighted`")
    ro = W["reopen"]
    r1, r2, rp = ro[f"{L}/h1"], ro[f"{L}/h2"], ro[f"{L}/patchy h2"]
    for name in ("tiny", "small", "medium", "large"):
        for h in ("h1", "h2"):
            assert ro[f"{name}/{h}"]["never"]["cost"] == ro[f"{name}/{h}"]["optimum"]
            assert ro[f"{name}/{h}"]["always"]["requeued_after_expansion"] == 0
        assert ro[f"{name}/patchy h2"]["always"]["cost"] == ro[f"{name}/patchy h2"]["optimum"]
        assert ro[f"{name}/patchy h2"]["admissible"] and ro[f"{name}/patchy h2"]["always"]["states_expanded_twice"] == 0
    assert not rp["consistent"] and rp["never"]["cost"] > opt
    assert rp["lifo"]["states_expanded_twice"] == 1 and rp["lifo"]["cost"] == opt
    assert f"cost={r1['never']['cost']} " in text["reopen"] and f"expanded={r1['never']['expanded']} " in text["reopen"]
    what_if("noreopen", "What if A* did not re-open states (`reopen=False`)?",
            "**Measured.** With h1 and h2 the cost stays optimal on all four layouts (large layout, h1: cost "
            f"{r1['never']['cost']} after {n(r1['never']['expanded'])} expansions instead of "
            f"{n(r1['always']['expanded'])}). With the \"patchy\" heuristic of {ref('inconsistent')}, which is "
            f"admissible but not consistent, the cost on the large layout is {rp['never']['cost']} instead of {opt}.",
            "**Theory.** Optimality needs the cheapest known path of every state to be the one that is in the "
            "queue. With `reopen=False` the FIRST path found is kept, even when a cheaper one turns up later (in "
            f"the normal A* run that happens {r1['always']['requeued_while_waiting']} times with h1 on the large "
            f"layout and {r2['always']['requeued_while_waiting']} times with h2). That this did no harm with h1 and "
            "h2 on our mazes "
            "is luck, not a guarantee. What a consistent heuristic does guarantee is something weaker: a state that "
            "has already been EXPANDED never has to be expanded again (0 cases in every run).",
            transcript="reopen")
    what_if("inconsistent", "What if the heuristic were admissible but not consistent?",
            "**Measured.** The \"patchy\" heuristic (h2 on every second cell, 0 on the others - the idea of one of "
            "our unit tests) is admissible but not consistent. Our A* still returns the optimum on all four "
            f"layouts (large layout: {rp['always']['cost']}, after {rp['always']['expanded']} expansions instead of "
            f"{a2['nodes_expanded']} with the real h2).",
            "**Theory.** With an inconsistent heuristic f can fall along a path, so a state may be expanded before "
            "its cheapest path is known. Re-opening repairs that, at the price of expanding some states twice. With "
            "our first-in-first-out ties this did not happen on our layouts; with newest-first ties one state of the "
            "large layout was expanded twice.",
            repeat="`python whatif_experiments.py reopen`")
    census = W["f_census"][L]
    assert census["h2"]["f_below_optimum"] + census["h2"]["f_equal_optimum_non_goal"] == a2["nodes_expanded"]
    assert r2["lifo"]["cost"] == r1["lifo"]["cost"] == opt
    small2 = ro["small/h2"]
    assert small2["lifo"]["expanded"] > small2["always"]["expanded"] and r2["lifo"]["expanded"] < r2["always"]["expanded"]
    what_if("ties", "What if the heap entries had no counter, or ties were broken the other way round?",
            "**Measured.** Without the counter Python stops at the first tie with "
            f"`{W['python']['heap_without_counter']}`. With \"newest first\" instead of \"oldest first\" A* still "
            f"returns the optimum; only the number of expansions changes: {r2['lifo']['expanded']} instead of "
            f"{r2['always']['expanded']} with h2 and {n(r1['lifo']['expanded'])} instead of "
            f"{n(r1['always']['expanded'])} with h1 on the large layout - but {small2['lifo']['expanded']} instead "
            f"of {small2['always']['expanded']} with h2 on the small one.",
            f"**Theory.** A* must expand every state with f < C* ({census['h2']['f_below_optimum']} states for h2 on "
            f"the large layout). Among the states with f = C* ({census['h2']['f_equal_optimum_non_goal']} of them) "
            "the tie-breaking decides, and no rule is best on every maze.",
            repeat="`python whatif_experiments.py reopen python`")
    zero_a, zero_g = goal["ucs"][L]["astar_h0"], goal["bfs"][L]["greedy_h0"]
    assert (zero_a["expanded"], zero_a["generated"], zero_a["max_memory"], zero_a["solution"]) == (
        ucs["nodes_expanded"], ucs["nodes_generated"], ucs["max_nodes_in_memory"], ucs["solution"])
    assert zero_g["solution"] == bfs["solution"]
    assert f"expanded={zero_a['expanded']} " in text["zero"] and f"expanded={zero_g['expanded']} " in text["zero"]
    what_if("zero", "What if the heuristic were 0 everywhere?",
            f"**Measured.** A* becomes exactly UCS: the same path, {n(zero_a['expanded'])} expansions, "
            f"{n(zero_a['generated'])} nodes generated, {n(zero_a['max_memory'])} in memory (also a unit test). "
            "Greedy becomes a breadth-first search with a late goal test: every f is 0, so the counter alone orders "
            f"the heap, first in, first out. It returns the path of BFS ({zero_g['steps']} steps, cost "
            f"{zero_g['cost']}) after {n(zero_g['expanded'])} expansions.",
            transcript="zero")
    hv = W["heuristic_variants"]
    mm = {name: hv[name]["h2 (Manhattan)"] for name in hv}
    assert all(mm[name]["admissible"] and mm[name]["consistent"] and mm[name]["astar_cost"] == OPT[name] for name in mm)
    assert all(mm[name]["astar_expanded"] > hv[name]["h2"]["astar_expanded"] for name in mm)
    what_if("manhattan", "What if h2 used Manhattan distances instead of true maze distances?",
            "**Measured.** It is still admissible and consistent (checked on every state), but weaker: on average it "
            f"reaches {mm[L]['mean_ratio'] * 100:.0f}% of the true cost instead of {hv[L]['h2']['mean_ratio'] * 100:.0f}% "
            f"(small layout {mm['small']['mean_ratio'] * 100:.0f}% instead of "
            f"{hv['small']['h2']['mean_ratio'] * 100:.0f}%, medium {mm['medium']['mean_ratio'] * 100:.0f}% instead of "
            f"{hv['medium']['h2']['mean_ratio'] * 100:.0f}%). A* then needs {mm[L]['astar_expanded']} expansions "
            f"instead of {hv[L]['h2']['astar_expanded']} ({mm['small']['astar_expanded']} instead of "
            f"{hv['small']['h2']['astar_expanded']}, and {mm['medium']['astar_expanded']} instead of "
            f"{hv['medium']['h2']['astar_expanded']}). The maze distances cost one breadth-first search per pellet, "
            f"{HEUR[(L, 'h2')]['setup_ms']:.2f} ms in total.",
            repeat="`python whatif_experiments.py heuristic_variants`")
    cache, calls = ro[f"{L}/cache"], r2["always"]["heuristic_calls"]
    what_if("cache", "What if the spanning tree were computed again on every call (no cache)?",
            "**Measured / theory.** The results would be identical; the cache changes only the speed. In one A* run "
            f"on the large layout h2 was called {calls} times, but only {cache['masks_cached']} different food "
            f"masks occurred (of {cache['possible_masks']} possible ones), so {calls - cache['masks_cached']} of the "
            f"{calls} runs of Prim's algorithm were saved.")

    # ------------------------------------------------------------------ local search
    doc.heading("5.4 Changing local search", 2)

    def both(label):
        row = local[label]
        return f"{row['eval']['hits']} of {row['eval']['runs']} runs on the seeds 0-29 and " \
               f"{row['tuning']['hits']} of {row['tuning']['runs']} on the tuning seeds"

    def pair(label):
        row = local[label]
        return f"{row['eval']['hits']} of {row['eval']['runs']} and {row['tuning']['hits']} of {row['tuning']['runs']}"

    fast, slow, final = local["SA cooling 0.9"], local["SA cooling 0.999"], local["SA final"]
    plain = local["HC plain"]
    assert fast["eval"]["hits"] < plain["eval"]["hits"] and fast["tuning"]["hits"] < plain["tuning"]["hits"]
    assert printed(text["sa"]) == [str(final["eval"]["hits"]), str(fast["eval"]["hits"]),
                                   str(local["SA start 1"]["eval"]["hits"])]
    assert slow["eval"]["hits"] == slow["eval"]["runs"] and slow["tuning"]["hits"] == slow["tuning"]["runs"]
    what_if("sa_fast", "What if simulated annealing cooled faster (rate 0.9)?",
            f"**Measured.** 10 x 0.9^{{n}} falls to 0.1 after {fast['eval']['iterations']:.0f} iterations, so a run "
            f"has only {fast['eval']['evaluations']:.0f} evaluations. It reaches the optimum in "
            f"{both('SA cooling 0.9')} - worse than plain hill climbing ({pair('HC plain')}), which spends "
            f"{plain['eval']['evaluations']:.0f} evaluations. With the rate 0.999 a run has "
            f"{n(slow['eval']['evaluations'])} evaluations and every run is optimal ({pair('SA cooling 0.999')}).",
            "**Take-away.** The cooling rate mostly sets the budget. A fast schedule is simply a short run.",
            repeat=f"the session shows the final settings, then the rate 0.9, then start temperature 1 "
                   f"({ref('sa_cold')})",
            transcript="sa")
    cold, hot, frozen = local["SA start 1"], local["SA start 100"], local["SA frozen"]
    assert frozen["eval"]["iterations"] == final["eval"]["iterations"] == 919
    assert cold["tuning"]["hits"] < frozen["tuning"]["hits"] < final["tuning"]["hits"]
    what_if("sa_cold", "What if it started colder - or never accepted a worse move at all?",
            f"**Measured.** Start temperature 1: {cold['eval']['iterations']:.0f} iterations, optimum in "
            f"{both('SA start 1')}. Start temperature 100: {n(hot['eval']['iterations'])} iterations, "
            f"{pair('SA start 100')}. No temperature at all (T practically 0, the same "
            f"{frozen['eval']['iterations']:.0f} iterations; equal-cost swaps are accepted, worse ones never): "
            f"{pair('SA frozen')}.",
            "**Take-away.** On this landscape most of the benefit of annealing is the long walk over the plateaus. "
            f"Real uphill moves add a few points ({final['tuning']['hits']} of {final['tuning']['runs']} with the "
            "final settings).",
            repeat="`python whatif_experiments.py local`")
    nomut, nox, none = local["GA no mutation"], local["GA no crossover"], local["GA no mutation, no crossover"]
    rs = W["restarts"]
    chance = rs["chance_optimal_order_in_30"]
    assert (rs["optimal_orders"], rs["orders"]) == (240, 40320) == (land["optimal_orders"], land["orders"])
    assert nomut["tuning"]["hits"] < nox["tuning"]["hits"] and abs(none["tuning"]["hits"] / none["tuning"]["runs"] - chance) < 0.05
    assert printed(text["ga"]) == [str(nomut["eval"]["hits"]), str(nox["eval"]["hits"])]
    what_if("ga_ops", "What if the genetic algorithm had no mutation, or no crossover?",
            f"**Measured.** Without mutation: optimum in {both('GA no mutation')}. Without crossover: "
            f"{pair('GA no crossover')} - no loss at all. Without both: {pair('GA no mutation, no crossover')}, "
            "which is just the chance that one of the 30 random starting orders is already optimal: 1 - (1 - 240 / "
            f"40,320)^{{30}} = {chance * 100:.0f}%.",
            "**Take-away.** Order crossover brings no measurable benefit (the Phase II report says the same). What "
            "counts on this small landscape is mutation, that is, fresh random orders: the report shows that the "
            "GA with its final settings is no better than random sampling here (Section 4.4).",
            repeat="the session shows \"no mutation\" and then \"no crossover\" on the seeds 0-29",
            transcript="ga")

    def one(parameter, value, algorithm="GA"):
        return ONE[(algorithm, parameter, value)]

    what_if("ga_more", "What if the genetic algorithm used elitism, a bigger tournament or a smaller population?",
            f"**Measured (result files, {TUNE_RUNS} tuning runs per setting).** Optimal runs with 0 / 1 / 2 / 5 "
            "elites: " + " / ".join(str(one("elite_count", v)["hits"]) for v in (0, 1, 2, 5))
            + ". Tournament size 2 / 3 / 5: " + " / ".join(str(one("tournament_size", v)["hits"]) for v in (2, 3, 5))
            + ". Population 10 / 20 / 30 / 60: " + " / ".join(str(TGA[(v, 0.8)]["hits"]) for v in (10, 20, 30, 60))
            + " (with " + " / ".join(n(TGA[(v, 0.8)]["evaluations"]) for v in (10, 20, 30, 60))
            + " evaluations). Generations 10 / 20 / 30 / 60: "
            + " / ".join(str(one("generations", v)["hits"]) for v in (10, 20, 30, 60)) + ".",
            "**Take-away.** More selection pressure (elites, large tournaments) makes the small population uniform "
            "too early. More individuals or more generations mean a larger budget and more reliability.")
    side = {m: local[f"HC sideways {m}"] for m in (5, 20, 100)}
    assert printed(text["sideways"]) == [str([plain["eval"]["hits"]] + [side[m]["eval"]["hits"] for m in (5, 20, 100)])]
    assert local["HC sideways 20/small"]["hits"] == local["HC sideways 20/medium"]["hits"] == 30
    assert all(side[m]["tuning"]["hits"] == one("max_sideways", m, "HC")["hits"] for m in side)
    what_if("sideways", "What if hill climbing allowed sideways moves?",
            "**Measured.** With up to 5 / 20 / 100 equal-cost moves in a row the optimum is reached in "
            + " / ".join(str(side[m]["tuning"]["hits"]) for m in (5, 20, 100))
            + f" of {TUNE_RUNS} tuning runs (without: {plain['tuning']['hits']}), at "
            + " / ".join(n(one("max_sideways", m, "HC")["evaluations"]) for m in (5, 20, 100))
            + " evaluations per run; on the seeds 0-29 in "
            + " / ".join(str(side[m]["eval"]["hits"]) for m in (5, 20, 100))
            + f" of 30 (without: {plain['eval']['hits']}). On the small and medium layouts 20 sideways moves give "
              "30 of 30.",
            "**Take-away.** Sideways moves help, because every stopping point is a shoulder. But they are "
            "expensive: each sideways step costs a full look at all 28 neighbours, and a random walk needs many "
            "steps to find the way off a large plateau.",
            repeat="the session counts the optimal runs on the seeds 0-29 for 0, 5, 20 and 100 sideways moves",
            transcript="sideways")
    assert LOC[(L, HC_RR)]["optimal_runs"] == local["HC 9 restarts"]["eval"]["hits"]
    what_if("restarts", "What if it used random restarts - and how many are enough?",
            "**Measured.** With 0 / 1 / 2 / 4 / 9 restarts: "
            + " / ".join(str(one("restarts", v, "HC")["hits"]) for v in (0, 1, 2, 4, 9))
            + f" of {TUNE_RUNS} tuning runs; with 9 restarts on the seeds 0-29: {LOC[(L, HC_RR)]['optimal_runs']} of "
            f"{N_SEEDS}, for {n(LOC[(L, HC_RR)]['mean_evaluations'])} evaluations per run.",
            "**Theory.** If one climb succeeds with probability p, then r + 1 independent climbs succeed with "
            f"probability 1 - (1 - p)^{{r+1}}. With p = {rs['p_single_climb']:.3f} from the landscape analysis this "
            "gives " + ", ".join(
                f"{100 * (1 - (1 - land['starts_ending_in_global_optimum'] / land['orders']) ** (r + 1)):.1f}%"
                for r in (0, 1, 2, 4, 9))
            + f". We checked the formula on {n(rs['seeds'])} further seeds: "
            + ", ".join(f"{rs[str(r)]['measured'] * 100:.1f}%" for r in (0, 1, 2, 4, 9))
            + f". ({TUNE_RUNS} runs are a sample: the tuning runs with 1 and 2 restarts, "
            + " and ".join(f"{100 * one('restarts', v, 'HC')['hits'] / TUNE_RUNS:.0f}%" for v in (1, 2))
            + ", lie a little below these values by chance.)",
            repeat="`python whatif_experiments.py restarts`")
    assert all(one("restarts", v, "HC")["hits"] / TUNE_RUNS < rs[str(v)]["predicted"] for v in (1, 2))
    costs = local["hc_costs_by_seed"]
    assert printed(text["seeds"]) == [str(costs[:10]), "True"] and local["same_seed_same_result"]
    what_if("seeds", "What if two different seeds are used - and the same seed twice?",
            "**Measured.** A different seed means a different random start and possibly a different result: the "
            "costs of plain hill climbing for the seeds 0 to 9 are " + ", ".join(str(c) for c in costs[:10])
            + ". The same seed gives exactly the same run - the same order, cost and history (a unit test; the "
            f"second line of the session compares two runs with seed 2). Simulated annealing and the genetic "
            f"algorithm returned {opt} for all {N_SEEDS} seeds, but only {final['tuning']['hits']} of "
            f"{final['tuning']['runs']} times on other seeds.",
            transcript="seeds")
    dec = W["decoding"]
    assert all(dec[name]["naive_minimum"] == OPT[name] for name in ("small", "medium", "large"))
    what_if("noskip", "What if pellets that are eaten in passing were not skipped?",
            "**Measured.** The best order would still cost the optimum: the cheapest \"walk to every pellet in "
            f"turn\" over all orders costs {dec[L]['naive_minimum']} on the large layout (and "
            f"{dec['small']['naive_minimum']} and {dec['medium']['naive_minimum']} on the others). But "
            f"{n(dec[L]['orders_where_naive_costs_more'])} of the {n(dec[L]['orders'])} orders would cost more "
            "than they do now, and their plans would walk back to cells that are already empty - some of them "
            "after the last pellet has been eaten, which is not a clean solution of the search model.",
            repeat="`python whatif_experiments.py decoding`")
    one_run, two_run = M1[(L, "BFS")], S2[(L, "BFS")]
    what_if("meantime", "What if we reported the mean running time instead of the fastest run?",
            "**Measured.** BFS on the large layout was timed in two sessions (the Phase I and the Phase II result "
            f"files). The fastest runs: {ms(one_run['time_ms'])} ms and {ms(two_run['time_ms'])} ms. The means: "
            f"{ms(one_run['time_mean_ms'])} ms and {ms(two_run['time_mean_ms'])} ms. The first session was disturbed "
            f"(standard deviation {ms(one_run['time_std_ms'])} ms); the mean carried the disturbance into the "
            "result, the minimum did not.",
            "For the randomised algorithms we do report a mean - over the seeds, because different seeds do "
            "different amounts of work - but the time of each seed is again the fastest of 3 identical runs.")
    assert asked == ORDER and len(asked) >= 25

    # ------------------------------------------------------------------ 6. cheat sheet
    doc.heading("6. Cheat sheet: the numbers to know by heart", 1, new_page=True)
    doc.para("Everything on this page is read from the two `results.json` files; the tuning column, the danger "
             "column and the counts marked \"plans\" and \"f < C*\" come from the experiments of Section 5.",
             size=9, space_after=3)
    doc.table(
        ["Layout", "Grid", "N", "k", "N x 2^{k}", "Valid", "Reachable", "Optimal cost C*", "Fewest steps d",
         "Cheapest plan with d steps", "BFS / IDS return"],
        [[name, SIZE[name]["grid"], n(SIZE[name]["free_cells"]), n(SIZE[name]["pellets"]), n(SIZE[name]["upper_bound"]),
          n(SIZE[name]["valid"]), n(SIZE[name]["reachable"]),
          f"{OPT[name]} ({TRADE[name]['fewest_steps_at_optimal_cost']} steps)", n(TRADE[name]["fewest_steps"]),
          f"cost {TRADE[name]['cheapest_cost_with_fewest_steps']}", f"cost {M1[(name, 'BFS')]['path_cost']}"]
         for name in ("small", "medium", "large")],
        widths_cm=[1.4, 1.2, 0.8, 0.7, 1.5, 1.4, 1.7, 2.3, 1.7, 2.3, 2.0], align=["l"] + ["c"] * 10, size=8.5,
        bold_first_col=True)
    paths = W["paths"][L]
    doc.table(
        ["Large layout", "Cost", "Steps", "Danger cells entered", "Generated", "Expanded", "Max frontier",
         "Max nodes in memory", "Time (ms)"],
        [[a, n(S2[(L, a)]["path_cost"]), n(S2[(L, a)]["steps"]), n(paths[a]["danger_entries"]),
          n(S2[(L, a)]["nodes_generated"]), n(S2[(L, a)]["nodes_expanded"]), n(S2[(L, a)]["max_frontier"]),
          n(S2[(L, a)]["max_nodes_in_memory"]), ms(S2[(L, a)]["time_ms"])]
         for a in ("BFS", "DFS", "UCS", "IDS", "Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)")],
        widths_cm=[2.5, 1.2, 1.2, 2.2, 1.9, 1.9, 1.9, 2.4, 1.8], align=["l"] + ["r"] * 8, size=8.5,
        bold_first_col=True)
    searches = ("BFS", "DFS", "UCS", "IDS", "Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)")
    doc.para("The other two layouts - path cost / nodes expanded of every search algorithm, and the optimal runs of "
             "plain hill climbing:", size=9, space_after=2, keep_with_next=True)
    doc.table(
        ["Layout"] + list(searches) + [f"HC optimal (of {N_SEEDS})"],
        [[name] + [f"{S2[(name, a)]['path_cost']} / {n(S2[(name, a)]['nodes_expanded'])}" for a in searches]
         + [n(LOC[(name, "Hill Climbing")]["optimal_runs"])] for name in ("small", "medium")],
        widths_cm=[1.4, 1.9, 1.8, 1.9, 2.3, 1.9, 1.5, 1.6, 1.5, 1.6], align=["l"] + ["c"] * 9, size=8.5,
        bold_first_col=True)
    tune_label = {"Hill Climbing": "HC plain", "Simulated Annealing": "SA final", "Genetic Algorithm": "GA final",
                  HC_RR: "HC 9 restarts"}
    doc.table(
        ["Large layout, local search", "Best", "Mean", "Worst", f"Optimal runs (of {N_SEEDS})",
         f"On the tuning seeds (of {TUNE_RUNS})", "Evaluations per run", "Orders in memory", "Time (ms)"],
        [[a, n(LOC[(L, a)]["best"]), f"{LOC[(L, a)]['mean']:.2f}", n(LOC[(L, a)]["worst"]),
          n(LOC[(L, a)]["optimal_runs"]), n(local[tune_label[a]]["tuning"]["hits"]),
          n(LOC[(L, a)]["mean_evaluations"]), n(LOC[(L, a)]["orders_in_memory"]), ms(LOC[(L, a)]["time_ms"])]
         for a in ("Hill Climbing", "Simulated Annealing", "Genetic Algorithm", HC_RR)],
        widths_cm=[3.9, 1.0, 1.2, 1.1, 2.1, 2.4, 2.0, 1.7, 1.6], align=["l"] + ["r"] * 8, size=8.5,
        bold_first_col=True)
    h1r, h2r = HEUR[(L, "h1")], HEUR[(L, "h2")]
    ratio_ids = ids["nodes_expanded"] / bfs["nodes_expanded"]
    doc.bullets([
        f"**Heuristics (large layout).** h1(start) = {h1r['h_start']}, h2(start) = {h2r['h_start']}, true cost "
        f"{h1r['true_cost_start']}. Mean h / h*: {h1r['mean_ratio']:.2f} for h1, {h2r['mean_ratio']:.2f} for h2 "
        f"(small {HEUR[('small', 'h1')]['mean_ratio']:.2f} / {HEUR[('small', 'h2')]['mean_ratio']:.2f}, medium "
        f"{HEUR[('medium', 'h1')]['mean_ratio']:.2f} / {HEUR[('medium', 'h2')]['mean_ratio']:.2f}). Both admissible "
        f"and consistent on all {n(h1r['states_checked'])} states and {n(h1r['transitions_checked'])} transitions; "
        f"h2 > h1 in {n(h1r['states_where_h2_is_larger'])} states. States with f < C*: "
        f"{n(census['h0']['f_below_optimum'])} (h = 0), {n(census['h1']['f_below_optimum'])} (h1), "
        f"{n(census['h2']['f_below_optimum'])} (h2).",
        f"**Landscape (large layout).** {n(land['orders'])} orders, {land['optimal_orders']} optimal, "
        f"{n(dec[L]['distinct_plans'])} different plans; costs {land['best_cost']} / {land['median_cost']:.0f} / "
        f"{land['worst_cost']} (best / median / worst). One climb succeeds from "
        f"{land['hc_success_probability'] * 100:.1f}% of the starts; it stops at "
        f"{n(land['stop_orders_shoulder'])} non-optimal orders, all of them shoulders - "
        f"{land['stop_orders_local_optimum']} true local optima. An uphill swap adds {land['mean_uphill_swap']:.1f} "
        "on average.",
        f"**Parameters.** Simulated annealing: start temperature {SA['start_temperature']:g}, cooling rate "
        f"{SA['cooling_rate']}, end temperature {SA['end_temperature']} - {W['python']['sa_iterations_formula']} "
        f"iterations, {n(LOC[(L, 'Simulated Annealing')]['mean_evaluations'])} evaluations. Genetic algorithm: "
        f"population {GA['population_size']}, {GA['generations']} generations, tournament size "
        f"{GA['tournament_size']}, crossover rate {GA['crossover_rate']}, mutation rate {GA['mutation_rate']}, "
        f"{GA['elite_count']} elites - {n(LOC[(L, 'Genetic Algorithm')]['mean_evaluations'])} evaluations. Hill "
        f"climbing: no parameters; extra experiment with {P2['hc_restarts']} restarts. Neighbours: "
        f"{dec[L]['neighbours']} swaps.",
        f"**Seeds and timing.** Results: seeds 0-{N_SEEDS - 1}. Tuning: seeds {P2['tuning_seeds'][0]}-"
        f"{P2['tuning_seeds'][1]}, {TUNE_RUNS} runs per setting. Running time = the fastest of up to "
        f"{P2['timing_repeats']} runs (local search: mean over the seeds, each seed the fastest of 3).",
        f"**Ratios.** BFS pays {bfs['path_cost']} = {d} + 3 x 4 instead of {opt}. DFS: "
        f"{dfs['path_cost'] / opt:.1f} times the optimum. IDS: {ratio_ids:.0f} times the expansions of BFS with "
        f"{ids['max_nodes_in_memory'] / bfs['max_nodes_in_memory'] * 100:.0f}% of its memory (with the memo table: "
        f"{n(memo['nodes_expanded'])} expansions, {n(memo['max_nodes_in_memory'])} nodes in memory). A* with h2: "
        f"{ucs['nodes_expanded'] / a2['nodes_expanded']:.0f} times fewer expansions than UCS, "
        f"{a1['nodes_expanded'] / a2['nodes_expanded']:.0f} times fewer than A* with h1; "
        f"{S2[('small', 'A* (h2)')]['nodes_expanded']} and {S2[('medium', 'A* (h2)')]['nodes_expanded']} expansions "
        "on the small and medium layouts.",
    ], size=9)

    # ------------------------------------------------------------------ 7. who demos what
    doc.heading("7. Who should be able to demo what", 1, new_page=True)
    doc.callout([
        "**Every member must be able to explain everything in this guide.** The discussion is individual, and the "
        "examiner may ask anyone about any file. The table only says who is responsible for which area - and so "
        "who should be the fastest and the surest there - and which demo that member should be able to run "
        "without notes. Practise your own row first, then one other row.",
    ], fill=NOTE)
    from team import TEAM
    q = question_refs
    areas = [
        ("the problem model, the layouts and the size of the state space - `problem.py`, `layouts.py`. **Demo:** "
         "`python main.py --list`, then Step 7 of the tour; derive 38 x 256 - 8 x 128 = 8,704 on paper and explain "
         "the 128 valid states that cannot be reached.",
         "the two heuristics, their proofs and their check on every state - `heuristics.py`. **Demo:** h1 and h2 "
         f"of the start state (12 and 24, true cost 28); `analyse_heuristic`; the proofs {q['h1_proof']} to "
         f"{q['dominance']} on the board."),
        ("BFS and DFS and the shared search core - `search_core.py`, the first two functions of `uninformed.py`. "
         "**Demo:** `python main.py -l tiny -a bfs dfs --show-path`; the BFS loop line by line; what each counter "
         "counts.",
         "Greedy Best-First and A* - `informed.py`. **Demo:** `python main.py -a greedy astar`; "
         f"`best_first_search` line by line; the `reopen` flag ({ref('noreopen')}) and why A* is optimal "
         f"({q['astar_optimal']})."),
        ("UCS and IDS and the steps-versus-cost analysis - `uninformed.py`, `step_cost_tradeoff`. **Demo:** "
         f"`python main.py -l tiny -a ucs ids --show-path`; the four-cell maze of {ref('ucs_early')}; IDS with and "
         f"without the memo table ({ref('ids_memo')}).",
         "the local-search formulation, Hill Climbing and the landscape analysis - `TourProblem`, "
         "`hill_climbing`, `analyse_landscape`. **Demo:** `python main.py -a hc --seed 2` and `--seed 7`; decode "
         "the order (5, 3, 4, 1, 2, 6, 7, 0) by hand on Figure 4 of the Phase II report."),
        ("the experiments and measurements, theory against measured - `experiments.py`, `run_phase1.py`, the "
         "tests. **Demo:** `python run_phase1.py --quick`; the unit tests; why the fastest run is reported "
         f"({ref('meantime')}).",
         "Simulated Annealing, the Genetic Algorithm and the parameter study - `simulated_annealing`, "
         "`genetic_algorithm`, `tuning_study`. **Demo:** `python main.py -a sa ga`; exp(-delta / T) for delta = 8 at "
         f"T = 10 and at T = 1; the crossover example of {q['crossover']}."),
        ("the visualization (explored states, search trees) and the take-away messages - `visualize.py`, "
         "`main.py`. **Demo:** read `explored_large.png` and `trees_tiny.png` aloud; "
         "`python main.py -l small -a ucs --show-path`.",
         "the comparison of all nine algorithms and the summary charts - `visualize_phase2.py`, `run_phase2.py`. "
         "**Demo:** `python run_phase2.py --quick`; read `summary_all_large.png` and Table 12 of the report; argue "
         f"why A* with h2 is the best choice ({q['best']})."),
    ]
    order = W["decoding"]["large_example"]["order"]
    assert order == [5, 3, 4, 1, 2, 6, 7, 0] and (h1r["h_start"], h2r["h_start"], opt) == (12, 24, 28)
    assert SIZE[L]["valid"] == 38 * 256 - 8 * 128 == 8704 and SIZE[L]["valid"] - SIZE[L]["reachable"] == 128
    doc.table(
        ["Member", "Phase I: responsible for ...", "Phase II: responsible for ..."],
        [[name + (" (team leader)" if index == 0 else ""), first, second]
         for index, ((name, _, _), (first, second)) in enumerate(zip(TEAM, areas))],
        widths_cm=[3.0, 7.2, 7.2], size=9, bold_first_col=True, stripe=False)
    doc.para(
        "A good final rehearsal: one member opens a file at a random place and asks \"what does this line do, and "
        "what happens if I change it?\" - the others answer without the guide.", space_before=4)
    return len(asked)
