"""
Unit tests for Phase I: the problem model, the four uninformed search algorithms and the
measurement helpers.

Run from the code folder:

    python -m unittest discover -s tests -v

The search results are checked against INDEPENDENT reference solvers written inside this
file (a brute force over pellet orders for the optimal cost, a plain breadth-first sweep
for the fewest steps), not against each other.
"""

import heapq
import itertools
import os
import sys
import unittest
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pacman_search.experiments import (  # noqa: E402
    actions_to_string, measure_peak_memory, measure_time, state_graph_profile, step_cost_tradeoff)
from pacman_search.layouts import LAYOUTS, OFFICIAL_LAYOUTS, load_problem  # noqa: E402
from pacman_search.problem import PacmanProblem, State  # noqa: E402
from pacman_search.uninformed import (  # noqa: E402
    UNINFORMED_ALGORITHMS, breadth_first_search, depth_first_search,
    iterative_deepening_search, uniform_cost_search)


# --------------------------------------------------------------------------------------
# Independent reference solvers (they do not use the project's search code)
# --------------------------------------------------------------------------------------
def brute_force_optimum(problem):
    """Optimal path cost: try EVERY order of eating the pellets.

    Any solution eats the pellets in some order, and between two consecutive pellets it
    cannot do better than the cheapest walk. So the optimum is the minimum, over all
    orders, of the sum of cheapest walking costs (computed here with a small Dijkstra).
    """
    def cheapest_from(source):
        cost = {source: 0}
        heap = [(0, source)]
        while heap:
            current, cell = heapq.heappop(heap)
            if current > cost[cell]:
                continue
            for _, nxt, step in problem.neighbors[cell]:
                if nxt not in cost or current + step < cost[nxt]:
                    cost[nxt] = current + step
                    heapq.heappush(heap, (current + step, nxt))
        return cost

    table = {point: cheapest_from(point) for point in [problem.start, *problem.food_cells]}
    best = None
    for order in itertools.permutations(problem.food_cells):
        total, position = 0, problem.start
        for pellet in order:
            total += table[position][pellet]
            position = pellet
        best = total if best is None else min(best, total)
    return best


def fewest_steps_by_sweep(problem):
    """Smallest number of moves that eats everything: breadth-first sweep written with the
    formal model only (actions() and result())."""
    start = problem.initial_state
    depth = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        if problem.is_goal(state):
            return depth[state]
        for action in problem.actions(state):
            nxt = problem.result(state, action)
            if nxt not in depth:
                depth[nxt] = depth[state] + 1
                queue.append(nxt)
    return None


class TestProblemModel(unittest.TestCase):

    def setUp(self):
        self.tiny = load_problem("tiny")

    def test_layout_is_parsed_correctly(self):
        self.assertEqual(self.tiny.start, (1, 1))
        self.assertEqual(self.tiny.food_cells, ((1, 5), (3, 1)))
        self.assertEqual(self.tiny.ghosts, [(2, 3)])
        self.assertEqual(self.tiny.danger_cells, {(1, 3)})
        self.assertEqual(len(self.tiny.free_cells), 14)

    def test_initial_state_and_goal_test(self):
        start = self.tiny.initial_state
        self.assertEqual(start, State((1, 1), 0b11))
        self.assertFalse(self.tiny.is_goal(start))
        self.assertTrue(self.tiny.is_goal(State((3, 1), 0)))

    def test_actions_respect_walls(self):
        self.assertEqual(self.tiny.actions(self.tiny.initial_state), ["RIGHT", "DOWN"])

    def test_result_moves_pacman_and_eats_food(self):
        before = State((1, 4), 0b11)
        after = self.tiny.result(before, "RIGHT")
        self.assertEqual(after, State((1, 5), 0b10))          # pellet 0 (bit 0) was eaten
        self.assertEqual(self.tiny.result(after, "LEFT"), State((1, 4), 0b10))   # it stays eaten

    def test_step_cost_is_5_next_to_a_ghost(self):
        state = State((1, 2), 0b11)
        self.assertEqual(self.tiny.step_cost(state, "RIGHT", self.tiny.result(state, "RIGHT")), 5)
        self.assertEqual(self.tiny.step_cost(state, "LEFT", self.tiny.result(state, "LEFT")), 1)

    def test_illegal_and_unknown_actions_are_rejected(self):
        with self.assertRaises(ValueError):
            self.tiny.result(self.tiny.initial_state, "UP")     # wall above the start cell
        with self.assertRaises(ValueError):
            self.tiny.result(self.tiny.initial_state, "JUMP")   # not an action at all
        self.assertFalse(self.tiny.is_solution(["JUMP"]))

    def test_ghost_cell_cannot_be_entered(self):
        self.assertNotIn("DOWN", self.tiny.actions(State((1, 3), 0b11)))   # the ghost is below (1, 3)

    def test_successors_agree_with_the_formal_model(self):
        for name in LAYOUTS:
            problem = load_problem(name)
            for state in problem.reachable_states():            # every reachable state
                expected = []
                for action in problem.actions(state):
                    nxt = problem.result(state, action)
                    expected.append((action, nxt, problem.step_cost(state, action, nxt)))
                self.assertEqual(problem.successors(state), expected)

    def test_state_space_size_of_tiny(self):
        report = self.tiny.state_space_report()
        self.assertEqual(report["upper_bound"], 14 * 2 ** 2)
        self.assertEqual(report["valid"], 14 * 4 - 2 * 2)
        self.assertEqual(report["reachable"], 45)

    def test_valid_state_formula_matches_enumeration(self):
        for name in LAYOUTS:
            problem = load_problem(name)
            valid = sum(1 for cell in problem.free_cells for mask in range(2 ** problem.num_food)
                        if not mask & problem.food_bit.get(cell, 0))
            self.assertEqual(problem.state_space_report()["valid"], valid)

    def test_official_layouts_are_in_the_required_size_range(self):
        for name in OFFICIAL_LAYOUTS:
            report = load_problem(name).state_space_report()
            self.assertLessEqual(report["reachable"], report["valid"])
            self.assertLessEqual(report["valid"], report["upper_bound"])
            for key in ("reachable", "valid", "upper_bound"):
                self.assertTrue(1000 <= report[key] <= 10000, f"{name}: {key} = {report[key]}")

    def test_execute_replays_a_plan(self):
        states, cost = self.tiny.execute(["RIGHT", "RIGHT", "RIGHT", "RIGHT"])
        self.assertEqual(states[-1], State((1, 5), 0b10))
        self.assertEqual(cost, 1 + 5 + 1 + 1)
        self.assertFalse(self.tiny.is_solution(["RIGHT"]))
        self.assertFalse(self.tiny.is_solution(["UP"]))          # illegal plan

    def test_bad_layouts_are_rejected(self):
        with self.assertRaises(ValueError):
            PacmanProblem("####\n#..#\n####")                    # no start cell
        with self.assertRaises(ValueError):
            PacmanProblem("#####\n#P#.#\n#####")                 # pellet walled off
        with self.assertRaises(ValueError):
            PacmanProblem("#####\n#P.#\n#####")                  # rows of different length
        with self.assertRaises(ValueError):
            PacmanProblem("####\n#P #\n####")                    # no pellet
        with self.assertRaises(ValueError):
            PacmanProblem("####\n#P.#\n####", step_cost=0)       # costs must be positive


class TestUninformedSearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.problems = {name: load_problem(name) for name in LAYOUTS}
        cls.results = {name: {key: search(problem, trace=True) for key, search in UNINFORMED_ALGORITHMS.items()}
                       for name, problem in cls.problems.items()}

    def test_every_algorithm_returns_a_valid_solution(self):
        for name, problem in self.problems.items():
            for key, result in self.results[name].items():
                with self.subTest(layout=name, algorithm=key):
                    self.assertTrue(result.found)
                    states, cost = problem.execute(result.actions)
                    self.assertTrue(problem.is_goal(states[-1]))
                    self.assertFalse(any(problem.is_goal(state) for state in states[:-1]))
                    self.assertEqual(cost, result.path_cost)
                    self.assertEqual(len(result.actions), result.depth)
                    self.assertEqual(states, result.states)

    def test_ucs_is_cost_optimal(self):
        for name, problem in self.problems.items():
            with self.subTest(layout=name):
                optimum = brute_force_optimum(problem)
                self.assertEqual(self.results[name]["ucs"].path_cost, optimum)
                for result in self.results[name].values():
                    self.assertGreaterEqual(result.path_cost, optimum)

    def test_bfs_and_ids_find_the_fewest_steps(self):
        for name, problem in self.problems.items():
            with self.subTest(layout=name):
                fewest = fewest_steps_by_sweep(problem)
                self.assertEqual(self.results[name]["bfs"].depth, fewest)
                self.assertEqual(self.results[name]["ids"].depth, fewest)
                for result in self.results[name].values():
                    self.assertGreaterEqual(result.depth, fewest)

    def test_known_results_on_the_tiny_layout(self):
        results = self.results["tiny"]
        self.assertEqual((results["bfs"].path_cost, results["bfs"].depth), (12, 8))
        self.assertEqual((results["ucs"].path_cost, results["ucs"].depth), (10, 10))
        self.assertEqual((results["dfs"].path_cost, results["dfs"].depth), (16, 12))
        self.assertEqual((results["ids"].path_cost, results["ids"].depth), (12, 8))

    def test_fewest_steps_plans_are_never_the_cheapest(self):
        # On every layout even the CHEAPEST plan with the fewest steps costs more than the
        # optimum: the steps-versus-cost trade-off is real, not a matter of tie-breaking.
        for name, problem in self.problems.items():
            with self.subTest(layout=name):
                trade = step_cost_tradeoff(problem)
                self.assertTrue(trade["genuine_tradeoff"])
                self.assertEqual(trade["fewest_steps"], fewest_steps_by_sweep(problem))
                self.assertEqual(trade["optimal_cost"], self.results[name]["ucs"].path_cost)
                self.assertGreater(trade["cheapest_cost_with_fewest_steps"], trade["optimal_cost"])
                self.assertGreater(trade["fewest_steps_at_optimal_cost"], trade["fewest_steps"])
                self.assertGreater(self.results[name]["bfs"].path_cost, self.results[name]["ucs"].path_cost)

    def test_generated_counter_matches_its_definition(self):
        # nodes generated = one root per (re)start + every successor of every expanded node
        for name, problem in self.problems.items():
            for key, result in self.results[name].items():
                with self.subTest(layout=name, algorithm=key):
                    roots = len(result.extra["iterations"]) if key == "ids" else 1
                    successors = sum(len(problem.successors(node.state)) for node in result.expanded_nodes)
                    self.assertEqual(result.nodes_generated, roots + successors)
                    self.assertEqual(result.nodes_expanded, len(result.expanded_nodes))

    def test_memory_counters(self):
        for name, problem in self.problems.items():
            reachable = problem.count_reachable_states()
            for key, result in self.results[name].items():
                with self.subTest(layout=name, algorithm=key):
                    self.assertEqual(result.max_frontier_size, max(result.frontier_history))
                    self.assertGreater(result.max_nodes_in_memory, result.max_frontier_size)
                    self.assertLessEqual(result.max_nodes_in_memory, result.max_frontier_size + reachable)
                    if key != "ids":                            # graph searches expand a state at most once
                        states = [node.state for node in result.expanded_nodes]
                        self.assertEqual(len(states), len(set(states)))
            # the textbook IDS keeps only the current path besides its stack
            ids = self.results[name]["ids"]
            self.assertLessEqual(ids.max_nodes_in_memory, ids.max_frontier_size + ids.depth + 1)

    def test_exact_counters_on_the_tiny_layout(self):
        # (generated, expanded, max frontier, max nodes in memory) - regression values.
        # Every cell of the tiny maze has exactly two neighbours, so generated = 1 + 2 * expanded
        # (IDS counts one root per iteration: 9 iterations, 9 + 2 * 80 = 169).
        expected = {"bfs": (45, 22, 4, 25), "dfs": (25, 12, 3, 15), "ucs": (43, 21, 4, 25),
                    "ids": (169, 80, 7, 15)}
        for key, numbers in expected.items():
            result = self.results["tiny"][key]
            self.assertEqual((result.nodes_generated, result.nodes_expanded, result.max_frontier_size,
                              result.max_nodes_in_memory), numbers, key)

    def test_trace_does_not_change_the_search(self):
        problem = self.problems["small"]
        for key, search in UNINFORMED_ALGORITHMS.items():
            with self.subTest(algorithm=key):
                traced, plain = self.results["small"][key], search(problem)
                self.assertEqual(plain.actions, traced.actions)
                self.assertEqual(plain.nodes_expanded, traced.nodes_expanded)
                self.assertEqual(plain.nodes_generated, traced.nodes_generated)
                self.assertEqual(plain.max_nodes_in_memory, traced.max_nodes_in_memory)
                self.assertEqual(plain.expanded_nodes, [])

    def test_both_ids_versions_return_the_same_solution(self):
        for name, problem in self.problems.items():
            with self.subTest(layout=name):
                textbook = self.results[name]["ids"]
                memo = iterative_deepening_search(problem, use_memo=True)
                self.assertEqual(memo.actions, textbook.actions)
                # the memo table saves work but costs memory
                self.assertLessEqual(memo.nodes_expanded, textbook.nodes_expanded)
                if name != "tiny":
                    self.assertGreater(memo.max_nodes_in_memory, textbook.max_nodes_in_memory)

    def test_ids_iterations_are_recorded(self):
        result = self.results["small"]["ids"]
        iterations = result.extra["iterations"]
        self.assertEqual([it["limit"] for it in iterations], list(range(result.depth + 1)))
        self.assertEqual(sum(it["expanded"] for it in iterations), result.nodes_expanded)
        self.assertEqual(sum(it["generated"] for it in iterations), result.nodes_generated)

    def test_ids_safety_limits(self):
        problem = self.problems["large"]
        stopped = iterative_deepening_search(problem, expansion_limit=500)
        self.assertFalse(stopped.found)
        self.assertTrue(stopped.extra["aborted"])
        shallow = iterative_deepening_search(problem, max_depth=5)
        self.assertFalse(shallow.found)
        self.assertTrue(shallow.extra["depth_limit_reached"])

    def test_algorithms_only_need_the_problem_interface(self):
        class LineProblem:                                       # 0 - 1 - 2 - 3, goal at 3
            initial_state = 0

            def is_goal(self, state):
                return state == 3

            def successors(self, state):
                return [("step", nxt, 1) for nxt in (state - 1, state + 1) if 0 <= nxt <= 3]

        for key, search in UNINFORMED_ALGORITHMS.items():
            result = search(LineProblem())
            self.assertTrue(result.found, key)
            self.assertEqual(result.path_cost, 3, key)


class TestMeasurementHelpers(unittest.TestCase):

    class FakeRun:
        def __init__(self, seconds):
            self.runtime_sec = seconds

    def test_measure_time_reports_milliseconds(self):
        values = iter([0.001, 0.002, 0.003, 0.004])
        timing = measure_time(lambda: self.FakeRun(next(values)), repeats=4)
        self.assertAlmostEqual(timing.best, 1.0)                 # the reported running time
        self.assertAlmostEqual(timing.median, 2.5)
        self.assertAlmostEqual(timing.mean, 2.5)
        self.assertAlmostEqual(timing.std, 1.2909944, places=5)  # sample standard deviation
        self.assertEqual(timing.runs, 4)

    def test_disturbed_runs_do_not_change_the_reported_time(self):
        values = iter([0.012, 0.011, 0.005, 0.013, 0.005])       # three of five runs were slowed down
        timing = measure_time(lambda: self.FakeRun(next(values)), repeats=5)
        self.assertAlmostEqual(timing.best, 5.0)                 # the fastest run is reported
        self.assertAlmostEqual(timing.median, 11.0)              # median and mean are pulled up
        self.assertAlmostEqual(timing.mean, 9.2)

    def test_measure_time_stops_slow_algorithms_early(self):
        calls = []

        def slow_run():
            calls.append(1)
            return self.FakeRun(1.5)                             # pretends to take 1.5 s

        timing = measure_time(slow_run, repeats=20, max_seconds=2.0)
        self.assertEqual(timing.runs, 3)                         # the minimum of three runs
        self.assertEqual(len(calls), 3)

    def test_measure_peak_memory_sees_allocations(self):
        small = measure_peak_memory(lambda: [0] * 10)
        large = measure_peak_memory(lambda: [0] * 200_000)
        self.assertGreater(large, small + 1000)                  # 200,000 pointers are about 1,560 KiB

    def test_actions_to_string(self):
        self.assertEqual(actions_to_string(["UP", "RIGHT", "DOWN", "LEFT"]), "URDL")

    def test_state_graph_profile_bounds_the_work_of_the_algorithms(self):
        for name in LAYOUTS:
            problem = load_problem(name)
            bfs, ucs = breadth_first_search(problem), uniform_cost_search(problem)
            profile = state_graph_profile(problem, bfs.depth, ucs.path_cost)
            levels = [int(count) for count in profile["states_per_depth"].split()]
            with self.subTest(layout=name):
                self.assertEqual(levels[0], 1)                                   # only the initial state
                self.assertEqual(sum(levels), problem.count_reachable_states())
                self.assertEqual(profile["largest_level"], max(levels))
                # BFS never expands a state at the solution depth or deeper ...
                self.assertLessEqual(bfs.nodes_expanded, profile["states_shallower_than_solution"])
                # ... and UCS must expand every state that is cheaper than the optimum.
                self.assertGreaterEqual(ucs.nodes_expanded, profile["states_cheaper_than_optimum"])
                # IDS with the memo table expands every state within the limit at least once per iteration.
                memo = iterative_deepening_search(problem, use_memo=True)
                self.assertGreaterEqual(memo.nodes_expanded, profile["restart_only_expansions"])
                self.assertLessEqual(profile["average_successors"], 4)

    def test_searches_are_deterministic(self):
        problem = load_problem("medium")
        for search in (breadth_first_search, depth_first_search, uniform_cost_search,
                       iterative_deepening_search):
            first, second = search(problem), search(problem)
            self.assertEqual(first.actions, second.actions)
            self.assertEqual(first.nodes_generated, second.nodes_generated)


if __name__ == "__main__":
    unittest.main()
