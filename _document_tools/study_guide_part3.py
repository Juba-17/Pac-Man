"""Study guide, Section 4: theory questions with model answers."""
import math

from study_guide_common import (
    GA, HEUR, IDS_ITER, L, LAND, LOC, M1, MEMO, N_SEEDS, ONE, OPT, P2, S2, SA, SIZE, TEXTBOOK, TGA, TRADE, TSA,
    TUNE_RUNS, VARIANT, W, effective_branching_factor, keep_header_with_first_row, ms, n)


class Questions:
    """Numbers the questions and writes question + answer paragraphs."""

    def __init__(self, doc, prefix):
        self.doc, self.prefix, self.count, self.refs = doc, prefix, 0, {}

    def ask(self, question, *answer, key=None):
        """`key` gives the question a name, so that other sections can refer to its number."""
        self.count += 1
        if key:
            self.refs[key] = f"{self.prefix}{self.count}"
        self.doc.para(f"**{self.prefix}{self.count}. {question}**", space_before=5, space_after=2,
                      keep_with_next=True)
        for paragraph in answer:
            self.doc.para(paragraph, space_after=3)


def power_of_ten(value):
    exponent = int(math.floor(math.log10(value)))
    return f"{value / 10 ** exponent:.0f} x 10^{{{exponent}}}"


def build(doc):
    q = Questions(doc, "Q")
    model, census = W["model"][L], W["f_census"]
    bfs, dfs, ucs, ids = (M1[(L, a)] for a in ("BFS", "DFS", "UCS", "IDS"))
    g1, g2, a1, a2 = (S2[(L, a)] for a in ("Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)"))
    opt, d = OPT[L], bfs["steps"]
    reach = SIZE[L]["reachable"]
    paths = W["paths"][L]
    memo = VARIANT[(L, MEMO)]
    land = LAND[L]
    hc, sa, ga = (LOC[(L, a)] for a in ("Hill Climbing", "Simulated Annealing", "Genetic Algorithm"))
    local = W["local"]

    doc.heading("4. Theory questions with model answers", 1)
    doc.para("Cover the answer, answer aloud, then compare. Numbers are for the large layout unless a layout is "
             "named; \"measured\" numbers are in the result files or in Section 5.")

    # ------------------------------------------------------------------ 4.1
    doc.heading("4.1 Search problems and uninformed search", 2)
    q.ask("What is a search problem, and what are its parts in our project?",
          "Five things: the states with an initial state, the actions that are possible in a state, a transition "
          "model (what an action does), a goal test, and a step cost for every action (which adds up to the path "
          "cost). A solution is a sequence of actions from the initial state to a goal state; an optimal solution "
          "has the lowest path cost. Ours is Section 2: state (pos, food), start with all pellets on the board, "
          "actions UP / RIGHT / DOWN / LEFT, moving eats the pellet in the new cell, goal food = 0, cost 1 or 5.")
    q.ask("What is the difference between a state and a node?",
          "A state is a situation of the world: (pos, food). A node is a record of the search: a state plus how we "
          "got there (parent, action, path cost g, depth) - the class `Node`. Different nodes can hold the same "
          f"state, reached along different paths. The large layout has {n(reach)} reachable states, but IDS "
          f"generated {n(ids['nodes_generated'])} nodes on it.")
    q.ask("Tree search or graph search - which of our algorithms is which?",
          "A tree search does not remember where it has been. The same state can be expanded again and again, and "
          "in a maze the search can walk in circles. A graph search keeps a table of the states it has reached and "
          "expands each state at most once; the table costs memory, up to the number of states. BFS (`reached`), "
          "DFS (`explored`), UCS, Greedy and A* (`best_cost`) are graph searches. IDS is a tree search that only "
          "refuses to step onto a state that is already on its current path - that is the price of its small "
          f"memory. Measured consequence: IDS expands {n(ids['nodes_expanded'])} nodes in a space of {n(reach)} "
          f"states; BFS expands {n(bfs['nodes_expanded'])}.")
    q.ask("Define completeness, optimality, time and space complexity. What are b, d, m, C* here?",
          "Complete: the algorithm finds a solution whenever one exists. Optimal: the solution it returns has the "
          "lowest path cost. Time and space complexity: how many nodes are generated, and how many are held in "
          "memory at once, written with b (branching factor), d (depth of the shallowest goal), m (maximum depth of "
          "the search tree) and, for UCS, C* (optimal cost) and e (smallest step cost).",
          f"Our values: at most 4 actions; a state has {model['mean_branching']:.2f} successors on average "
          f"({n(model['transitions'])} transitions / {n(reach)} states) and never more than "
          f"{model['max_branching']}; d = {d}; C* = {opt}; e = 1; {n(reach)} reachable states.")
    doc.para("**Q5. Give the properties of the four uninformed algorithms, in theory and as we measured them.**",
             space_before=5, space_after=3, keep_with_next=True)
    q.count += 1
    doc.table(
        ["", "Complete?", "Optimal?", "Time (theory)", "Space (theory)", "Measured: cost / expanded / max in memory"],
        [["BFS", "yes (b finite)", "only if all steps cost the same; here: fewest steps", "O(b^{d})", "O(b^{d})",
          f"{bfs['path_cost']} / {n(bfs['nodes_expanded'])} / {n(bfs['max_nodes_in_memory'])}"],
         ["DFS", "tree search: no (loops); ours, a graph search on a finite space: yes", "no", "O(b^{m})",
          "tree search O(b m); ours up to the number of states (explored set)",
          f"{dfs['path_cost']} / {n(dfs['nodes_expanded'])} / {n(dfs['max_nodes_in_memory'])}"],
         ["UCS", "yes (every step costs at least e > 0)", "yes", "O(b^{1 + floor(C*/e)})", "O(b^{1 + floor(C*/e)})",
          f"{ucs['path_cost']} / {n(ucs['nodes_expanded'])} / {n(ucs['max_nodes_in_memory'])}"],
         ["IDS", "yes", "like BFS: fewest steps", "O(b^{d})", "O(b d)",
          f"{ids['path_cost']} / {n(ids['nodes_expanded'])} / {n(ids['max_nodes_in_memory'])}"]],
        widths_cm=[1.2, 3.6, 3.3, 2.4, 3.1, 3.4], size=9, bold_first_col=True, stripe=False)
    tree_bound = model["mean_branching"] ** d
    q.ask(f"Theory says O(b^{{d}}). Why did BFS expand only {n(bfs['nodes_expanded'])} nodes, when "
          f"{model['mean_branching']:.2f}^{{{d}}} is about {power_of_ten(tree_bound)}?",
          "O(b^{d}) counts the nodes of a search TREE, in which every path is a different node. Our state graph "
          "has very many paths to the same state, and a graph search expands every state at most once, so its "
          f"work is also limited by the number of states, {n(reach)}. That limit is the one that matters here: BFS "
          f"expanded {bfs['nodes_expanded'] / reach * 100:.0f}% of the states. The tree formula shows itself in "
          "IDS, which is a tree search.")
    b = census[L]["bfs"]
    assert b["states_up_to_d_minus_2"] + b["states_at_d_minus_1"] > bfs["nodes_expanded"] > b["states_up_to_d_minus_2"]
    q.ask("Why is BFS not optimal here, although the textbook calls BFS optimal?",
          "BFS returns a solution with the fewest steps. That is the cheapest solution only when all steps cost the "
          f"same, and ours do not. Its {d}-step plan enters danger cells {paths['BFS']['danger_entries']} times and "
          f"costs {d} + {paths['BFS']['danger_entries']} x 4 = {bfs['path_cost']}; the cheapest plan has "
          f"{ucs['steps']} steps, none of them into a danger cell, and costs {opt}. This is not bad luck in the "
          f"tie-breaking: `step_cost_tradeoff` shows that even the cheapest of all {d}-step plans costs "
          f"{TRADE[L]['cheapest_cost_with_fewest_steps']}. With a danger cost of 1, BFS is optimal (Section 5).")
    q.ask("Why is UCS optimal? Give the argument.",
          "UCS always expands the waiting node with the lowest path cost g, and every step costs more than zero, "
          "so g can only grow along a path. When a goal node is taken from the queue, every other waiting node "
          "costs at least as much, and any other solution would have to pass through one of them - so none can be "
          "cheaper. Two details of the code are needed for this: the goal test at expansion time, and `best_cost`, "
          f"which keeps the cheapest known path of every state in the queue. Measured: cost {opt}, equal to the "
          "brute-force optimum of the unit tests.")
    u = census[L]["h0"]
    assert u["expanded"] == ucs["nodes_expanded"] and u["f_below_optimum"] < ucs["nodes_expanded"]
    q.ask(f"Why does UCS expand fewer nodes than BFS on the large layout ({n(ucs['nodes_expanded'])} against "
          f"{n(bfs['nodes_expanded'])}) but more on the small and medium layouts?",
          "BFS grows a ball by depth, UCS a ball by cost. BFS expands every state up to depth d - 2 "
          f"({n(b['states_up_to_d_minus_2'])} states) and part of level d - 1 "
          f"({n(bfs['nodes_expanded'] - b['states_up_to_d_minus_2'])} of {n(b['states_at_d_minus_1'])}). UCS expands "
          f"every state that can be reached for less than C* ({n(u['f_below_optimum'])} states) and part of those "
          f"that cost exactly C* ({n(ucs['nodes_expanded'] - u['f_below_optimum'])} of "
          f"{n(u['f_equal_optimum_non_goal'])}). On the large layout the danger cost puts many states that are near "
          "in steps far away in cost, so the cost ball is the smaller one. On the small and medium layouts C* lies "
          f"far above d ({OPT['small']} against {TRADE['small']['fewest_steps']}, {OPT['medium']} against "
          f"{TRADE['medium']['fewest_steps']}), the cost ball is larger "
          f"({n(M1[('small', 'UCS')]['nodes_expanded'])} against {n(M1[('small', 'BFS')]['nodes_expanded'])} and "
          f"{n(M1[('medium', 'UCS')]['nodes_expanded'])} against {n(M1[('medium', 'BFS')]['nodes_expanded'])} "
          "expansions), and UCS cannot stop when a goal is merely generated.")
    ratio, memo_ratio = ids["nodes_expanded"] / bfs["nodes_expanded"], memo["nodes_expanded"] / bfs["nodes_expanded"]
    restart = model["restart_only_expansions"]
    assert model["fewest_steps"] == d == len(IDS_ITER[L]) - 1 and restart < memo["nodes_expanded"]
    q.ask(f"Why does IDS need {ratio:.0f} times as many expansions as BFS, and what does it get in return?",
          f"It gets memory: never more than {ids['max_nodes_in_memory']} nodes (its stack and the current path), "
          f"about {ids['max_nodes_in_memory'] / bfs['max_nodes_in_memory'] * 100:.0f}% of the "
          f"{n(bfs['max_nodes_in_memory'])} of BFS, and this depends on the depth of the solution only.",
          f"It pays with repeated work, for two reasons. (1) It starts again from the root for each of the "
          f"{len(IDS_ITER[L])} depth limits. Even a search that expanded every state within the limit exactly once "
          f"per iteration would need {n(restart)} expansions for the {len(IDS_ITER[L]) - 1} unsuccessful "
          f"iterations, {restart / bfs['nodes_expanded']:.1f} times BFS. In a tree whose levels grow by a factor b "
          "this overhead would only be about b / (b - 1), because the last level dominates; our state graph grows "
          f"slowly (never more than {n(model['largest_level'])} new states per level), so the shallow levels are a "
          "large part of the work. (2) It is a tree search: it explores a state again through every path that "
          f"reaches it. This accounts for the rest, a further factor of about "
          f"{ids['nodes_expanded'] / restart:.0f}.",
          f"The memo-table version removes most of the second effect: {n(memo['nodes_expanded'])} expansions, "
          f"{memo_ratio:.1f} times BFS. But it stores {n(memo['max_nodes_in_memory'])} states, and the memory "
          "advantage is gone.")
    for name in ("small", "medium", "large"):
        assert M1[(name, "BFS")]["solution"] == M1[(name, "IDS")]["solution"]
        swapped = W["action_order"][name]["reversed"]
        assert swapped["BFS"]["solution"] == swapped["IDS"]["solution"] != M1[(name, "BFS")]["solution"]
    q.ask("Do BFS and IDS return the same plan?",
          "Yes - on all three layouts, and also when the action order is reversed (measured). It is not a "
          "coincidence. Both produce the successors in the same action order. The first-in-first-out queue of BFS "
          "keeps every level sorted by action sequence, and the depth-first order of IDS is the same order, so both "
          "return the first of all shortest solutions in that order. Both guarantee only the fewest steps, not the "
          "lowest cost.")
    no_set = W["dfs"][L]["no_explored_set"]
    q.ask(f"Is DFS complete? And why did it expand only {dfs['nodes_expanded']} nodes?",
          "As a tree search DFS is not complete: in a maze it walks in circles (measured: without the explored set "
          f"our DFS was still bouncing between two cells after {n(no_set['expanded'])} expansions). With the "
          "explored set it is complete on a finite state space.",
          f"It expanded only {dfs['nodes_expanded']} nodes for a path of {dfs['steps']} steps because this problem "
          "has no dead ends: from every state the remaining pellets can still be eaten, so DFS almost never has to "
          "back up - it wanders until everything is eaten. The plan it returns is poor (cost "
          f"{dfs['path_cost']}, {dfs['path_cost'] / opt:.1f} times the optimum) and depends on the action order.")

    # ------------------------------------------------------------------ 4.2
    doc.heading("4.2 Heuristics and informed search", 2)
    h1r, h2r = HEUR[(L, "h1")], HEUR[(L, "h2")]
    q.ask("What is a heuristic? What do \"admissible\" and \"consistent\" mean, and how are they related?",
          "h(s) estimates the cheapest cost from s to a goal; h*(s) is the true value. **Admissible:** h(s) <= h*(s) "
          "for every state - it never overestimates. **Consistent:** h = 0 at a goal and h(s) <= c(s, a, s') + h(s') "
          "for every transition - one step never lowers the estimate by more than the step costs.",
          "Consistent implies admissible (add the inequality up along a cheapest path to the goal). The reverse is "
          "false: the \"patchy\" heuristic of our unit test (h2 on every second cell, 0 elsewhere) is admissible but "
          "not consistent.")
    q.ask("Define h1 and h2. Which relaxed problem does each solve?",
          "**h1** = the Manhattan distance from Pac-Man to the FARTHEST remaining pellet. Relaxed problem: no "
          "walls, no danger cost, and only that one pellet has to be reached.",
          "**h2** = the maze distance (in steps, around the walls) to the NEAREST remaining pellet + the weight of "
          "the minimum spanning tree (MST) that connects all remaining pellets, with maze distances as edge weights. "
          "Relaxed problem: the walls are kept, the danger cost is ignored, and after the first pellet the others "
          "only have to be CONNECTED by a tree instead of visited along one path.",
          "The cheapest solution of an easier problem can never cost more than the cheapest solution of the real "
          "one - that is why relaxed problems give admissible heuristics. For the start state h1 = "
          f"{h1r['h_start']} and h2 = {h2r['h_start']}; the true cost is {h1r['true_cost_start']}.")
    q.ask("Prove that h1 is admissible and consistent.",
          "__Admissible.__ Let p be the farthest remaining pellet. Every solution must enter the cell of p. One "
          "move changes the Manhattan distance to p by exactly 1, so at least Manhattan(pos, p) moves are needed, "
          "and each costs at least 1.",
          "__Consistent.__ One move changes the distance to every pellet by exactly 1, so the largest of these "
          "distances falls by at most 1. If the move eats a pellet, that pellet was at distance 1, and the others "
          "still change by at most 1; if it was the last pellet, h1 goes from 1 to 0. So h1(s) - h1(s') <= 1 <= c.",
          key="h1_proof")
    q.ask("Prove that h2 is admissible.",
          "Take any solution from s and write down the remaining pellets in the order in which it first reaches "
          "them: q1, q2, ..., qm. The solution needs at least d(pos, q1) + d(q1, q2) + ... + d(q(m-1), qm) moves, "
          "because d is the smallest number of moves between two cells. The first term is at least the distance to "
          "the nearest pellet. The other terms are the edges of a path through all remaining pellets; a path is "
          "one particular spanning tree, so their sum is at least the weight of the MINIMUM spanning tree. Every "
          "move costs at least 1. So every solution costs at least h2(s).")
    q.ask("Prove that h2 is consistent.",
          "__Case A - the move eats nothing.__ The set of pellets, and so the MST, is unchanged. One step changes "
          "any maze distance by at most 1, so the distance to the nearest pellet falls by at most 1.",
          "__Case B - the move eats pellet q.__ Before the move q was one step away, so h2(s) <= 1 + MST(F). Let F' "
          "be the pellets without q. Hanging q onto the minimum spanning tree of F' by its cheapest edge gives a "
          "spanning tree of F, so MST(F) <= MST(F') + (distance from q to its nearest pellet in F'). The right-hand "
          "side is exactly h2(s'), because after the move Pac-Man stands on q. Together: h2(s) <= 1 + h2(s') <= c + "
          "h2(s'). If q was the last pellet, h2 goes from 1 to 0.")
    c = census[L]
    assert c["h2"]["f_below_optimum"] < c["h1"]["f_below_optimum"] < c["h0"]["f_below_optimum"]
    q.ask("What does \"h2 dominates h1\" mean, why is it true, and what does it buy?",
          "It means h2(s) >= h1(s) in every state (and both are admissible). Why it is true: walk from Pac-Man to "
          "the nearest pellet and then along tree edges to the pellet that is farthest in Manhattan distance. This "
          "is a real walk of at most h2 steps, and no walk to that pellet can be shorter than its Manhattan "
          "distance, which is h1.",
          "What it buys: A* with a consistent heuristic has to expand every state whose f = g + h is below C*. A "
          f"larger h leaves fewer such states. Measured: {n(c['h0']['f_below_optimum'])} states have f < {opt} with "
          f"h = 0 (that is UCS), {n(c['h1']['f_below_optimum'])} with h1 and {n(c['h2']['f_below_optimum'])} with "
          f"h2. The real numbers of expansions are {n(ucs['nodes_expanded'])}, {n(a1['nodes_expanded'])} and "
          f"{n(a2['nodes_expanded'])}; the difference are states with f exactly {opt}, where the tie-breaking "
          f"decides. h2 is strictly larger than h1 in {n(h1r['states_where_h2_is_larger'])} of the "
          f"{n(h1r['states_checked'])} states.", key="dominance")
    q.ask("How accurate are the two heuristics, and what does h2 still miss?",
          f"Averaged over all non-goal states, h1 reaches {h1r['mean_ratio'] * 100:.0f}% of the true remaining cost "
          f"and h2 {h2r['mean_ratio'] * 100:.0f}% (small layout: "
          f"{HEUR[('small', 'h1')]['mean_ratio'] * 100:.0f}% and {HEUR[('small', 'h2')]['mean_ratio'] * 100:.0f}%; "
          f"medium: {HEUR[('medium', 'h1')]['mean_ratio'] * 100:.0f}% and "
          f"{HEUR[('medium', 'h2')]['mean_ratio'] * 100:.0f}%). h1 ignores the walls and every pellet except one. "
          "h2 still misses three things: the danger cost (it counts steps), the fact that a real route is one path "
          "(a tree may branch, a walker has to come back), and it uses only the nearest pellet for the first leg. "
          f"Preparing h2 takes {h2r['setup_ms']:.2f} ms.")
    q.ask("How do UCS, Greedy Best-First and A* differ?",
          "Only in the number f that orders the frontier: UCS uses f = g (the cost paid so far), Greedy f = h (the "
          "estimated cost still to pay), A* f = g + h (the estimated cost of the whole solution through this node). "
          "In our code they are one function, `best_first_search`, with a different `evaluate`; and A* puts a "
          "state back in the queue when a cheaper path to it is found, while Greedy does not. A* with h = 0 is UCS.")
    q.ask("Why is A* optimal, and why is Greedy not?",
          "__A*.__ Suppose it returned a goal G that costs more than C*. At that moment some node n of an optimal "
          "path was still waiting in the frontier with its cheapest path cost. Because h is admissible, f(n) = g(n) "
          "+ h(n) <= C* < g(G) = f(G). So n would have left the queue before G - a contradiction. The proof uses "
          "three things: an admissible h, the goal test at expansion time, and re-queueing a state when a cheaper "
          "path is found.",
          "__Greedy__ ignores g. It runs towards whatever looks closest and never looks back. Measured: A* returns "
          f"{opt} with both heuristics; Greedy returns {g1['path_cost']} with h1 and {g2['path_cost']} with h2 "
          f"(small layout: {S2[('small', 'Greedy (h1)')]['path_cost']} and "
          f"{S2[('small', 'Greedy (h2)')]['path_cost']} instead of {OPT['small']}; medium: "
          f"{S2[('medium', 'Greedy (h1)')]['path_cost']} and {S2[('medium', 'Greedy (h2)')]['path_cost']} instead "
          f"of {OPT['medium']}).", key="astar_optimal")
    q.ask("Admissible or consistent - which of the two does A* need?",
          "A tree-search A*, and a graph-search A* that re-queues states as ours does, need only an admissible "
          "heuristic to be optimal. A graph search that never touches an expanded state again needs a consistent "
          "one. With a consistent heuristic f never decreases along a path, the first expansion of a state already "
          "uses its cheapest path, and no state is expanded twice.",
          "We have both: h1 and h2 are consistent (a unit test checks that no state is expanded twice), and because "
          "of the re-queueing our A* stays optimal even with an inconsistent admissible heuristic (the unit test "
          "with the patchy heuristic).")
    variants = W["heuristic_variants"][L]
    q.ask(f"Is Greedy complete? Why does it need {n(g1['nodes_expanded'])} expansions with h1 and only "
          f"{g2['nodes_expanded']} with h2?",
          "In our finite state space it is complete: a state enters the queue at most once, so after at most as "
          "many expansions as there are states it has found a goal or run out of states. (As a tree search it "
          "could loop.)",
          "Greedy always expands the frontier node with the smallest h. So before it can expand any state whose "
          "h is at least h(start), it must have expanded EVERY state that can be reached through smaller values. "
          f"For h1 that region holds {n(HEUR[(L, 'h1')]['states_below_start_value'])} of the {n(reach)} states and "
          "contains no goal (`descent_region()` in `heuristics.py`): walking towards the farthest pellet lowers h1, "
          "but when that pellet is eaten another one becomes the farthest and h1 jumps up again. The region is a "
          "basin - a local minimum of the heuristic - and Greedy searches all of it before it climbs out. (h1 also "
          f"takes only {variants['h1']['distinct_values']} different values, so many states tie and are served "
          "first-in-first-out; that makes the search inside the basin blind, but the basin is the cause.) For h2 "
          "the same region does contain a goal on all three layouts: h2 "
          "falls with almost every step towards the nearest pellet, so Greedy runs straight ahead: "
          f"{g2['nodes_expanded']} expansions for a path of {g2['steps']} steps. On all three layouts Greedy with "
          "h2 returns a plan with the fewest steps, like BFS, and never the cheapest: h2 counts steps and does not "
          f"see the danger (its plan enters danger cells {paths['Greedy (h2)']['danger_entries']} times: "
          f"{g2['steps']} + {paths['Greedy (h2)']['danger_entries']} x 4 = {g2['path_cost']}).")
    for name in ("small", "medium", "large"):
        assert S2[(name, "Greedy (h2)")]["steps"] == TRADE[name]["fewest_steps"]
    bstar = {a: effective_branching_factor(S2[(L, a)]["nodes_generated"], S2[(L, a)]["steps"])
             for a in ("UCS", "A* (h1)", "A* (h2)")}
    assert [f"{bstar[a]:.2f}" for a in ("UCS", "A* (h1)", "A* (h2)")] == ["1.30", "1.25", "1.13"]
    q.ask("What is the effective branching factor b*?",
          "If a search generated N nodes and found its solution at depth d, b* is the branching factor that a "
          "uniform tree of depth d would need in order to contain N + 1 nodes: N + 1 = 1 + b* + (b*)^{2} + ... + "
          "(b*)^{d}. The closer b* is to 1, the better the heuristic focuses the search. On the large layout: "
          f"{bstar['UCS']:.2f} for UCS, {bstar['A* (h1)']:.2f} for A* with h1 and {bstar['A* (h2)']:.2f} for A* "
          "with h2 (Phase II report, Section 3.3).")

    # ------------------------------------------------------------------ 4.3
    doc.heading("4.3 Local search", 2)
    dec = W["decoding"][L]
    q.ask("What does local search give up, and what does it gain?",
          "It keeps one complete candidate solution (or a population of them) and changes it step by step; it "
          "builds no search tree. It gives up systematic coverage, optimality and every proof (it always returns a valid plan, because every order is one, but it cannot tell whether its "
          "answer is optimal - we only know because UCS and A* told us the optimum). It gains memory and scale: "
          f"simulated annealing holds {sa['orders_in_memory']} orders, hill climbing {hc['orders_in_memory']}, the "
          f"genetic algorithm {ga['orders_in_memory']}, against {n(ucs['max_nodes_in_memory'])} nodes for UCS. It "
          "always has a valid answer, and it still works when the state space is far too big for a systematic "
          "search.")
    q.ask("How did we turn the Pac-Man problem into a local-search problem?",
          "**Representation:** a priority order of the k pellets (a permutation of 0 .. k-1). **Decoding:** Pac-Man "
          "walks, along the cheapest path, to the first pellet of the order that is still uneaten; pellets on the "
          "way are eaten in passing and skipped later; the plan ends when the last pellet is eaten. **Objective "
          "(to minimise):** cost(order) = the path cost of this plan = the sum of the cheapest walking costs over "
          "the legs that are really walked; the GA uses fitness = -cost. **Neighbours:** swap two pellets of the "
          f"order, k(k-1)/2 = {dec['neighbours']} neighbours. The search space has k! = {n(dec['orders'])} orders "
          f"({W['decoding']['small']['orders']} and {W['decoding']['medium']['orders']} on the small and medium "
          "layouts).")
    q.ask("Why does the best order cost exactly the optimal path cost?",
          "No order can be cheaper than C*: every order decodes into a real plan of the search model. And some "
          "order is as cheap as C*: take an optimal path and list the pellets in the order in which it first "
          "reaches them. Between two consecutive first visits the path cannot be cheaper than the cheapest walk, "
          "and skipping a pellet that is already eaten only shortens our plan. So this order costs at most C*. A "
          "unit test confirms it: the minimum over all orders equals the UCS cost on all four layouts.")
    q.ask("How does hill climbing work, and where can it get stuck?",
          "Steepest ascent (here: steepest descent of the cost): look at ALL neighbours, move to the best one if it "
          "is strictly better, otherwise stop. It is greedy and looks one step ahead only.",
          "It can stop in three kinds of places. A **local optimum**: every neighbour is worse, but the order is "
          "not the best one. A **plateau**: neighbours with the same cost, so there is no direction to follow; a "
          "plateau from which a chain of equal-cost moves leads to something better is called a **shoulder**. A "
          "**ridge**: an improvement would need two moves at once. The standard cures are random restarts, "
          "sideways moves, and accepting a worse move now and then (simulated annealing).")
    q.ask("What did our landscape analysis find?",
          f"On the large layout {land['optimal_orders']} of the {n(land['orders'])} orders are optimal "
          f"({land['optimal_orders'] / land['orders'] * 100:.1f}%); the costs run from {land['best_cost']} (best) "
          f"over {land['median_cost']:.0f} (median) to {land['worst_cost']} (worst). The climb reaches an optimum "
          f"from {land['hc_success_probability'] * 100:.1f}% of all starting orders. From the others it stops at "
          f"one of {n(land['stop_orders_shoulder'])} non-optimal orders - and NOT ONE of them is a true local "
          "optimum. All are shoulders, on all three layouts (small: "
          f"{LAND['small']['stop_orders_shoulder']} such orders, {LAND['small']['hc_success_probability'] * 100:.1f}% "
          f"success; medium: {LAND['medium']['stop_orders_shoulder']}, "
          f"{LAND['medium']['hc_success_probability'] * 100:.1f}%). So hill climbing fails here because it refuses "
          "sideways moves, not because of local optima.",
          "Why are there so many plateaus? Many orders decode into the same plan - the "
          f"{n(dec['orders'])} orders give only {n(dec['distinct_plans'])} different plans - because pellets that "
          "are eaten in passing make part of the order irrelevant, and swapping two such pellets changes nothing. "
          f"The measured runs agree with the {land['hc_success_probability'] * 100:.1f}%: "
          f"{hc['optimal_runs']} of {N_SEEDS} on the seeds 0-{N_SEEDS - 1} and "
          f"{ONE[('HC', 'restarts', 0)]['hits']} of {TUNE_RUNS} on the tuning seeds.")
    py = W["python"]
    up = round(land["mean_uphill_swap"], 1)
    q.ask("Explain the acceptance rule and the cooling schedule of simulated annealing with our numbers.",
          "A random swap that is not worse is always accepted. A swap that is worse by delta is accepted with "
          "probability exp(-delta / T). The temperature T starts at T0 = "
          f"{SA['start_temperature']:g} and is multiplied by {SA['cooling_rate']} after every iteration: T(n) = "
          f"{SA['start_temperature']:g} x {SA['cooling_rate']}^{{n}} (geometric cooling). It halves about every "
          f"{py['sa_halving_iterations']:.0f} iterations, reaches 1 after {py['sa_iterations_until_T1']} iterations "
          f"and the end temperature {SA['end_temperature']} after {py['sa_iterations_formula']}.",
          f"An uphill swap raises the cost by {up:.1f} on average. At T = 10 it is accepted with probability "
          f"e^{{-{up / 10:.2f}}} = {math.exp(-up / 10):.2f}; at T = 1 with {math.exp(-up):.5f}; at T = 0.1 even "
          f"delta = 1 passes only with e^{{-10}}, about {math.exp(-10):.5f} - the search is frozen and behaves "
          "like hill climbing. High temperature means exploration, low temperature exploitation. The best order "
          "ever seen is returned, not the last one.")
    frozen = local["SA frozen"]["tuning"]
    q.ask("Does theory guarantee that simulated annealing finds the optimum? Why does it work so well here?",
          "Theory: only if the temperature falls slowly enough does the probability of ending in a global optimum "
          "approach 1 - far more slowly than any practical schedule. With geometric cooling there is no guarantee, "
          f"only measurements: {sa['optimal_runs']} of {N_SEEDS} runs on the seeds 0-{N_SEEDS - 1}, "
          f"{local['SA final']['tuning']['hits']} of {TUNE_RUNS} on the tuning seeds.",
          "It works here because plateaus are the difficulty, and annealing walks across them: an equal-cost swap "
          "is always accepted. Our extra experiment (Section 5): with a temperature of practically zero, so that no "
          f"uphill move is ever accepted, and the same {py['sa_iterations_formula']} iterations, it still reaches "
          f"the optimum in {frozen['hits']} of {frozen['runs']} runs. The real uphill moves add the last few "
          "points.")
    budget = GA["population_size"] * (GA["generations"] + 1)
    q.ask("Explain the parts of our genetic algorithm.",
          "**Chromosome:** an order of the pellets, one gene per pellet. **Fitness:** -cost. **Population:** "
          f"{GA['population_size']} random orders, {GA['generations']} generations. **Selection:** tournament of "
          f"size {GA['tournament_size']} - draw {GA['tournament_size']} individuals at random, the cheaper one "
          f"becomes a parent. **Crossover** (probability {GA['crossover_rate']}): order crossover. **Mutation** "
          f"(probability {GA['mutation_rate']}): swap two genes. **Replacement:** the children replace the whole "
          f"population; elite count {GA['elite_count']}, i.e. no elitism, but the best order ever seen is stored "
          f"separately. One run evaluates {GA['population_size']} x {GA['generations'] + 1} = {budget} orders, "
          f"the same budget as simulated annealing ({n(sa['mean_evaluations'])}).")
    q.ask("Why can we not use ordinary one-point crossover? Show order crossover on an example.",
          "A chromosome must contain every pellet exactly once. Cutting two permutations and gluing the halves "
          "together usually breaks that: A = 0 1 2 3 | 4 5 6 7 and B = 7 6 5 4 | 3 2 1 0 give 0 1 2 3 3 2 1 0 - the "
          "pellets 0 to 3 twice, 4 to 7 never.",
          "Order crossover keeps a slice of A where it is and fills the other positions, from left to right, with "
          "the missing pellets in the order in which B has them. Example from the unit test: A = (0,1,2,3,4,5), B = "
          "(5,4,3,2,1,0), slice = positions 2 to 4. The child keeps 2,3,4 in place and gets 5, 1, 0 in B's order: "
          "(5,1,2,3,4,0). The result is always a valid permutation.", key="crossover")
    q.ask("Why do the random algorithms need seeds, and why two different sets of seeds?",
          "A random algorithm gives a different result on every run. With a fixed seed a run can be repeated "
          "exactly (the project description demands it; every run uses its own `random.Random(seed)`). One run "
          f"proves nothing, so we report best, mean and worst over {N_SEEDS} seeds (0 to {N_SEEDS - 1}; the "
          "description asks for at least 10).",
          f"The parameters were chosen on {TUNE_RUNS} OTHER seeds ({P2['tuning_seeds'][0]} to "
          f"{P2['tuning_seeds'][1]}), so the reported runs are a fair "
          "test and not the runs the parameters were fitted to. Why this matters: simulated annealing and the "
          f"genetic algorithm reached the optimum in {sa['optimal_runs']} of {N_SEEDS} reported runs, but in "
          f"{local['SA final']['tuning']['hits']} of {TUNE_RUNS} tuning runs - \"{N_SEEDS} of {N_SEEDS}\" is not "
          "a guarantee.")

    def share(row):
        """Share of the tuning runs that reached the optimum, in whole percent."""
        return round(100 * row["hits"] / row["runs"])

    def sa_hits(start, rate):
        return share(TSA[(start, rate)])

    def ga_hits(size, rate):
        return share(TGA[(size, rate)])

    q.ask("How were the parameter values chosen?",
          f"With the sensitivity study (`tuning_study`): {TUNE_RUNS} runs per setting on the large layout, recording "
          "the share of optimal runs and the evaluations per run.",
          "__Simulated annealing.__ The cooling rate matters most, because it fixes the number of iterations: "
          f"{sa_hits(10.0, 0.9)}% (0.9), {sa_hits(10.0, 0.95)}% (0.95), {sa_hits(10.0, 0.99)}% (0.99), "
          f"{sa_hits(10.0, 0.995)}% (0.995), {sa_hits(10.0, 0.999)}% (0.999, five times the work). A start "
          f"temperature of 1 freezes too early ({sa_hits(1.0, 0.995)}%); 5, 10 and 20 are within the noise "
          f"({sa_hits(5.0, 0.995)}%, {sa_hits(10.0, 0.995)}%, {sa_hits(20.0, 0.995)}%).",
          "__Genetic algorithm.__ Mutation matters "
          f"({ga_hits(30, 0.05)}% at rate 0.05, {ga_hits(30, 0.8)}% at 0.8); crossover does not "
          f"({share(ONE[('GA', 'crossover_rate', 0.0)])}% without it); stronger selection and elitism hurt "
          f"(tournament size 5: {share(ONE[('GA', 'tournament_size', 5)])}%; 5 elites: "
          f"{share(ONE[('GA', 'elite_count', 5)])}%).",
          "For all three methods more evaluations mean more reliability, so we gave simulated annealing and the "
          f"genetic algorithm about the same budget ({n(sa['mean_evaluations'])} and {budget} evaluations).")
    assert TUNE_RUNS == 300
    base = LOC[(L, P2["baseline_label"])]
    base_n = P2["baseline_evaluations"]
    one_in = land["orders"] / land["optimal_orders"]
    chance = 100 * (1 - (1 - 1 / one_in) ** base_n)
    sa_tuned = share(TSA[(SA["start_temperature"], SA["cooling_rate"])])
    ga_tuned = share(TGA[(GA["population_size"], GA["mutation_rate"])])
    climb_n = ONE[("HC", "restarts", 0)]["evaluations"]
    chance_climb = 100 * (1 - (1 - 1 / one_in) ** climb_n)
    assert base["optimal_runs"] == N_SEEDS and sa_tuned < chance and ga_tuned < chance
    assert 100 * land["hc_success_probability"] > chance_climb + 5
    q.ask("Are simulated annealing and the genetic algorithm better than guessing on our layouts?",
          f"No - and we say so in the report (Section 4.4). {land['optimal_orders']} of the {n(land['orders'])} "
          f"orders are optimal, one in {one_in:.0f}. If you simply draw {n(base_n)} random orders, at least one is "
          f"optimal with probability 1 - (1 - 1/{one_in:.0f})^{{{base_n}}} = {chance:.1f}%. Our baseline "
          f"`random_sampling()` does exactly that and is optimal in {base['optimal_runs']} of {N_SEEDS} runs. "
          f"Simulated annealing and the genetic algorithm reach {sa_tuned}% and {ga_tuned}% on the tuning seeds "
          "with the same budget: not better, even slightly worse, because they spend part of the budget near "
          "orders they have already seen. On the small and medium layouts the budget is even larger than the "
          f"number of orders that exist ({LAND['small']['orders']} and {LAND['medium']['orders']}).",
          f"Hill climbing is the exception: one climb costs about {n(climb_n)} evaluations and succeeds from "
          f"{land['hc_success_probability'] * 100:.1f}% of the starts; {n(climb_n)} random orders succeed with "
          f"{chance_climb:.0f}%. So the climb really uses the structure of the landscape.",
          "What to say if asked: the official layouts must stay below 10,000 states, and at that size a budget of "
          "about 900 evaluations is enough for blind sampling. The brief asks for the algorithms and their "
          "comparison, which we give; the baseline shows honestly what the comparison can and cannot prove.",
          key="baseline")
    scale = {(r["pellets"], r["method"]): r for r in P2["scaling_methods"]}
    inst = {r["pellets"]: r for r in P2["scaling_instances"]}
    ks = sorted(inst)
    kmax = ks[-1]

    def above(k, method):
        return scale[(k, method)]["mean_percent_above_optimum"]

    assert above(kmax, "Simulated Annealing") < above(kmax, "Hill Climbing (restarts)") \
        < above(kmax, "Genetic Algorithm") < above(kmax, "Random sampling")
    q.ask("So does local search ever beat random sampling? What did the experiment on larger mazes show?",
          f"Yes. `scaling.py` builds a 13x19 maze with {inst[kmax]['free_cells']} free cells and scatters "
          f"{', '.join(str(k) for k in ks)} pellets on it (not official instances). Every method gets "
          f"{n(P2['scaling_budget'])} evaluations per run and {P2['scaling_seeds']} seeded runs; A* with h2 gives "
          "the optimal cost. Mean cost above the optimum, random sampling / hill climbing with restarts / "
          "simulated annealing / genetic algorithm: "
          + "; ".join(f"{k} pellets: " + " / ".join(
              f"{above(k, m):.1f}%" for m in ("Random sampling", "Hill Climbing (restarts)", "Simulated Annealing",
                                              "Genetic Algorithm")) for k in ks) + ".",
          f"With {ks[0]} pellets everything is easy. From {ks[1]} pellets on random sampling never finds the "
          "optimum again, while hill climbing with restarts and simulated annealing stay much closer; simulated "
          f"annealing is the best method with {kmax} pellets. The genetic algorithm is the weakest of the three. "
          "Know what was changed for it: only the population (100 instead of 30) and the number of generations "
          "(99) were scaled to the budget, in `budget_methods()`; mutation, crossover and selection are the "
          "settings chosen on a layout where randomness was all that mattered, and we did not retune them.",
          f"The second result: A* with h2 still solves the {kmax}-pellet maze exactly - "
          f"{n(inst[kmax]['astar_h2_nodes_expanded'])} expansions, {ms(inst[kmax]['astar_h2_time_ms'])} ms, for a "
          f"state space of up to {n(inst[kmax]['state_space_upper_bound'])} states. So \"local search wins on big "
          "instances\" is an expectation for much bigger problems, not something we measured.", key="scaling")
    q.ask("Which of the nine algorithms suits this problem best? When would that change?",
          "A* with h2. It is complete and guaranteed optimal like UCS, with "
          f"{n(a2['nodes_expanded'])} expansions instead of {n(ucs['nodes_expanded'])}, "
          f"{n(a2['max_nodes_in_memory'])} nodes in memory instead of {n(S2[(L, 'UCS')]['max_nodes_in_memory'])}, "
          f"and {ms(a2['time_ms'])} ms instead of {ms(S2[(L, 'UCS')]['time_ms'])} ms. The methods that are faster "
          "(DFS, Greedy with h2, one hill climb) give no guarantee and miss the optimum.",
          "When would it change? The state space doubles with every pellet. The uninformed searches die first "
          "(IDS runs out of time, BFS and UCS out of memory). In theory A* is exponential too and keeps its "
          f"frontier in memory, but in our scaling experiment it was still the best method with {kmax} pellets "
          f"({n(inst[kmax]['astar_h2_nodes_expanded'])} expansions, while the local-search methods ended "
          f"{above(kmax, 'Simulated Annealing'):.0f}% to {above(kmax, 'Genetic Algorithm'):.0f}% above the "
          "optimum). Its work grew by a factor of "
          f"{inst[kmax]['astar_h2_nodes_expanded'] / inst[ks[0]]['astar_h2_nodes_expanded']:.0f} from {ks[0]} to "
          f"{kmax} pellets, so for much larger instances we EXPECT local search on the pellet order to become the "
          "practical choice - without a guarantee. We did not test that.", key="best")
    doc.para("**Q" + str(q.count + 1) + ". Summarise the guarantees of the informed and the local-search "
             "algorithms.**", space_before=5, space_after=3, keep_with_next=True)
    q.count += 1
    keep_header_with_first_row(doc.table(
        ["", "Complete?", "Optimal (guaranteed)?", "Cost in theory", "Where it struggles here"],
        [["Greedy Best-First", "yes in a finite space (graph search)", "no",
          "worst case like DFS: O(b^{m}) time and space",
          f"depends entirely on h: {g2['nodes_expanded']} expansions with h2, {n(g1['nodes_expanded'])} with h1 "
          "(a basin of h1)"],
         ["A*", "yes", "yes, if h is admissible", "exponential in the worst case; keeps every generated node in "
                                                  "memory", "nothing with h2 on these layouts; memory on much "
                                                            "larger instances"],
         ["Hill Climbing", "always returns a valid plan (every order is one) - in that sense complete",
          "no", "a handful of orders in memory",
          f"stops on plateaus: {hc['optimal_runs']} of {N_SEEDS} runs optimal"],
         ["Simulated Annealing", "as hill climbing", "no (only with impractically slow cooling)",
          "3 orders in memory", "needs enough iterations; three parameters; no better than random sampling on the "
                                "official layouts"],
         ["Genetic Algorithm", "as hill climbing", "no", "two populations in memory",
          f"slowest of the three ({ms(ga['time_ms'])} ms per run); most parameters; weakest on the larger mazes"]],
        widths_cm=[2.8, 3.4, 3.1, 4.0, 4.1], size=9, bold_first_col=True, stripe=False, keep_together=False))

    # ------------------------------------------------------------------ 4.4
    doc.heading("4.4 How to read the tables and figures of the two reports", 2)
    doc.para("An examiner may open a report and point at any table or figure. For each one: what it shows, and "
             "the one thing to say about it.", space_after=3, keep_with_next=True)
    growth = IDS_ITER[L][-2]["expanded"]
    keep_header_with_first_row(doc.table(
        ["Phase I report", "What it shows - and what to say"],
        [["Tables 1 and 2", "The search problem (state, initial state, goal test, actions, transition, costs) and "
                            "the size of the three layouts: N, k, N x 2^{k}, valid, reachable. All three counts lie "
                            "between 1,000 and 10,000."],
         ["Table 3", "How each of the four algorithms is implemented: frontier, repeated states, goal test."],
         ["Tables 4 and 5", "Table 4: the measurements on all three layouts. Read a row from left to right: "
                            "path cost, steps, nodes generated, nodes expanded, maximum frontier, maximum nodes in "
                            "memory, time, peak memory. Only UCS has \"yes\" under \"lowest cost\"; BFS and IDS "
                            "have \"yes\" under \"fewest steps\". Table 5: the four solution paths on the large "
                            "layout as strings of U, R, D, L (Table 9 in the appendix: the other two layouts)."],
         ["Table 6", "Fewest steps against lowest cost, computed exactly (`step_cost_tradeoff`). Even the "
                     "cheapest fewest-step plan costs more than the optimum on every layout."],
         ["Table 7", "The two versions of IDS: the memo table buys speed with memory."],
         ["Table 8", "Complete / optimal / time / space in theory next to what we measured."],
         ["Figure 1", "The four layouts with pellet numbers and danger cells."],
         ["Figure 2", "Nodes expanded by IDS at every depth limit. Every limit costs more than the one before; "
                      f"the last complete one needs {n(growth)} expansions. The final bar is short because the "
                      "search stops at the first goal."],
         ["Figure 3", "Nodes expanded against the size of the state space (both axes logarithmic). BFS grows "
                      "with the number of states (it expands about half of them); IDS follows the depth of the "
                      "solution, not the number of states (it is largest on the medium layout); DFS hardly grows."],
         ["Figure 4", "Explored states and returned path, one panel per algorithm. The darker a cell, the more of "
                      "its 256 food combinations were expanded with Pac-Man standing there. The orange line is "
                      "the returned plan; the circled numbers give the order in which the pellets are eaten."],
         ["Figures 5 and 7", "Search trees on the tiny layout. A node shows (row, col), the small number next to "
                             "it the order of expansion, its colour the number of pellets left; the orange branch "
                             "is the solution. Figure 7: IDS builds the tree again from the root for every limit."],
         ["Figure 6", "Frontier size while the search runs (x = progress in percent, y logarithmic). The two "
                      "stacks stay below 30 nodes; the queues of BFS and UCS grow to several hundred."]],
        widths_cm=[2.6, 14.8], size=9, bold_first_col=True, stripe=False, keep_together=False))
    keep_header_with_first_row(doc.table(
        ["Phase II report", "What it shows - and what to say"],
        [["Tables 1 and 2", "The changes since Phase I (none in the model) and the two heuristics: definition, "
                            "idea, relaxed problem, cost of computing, value at the start."],
         ["Table 3", "The exhaustive check: states and transitions checked, admissible, consistent, mean h / h*, "
                     "h(start) against h*(start), preparation time."],
         ["Tables 4 and 5", "Greedy and A* with both heuristics, UCS as the baseline. A* always has the optimal "
                            "cost; compare the \"nodes expanded\" column."],
         ["Table 6", "The local-search formulation: representation, decoding, objective, neighbours."],
         ["Table 7", "The landscape: number of orders, optimal orders, best / median / worst cost, the orders "
                     "where the climb stops (optimal / shoulder / local optimum), the share of starts that reach "
                     "an optimum, the mean size of an uphill swap."],
         ["Table 8", "Every parameter with its value and the measurements behind it. A percentage is the share "
                     f"of {TUNE_RUNS} tuning runs that reached the optimum; the tested value is in brackets."],
         ["Table 9", "Local search on the 30 seeds: best, mean, worst, standard deviation, optimal runs, "
                     "evaluations, time. The last row of each layout is the random-sampling baseline."],
         ["Tables 10 and 11", "The larger mazes (Section 4.6): what A* with h2 needs to solve them exactly, and "
                              "how far above the optimum the four budget-matched methods end."],
         ["Table 15", "Appendix C: the solution paths of the eight search runs on the large layout as strings "
                      "of U, R, D, L. BFS and IDS return the same string, and so do UCS and both A* runs."],
         ["Tables 12 to 14", "All algorithms in one table (Table 12 = large layout, the one the brief asks for). For local search the cost is the mean (best-worst). "
                             "\"Items in memory\" are search nodes or pellet orders; \"effort\" is expansions or "
                             "evaluations - two different units, to be compared within a family only."],
         ["Figure 1", "Nodes expanded (top) and path cost (bottom) for UCS, Greedy and A* on the three layouts; "
                      "the black line is the optimal cost."],
         ["Figure 2", "Explored states of Greedy and A* with both heuristics, one colour scale. The two h2 "
                      f"panels stay pale ({g2['nodes_expanded']} and {a2['nodes_expanded']} expansions); Greedy "
                      f"with h1 is the darkest ({n(g1['nodes_expanded'])})."],
         ["Figure 3", "Nodes expanded against the size of the state space. A* with h2 needs about a hundred "
                      f"expansions on every layout ({S2[('small', 'A* (h2)')]['nodes_expanded']}, "
                      f"{S2[('medium', 'A* (h2)')]['nodes_expanded']}, {a2['nodes_expanded']})."],
         ["Figure 4", "An optimal plan next to the plan where one hill-climbing run stopped (cost "
                      f"{W['decoding']['large_example']['cost']}). Small numbers = pellet indices, circled numbers = "
                      "eating order."],
         ["Figures 5 and 6", "The parameter study as heat maps. Every cell: share of optimal runs and evaluations "
                             "per run. The orange frame is the setting we use."],
         ["Figure 7", "Share of optimal runs against the evaluations spent. Hill climbing with restarts, "
                      "simulated annealing and the genetic algorithm lie on similar curves; sideways moves use "
                      "their budget badly. The grey curve is random sampling: on this layout SA and the GA do not "
                      "beat it."],
         ["Figures 8 and 9", "Convergence: the best cost found so far in each run (grey) and the average (blue) - "
                             "the lines can never go up. Then the number of runs that ended with each cost."],
         ["Figure 10", "One annealing run: the cost of the current order (grey) goes up and down while it is hot; "
                       "the best so far (blue) only falls; below, the temperature on a logarithmic axis."],
         ["Figures 11 and 12", "The mazes of the scaling experiment, and the mean cost above the optimum of "
                               "the four methods as the number of pellets grows: random sampling falls behind."],
         ["Figure 13", "The summary chart: cost, time, memory and effort of all algorithms (time, memory and "
                       "effort on logarithmic axes). Colours are the three families, the baseline is grey; for "
                       "local search the bar is the mean and the black line runs from best to worst."]],
        widths_cm=[2.6, 14.8], size=9, bold_first_col=True, stripe=False, keep_together=False))
    assert q.count >= 30, q.count
    assert set(q.refs) == {"h1_proof", "dominance", "astar_optimal", "crossover", "best", "baseline", "scaling"}
    return q.count, q.refs
