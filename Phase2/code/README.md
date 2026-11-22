# Pac-Man Food Collection as a Search Problem - Phase II

CSAI 301 project, Phase II: **heuristic search (Greedy Best-First, A*), local search
(Hill Climbing, Simulated Annealing, Genetic Algorithm) and the comparison of all nine
algorithms**. This folder also contains the complete Phase I code: the Phase I modules,
`run_phase1.py` and the Phase I tests are unchanged, and only `main.py` was extended to
offer all nine algorithms.

Team: Almoatasembellah Aboubakr (202400993), Rabie Al Sayed Mosa (202400113),
Amir Elsamahy (202401724), Ebrahim Mohamed Rabia (202401474), Ahmed Mostafa (202401612).

## The problem in one paragraph

Pac-Man moves through a maze and must eat every food pellet. Ghosts stand still; their
cells cannot be entered, and entering a cell directly next to a ghost costs 5 instead of 1.
A **state** is `(pos, food)`: Pac-Man's cell and a bitmask of the pellets still uneaten.
The **goal** is `food == 0`. **Actions**: UP, RIGHT, DOWN, LEFT. We look for the cheapest
sequence of moves. The model is exactly the one of Phase I.

## Requirements

* Python 3 (developed with Python 3.13; also tested with 3.12 and 3.15).
* `main.py` and the unit tests use **only the Python standard library**.
* The figures and animations need Matplotlib: `pip install -r requirements.txt`

All nine algorithms are written from scratch; no search or optimisation library is used.

## How to run

Run every command from inside this `code` folder.

| Command | What it does |
|---|---|
| `python main.py` | all nine algorithms on the large layout |
| `python main.py -a astar --heuristic h2` | A* with the MST heuristic |
| `python main.py -a greedy astar` | Greedy and A* with both heuristics |
| `python main.py -a hc sa ga --seed 7` | the three local-search algorithms with seed 7 |
| `python main.py -l medium -a ucs astar --show-path` | two algorithms on the medium layout, with the paths drawn in the maze |
| `python main.py --list` | shows the built-in layouts |
| `python main.py --layout-file example_maze.txt` | a maze from a text file |
| `python run_phase2.py` | ALL Phase II experiments (about two minutes) |
| `python run_phase2.py --quick` | faster: 10 seeds, no landscape analysis, no tuning study, no scaling experiment, no animations; writes to `results/phase2_quick` |
| `python run_phase1.py` | the Phase I experiments (unchanged) |
| `python -m unittest discover -s tests -v` | 74 unit tests (33 from Phase I + 41 new) |

Algorithm names for `-a`: `bfs dfs ucs ids` (uninformed), `greedy astar` (informed, choose
the heuristic with `--heuristic h1 h2`), `hc sa ga` (local search, choose the seed with
`--seed`, 0 or larger).

`run_phase2.py` writes everything to `results/phase2/`. The submitted folder was produced
by this script, run with Python pinned to one processor core (see "Reproducibility and
seeds").

| File | Content |
|---|---|
| `search_metrics.csv` | the eight search runs (BFS, DFS, UCS, IDS, Greedy h1/h2, A* h1/h2) with the same measurements as in Phase I |
| `heuristic_analysis.csv` | h1 and h2 checked on every reachable state: admissible, consistent, mean h/h*, dominance, and how far Greedy can get before the heuristic has to rise again |
| `local_search_summary.csv` | HC, SA, GA, HC with restarts and the random-sampling baseline: best / mean / worst cost over the 30 seeds, optimal runs, evaluations, time, memory |
| `local_search_runs.csv` | every single seeded run |
| `landscape.csv` | exhaustive look at all pellet orders: how many are optimal, where hill climbing stops |
| `tuning_sa.csv`, `tuning_ga.csv`, `tuning_one_at_a_time.csv` | parameter-sensitivity study (300 runs per setting) |
| `comparison_all.csv` | all algorithms in one table: cost, time, memory, effort, completeness, optimality |
| `scaling_instances.csv`, `scaling_methods.csv` | the extra experiment on larger mazes (8 to 24 pellets): A* with h2, and local search against random sampling |
| `solutions.txt`, `summary.md`, `results.json` | solution paths, readable tables, everything in one file |
| `figures/` | explored states + path for Greedy/A*, heuristic comparison, convergence plots, final-cost distributions, SA trace, tuning heat maps, reliability against budget, summary chart of all algorithms, routes, the scaling experiment |
| `animations/` | animated GIFs of Greedy and A* on the large layout |

## Files

| File | What it contains | Phase |
|---|---|---|
| `pacman_search/problem.py` | the formal model (state, actions, transition, costs, goal test) | I (unchanged) |
| `pacman_search/layouts.py` | the four maze layouts | I (unchanged) |
| `pacman_search/search_core.py` | `Node`, `SearchResult`, counters | I (unchanged) |
| `pacman_search/uninformed.py` | BFS, DFS, UCS, IDS | I (unchanged) |
| `pacman_search/experiments.py` | timing, memory, table helpers | I (unchanged) |
| `pacman_search/visualize.py` | maze pictures, search trees, charts | I (unchanged) |
| `pacman_search/heuristics.py` | **h1** (farthest pellet, Manhattan), **h2** (nearest pellet + MST), exhaustive verification | II |
| `pacman_search/informed.py` | **Greedy Best-First Search, A*** | II |
| `pacman_search/local_search.py` | **Hill Climbing, Simulated Annealing, Genetic Algorithm** on pellet orders; random sampling as the baseline | II |
| `pacman_search/scaling.py` | the extra experiment on larger mazes | II |
| `pacman_search/visualize_phase2.py` | convergence plots, tuning heat maps, summary chart | II |
| `main.py` | command-line interface for all nine algorithms | II (extended) |
| `run_phase1.py` | Phase I experiments | I (unchanged) |
| `run_phase2.py` | Phase II experiments | II |
| `tests/test_phase1.py`, `tests/test_phase2.py` | unit tests | I (unchanged) / II |
| `example_maze.txt` | a small maze file for `--layout-file` | I (unchanged) |

## Heuristics

Both heuristics count steps and multiply the count by the cheapest step cost of the maze,
which is 1 in all our layouts.

| | Definition | Admissible | Consistent |
|---|---|---|---|
| `h1` | Manhattan distance to the farthest remaining pellet | yes | yes |
| `h2` | maze distance (in steps) to the nearest remaining pellet + weight of the minimum spanning tree over the remaining pellets | yes | yes |

`h2 >= h1` in every state. Both properties are proved in the report and checked on every
reachable state and every transition by `analyse_heuristic()` (see `heuristic_analysis.csv`).

Greedy Best-First orders the frontier by `h` alone and never re-opens a state; A* orders
it by `f = g + h` and re-opens a state when a cheaper path to it is found.

## Local search

* **Candidate solution** = a priority order of the pellets (a permutation).
* **Decoding** = Pac-Man repeatedly walks the cheapest path to the first pellet of the
  order that is still uneaten; pellets eaten on the way count as eaten. The plan therefore
  stops exactly when the last pellet is eaten.
* **Objective** = path cost of the decoded plan (minimise). The best order has exactly the
  optimal path cost.
* **Neighbours** = all orders obtained by swapping two pellets.

| Algorithm | Parameters used in the experiments |
|---|---|
| Hill Climbing | steepest descent from a random order, stops when no swap is strictly better; no parameters. Extra experiment: 9 random restarts. Option: sideways moves (`max_sideways`) |
| Simulated Annealing | start temperature 10, geometric cooling T <- 0.995 T, stop when T < 0.1 (919 iterations) |
| Genetic Algorithm | population 30, 30 generations, tournament selection (size 2), order crossover (rate 0.9), swap mutation (rate 0.8 per child), no elitism |

The parameters were chosen from the sensitivity study in `tuning_*.csv`, which uses its own
seeds, so they were not tuned on the runs that are reported as results.

**Baseline.** Next to the three algorithms the experiments run blind random sampling (the
best of 920 random orders, the same number of evaluations as one simulated-annealing run).
On the official layouts it is as reliable as the local-search methods; the extra
experiment in `scaling.py` shows from which maze size on they are better.

## What is measured

The definitions of Phase I are kept (nodes generated / expanded, max frontier, max nodes in
memory, running time = fastest of up to 20 repeated runs, peak memory by `tracemalloc`).
For every algorithm the time and the memory reported by `run_phase2.py` include what it
needs in advance: the distance tables of `h2` and of the local-search methods are built
inside the measured part. For the local-search methods the effort is the number of
objective evaluations, and the time is the mean over the 30 seeds (each seed timed as the
fastest of 3 identical runs) plus the time to build the distance table.

`main.py` prints the time of a single run of the search alone, without this preparation.

## Reproducibility and seeds

* The search algorithms are deterministic.
* The local-search algorithms are random, and each run uses its own `random.Random(seed)`
  generator. `run_phase2.py` uses the fixed seeds **0 to 29** for the reported results,
  **1000 to 1299** for the parameter-sensitivity study and **0 to 19** for the scaling
  experiment, so every run of the script produces the same costs. Only the running times
  (and, slightly, the peak-memory readings) differ from run to run and from machine to
  machine.
* `python main.py -a hc sa ga --seed N` reproduces a single run.

Steady timings: on a laptop whose processor has fast and slow cores, the operating system
moves a running program between the cores, and identical runs can then differ by a factor
of two to three. The submitted results were therefore measured with Python pinned to one
fast core, at high priority:

| System | Command |
|---|---|
| Windows | `cmd /c start /b /wait /high /affinity 1000 python run_phase2.py` |
| Linux | `taskset -c 0 python run_phase2.py` |

`1000` is a hexadecimal mask that selects core 12, one of the fast cores of our laptop. On
another computer use `/affinity 1` (the first core); if the processor has fast and slow
cores, choose a fast one.

## Use of AI tools

An AI assistant was used during the development of this project. It is acknowledged in
the report, in the section "Use of AI tools".
