"""
main.py - command-line entry point for Phase I (uninformed search).

Examples
--------
    python main.py                                  run BFS, DFS, UCS and IDS on the large layout
    python main.py --layout small --algorithm ucs   one algorithm on one layout
    python main.py -l medium -a bfs dfs --show-path print the action sequence and the maze
    python main.py --list                           list the available layouts
    python main.py --layout-file example_maze.txt   use a maze from a text file

Only the Python standard library is needed for this script (no Matplotlib).
"""

import argparse

from pacman_search.experiments import actions_to_string, text_table
from pacman_search.layouts import DEFAULT_LAYOUT, LAYOUTS, load_problem, load_problem_from_file
from pacman_search.uninformed import UNINFORMED_ALGORITHMS


def build_parser():
    """The command-line options of this script."""
    parser = argparse.ArgumentParser(
        description="Uninformed search (BFS, DFS, UCS, IDS) on the Pac-Man food-collection problem.")
    parser.add_argument("-l", "--layout", default=DEFAULT_LAYOUT, choices=list(LAYOUTS),
                        help=f"built-in maze layout (default: {DEFAULT_LAYOUT})")
    parser.add_argument("--layout-file", help="text file with a custom ASCII maze (overrides --layout)")
    parser.add_argument("-a", "--algorithm", nargs="+", default=["all"],
                        choices=list(UNINFORMED_ALGORITHMS) + ["all"],
                        help="algorithm(s) to run (default: all)")
    parser.add_argument("--show-path", action="store_true",
                        help="also print each solution as a sequence of moves and draw it in the maze")
    parser.add_argument("--list", action="store_true", help="list the built-in layouts and exit")
    return parser


def print_layouts():
    """Print every built-in layout with its size (the --list option)."""
    for name in LAYOUTS:
        problem = load_problem(name)
        print(problem.describe())
        print(problem.render())
        print()


def main():
    """Load the chosen maze, run the chosen algorithms once and print a table of the results."""
    parser = build_parser()
    args = parser.parse_args()
    if args.list:
        print_layouts()
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

    names = list(UNINFORMED_ALGORITHMS) if "all" in args.algorithm else args.algorithm
    rows, results = [], []
    for name in names:
        result = UNINFORMED_ALGORITHMS[name](problem)
        results.append(result)
        rows.append({
            "algorithm": result.algorithm,
            "found": result.found,
            "path cost": result.path_cost,
            "steps": result.depth,
            "generated": result.nodes_generated,
            "expanded": result.nodes_expanded,
            "max frontier": result.max_frontier_size,
            "max in memory": result.max_nodes_in_memory,
            "time (ms)": result.runtime_sec * 1000.0,
        })
    print(text_table(rows, list(rows[0].keys())))

    if args.show_path:
        for result in results:
            print(f"\n{result.algorithm} solution ({result.depth} moves, cost {result.path_cost}):")
            print("  " + actions_to_string(result.actions) + "    (U = up, R = right, D = down, L = left)")
            print(problem.render(result.states))


if __name__ == "__main__":
    main()
