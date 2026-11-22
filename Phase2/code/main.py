"""
main.py - command-line entry point for Phase II (all nine algorithms).

Examples
--------
    python main.py                                   run every algorithm on the large layout
    python main.py -a astar --heuristic h2           A* with the MST heuristic
    python main.py -a greedy astar --heuristic h1 h2 Greedy and A* with both heuristics
    python main.py -a hc sa ga --seed 7              the three local-search algorithms, seed 7
    python main.py -l medium -a ucs astar --show-path
    python main.py --list                            list the available layouts
    python main.py --layout-file example_maze.txt    use a maze from a text file

Algorithms:  bfs dfs ucs ids   (Phase I, uninformed)
             greedy astar      (Phase II, informed - choose the heuristic with --heuristic)
             hc sa ga          (Phase II, local search - choose the random seed with --seed)

The times printed here are those of ONE run of the search itself; the heuristic and the
distance table of the local-search methods are prepared before the clock starts. The
times in the report come from run_phase2.py, which repeats every run and includes the
preparation.

Only the Python standard library is needed for this script (no Matplotlib).
"""

import argparse

from pacman_search.experiments import actions_to_string, text_table
from pacman_search.heuristics import HEURISTICS
from pacman_search.informed import a_star_search, greedy_best_first_search
from pacman_search.layouts import DEFAULT_LAYOUT, LAYOUTS, load_problem, load_problem_from_file
from pacman_search.local_search import LOCAL_SEARCH_ALGORITHMS, TourProblem
from pacman_search.uninformed import UNINFORMED_ALGORITHMS

INFORMED_ALGORITHMS = {"greedy": greedy_best_first_search, "astar": a_star_search}
ALL_NAMES = list(UNINFORMED_ALGORITHMS) + list(INFORMED_ALGORITHMS) + list(LOCAL_SEARCH_ALGORITHMS)


def seed_value(text):
    """argparse type for --seed: a whole number that is not negative.

    random.Random() ignores the sign of an integer seed, so -7 would silently repeat the
    run of seed 7; refusing negative values avoids that surprise.
    """
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be 0 or larger")
    return value


def build_parser():
    """The command-line options of this script."""
    parser = argparse.ArgumentParser(
        description="Uninformed, informed and local search on the Pac-Man food-collection problem.")
    parser.add_argument("-l", "--layout", default=DEFAULT_LAYOUT, choices=list(LAYOUTS),
                        help=f"built-in maze layout (default: {DEFAULT_LAYOUT})")
    parser.add_argument("--layout-file", help="text file with a custom ASCII maze (overrides --layout)")
    parser.add_argument("-a", "--algorithm", nargs="+", default=["all"], choices=ALL_NAMES + ["all"],
                        help="algorithm(s) to run (default: all)")
    parser.add_argument("--heuristic", nargs="+", default=list(HEURISTICS), choices=list(HEURISTICS),
                        help="heuristic(s) for greedy and astar (default: both)")
    parser.add_argument("--seed", type=seed_value, default=0,
                        help="random seed for hc, sa and ga: 0 or larger (default 0)")
    parser.add_argument("--show-path", action="store_true",
                        help="also print each solution as a sequence of moves and draw it in the maze")
    parser.add_argument("--list", action="store_true", help="list the built-in layouts and exit")
    return parser


def search_row(result):
    """One line of the table of search algorithms."""
    return {
        "algorithm": result.algorithm, "path cost": result.path_cost, "steps": result.depth,
        "generated": result.nodes_generated, "expanded": result.nodes_expanded,
        "max frontier": result.max_frontier_size, "max in memory": result.max_nodes_in_memory,
        "time (ms)": result.runtime_sec * 1000.0,
    }


def local_row(result, problem, tour):
    """One line of the table of local-search algorithms (the plan is checked first)."""
    states, cost = problem.execute(result.actions)        # replay the plan in the search model
    assert problem.is_goal(states[-1]) and cost == result.cost
    return {
        "algorithm": result.algorithm, "seed": result.seed, "cost": result.cost,
        "steps": len(result.actions),
        "pellets eaten in order": " ".join(str(p) for p in tour.eating_order(result.order)),
        "evaluations": result.evaluations, "iterations": result.iterations,
        "time (ms)": result.runtime_sec * 1000.0,
    }


def main():
    """Load the chosen maze, run the chosen algorithms once and print the result tables."""
    parser = build_parser()
    args = parser.parse_args()
    if args.list:
        for name in LAYOUTS:
            problem = load_problem(name)
            print(problem.describe())
            print(problem.render())
            print()
        return

    if args.layout_file:
        try:
            problem = load_problem_from_file(args.layout_file)
        except (OSError, UnicodeError, ValueError) as error:      # missing file, bad encoding, bad maze
            parser.error(f"cannot use layout file '{args.layout_file}': {error}")
    else:
        problem = load_problem(args.layout)
    print(problem.describe())
    print(problem.render())
    print(f"Initial state: {problem.initial_state}   (food mask {problem.all_food:0{problem.num_food}b})")
    print("Goal test: food mask == 0   |   step cost: 1, or "
          f"{problem.danger_cost} when entering a cell next to a ghost\n")

    names = ALL_NAMES if "all" in args.algorithm else args.algorithm
    search_rows, local_rows, solutions = [], [], []
    tour = None

    for name in names:
        if name in UNINFORMED_ALGORITHMS:
            result = UNINFORMED_ALGORITHMS[name](problem)
            search_rows.append(search_row(result))
            solutions.append((result.algorithm, result.actions))
        elif name in INFORMED_ALGORITHMS:
            for label in args.heuristic:
                heuristic = HEURISTICS[label](problem)
                result = INFORMED_ALGORITHMS[name](problem, heuristic)
                search_rows.append(search_row(result))
                solutions.append((result.algorithm, result.actions))
        else:
            tour = tour or TourProblem(problem)
            result = LOCAL_SEARCH_ALGORITHMS[name](tour, seed=args.seed)
            local_rows.append(local_row(result, problem, tour))
            solutions.append((result.algorithm, result.actions))

    if search_rows:
        print("Search algorithms")
        print(text_table(search_rows, list(search_rows[0].keys())))
    if local_rows:
        print("\nLocal search (a solution is a priority order of the pellets; seed "
              f"{args.seed})")
        print(text_table(local_rows, list(local_rows[0].keys())))

    if args.show_path:
        for label, actions in solutions:
            states, cost = problem.execute(actions)
            print(f"\n{label} solution ({len(actions)} moves, cost {cost}):")
            print("  " + actions_to_string(actions) + "    (U = up, R = right, D = down, L = left)")
            print(problem.render(states))


if __name__ == "__main__":
    main()
