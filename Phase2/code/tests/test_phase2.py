"""
Unit tests for Phase II: heuristics, informed search and local search.

Run from the code folder:

    python -m unittest discover -s tests -v
"""

import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pacman_search.heuristics import (  # noqa: E402
    FarthestFoodHeuristic, MazeMSTHeuristic, ZeroHeuristic, analyse_heuristic, descent_region,
    manhattan, maze_distances_from, optimal_costs_to_goal)
from pacman_search.informed import a_star_search, greedy_best_first_search  # noqa: E402
from pacman_search.layouts import LAYOUTS, load_problem  # noqa: E402
from pacman_search.local_search import (  # noqa: E402
    TourProblem, genetic_algorithm, hill_climbing, order_crossover, random_sampling,
    simulated_annealing, swap_mutation)
from pacman_search.problem import PacmanProblem, State  # noqa: E402
from pacman_search.scaling import (  # noqa: E402
    SCALING_MAZE, budget_methods, cooling_rate_for, hill_climbing_with_budget, scaling_problem,
    scaling_study, scatter_pellets)
from pacman_search.uninformed import uniform_cost_search  # noqa: E402

OFFICIAL = ("small", "medium", "large")


class TestHeuristics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.problems = {name: load_problem(name) for name in LAYOUTS}
        cls.true_costs = {name: optimal_costs_to_goal(problem) for name, problem in cls.problems.items()}

    def test_true_cost_table_matches_ucs(self):
        for name, problem in self.problems.items():
            self.assertEqual(self.true_costs[name][problem.initial_state],
                             uniform_cost_search(problem).path_cost)

    def test_heuristics_are_zero_at_goal_states(self):
        problem = self.problems["small"]
        for heuristic in (FarthestFoodHeuristic(problem), MazeMSTHeuristic(problem)):
            for cell in problem.free_cells:
                self.assertEqual(heuristic(State(cell, 0)), 0)

    def test_h1_and_h2_are_admissible_and_consistent_everywhere(self):
        for name, problem in self.problems.items():
            for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
                with self.subTest(layout=name, heuristic=heuristic_class.label):
                    report = analyse_heuristic(problem, heuristic_class(problem), self.true_costs[name])
                    self.assertTrue(report["admissible"])
                    self.assertTrue(report["consistent"])
                    self.assertEqual(report["states_checked"], problem.count_reachable_states())

    def test_h2_dominates_h1(self):
        for name, problem in self.problems.items():
            h1, h2 = FarthestFoodHeuristic(problem), MazeMSTHeuristic(problem)
            for state in self.true_costs[name]:
                self.assertGreaterEqual(h2(state), h1(state))

    def test_h2_is_more_accurate_than_h1(self):
        for name in OFFICIAL:
            problem = self.problems[name]
            ratio_h1 = analyse_heuristic(problem, FarthestFoodHeuristic(problem), self.true_costs[name])["mean_ratio"]
            ratio_h2 = analyse_heuristic(problem, MazeMSTHeuristic(problem), self.true_costs[name])["mean_ratio"]
            self.assertGreater(ratio_h2, ratio_h1)

    def test_analysis_detects_a_bad_heuristic(self):
        problem = self.problems["small"]

        class TooBig:
            label = "bad"

            def __call__(self, state):
                return 100 if state.food else 0             # wildly overestimates

        report = analyse_heuristic(problem, TooBig(), self.true_costs["small"])
        self.assertFalse(report["admissible"])
        self.assertFalse(report["consistent"])

    def test_heuristics_stay_correct_for_other_step_costs(self):
        # "What if a step cost 0.5, or danger cost less than a normal step?" The heuristics
        # are scaled by the cheapest step, so they must stay admissible and A* optimal.
        for step_cost, danger_cost in ((0.5, 5), (1, 0.5), (2, 10), (3, 3)):
            problem = PacmanProblem(LAYOUTS["small"], "small", step_cost=step_cost, danger_cost=danger_cost)
            true_costs = optimal_costs_to_goal(problem)
            optimum = uniform_cost_search(problem).path_cost
            for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
                with self.subTest(costs=(step_cost, danger_cost), heuristic=heuristic_class.label):
                    report = analyse_heuristic(problem, heuristic_class(problem), true_costs)
                    self.assertTrue(report["admissible"] and report["consistent"])
                    self.assertEqual(a_star_search(problem, heuristic_class(problem)).path_cost, optimum)

    def test_maze_distance_is_never_below_manhattan(self):
        problem = self.problems["medium"]
        for source in problem.food_cells:
            distances = maze_distances_from(problem, source)
            for cell, steps in distances.items():
                self.assertGreaterEqual(steps, manhattan(source, cell))

    def test_mst_weight_of_small_sets(self):
        problem = self.problems["medium"]
        h2 = MazeMSTHeuristic(problem)
        self.assertEqual(h2.mst_weight(0b000001), 0)                     # a single pellet needs no edge
        self.assertEqual(h2.mst_weight(0b000011), h2.between[0][1])      # two pellets: one edge
        # three pellets: the MST drops the longest of the three edges
        edges = [h2.between[0][1], h2.between[0][2], h2.between[1][2]]
        self.assertEqual(h2.mst_weight(0b000111), sum(edges) - max(edges))


class TestInformedSearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.problems = {name: load_problem(name) for name in LAYOUTS}
        cls.ucs = {name: uniform_cost_search(problem) for name, problem in cls.problems.items()}

    def test_a_star_is_optimal_with_both_heuristics(self):
        for name, problem in self.problems.items():
            for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
                with self.subTest(layout=name, heuristic=heuristic_class.label):
                    result = a_star_search(problem, heuristic_class(problem))
                    self.assertTrue(problem.is_solution(result.actions))
                    self.assertEqual(problem.execute(result.actions)[1], result.path_cost)
                    self.assertEqual(result.path_cost, self.ucs[name].path_cost)

    def test_a_star_with_zero_heuristic_is_ucs(self):
        for name, problem in self.problems.items():
            result = a_star_search(problem, ZeroHeuristic(problem))
            ucs = self.ucs[name]
            self.assertEqual(result.actions, ucs.actions)
            self.assertEqual((result.nodes_expanded, result.nodes_generated, result.max_frontier_size,
                              result.max_nodes_in_memory),
                             (ucs.nodes_expanded, ucs.nodes_generated, ucs.max_frontier_size,
                              ucs.max_nodes_in_memory))

    def test_h2_needs_fewer_expansions_than_h1_on_the_official_layouts(self):
        # An observation on our layouts, not a theorem. What theory guarantees for consistent
        # heuristics with h2 >= h1: every node with f < C* that A*(h2) expands is also
        # expanded by A*(h1); nodes with f = C* can go either way (tie-breaking).
        for name in OFFICIAL:
            problem = self.problems[name]
            with_h1 = a_star_search(problem, FarthestFoodHeuristic(problem)).nodes_expanded
            with_h2 = a_star_search(problem, MazeMSTHeuristic(problem)).nodes_expanded
            self.assertLess(with_h2, with_h1)
            self.assertLess(with_h1, self.ucs[name].nodes_expanded)

    def test_no_state_is_expanded_twice(self):
        # A* with a consistent heuristic never has to; Greedy never re-opens a state.
        for name, problem in self.problems.items():
            for search in (a_star_search, greedy_best_first_search):
                for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
                    result = search(problem, heuristic_class(problem), trace=True)
                    states = [node.state for node in result.expanded_nodes]
                    self.assertEqual(len(states), len(set(states)), (name, result.algorithm))
                    self.assertLessEqual(result.max_nodes_in_memory,
                                         result.max_frontier_size + problem.count_reachable_states())

    def test_generated_counter_matches_its_definition(self):
        problem = self.problems["large"]
        for search in (a_star_search, greedy_best_first_search):
            result = search(problem, MazeMSTHeuristic(problem), trace=True)
            successors = sum(len(problem.successors(node.state)) for node in result.expanded_nodes)
            self.assertEqual(result.nodes_generated, 1 + successors)

    def test_a_star_stays_optimal_with_an_inconsistent_heuristic(self):
        # Admissible but not consistent: A* must then re-open states to stay optimal.
        problem = self.problems["small"]
        h2 = MazeMSTHeuristic(problem)

        class Patchy:
            label = "patchy"

            def __call__(self, state):
                return h2(state) if (state.pos[0] + state.pos[1]) % 2 else 0

        self.assertEqual(a_star_search(problem, Patchy()).path_cost, self.ucs["small"].path_cost)

    def test_greedy_searches_the_whole_descent_region_first(self):
        # Greedy expands a state with h >= h(start) only after every state that can be reached
        # with h below h(start) has been expanded (descent_region).
        for name in OFFICIAL:
            problem = self.problems[name]
            for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
                heuristic = heuristic_class(problem)
                region, goal_inside = descent_region(problem, heuristic)
                result = greedy_best_first_search(problem, heuristic, trace=True)
                values = [heuristic(node.state) for node in result.expanded_nodes]
                with self.subTest(layout=name, heuristic=heuristic.label):
                    if goal_inside:
                        self.assertTrue(all(value < values[0] for value in values[1:]))
                        self.assertLessEqual(result.nodes_expanded, region)
                    else:                                   # the basin is emptied before the climb
                        self.assertGreater(result.nodes_expanded, region)
                        self.assertTrue(all(value < values[0] for value in values[1:region]))
                        self.assertGreaterEqual(values[region], values[0])
        zero = ZeroHeuristic()
        self.assertEqual(descent_region(self.problems["large"], zero), (1, False))

    def test_greedy_returns_a_valid_but_not_optimal_solution(self):
        for name in OFFICIAL:
            problem = self.problems[name]
            for heuristic_class in (FarthestFoodHeuristic, MazeMSTHeuristic):
                result = greedy_best_first_search(problem, heuristic_class(problem))
                self.assertTrue(problem.is_solution(result.actions))
                self.assertEqual(problem.execute(result.actions)[1], result.path_cost)
                self.assertGreater(result.path_cost, self.ucs[name].path_cost)


class TestLocalSearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.problems = {name: load_problem(name) for name in LAYOUTS}
        cls.tours = {name: TourProblem(problem) for name, problem in cls.problems.items()}
        cls.optimum = {name: uniform_cost_search(problem).path_cost for name, problem in cls.problems.items()}

    def _all_orders(self, name):
        return itertools.permutations(range(self.tours[name].num_food))

    def test_every_order_is_a_plan_that_stops_at_the_goal(self):
        # cost(order) must be the path cost of the decoded plan, and the plan must end at
        # the FIRST goal state (no walking on after the last pellet).
        rng = random.Random(1)
        for name, problem in self.problems.items():
            tour = self.tours[name]
            orders = list(self._all_orders(name))
            if len(orders) > 800:
                orders = rng.sample(orders, 800)
            for order in orders:
                states, cost = problem.execute(tour.to_actions(order))
                self.assertEqual(cost, tour.cost(order))
                self.assertTrue(problem.is_goal(states[-1]))
                self.assertFalse(any(problem.is_goal(state) for state in states[:-1]))

    def test_eating_order_skips_nothing_and_respects_the_priorities(self):
        tour = self.tours["large"]
        rng = random.Random(2)
        for _ in range(200):
            order = tour.random_order(rng)
            eaten = tour.eating_order(order)
            self.assertEqual(sorted(eaten), list(range(tour.num_food)))
            # the targets that were actually walked to appear in priority order
            targets = [b - 1 for _, b in tour.walked_legs(order)]
            self.assertEqual(targets, [pellet for pellet in order if pellet in targets])
            self.assertEqual(tour.eating_order(eaten), eaten)            # the eating order is a fixed point
            self.assertEqual(tour.cost(eaten), tour.cost(order))

    def test_best_order_costs_exactly_the_optimal_path_cost(self):
        for name in LAYOUTS:
            tour = self.tours[name]
            best = min(tour.cost(order) for order in self._all_orders(name))
            self.assertEqual(best, self.optimum[name])

    def test_distance_table_is_directed_and_correct(self):
        # entering a danger cell costs more than leaving it, so d(a, b) can differ from d(b, a)
        problem = PacmanProblem("#######\n#P   .#\n# #G# #\n#.    #\n#######", "asym")
        tour = TourProblem(problem)
        for a in range(len(tour.points)):
            for b in range(len(tour.points)):
                state, total = State(tour.points[a], 0), 0
                for action in tour.leg[a][b]:
                    nxt = problem.result(state, action)
                    total += problem.step_cost(state, action, nxt)
                    state = nxt
                self.assertEqual(state.pos, tour.points[b])
                self.assertEqual(total, tour.distance[a][b])

    def test_number_of_neighbours(self):
        tour = self.tours["large"]
        order = tuple(range(tour.num_food))
        neighbours = tour.neighbours(order)
        self.assertEqual(len(neighbours), tour.num_food * (tour.num_food - 1) // 2)
        self.assertEqual(len(set(neighbours)), len(neighbours))
        for neighbour in neighbours:
            self.assertEqual(sorted(neighbour), list(order))
            self.assertEqual(sum(a != b for a, b in zip(neighbour, order)), 2)

    def _check_result(self, name, result):
        problem, tour = self.problems[name], self.tours[name]
        self.assertEqual(sorted(result.order), list(range(tour.num_food)))       # a permutation
        self.assertEqual(result.cost, tour.cost(result.order))
        states, cost = problem.execute(result.actions)
        self.assertTrue(problem.is_goal(states[-1]))
        self.assertFalse(any(problem.is_goal(state) for state in states[:-1]))
        self.assertEqual(cost, result.cost)
        self.assertGreaterEqual(result.cost, self.optimum[name])                  # never below the optimum
        self.assertEqual(result.history[-1], result.cost)
        self.assertTrue(all(later <= earlier for earlier, later in zip(result.history, result.history[1:])))

    def test_all_algorithms_return_valid_solutions(self):
        for name in LAYOUTS:
            tour = self.tours[name]
            for algorithm in (hill_climbing, simulated_annealing, genetic_algorithm):
                for seed in (0, 1, 2):
                    with self.subTest(layout=name, algorithm=algorithm.__name__, seed=seed):
                        self._check_result(name, algorithm(tour, seed=seed))

    def test_same_seed_gives_the_same_result(self):
        tour = self.tours["large"]
        for algorithm in (hill_climbing, simulated_annealing, genetic_algorithm):
            first, second = algorithm(tour, seed=5), algorithm(tour, seed=5)
            self.assertEqual((first.order, first.cost, first.history), (second.order, second.cost, second.history))

    def test_different_seeds_give_different_runs(self):
        tour = self.tours["large"]
        starts = {hill_climbing(tour, seed=seed).history[0] for seed in range(10)}
        self.assertGreater(len(starts), 1)

    def test_history_switch_does_not_change_the_result(self):
        tour = self.tours["large"]
        for algorithm in (hill_climbing, simulated_annealing, genetic_algorithm):
            with_history = algorithm(tour, seed=3)
            without = algorithm(tour, seed=3, record_history=False)
            self.assertEqual((with_history.order, with_history.cost, with_history.evaluations),
                             (without.order, without.cost, without.evaluations))
            self.assertEqual(without.history, [])

    def test_hill_climbing_stops_where_no_neighbour_is_better(self):
        tour = self.tours["large"]
        for seed in range(10):
            result = hill_climbing(tour, seed=seed)
            self.assertTrue(all(tour.cost(n) >= result.cost for n in tour.neighbours(result.order)))

    def test_hill_climbing_evaluation_count(self):
        # one evaluation for the start, and all k(k-1)/2 neighbours for every move plus the final look
        tour = self.tours["large"]
        per_scan = tour.num_food * (tour.num_food - 1) // 2
        for seed in range(5):
            result = hill_climbing(tour, seed=seed)
            self.assertEqual(result.evaluations, 1 + (result.iterations + 1) * per_scan)

    def test_restarts_never_make_hill_climbing_worse(self):
        tour = self.tours["large"]
        for seed in range(5):
            self.assertLessEqual(hill_climbing(tour, seed=seed, restarts=9).cost,
                                 hill_climbing(tour, seed=seed).cost)

    def test_sideways_moves_help_on_plateaus(self):
        # Sideways moves never make a climb worse (same start, the cost never goes up) ...
        tour = self.tours["medium"]
        plain = [hill_climbing(tour, seed=seed) for seed in range(30)]
        sideways = [hill_climbing(tour, seed=seed, max_sideways=20) for seed in range(30)]
        for a, b in zip(plain, sideways):
            self.assertEqual(a.history[0], b.history[0])                 # same random start
            self.assertLessEqual(b.cost, a.cost)
            self._check_result("medium", b)
        # ... and on this layout they remove every failure (all stops are plateau shoulders)
        self.assertTrue(any(run.cost > self.optimum["medium"] for run in plain))
        self.assertTrue(all(run.cost == self.optimum["medium"] for run in sideways))

    def test_simulated_annealing_cooling_schedule(self):
        tour = self.tours["small"]
        result = simulated_annealing(tour, seed=0, start_temperature=10.0, cooling_rate=0.9, end_temperature=1.0)
        # 10 * 0.9^n drops below 1 after 22 iterations
        self.assertEqual(result.iterations, 22)
        self.assertEqual(result.evaluations, 23)
        with self.assertRaises(ValueError):
            simulated_annealing(tour, cooling_rate=1.0)                  # would never cool down
        with self.assertRaises(ValueError):
            simulated_annealing(tour, start_temperature=0.05)            # below the end temperature

    def test_genetic_operators_keep_permutations_valid(self):
        rng = random.Random(3)
        genes = list(range(8))
        for _ in range(200):
            a, b = genes[:], genes[:]
            rng.shuffle(a)
            rng.shuffle(b)
            child = order_crossover(tuple(a), tuple(b), rng)
            self.assertEqual(sorted(child), genes)
            self.assertEqual(sorted(swap_mutation(child, rng)), genes)

    def test_order_crossover_example(self):
        class FixedCuts:                                     # forces the slice to be positions 2..4
            def sample(self, population, count):
                return [2, 4]

        child = order_crossover((0, 1, 2, 3, 4, 5), (5, 4, 3, 2, 1, 0), FixedCuts())
        # slice 2,3,4 from parent A stays in place; 5, 1, 0 are filled in parent B's order
        self.assertEqual(child, (5, 1, 2, 3, 4, 0))

    def test_genetic_algorithm_evaluation_count(self):
        tour = self.tours["small"]
        result = genetic_algorithm(tour, seed=0, population_size=20, generations=10)
        self.assertEqual(result.evaluations, 20 * 11)
        self.assertEqual(len(result.history), 11)

    def test_local_search_reaches_the_optimum_on_the_main_layout(self):
        tour = self.tours["large"]
        for algorithm in (simulated_annealing, genetic_algorithm):
            best = min(algorithm(tour, seed=seed).cost for seed in range(5))
            self.assertEqual(best, self.optimum["large"])

    def test_a_maze_with_one_pellet_needs_no_search(self):
        # only one order exists: every algorithm must return it instead of failing
        problem = PacmanProblem("#####\n#P .#\n#####", "one pellet")
        tour = TourProblem(problem)
        runs = [hill_climbing(tour, seed=0), hill_climbing(tour, seed=0, restarts=3, max_sideways=5),
                simulated_annealing(tour, seed=0), genetic_algorithm(tour, seed=0),
                random_sampling(tour, seed=0, evaluations=5)]
        for result in runs:
            self.assertEqual((result.order, result.cost), ((0,), 2))
            self.assertTrue(problem.is_solution(result.actions))


class TestBaselineAndScaling(unittest.TestCase):
    """The random-sampling baseline and the larger mazes of the scaling experiment."""

    SA = {"start_temperature": 10.0, "cooling_rate": 0.995, "end_temperature": 0.1}
    GA = {"population_size": 30, "generations": 30, "crossover_rate": 0.9, "mutation_rate": 0.8,
          "tournament_size": 2, "elite_count": 0}

    def test_random_sampling_is_the_best_of_n_random_orders(self):
        problem = load_problem("large")
        tour = TourProblem(problem)
        rng = random.Random(4)
        expected = min(tour.cost(tour.random_order(rng)) for _ in range(200))
        result = random_sampling(tour, seed=4, evaluations=200)
        self.assertEqual(result.cost, expected)
        self.assertEqual((result.evaluations, len(result.history)), (200, 200))
        self.assertEqual(result.cost, tour.cost(result.order))
        self.assertEqual(problem.execute(result.actions)[1], result.cost)
        # more samples from the same seed can only improve the result
        self.assertLessEqual(random_sampling(tour, seed=4, evaluations=2000).cost, result.cost)

    def test_scattered_pellets_are_nested(self):
        small, large = scatter_pellets(SCALING_MAZE, 8), scatter_pellets(SCALING_MAZE, 24)
        self.assertEqual((small.count("."), large.count(".")), (8, 24))
        self.assertEqual(scatter_pellets(SCALING_MAZE, 8), small)                # fixed seed
        self.assertTrue(all(big == "." for few, big in zip(small, large) if few == "."))
        with self.assertRaises(ValueError):
            scatter_pellets(SCALING_MAZE, 10_000)

    def test_a_star_is_optimal_on_the_smallest_scaling_maze(self):
        problem = scaling_problem(8)                         # 33,024 states: UCS can still check it
        self.assertEqual(a_star_search(problem, MazeMSTHeuristic(problem)).path_cost,
                         uniform_cost_search(problem).path_cost)

    def test_every_method_gets_the_same_budget(self):
        tour = TourProblem(scaling_problem(12))
        budget = 2000
        self.assertAlmostEqual(10.0 * cooling_rate_for(budget, 10.0, 0.1) ** budget, 0.1)
        per_climb = hill_climbing(tour, seed=0).evaluations
        for name, run in budget_methods(budget, self.SA, self.GA).items():
            result = run(tour, 0)
            with self.subTest(method=name):
                self.assertGreaterEqual(result.evaluations, budget - tour.num_food * 30)
                self.assertLess(result.evaluations, budget + 3 * per_climb)
                self.assertEqual(result.cost, tour.cost(result.order))
        restarted = hill_climbing_with_budget(tour, seed=1, budget=budget)
        self.assertGreaterEqual(restarted.evaluations, budget)
        self.assertLessEqual(restarted.cost, hill_climbing(tour, seed=1000).cost)   # its first climb

    def test_scaling_study_rows(self):
        instances, methods = scaling_study(seeds=range(2), budget=300, sa_params=self.SA, ga_params=self.GA,
                                           pellet_counts=(8, 12))
        self.assertEqual([row["pellets"] for row in instances], [8, 12])
        self.assertEqual(len(methods), 2 * 4)
        for row in methods:
            self.assertGreaterEqual(row["best"], row["optimal_cost"])
            self.assertGreaterEqual(row["mean_percent_above_optimum"], 0)
            self.assertLessEqual(row["optimal_runs"], row["runs"])


if __name__ == "__main__":
    unittest.main()
