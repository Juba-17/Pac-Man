# Pac-Man Food Collection as a Search Problem - Phase I

CSAI 301 project, Phase I: **problem modeling and uninformed search (BFS, DFS, UCS, IDS)**.

Team: Almoatasembellah Aboubakr (202400993), Rabie Al Sayed Mosa (202400113),
Amir Elsamahy (202401724), Ebrahim Mohamed Rabia (202401474), Ahmed Mostafa (202401612).

## The problem in one paragraph

Pac-Man moves through a maze and must eat every food pellet. Ghosts stand still; their
cells cannot be entered, and entering a cell directly next to a ghost costs 5 instead of 1.
A **state** is `(pos, food)`: Pac-Man's cell and a bitmask of the pellets still uneaten.
The **goal** is `food == 0`. **Actions**: UP, RIGHT, DOWN, LEFT. We look for the cheapest
sequence of moves. The three official layouts have 1,016 / 4,160 / 8,576 reachable states,
and on each of them the plan with the fewest moves is not the cheapest plan.

## Requirements

* Python 3 (developed with Python 3.13; also tested with 3.12 and 3.15).
* `main.py` and the unit tests use **only the Python standard library**.
* The figures and animations need Matplotlib: `pip install -r requirements.txt`

All search algorithms are written from scratch; no search library is used.

## How to run

Run every command from inside this `code` folder.

| Command | What it does |
|---|---|
| `python main.py` | BFS, DFS, UCS and IDS on the large layout (table of results) |
| `python main.py --list` | shows the four built-in layouts |
| `python main.py -l small -a ucs --show-path` | one algorithm on one layout; prints the path and draws it in the maze |
| `python main.py -l medium -a bfs dfs` | several algorithms |
| `python main.py --layout-file example_maze.txt` | a maze from a text file (same ASCII symbols as in `layouts.py`) |
| `python run_phase1.py` | ALL Phase I experiments: tables, figures, animations (about 1 minute) |
| `python run_phase1.py --quick` | faster: 3 timing repeats, no animations; writes to `results/phase1_quick` |
| `python -m unittest discover -s tests -v` | 33 unit tests |

`run_phase1.py` writes everything to `results/phase1/`. The submitted folder was produced
by this script, run with Python pinned to one processor core (see "Reproducibility").

| File | Content |
|---|---|
| `metrics.csv` | path cost, steps, nodes generated / expanded, max frontier, max nodes in memory, running time, peak memory, solution path - per layout and algorithm |
| `state_space.csv` | size of the state space of each layout (upper bound, valid, reachable) |
| `tradeoff.csv` | fewest steps versus lowest cost, computed exactly for each layout |
| `state_graph.csv` | shape of the state graph: states per depth, branching factor, and the counts used in the analysis of the running times |
| `ids_iterations.csv` | work done by IDS at every depth limit |
| `ids_variants.csv` | the textbook IDS that we use versus IDS with a memo table |
| `solutions.txt` | every solution path as text, drawn in the maze |
| `summary.md` | the same tables in readable form |
| `results.json` | everything above in one file (used to build the report) |
| `figures/` | layouts, explored states + final path, search trees, bar charts, frontier growth, IDS iterations, scaling |
| `animations/` | animated GIFs of the four searches on the large layout |


## The four algorithms in one line each

| Algorithm | Frontier | Duplicate handling | Goal test |
|---|---|---|---|
| BFS | FIFO queue | set of reached states | when a node is generated |
| DFS | stack | set of explored states | when a node is taken from the frontier |
| UCS | priority queue ordered by path cost g | cheapest known cost per state | when a node is taken from the frontier |
| IDS | depth-limited DFS with limits 0, 1, 2, ... | only the states on the current path (textbook version) | when a node is taken from the stack |

IDS keeps nothing but its stack and the current path, which is what gives it its small
memory. `iterative_deepening_search(problem, use_memo=True)` is an optional variant that
also remembers the states seen in the current iteration: it is several times faster, but
it gives up the memory advantage. `ids_variants.csv` compares the two.

## What is measured (same definitions for every algorithm)

* **nodes generated** - every successor produced (including duplicates that are discarded),
  plus the root (IDS: the root of every iteration)
* **nodes expanded** - nodes whose successors were generated
* **max frontier** - largest number of nodes waiting in the frontier
* **max nodes in memory** - largest value of (frontier size + states remembered by the search)
* **running time** - the fastest of up to 20 repeated runs (`time.perf_counter`, garbage
  collector switched off while timing); the median, mean and standard deviation of the runs
  are stored in `metrics.csv` as well
* **peak memory** - measured in a separate run with `tracemalloc`

All timings are taken before any search is traced for a picture. `main.py` prints the time
of a single run, so its times are a little higher and less steady than those of the tables.


