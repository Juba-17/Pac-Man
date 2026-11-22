"""Builds the Phase II video kit:

    Phase2_Slides.pptx          7 slides (16:9); the spoken text of every slide is in its speaker notes
    Phase2_Video_Script.docx    who says what and when (five speakers, 3:00), with word counts
    slide_figures/*.png         slide-sized versions of the project's figures

Usage (from this folder):  python build_video_kit_phase2.py [output folder]
The default output folder is Phase2/video/preparation of the project.

Every number on the slides and in the spoken text is read from results/phase2/results.json or
recomputed with the project code, and the facts the wording relies on are asserted, so the kit
cannot silently drift from the results. The figures are drawn with the project's own plotting
code (pacman_search.visualize / visualize_phase2); only their size and arrangement are new, so
that the labels stay readable on a slide.
"""
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True          # importing the project code must not leave __pycache__ folders in it

from docbuilder import ACCENT as DOC_ACCENT  # noqa: E402
from docbuilder import SOFT as DOC_SOFT  # noqa: E402
from docbuilder import Doc  # noqa: E402
from slidebuilder import BOTTOM_BODY, LEFT, RIGHT, SOFT, TOP_BODY, WHITE, Deck, W  # noqa: E402
from team import COURSE, LEADER, PROBLEM_TITLE, TEAM, UNIVERSITY  # noqa: E402

CODE = Path(__file__).resolve().parent.parent / "Phase2" / "code"
RESULTS = CODE / "results" / "phase2"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else CODE.parent / "video" / "preparation"
FIG = OUT / "slide_figures"

sys.path.insert(0, str(CODE))
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402
from PIL import ImageFont  # noqa: E402
from pptx.enum.text import PP_ALIGN  # noqa: E402
from pptx.util import Inches  # noqa: E402

from pacman_search import visualize as viz  # noqa: E402
from pacman_search import visualize_phase2 as viz2  # noqa: E402
from pacman_search.heuristics import (  # noqa: E402
    FarthestFoodHeuristic, MazeMSTHeuristic, manhattan, maze_distances_from)
from pacman_search.informed import a_star_search, greedy_best_first_search  # noqa: E402
from pacman_search.layouts import load_problem  # noqa: E402
from pacman_search.local_search import (  # noqa: E402
    TourProblem, genetic_algorithm, hill_climbing, simulated_annealing)
from pacman_search.problem import State  # noqa: E402
from pacman_search.uninformed import uniform_cost_search  # noqa: E402

# =====================================================================================
# 1. The results
# =====================================================================================
data = json.loads((RESULTS / "results.json").read_text(encoding="utf-8"))
L = "large"                                                   # the main layout
SEARCH = {r["algorithm"]: r for r in data["search_metrics"] if r["layout"] == L}
LOCAL = {r["algorithm"]: r for r in data["local_search_summary"] if r["layout"] == L}
HEUR = {r["heuristic"]: r for r in data["heuristic_analysis"] if r["layout"] == L}
LAND = next(r for r in data["landscape"] if r["layout"] == L)
COMP = [r for r in data["comparison"] if r["layout"] == L]
OPT = data["optimum"][L]
SA, GA = data["sa_parameters"], data["ga_parameters"]
SEEDS = data["seeds"]
RUNS = len(SEEDS)
TUNE_RUNS = data["tuning_runs"]

ucs, g1, g2, a1, a2 = (SEARCH[name] for name in ("UCS", "Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)"))
hc, sa, ga = (LOCAL[name] for name in ("Hill Climbing", "Simulated Annealing", "Genetic Algorithm"))
problem = load_problem(L)
REACHABLE = problem.count_reachable_states()
K = problem.num_food
ORDERS = LAND["orders"]
SWAPS = K * (K - 1) // 2
fewer = ucs["nodes_expanded"] / a2["nodes_expanded"]             # how much less work A* (h2) does than UCS
ucs_about = round(ucs["nodes_expanded"], -2)                     # "about 2,800"
guaranteed = [r["algorithm"] for r in COMP if r["optimal_guaranteed"].startswith("yes")]

# ---- facts the wording relies on: fail loudly if the experiments ever change them ----
assert REACHABLE == HEUR["h1"]["states_checked"] == HEUR["h2"]["states_checked"]
for row in data["heuristic_analysis"]:                           # true on all three layouts
    assert row["admissible"] and row["consistent"] and row["h2_dominates_h1"], row
assert HEUR["h1"]["true_cost_start"] == OPT == ucs["path_cost"] == a1["path_cost"] == a2["path_cost"]
assert HEUR["h1"]["h_start"] < HEUR["h2"]["h_start"] < OPT
assert HEUR["h2"]["mean_ratio"] > 0.8 > 0.5 > HEUR["h1"]["mean_ratio"]       # "h2 is close to the true cost"
assert g1["path_cost"] > OPT and g2["path_cost"] > OPT
assert g2["nodes_expanded"] < a2["nodes_expanded"] < a1["nodes_expanded"] < g1["nodes_expanded"] < ucs["nodes_expanded"]
assert abs(ucs["nodes_expanded"] - ucs_about) <= 50              # "about 2,800 nodes"
assert 1000 < a1["nodes_expanded"] <= 1100                       # "just over a thousand"
assert 25.5 <= fewer < 26.5                                      # "26 times fewer"
assert SA == {"start_temperature": 10.0, "cooling_rate": 0.995, "end_temperature": 0.1}   # "half a percent"
assert GA["population_size"] == 30 and GA["generations"] == 30
assert SEEDS == list(range(30)) and data["tuning_seeds"] == [1000, 1299] and TUNE_RUNS == 300
assert sa["best"] == sa["worst"] == ga["best"] == ga["worst"] == OPT and sa["optimal_runs"] == ga["optimal_runs"] == RUNS
assert hc["best"] == OPT < hc["worst"] and hc["optimal_runs"] < RUNS
assert max(sa["mean_evaluations"], ga["mean_evaluations"]) < 1000 and sa["mean_iterations"] == 919
assert ORDERS == 40320 and LAND["stop_orders_local_optimum"] == 0 and LAND["starts_ending_in_local_optimum"] == 0
assert LAND["starts_ending_on_shoulder"] + LAND["starts_ending_in_global_optimum"] == ORDERS
assert guaranteed == ["UCS", "A* (h1)", "A* (h2)"]
for key in ("time_ms", "peak_memory_kib", "memory_items", "effort"):         # "cheapest method with a guarantee":
    others = [r[key] for r in COMP if r["algorithm"] in guaranteed and r["algorithm"] != "A* (h2)"]
    assert 2 * next(r[key] for r in COMP if r["algorithm"] == "A* (h2)") < min(others), key    # by a wide margin
assert all(SEARCH[name]["path_cost"] > OPT for name in ("BFS", "DFS", "IDS", "Greedy (h1)", "Greedy (h2)"))
assert all(r["complete"].startswith("yes") for r in COMP if r["family"] != "local search")
assert [r["algorithm"] for r in COMP][:11] == [
    "BFS", "DFS", "UCS", "IDS", "Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)", "Hill Climbing",
    "Simulated Annealing", "Genetic Algorithm"]
# "entering a cell next to a ghost costs 5 instead of 1": the cost of a move is the cost of the cell that is
# entered, so a move OUT of a danger cell into a normal cell costs 1
assert (problem.normal_cost, problem.danger_cost, len(problem.ghosts)) == (1, 5, 1) and problem.danger_cells
for cell in problem.danger_cells:
    assert problem.enter_cost(cell) == problem.danger_cost
    assert [cost for _, target, cost in problem.neighbors[cell] if target not in problem.danger_cells] \
        and all(cost == problem.normal_cost for _, target, cost in problem.neighbors[cell]
                if target not in problem.danger_cells)
# "found the optimum every time" is a statement about the 30 evaluation seeds only: with the same settings the
# tuning study (other seeds) did not reach the optimum in every run. The script says so.
SA_TUNED = next(r for r in data["tuning_sa"]
                if (r["start_temperature"], r["cooling_rate"]) == (SA["start_temperature"], SA["cooling_rate"]))
GA_TUNED = next(r for r in data["tuning_ga"]
                if (r["population_size"], r["mutation_rate"]) == (GA["population_size"], GA["mutation_rate"]))
assert SA_TUNED["runs"] == GA_TUNED["runs"] == TUNE_RUNS
assert sa["mean_evaluations"] == sa["mean_iterations"] + 1 == SA_TUNED["evaluations"]             # 919 + start order
assert ga["mean_evaluations"] == GA["population_size"] * (GA["generations"] + 1) == GA_TUNED["evaluations"]
# Running times: the fastest of up to 20 identical runs; the Phase I algorithms were measured again in the
# Phase II session, with identical counts and slightly different times (quoted in the script).
PHASE1 = json.loads((CODE.parent.parent / "Phase1" / "code" / "results" / "phase1" / "results.json")
                    .read_text(encoding="utf-8"))
ids_now = SEARCH["IDS"]
ids_then = next(r for r in PHASE1["metrics"] if r["layout"] == L and r["algorithm"] == "IDS")
assert data["timing_repeats"] == PHASE1["timing_repeats"] == 20
assert all(r["time_runs"] <= 20 for r in SEARCH.values()) and ucs["time_runs"] == 20
assert all(ids_now[key] == ids_then[key] for key in ("path_cost", "steps", "nodes_expanded", "nodes_generated"))
# The honest reading of "found the optimum every time": on this layout random sampling with the same budget
# does it too, and only the larger mazes of the scaling experiment separate the methods from it.
BASE = LOCAL[data["baseline_label"]]
BASE_N = data["baseline_evaluations"]
SCALE = {(r["pellets"], r["method"]): r["mean_percent_above_optimum"] for r in data["scaling_methods"]}
K_MAX = max(pellets for pellets, _ in SCALE)
assert BASE["optimal_runs"] == RUNS and abs(BASE_N - sa["mean_evaluations"]) <= 1
assert SCALE[(K_MAX, "Simulated Annealing")] < SCALE[(K_MAX, "Hill Climbing (restarts)")] \
    < SCALE[(K_MAX, "Genetic Algorithm")] < SCALE[(K_MAX, "Random sampling")]
assert SCALE[(K_MAX, "Random sampling")] > 2 * SCALE[(K_MAX, "Simulated Annealing")]


def n(value):
    return f"{value:,.0f}"


# =====================================================================================
# 2. The spoken text
# =====================================================================================
SPEAKERS = [name for name, _, _ in TEAM]
PART_SECONDS = 36                                    # every speaker has the same window: 5 x 36 s = 3:00

SLIDE_TITLES = {
    1: "Title",
    2: "Two heuristics: h1 and h2",
    3: "Greedy Best-First and A* against UCS",
    4: "Local search and Hill Climbing",
    5: "Simulated Annealing and Genetic Algorithm",
    6: "All nine algorithms compared",
    7: "Take-away messages",
}

# (slide, speaker index, seconds on this slide, the sentences that are spoken)
SEGMENTS = [
    (1, 0, 12, [
        "This is Phase Two of our Pac-Man project.",
        # The cost belongs to the cell that is ENTERED (problem.enter_cost): leaving a danger cell costs 1.
        "The model is unchanged: Pac-Man must eat every pellet at the lowest cost, and entering a cell next "
        f"to a ghost costs {problem.danger_cost} instead of {problem.normal_cost}.",
    ]),
    (2, 0, 24, [
        "We designed two heuristics.",
        "h1 is the Manhattan distance to the farthest pellet.",
        "h2 is the maze distance to the nearest pellet, plus the minimum spanning tree that links all "
        "remaining pellets.",
        "Both are admissible and consistent: we proved it and checked every reachable state.",
        "h2 is never smaller than h1, so it dominates.",
    ]),
    (3, 1, 36, [
        "Greedy Best-First follows the heuristic alone.",
        f"With h2 it needs only {g2['nodes_expanded']} expansions, but its path costs {g2['path_cost']} "
        f"instead of {OPT}.",
        f"With h1 it costs {g1['path_cost']}.",
        "So Greedy can be fast, but not optimal.",
        "A* also counts the cost so far, and returns the optimal cost with both heuristics.",
        f"The difference is the work: UCS expands about {n(ucs_about)} nodes, A* with h1 just over a thousand, "
        f"and with h2 only {a2['nodes_expanded']}.",
        "Lighter pictures mean fewer states explored.",
    ]),
    (4, 2, 36, [
        "Local search works on complete solutions.",
        f"Ours is a priority order of the {K} pellets: Pac-Man walks to the next uneaten pellet in that order.",
        "The cost of that walk is the objective, and a neighbour swaps two pellets.",
        "Hill Climbing takes the best swap and stops when none is strictly better.",
        f"Only {hc['optimal_runs']} of {RUNS} runs are optimal.",
        "We checked every order: there is no true local optimum.",
        "The climb stops on plateau shoulders: equal-cost swaps would lead further down, but Hill Climbing "
        "refuses them.",
    ]),
    (5, 3, 36, [
        "Simulated Annealing also accepts worse swaps while it is hot.",
        f"It starts at temperature {SA['start_temperature']:g} and cools by half a percent each iteration.",
        f"The Genetic Algorithm evolves {GA['population_size']} orders for {GA['generations']} generations, "
        "with selection, crossover and mutation.",
        f"Each method ran on {RUNS} fixed seeds.",
        f"These two found the optimum every time: best, average and worst are all {OPT}.",
        f"Hill Climbing has {hc['best']}, {hc['mean']:.1f} and {hc['worst']}.",
        "On a maze this small random sampling does as well; larger mazes show the difference.",
    ]),
    (6, 4, 21, [
        "This chart shows all nine algorithms.",
        f"Only UCS and A* guarantee the optimal cost, {OPT}.",
        "The other search algorithms return costlier paths.",
        "A* with h2 suits this problem best: optimal, complete, and the cheapest method with a guarantee, "
        "because h2 is close to the true cost.",
    ]),
    (7, 4, 15, [
        "Our take-aways.",
        "A good admissible heuristic makes optimal search cheap.",
        "Greedy ignores the path cost, so it gives no guarantee.",
        "Local search needs a way off plateaus, and cannot prove optimality.",
        "Thank you.",
    ]),
]

TAKEAWAYS = {                                        # one sentence per content slide (the bar at the bottom)
    2: "Both heuristics are admissible and consistent; h2 dominates h1 and is much closer to the true cost.",
    3: f"A* with h2 returns the optimal path after {a2['nodes_expanded']} expansions: {fewer:.0f} times fewer "
       "than UCS.",
    4: f"Hill Climbing is cheap but stops on plateaus: only {hc['optimal_runs']} of {RUNS} runs reach the "
       "optimal cost.",
    5: f"Simulated Annealing and the Genetic Algorithm are optimal in all {RUNS} runs - on this small maze so is "
       "random sampling.",
    6: "A* with h2 suits this problem best: optimal, complete and the cheapest method that guarantees the optimum.",
}

VIDEO_TAKEAWAYS = [                                  # the messages of the whole video (slide 7 and the script)
    f"**A good admissible heuristic makes optimal search cheap.** A* with h2 expands {a2['nodes_expanded']} "
    f"nodes, UCS {n(ucs['nodes_expanded'])}, for the same optimal cost.",
    f"**A heuristic alone is not enough.** Greedy Best-First ignores the path cost and returns "
    f"{g1['path_cost']} and {g2['path_cost']} instead of {OPT}.",
    f"**Local search needs a way off plateaus.** Hill Climbing is optimal in {hc['optimal_runs']} of {RUNS} "
    f"runs, the other two in all {sa['optimal_runs']} - like random sampling on this small maze. None can prove "
    "optimality.",
    "**A* with h2 is the best choice for this problem.** It is optimal, complete and the cheapest method that "
    "guarantees the optimum.",
]

ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "- - twenty thirty forty fifty sixty seventy eighty ninety".split()
LETTERS = {"U": "you", "C": "see", "S": "ess", "B": "bee", "F": "eff", "D": "dee", "I": "eye"}


def number_words(value):
    """An integer the way it is read aloud ('2800' -> 'two thousand eight hundred')."""
    if value < 20:
        return ONES[value]
    if value < 100:
        return TENS[value // 10] + ("" if value % 10 == 0 else " " + ONES[value % 10])
    if value < 1000:
        rest = value % 100
        return ONES[value // 100] + " hundred" + ("" if rest == 0 else " and " + number_words(rest))
    rest = value % 1000
    return number_words(value // 1000) + " thousand" + ("" if rest == 0 else " " + number_words(rest))


def read_aloud(text):
    """The text as it is spoken: numbers and abbreviations written out (only used to estimate the time)."""
    spoken = []
    for token in text.split():
        core = token.strip(".,;:!?()")
        if core in ("h1", "h2"):
            spoken.append("aitch " + ("one" if core == "h1" else "two"))
        elif core == "A*":
            spoken.append("ay star")
        elif re.fullmatch(r"[\d,]+", core):
            spoken.append(number_words(int(core.replace(",", ""))))
        elif re.fullmatch(r"\d+\.\d+", core):
            whole, fraction = core.split(".")
            spoken.append(number_words(int(whole)) + " point " + " ".join(ONES[int(d)] for d in fraction))
        elif core in ("UCS", "BFS", "DFS", "IDS"):
            spoken.append(" ".join(LETTERS[letter] for letter in core))
        else:
            spoken.append(core)
    return " ".join(spoken).replace("-", " ")


def syllables(text):
    """Rough number of syllables of an English text (vowel groups per word)."""
    total = 0
    for word in read_aloud(text).split():
        word = re.sub(r"[^a-z]", "", word.lower())
        if not word:
            continue
        count = len(re.findall(r"[aeiouy]+", word))
        if word.endswith("e") and not word.endswith(("le", "ee", "ie")) and count > 1:
            count -= 1
        if word.endswith("ed") and not word.endswith(("ted", "ded", "hundred")) and count > 1:
            count -= 1
        total += max(count, 1)
    return total


def word_count(text):
    """Words as a word processor counts them. The text must not contain free-standing dashes."""
    tokens = text.split()
    assert all(re.search(r"[A-Za-z0-9]", token) for token in tokens), text
    return len(tokens)


def clock(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"


# ---- timetable and word counts ----
TIMETABLE = []                                       # (slide, speaker index, start, end, text, words)
elapsed = 0
for slide_no, speaker, seconds, sentences in SEGMENTS:
    text = " ".join(sentences)
    TIMETABLE.append((slide_no, speaker, elapsed, elapsed + seconds, text, word_count(text)))
    elapsed += seconds
TOTAL_SECONDS = elapsed
WORDS = [sum(row[5] for row in TIMETABLE if row[1] == index) for index in range(len(SPEAKERS))]
TOTAL_WORDS = sum(WORDS)
SPOKEN = {row[0]: row[4] for row in TIMETABLE}

assert TOTAL_SECONDS == 180 and [row[0] for row in TIMETABLE] == list(range(1, 8))
assert [row[1] for row in TIMETABLE] == sorted(row[1] for row in TIMETABLE), "speakers must keep the team order"
for index in range(len(SPEAKERS)):
    assert sum(row[3] - row[2] for row in TIMETABLE if row[1] == index) == PART_SECONDS

# The limits: 400-430 words in total, and nobody has to rush. Numbers and abbreviations take longer to
# say than their word count suggests, so the pace is also checked in syllables of the read-aloud form
# (3.5 to 3.9 syllables per second is an ordinary presentation pace, about 150 spoken words a minute).
print(f"{'slide':5s} {'time':11s} {'speaker':27s} {'words':>5s} {'words/s':>8s} {'syllables':>9s} {'syll/s':>7s}")
pace_problems = []
for slide_no, speaker, start_s, end_s, text, words in TIMETABLE:
    rate = syllables(text) / (end_s - start_s)
    print(f"{slide_no:<5d} {clock(start_s)}-{clock(end_s):6s} {SPEAKERS[speaker]:27s} {words:5d} "
          f"{words / (end_s - start_s):8.2f} {syllables(text):9d} {rate:7.2f}")
    if not 3.3 <= rate <= 3.9:
        pace_problems.append(f"slide {slide_no}")
SYLLABLES = [sum(syllables(row[4]) for row in TIMETABLE if row[1] == index) for index in range(len(SPEAKERS))]
for index, name in enumerate(SPEAKERS):
    rate = SYLLABLES[index] / PART_SECONDS
    print(f"      {name:27s} {WORDS[index]:5d} words in {PART_SECONDS} s = {WORDS[index] / PART_SECONDS:.2f} words/s, "
          f"about {SYLLABLES[index]} syllables = {rate:.2f} per second")
    if not (73 <= WORDS[index] <= 92 and 3.4 <= rate <= 3.85):   # the five parts take about the same time
        pace_problems.append(name)
print(f"      total {TOTAL_WORDS} words, about {sum(SYLLABLES)} syllables, {clock(TOTAL_SECONDS)}")
assert not pace_problems, pace_problems
assert 400 <= TOTAL_WORDS <= 430, TOTAL_WORDS

# The same text as it is pronounced ("h2" is two words, "2,800" four, "Best-First" two). This is the real
# speaking rate; the script prints it next to the written count, so that nobody mistakes 136 written words
# a minute for a slow pace.
READ_ALOUD_WORDS = sum(len(read_aloud(row[4]).split()) for row in TIMETABLE)
READ_ALOUD_RATE = READ_ALOUD_WORDS / (TOTAL_SECONDS / 60)
print(f"      read aloud: {READ_ALOUD_WORDS} words = {READ_ALOUD_RATE:.0f} per minute")
assert 435 <= READ_ALOUD_WORDS <= 464 and 145 <= READ_ALOUD_RATE < 155        # "about 450 words, about 150 a minute"

# Two sentences only repeat what their slide shows (the caption of slide 3, the table of slide 5). The script
# names them as the ones to leave out if a rehearsal still runs over 3:00; section 4 checks that the slides
# really show the same information.
OPTIONAL = {3: "Lighter pictures mean fewer states explored.",
            5: f"Hill Climbing has {hc['best']}, {hc['mean']:.1f} and {hc['worst']}."}
assert SEGMENTS[2][0] == 3 and SEGMENTS[2][3][-1] == OPTIONAL[3]
assert SEGMENTS[4][0] == 5 and OPTIONAL[5] in SEGMENTS[4][3]

# =====================================================================================
# 3. Slide-sized figures (the project's plotting code, new arrangement)
# =====================================================================================
DPI = 300
ZOOM = 1.5              # the figures are drawn small and shown 1.5 times larger: 8 pt labels become 12 pt
BODY_W = W - LEFT - RIGHT                                        # usable width of a slide (inches)
FULL_W = BODY_W / ZOOM                                           # drawing width of a full-width figure

FIG.mkdir(parents=True, exist_ok=True)


def save_white(fig, path, tight=False):
    """Save a figure on a white background (the slides are white)."""
    fig.patch.set_facecolor("white")
    for ax in fig.axes:
        ax.set_facecolor("white")
    if tight:
        fig.savefig(path, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.04)
    else:
        fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)
    return path


def symbols(path_label=None):
    """The project's legend entries for the maze symbols; the path entry is renamed or left out."""
    handles = viz.symbol_handles(with_path=path_label is not None)
    if path_label is not None:
        handles[-1].set_label(path_label)
    return handles


def maze_row(panels, path, panel_in, gap=0.13, side=0.06, colorbar=None, legend=None, legend_cols=6,
             footnote=None):
    """A row of maze pictures, drawn with the project's draw_maze() and draw_path().

    panels   list of dictionaries: heading, notes (list of lines), heat ({cell: count}), states (a
             solution path), label_food, overlay (function(ax) that draws more paths)
    legend   list of legend handles (None = no legend); footnote = one line of text under the mazes
    """
    viz.apply_style()
    crop = viz.BORDER_CROP
    panel_h = panel_in * (problem.height - 2 * crop) / (problem.width - 2 * crop)
    note_lines = max(len(panel.get("notes", [])) for panel in panels)
    has_heading = any(panel.get("heading") for panel in panels)
    head = (0.22 if has_heading else 0.0) + 0.17 * note_lines + (0.07 if has_heading or note_lines else 0.0)
    bar_h = 0.46 if colorbar else 0.0
    foot_h = 0.22 if footnote else 0.0
    legend_rows = -(-len(legend) // legend_cols) if legend else 0
    legend_h = (0.1 + 0.19 * legend_rows) if legend else 0.04
    top = 0.03
    fig_w = 2 * side + len(panels) * panel_in + (len(panels) - 1) * gap
    fig_h = top + head + panel_h + bar_h + foot_h + legend_h
    fig = plt.figure(figsize=(fig_w, fig_h))
    heat_max = max([max(panel["heat"].values()) for panel in panels if panel.get("heat")] + [1])
    small = panel_in < 2.1                                       # small mazes: no fine print inside the cells
    text_scale = min(1.0, max(0.6, panel_in / 2.3))              # the letters P and G follow the panel size
    for index, panel in enumerate(panels):
        left = side + index * (panel_in + gap)
        ax = fig.add_axes([left / fig_w, 1 - (top + head + panel_h) / fig_h, panel_in / fig_w, panel_h / fig_h])
        viz.draw_maze(ax, problem, heat=panel.get("heat"), heat_max=heat_max if panel.get("heat") else None,
                      label_food=panel.get("label_food", False))
        for label in ax.texts:
            label.set_fontsize(label.get_fontsize() * text_scale)
            if small and label.get_text() == str(problem.danger_cost):
                label.set_visible(False)                         # the legend says what a red frame costs
        if panel.get("overlay"):
            drawn = len(ax.lines)
            panel["overlay"](ax)
            for line in ax.lines[drawn:]:                        # keep the pellets visible on top of these lines
                line.set_zorder(3.2 + line.get_zorder() / 20)
        if panel.get("states"):
            viz.draw_path(ax, panel["states"], number_food=False)
        y = top + 0.17
        if panel.get("heading"):
            fig.text(left / fig_w, 1 - y / fig_h, panel["heading"], fontsize=11, fontweight="bold",
                     ha="left", va="baseline")
            y += 0.19
        for note in panel.get("notes", []):
            fig.text(left / fig_w, 1 - y / fig_h, note, fontsize=8.5, color=viz.INK_SOFT, ha="left", va="baseline")
            y += 0.17
    if colorbar:
        bar_w = min(3.6, fig_w * 0.5)
        cax = fig.add_axes([(fig_w - bar_w) / 2 / fig_w, (legend_h + foot_h + 0.3) / fig_h, bar_w / fig_w,
                            0.08 / fig_h])
        bar = fig.colorbar(ScalarMappable(norm=Normalize(0, heat_max), cmap=viz.HEAT), cax=cax,
                           orientation="horizontal")
        bar.outline.set_visible(False)
        bar.ax.tick_params(labelsize=7.5, length=2)
        bar.ax.xaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
        bar.set_label(colorbar, fontsize=8, color=viz.INK_SOFT, labelpad=2)
    if footnote:
        fig.text(side / fig_w, (legend_h + 0.05) / fig_h, footnote, fontsize=8.5, color=viz.INK_SOFT, ha="left",
                 va="baseline")
    if legend:
        fig.legend(handles=legend, loc="lower center", ncol=min(legend_cols, len(legend)), fontsize=8,
                   bbox_to_anchor=(0.5, 0.0), handlelength=1.5, columnspacing=1.1, borderaxespad=0.2)
    return save_white(fig, path)


def as_states(cells):
    """Cells as a list of states, the form in which draw_path() takes a path."""
    return [State(cell, 0) for cell in cells]


def step_path(source, target):
    """Cells of one shortest walk (counted in steps) from source to target."""
    distance = maze_distances_from(problem, source)
    cells = [target]
    while cells[-1] != source:
        cells.append(next(cell for _, cell, _ in problem.neighbors[cells[-1]]
                          if distance[cell] == distance[cells[-1]] - 1))
    return cells[::-1]


def project_figure(module, function, *args, **kwargs):
    """Call one of the project's plot functions, but get the open figure back instead of an image file."""
    original = module.save_figure
    module.save_figure = lambda fig, path, dpi=200: fig
    try:
        return function(*args, **kwargs)
    finally:
        module.save_figure = original


# ---- the runs behind the pictures: recomputed with the project code and compared with results.json ----
h1, h2 = FarthestFoodHeuristic(problem), MazeMSTHeuristic(problem)
start = problem.initial_state
traced = {
    "UCS": uniform_cost_search(problem, trace=True),
    "Greedy (h1)": greedy_best_first_search(problem, h1, trace=True),
    "Greedy (h2)": greedy_best_first_search(problem, h2, trace=True),
    "A* (h1)": a_star_search(problem, h1, trace=True),
    "A* (h2)": a_star_search(problem, h2, trace=True),
}
for name, result in traced.items():
    assert (result.path_cost, result.nodes_expanded) == (SEARCH[name]["path_cost"], SEARCH[name]["nodes_expanded"]), name
tour = TourProblem(problem)
local_runs = {
    "Hill Climbing": [hill_climbing(tour, seed=seed) for seed in SEEDS],
    "Simulated Annealing": [simulated_annealing(tour, seed=seed, **SA) for seed in SEEDS],
    "Genetic Algorithm": [genetic_algorithm(tour, seed=seed, **GA) for seed in SEEDS],
}
for name, runs in local_runs.items():
    costs = [run.cost for run in runs]
    assert (min(costs), max(costs), costs.count(OPT)) == (LOCAL[name]["best"], LOCAL[name]["worst"],
                                                          LOCAL[name]["optimal_runs"]), name
    assert round(sum(costs) / len(costs), 2) == LOCAL[name]["mean"], name

# ---- slide 1: the maze ----
maze_png = maze_row([{"label_food": True}], FIG / "slide1_maze_large.png", panel_in=2.2,
                    legend=symbols()[:4], legend_cols=2)

# ---- slide 2: what the two heuristics measure in the start state ----
assert (h1(start), h2(start)) == (HEUR["h1"]["h_start"], HEUR["h2"]["h_start"])
farthest = max(problem.food_cells, key=lambda cell: manhattan(problem.start, cell))
(row0, col0), (row1, col1) = problem.start, farthest
assert row1 >= row0 and col1 >= col0
straight = [(row0, col) for col in range(col0, col1 + 1)] + [(row, col1) for row in range(row0 + 1, row1 + 1)]
assert len(straight) - 1 == manhattan(problem.start, farthest) == h1(start)
assert any(cell in problem.walls for cell in straight)           # the straight walk really ignores a wall
nearest = min(range(K), key=lambda index: h2.steps[index][problem.start])
nearest_steps = h2.steps[nearest][problem.start]
in_tree, tree_edges = {0}, []                                    # Prim's algorithm again, keeping the edges
while len(in_tree) < K:
    a, b = min(((i, j) for i in in_tree for j in range(K) if j not in in_tree),
               key=lambda pair: h2.between[pair[0]][pair[1]])
    in_tree.add(b)
    tree_edges.append((a, b))
tree_steps = sum(h2.between[a][b] for a, b in tree_edges)
assert tree_steps == h2.mst_weight(problem.all_food) and nearest_steps + tree_steps == h2(start)


def draw_h1(ax):
    viz.draw_path(ax, as_states(straight), color=viz.BLUE, lane=0.0, number_food=False, arrows=False)


def draw_h2(ax):
    for a, b in tree_edges:
        viz.draw_path(ax, as_states(step_path(problem.food_cells[a], problem.food_cells[b])), color=viz.BLUE,
                      lane=0.0, number_food=False, arrows=False)
    viz.draw_path(ax, as_states(step_path(problem.start, problem.food_cells[nearest])), color=viz.AQUA,
                  lane=0.0, number_food=False, arrows=False)


heuristics_png = maze_row([
    {"heading": f"h1 = {h1(start)}", "notes": ["straight to the farthest pellet,", "walls ignored"],
     "overlay": draw_h1},
    {"heading": f"h2 = {nearest_steps} + {tree_steps} = {h2(start)}",
     "notes": [f"nearest pellet: {nearest_steps} steps (green)", f"+ spanning tree: {tree_steps} steps (blue)"],
     "overlay": draw_h2},
], FIG / "slide2_heuristics_start_state.png", panel_in=1.9,
    footnote=f"The true cost from this start state is {OPT}.")


# ---- slide 3: explored states and returned path, with UCS as the baseline ----
def explored_panel(result, heading=None):
    quality = "optimal" if result.path_cost == OPT else "not optimal"
    return {"heading": heading or result.algorithm,
            "notes": [f"cost {result.path_cost:g} ({quality})", f"{result.nodes_expanded:,} nodes expanded"],
            "heat": viz.expanded_per_cell(result), "states": result.states}


explored_png = maze_row(
    [explored_panel(traced["UCS"], "UCS (Phase I)")] + [explored_panel(traced[name]) for name in list(traced)[1:]],
    FIG / "slide3_explored_ucs_greedy_astar.png", panel_in=(FULL_W - 2 * 0.06 - 4 * 0.12) / 5, gap=0.12,
    colorbar="distinct states expanded on the cell (white = none)", legend=symbols("returned path"))

# ---- slide 4: an optimal order and the order where a hill-climbing run stopped ----
stuck = max(local_runs["Hill Climbing"], key=lambda run: run.cost)
best_order = next(run for run in local_runs["Simulated Annealing"] if run.cost == OPT)
best_states, best_cost = problem.execute(best_order.actions)
stuck_states, stuck_cost = problem.execute(stuck.actions)
assert best_cost == OPT and stuck_cost == stuck.cost == hc["worst"]
assert min(tour.cost(order) for order in tour.neighbours(stuck.order)) >= stuck.cost     # no swap is better
routes_png = maze_row([
    {"heading": "An optimal order", "notes": [f"cost {best_cost}"], "states": best_states},
    {"heading": "Where one climb stopped", "notes": [f"cost {stuck_cost}: no swap is strictly better"],
     "states": stuck_states},
], FIG / "slide4_routes_optimal_and_stuck.png", panel_in=1.9,
    legend=[Line2D([], [], color=viz.ORANGE, linewidth=2, label="the walk that the order produces")])

# ---- slide 5: convergence, drawn by the project's plot_convergence() at slide size ----
fig = project_figure(viz2, viz2.plot_convergence, local_runs, OPT, None)
fig.set_size_inches(FULL_W, 2.2)
fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.0)
convergence_png = save_white(fig, FIG / "slide5_convergence_large.png", tight=True)


# ---- slide 6: all nine algorithms (panels of the project's summary chart, in one row) ----
def summary_row(rows, path):
    viz.apply_style()
    labels = [row["algorithm"] for row in rows]
    colors = [viz2.FAMILY_COLOR[row["family"]] for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 2.95))
    ends = [row["cost_range"][1] if row.get("cost_range") else row["cost"] for row in rows]
    viz.bar_panel(axes[0], labels, [row["cost"] for row in rows], f"Solution cost (line = optimal, {OPT:g})",
                  "{:,.1f}", color=colors, reference=OPT, label_from=ends)
    for position, row in enumerate(rows):                        # best-to-worst whisker of the random methods
        if row.get("cost_range"):
            axes[0].plot(row["cost_range"], [position, position], color=viz.INK, linewidth=1.1, zorder=4,
                         marker="|", markersize=5)
    viz.bar_panel(axes[1], labels, [row["time_ms"] for row in rows], "Running time (ms)", "{:,.2f}", color=colors)
    viz.bar_panel(axes[2], labels, [row["peak_memory_kib"] for row in rows], "Peak memory (KiB)", "{:,.0f}",
                  color=colors)
    for ax in axes[1:]:
        ax.set_yticklabels([])
    for label in axes[0].get_yticklabels():                      # the methods that guarantee the optimum
        if label.get_text() in guaranteed:
            label.set_fontweight("bold")
            label.set_color(viz.INK)
    handles = [Patch(facecolor=color, edgecolor="none", label=family) for family, color in viz2.FAMILY_COLOR.items()
               if family != "baseline"]            # the slide chart has no baseline row
    handles.append(Line2D([], [], color=viz.INK, linewidth=1.1, marker="|", markersize=5,
                          label=f"local search: bar = mean, line = best to worst of {RUNS} runs"))
    handles.append(Line2D([], [], linestyle="none", label="bold name = optimal cost guaranteed"))
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=8, bbox_to_anchor=(0.5, -0.01),
               columnspacing=1.2, handlelength=1.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1), w_pad=1.0)
    return save_white(fig, path, tight=True)


summary_png = summary_row(COMP[:11], FIG / "slide6_summary_all_nine.png")

# =====================================================================================
# 4. The slides
# =====================================================================================
FONT_FILES = {False: r"C:\Windows\Fonts\calibri.ttf", True: r"C:\Windows\Fonts\calibrib.ttf"}
FONTS = {bold: ImageFont.truetype(path, 1000) for bold, path in FONT_FILES.items()}


def text_width(text, size, bold=False):
    """Width in inches of one line of Calibri text; '**' switches bold on and off as on the slides."""
    width = 0.0
    for index, piece in enumerate(text.split("**")):
        width += FONTS[bold or index % 2 == 1].getlength(piece) / 1000 * size / 72
    return width


def wrapped_lines(text, size, width, bold=False):
    """Number of lines the text needs in a box of the given width (greedy word wrap, a little pessimistic)."""
    lines, line = 1, ""
    for word in text.split(" "):
        candidate = (line + " " + word).strip()
        if line and text_width(candidate, size, bold) > width * 0.97:
            lines, line = lines + 1, word
        else:
            line = candidate
    return lines


BULLET = chr(8226) + "  "                            # what the deck writes in front of every bullet


def bullets_fit(bullets, size, width, height):
    """True if a list of bullets fits into its text box (the box keeps 0.1 inch of inner margin on each side)."""
    lines = sum(wrapped_lines(BULLET + bullet, size, width - 0.2 - text_width(BULLET, size)) for bullet in bullets)
    return lines * size * 1.2 / 72 + len(bullets) * 9 / 72 + 0.1 <= height


def hang_bullets(slide, size):
    """Give the bullets of a slide a hanging indent: wrapped lines start under the text, not under the dot."""
    indent = int(Inches(text_width(BULLET, size)))
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.startswith(BULLET.strip()):
            for paragraph in shape.text_frame.paragraphs:
                properties = paragraph._p.get_or_add_pPr()
                properties.set("marL", str(indent))
                properties.set("indent", str(-indent))


def tag(slide_no):
    _, speaker, start_s, end_s, _, _ = TIMETABLE[slide_no - 1]
    return f"{SPEAKERS[speaker]}  |  {clock(start_s)}-{clock(end_s)}"


for slide_no in range(2, 8):                                     # layout guards: these must stay on one line
    assert text_width(SLIDE_TITLES[slide_no], 30, bold=True) <= BODY_W - 3.4 - 0.1, SLIDE_TITLES[slide_no]
    assert text_width(tag(slide_no), 13) <= 3.4 - 0.1, tag(slide_no)
for sentence in TAKEAWAYS.values():
    assert text_width(sentence, 16, bold=True) <= BODY_W - 0.4 - 0.1, sentence
for item in VIDEO_TAKEAWAYS:
    assert wrapped_lines(item, 19, BODY_W - 1.2 - 0.1) <= 2, item

deck = Deck(f"{COURSE}  |  Pac-Man Food Collection  |  Phase II video")

# ---- slide 1: title, team, the maze ----
slide = deck.title_slide(PROBLEM_TITLE,
                         "Phase II: heuristic search, local search and the comparison of all nine algorithms",
                         [], note=SPOKEN[1])
deck._text(slide, W - RIGHT - 4.0, 0.3, 4.0, 0.4, tag(1), size=13, color=WHITE, align=PP_ALIGN.RIGHT)
deck._text(slide, 0.9, 3.15, 7.4, 0.4, f"{COURSE}  |  {UNIVERSITY}", size=16, color=SOFT)
top = 3.7
for name, student_id, _ in TEAM:
    deck._text(slide, 0.9, top, 5.6, 0.45, name + ("  (team leader)" if name == LEADER else ""), size=20)
    deck._text(slide, 6.5, top, 1.8, 0.45, student_id, size=20, color=SOFT)
    top += 0.5
model_line = (f"Same model as in Phase I: eat every pellet at the lowest cost. A step costs {problem.normal_cost}, "
              f"or {problem.danger_cost} into a cell next to the ghost.")
assert wrapped_lines(model_line, 18, 7.5) <= 2
deck._text(slide, 0.9, 6.4, 7.6, 0.8, model_line, size=18, color=SOFT)
deck._picture(slide, maze_png, 8.75, 3.1, 3.95, 4.25)

# ---- slide 2: the two heuristics ----
bullets = [
    "**h1** = Manhattan distance to the **farthest** pellet",
    "**h2** = maze distance to the **nearest** pellet + minimum spanning tree over the remaining pellets",
    f"Both **admissible** and **consistent**: proved, and checked on all {n(REACHABLE)} reachable states",
    f"**h2 \u2265 h1** in every state: h2 dominates. On average h1 gives {HEUR['h1']['mean_ratio'] * 100:.0f}% of "
    f"the true cost, h2 {HEUR['h2']['mean_ratio'] * 100:.0f}%",
]
HALF = BODY_W * 0.5 - 0.3                                        # width of the text next to a half-width picture
assert bullets_fit(bullets, 20, HALF, BOTTOM_BODY - TOP_BODY - 0.1)
slide = deck.bullets_slide(SLIDE_TITLES[2], bullets, speaker=tag(2), takeaway=TAKEAWAYS[2], note=SPOKEN[2],
                           image=heuristics_png, image_share=0.5, size=20)
hang_bullets(slide, 20)

# ---- slide 3: Greedy and A*, explored states and returned path ----
caption = (f"Large layout, {n(REACHABLE)} reachable states. The five pictures share one colour scale: "
           "the lighter a maze, the fewer states were explored.")
assert text_width(caption, 13) <= BODY_W - 0.1
assert "the lighter a maze, the fewer states were explored" in caption       # what OPTIONAL[3] repeats
deck.figure_slide(SLIDE_TITLES[3], explored_png, caption=caption, speaker=tag(3), takeaway=TAKEAWAYS[3],
                  note=SPOKEN[3])

# ---- slide 4: local-search formulation and hill climbing ----
bullets = [
    f"**Solution**: a priority order of the {K} pellets",
    "**Objective**: the cost of the walk that follows the order",
    f"**Neighbour**: the same order with two pellets swapped ({SWAPS} swaps)",
    "**Hill Climbing**: take the best swap; stop when none is strictly better",
    f"Checked all {n(ORDERS)} orders: **no true local optimum**; it stops on plateau **shoulders**",
]
assert sum(wrapped_lines(BULLET + bullet, 20, HALF - 0.2 - text_width(BULLET, 20)) for bullet in bullets) <= 9
assert bullets_fit(bullets, 20, HALF, BOTTOM_BODY - TOP_BODY - 0.1)
slide = deck.bullets_slide(SLIDE_TITLES[4], bullets, speaker=tag(4), takeaway=TAKEAWAYS[4], note=SPOKEN[4],
                           image=routes_png, image_share=0.5, size=20)
hang_bullets(slide, 20)

# ---- slide 5: simulated annealing and the genetic algorithm (convergence plot above a small table) ----
TABLE_ROW, TABLE_SIZE = 0.37, 15
table_headers = ["Algorithm", f"Parameters (chosen on {TUNE_RUNS} separate seeds)", "Best / mean / worst cost",
                 "Optimal runs"]
table_rows = [
    ["Hill Climbing", "none: random start, best swap until no swap is better",
     f"{hc['best']} / {hc['mean']:.2f} / {hc['worst']}", f"{hc['optimal_runs']} of {RUNS}"],
    ["Simulated Annealing",
     f"temperature {SA['start_temperature']:g} \u2192 {SA['end_temperature']:g}, \u00d7 {SA['cooling_rate']:g} "
     "per iteration",
     f"{sa['best']} / {sa['mean']:.2f} / {sa['worst']}", f"{sa['optimal_runs']} of {RUNS}"],
    ["Genetic Algorithm",
     f"population {GA['population_size']}, {GA['generations']} generations, crossover {GA['crossover_rate']:g}, "
     f"mutation {GA['mutation_rate']:g}",
     f"{ga['best']} / {ga['mean']:.2f} / {ga['worst']}", f"{ga['optimal_runs']} of {RUNS}"],
]
assert table_rows[0][0] == "Hill Climbing" and table_rows[0][2] == f"{hc['best']} / {hc['mean']:.2f} / {hc['worst']}"
table_widths = [2.55, 5.5, 2.5, 1.58]                            # (the row above is what OPTIONAL[5] repeats)
assert abs(sum(table_widths) - BODY_W) < 0.01
for column, width in enumerate(table_widths):                    # no cell may wrap onto a second line
    assert text_width(table_headers[column], TABLE_SIZE, bold=True) <= width - 0.2, table_headers[column]
    for row in table_rows:
        assert text_width(row[column], TABLE_SIZE) <= width - 0.2, row[column]
table_h = TABLE_ROW * (len(table_rows) + 1)
slide = deck.table_slide(SLIDE_TITLES[5], table_headers, table_rows, speaker=tag(5), takeaway=TAKEAWAYS[5],
                         note=SPOKEN[5], col_widths=table_widths, size=TABLE_SIZE, row_height=TABLE_ROW)
table_shape = next(shape for shape in slide.shapes if shape.has_table)
table_shape.top = Inches(BOTTOM_BODY - table_h)                  # the table sits at the bottom, the plot above it
deck._picture(slide, convergence_png, LEFT, TOP_BODY, BODY_W, BOTTOM_BODY - table_h - 0.08 - TOP_BODY)

# ---- slide 6: all nine algorithms ----
caption = ("Large layout. Bold names guarantee the optimal cost. All search algorithms are complete here; local "
           "search always returns a valid plan but cannot prove optimality.")
assert text_width(caption, 13) <= BODY_W - 0.1
deck.figure_slide(SLIDE_TITLES[6], summary_png, caption=caption, speaker=tag(6), takeaway=TAKEAWAYS[6],
                  note=SPOKEN[6])

# ---- slide 7: take-away messages ----
deck.takeaways_slide(SLIDE_TITLES[7], VIDEO_TAKEAWAYS, speaker=tag(7), note=SPOKEN[7])

deck.save(OUT / "Phase2_Slides.pptx")
print("written", OUT / "Phase2_Slides.pptx")

# =====================================================================================
# 5. The script
# =====================================================================================
change_1, change_2 = clock(TIMETABLE[0][3]), clock(TIMETABLE[5][3])
NBSP = chr(160)                                      # a space at which a line may not be broken
parts = []                                           # "Rabie 0:36 (slide 3)", one entry per speaker
for index, name in enumerate(SPEAKERS):
    own = [row for row in TIMETABLE if row[1] == index]
    label = f"slide {own[0][0]}" if len(own) == 1 else f"slides {own[0][0]}-{own[-1][0]}"
    parts.append(f"{name.split()[0]} {clock(own[0][2])} ({label})")

doc = Doc(margins_cm=1.4, body_pt=10)                # page 1 = how to record + the whole script table
doc.para("Phase II video: recording script", size=17, bold=True, color=DOC_ACCENT, space_after=1)
doc.para(f"{COURSE}  |  {PROBLEM_TITLE}  |  3 minutes, {len(TIMETABLE)} slides, {len(SPEAKERS)} speakers  |  "
         "use with `Phase2_Slides.pptx`", size=9.5, color=DOC_SOFT, space_after=5)
doc.callout([
    f"**How to record (one sitting, total {clock(TOTAL_SECONDS)})**",
    "**What is asked.** A 3-minute video showing the heuristic and local search results and the final "
    "comparison. It is graded on being a clear presentation with clear take-away messages.",
    f"**Who speaks when.** Five parts in the team order, {PART_SECONDS} seconds each: {', '.join(parts)}. The "
    "time window is also printed at the top right of every slide. Everyone appears or speaks: each member reads "
    "their own part.",
    "**Recording.** Open `Phase2_Slides.pptx`, start the slide show (F5) and record the screen and the voices in "
    f"one take. Change the slide when its text is finished (slide 1 to 2 at {change_1}, slide 6 to 7 at "
    f"{change_2}). Save the recording in the `video` folder.",
    "**What to say.** Read the text below as it is written; it is also in the speaker notes of each slide. Say "
    "\"h one\", \"h two\" and \"A star\".",
    "**One take-away per slide.** It is the sentence in the bar at the bottom of slides 2 to 6; slide 7 lists "
    "the take-aways of the whole video. Do not add other points.",
    f"**Rehearse once with a timer.** A part should take about {PART_SECONDS} seconds (33 to 38). If the total "
    f"passes {clock(TOTAL_SECONDS)}, speak a little faster. If that is not enough, leave out the last sentence of "
    "slide 3 or the Hill Climbing sentence of slide 5: both only repeat what is on the slide.",
])
rows = []
for slide_no, speaker, start_s, end_s, text, words in TIMETABLE:
    rows.append([f"{clock(start_s)}-{clock(end_s)}", SPEAKERS[speaker], f"{slide_no}. {SLIDE_TITLES[slide_no]}",
                 f"{text}  __({words}{NBSP}words)__"])
doc.table(["Time", "Speaker", "Slide", "What to say (exact spoken text)"], rows, widths_cm=[1.8, 3.3, 2.6, 10.5],
          size=9.5, keep_together=True)
words_line = ("**Words per speaker:** "
              + ", ".join(f"{name.split()[0]} {count}" for name, count in zip(SPEAKERS, WORDS))
              + f". **Total: {TOTAL_WORDS} words** as written. Read aloud, with numbers, h2 and A* in full, it is "
              f"about {round(READ_ALOUD_WORDS, -1)} words, or {round(READ_ALOUD_RATE, -1):.0f} a minute: a steady pace "
              "with no spare time.")
assert wrapped_lines(words_line, 9.5, doc.text_width_cm / 2.54) <= 2     # a third line would not fit on page 1
doc.para(words_line, size=9.5, space_after=6)
doc.para("Take-away messages of the video", size=12, bold=True, color=DOC_ACCENT, space_after=3,
         keep_with_next=True)
doc.numbered(VIDEO_TAKEAWAYS, size=10)

doc.para("Where the numbers come from", size=12, bold=True, color=DOC_ACCENT, space_before=8, space_after=2,
         keep_with_next=True)
doc.para("Every number was checked against `code/results/phase2/results.json` (large layout unless stated). "
         "Numbers after \"about\" or \"just over\" are rounded; the slides show the exact values. Node counts and "
         "costs are exact and reproducible. A running time is the fastest of repeated identical runs (up to "
         f"{data['timing_repeats']} for a search algorithm) and still differs a little between sessions: "
         f"BFS, DFS, UCS and IDS were measured again for Phase II, so slide 6 shows IDS at {ids_now['time_ms']:.0f} ms "
         f"where the Phase I results say {ids_then['time_ms']:.0f} ms.",
         size=9.5, color=DOC_SOFT, space_after=3, keep_with_next=True)
metrics, summary = "`search_metrics`", "`local_search_summary`"
doc.table(
    ["Said in the video", "Exact value", "Source in results.json"],
    [
        [f"entering a cell next to a ghost costs {problem.danger_cost} instead of {problem.normal_cost}",
         f"{problem.danger_cost} and {problem.normal_cost}; the cost belongs to the cell that is entered",
         "the model: `DANGER_COST`, `STEP_COST`, `enter_cost()` in `problem.py`"],
        ["admissible and consistent, checked on every reachable state; h2 never smaller than h1",
         f"large layout: {n(REACHABLE)} states and {n(HEUR['h1']['transitions_checked'])} transitions; the small "
         "and medium layouts pass the same check",
         "`heuristic_analysis`: admissible, consistent, h2_dominates_h1"],
        [f"Greedy with h2: {g2['nodes_expanded']} expansions, cost {g2['path_cost']}; with h1: cost "
         f"{g1['path_cost']}", f"{g2['nodes_expanded']}, {g2['path_cost']}, {g1['path_cost']}",
         f"{metrics}: Greedy (h2), Greedy (h1)"],
        [f"the optimal cost, {OPT}", f"{OPT}", f"`optimum`; {metrics}: UCS, A* (h1), A* (h2)"],
        [f"UCS about {n(ucs_about)} nodes; A* with h1 just over a thousand; with h2 only {a2['nodes_expanded']}",
         f"{n(ucs['nodes_expanded'])}; {n(a1['nodes_expanded'])}; {a2['nodes_expanded']} "
         f"({fewer:.1f} times fewer than UCS)", f"{metrics}: nodes_expanded"],
        [f"{K} pellets; every order checked; no true local optimum",
         f"{n(ORDERS)} orders, {LAND['stop_orders_local_optimum']} local optima, "
         f"{n(LAND['stop_orders_shoulder'])} shoulder orders",
         "`landscape`: orders, stop_orders_local_optimum, stop_orders_shoulder"],
        [f"only {hc['optimal_runs']} of {RUNS} runs are optimal; Hill Climbing has {hc['best']}, "
         f"{hc['mean']:.1f} and {hc['worst']}",
         f"{hc['optimal_runs']} of {RUNS}; best {hc['best']}, mean {hc['mean']:.2f}, worst {hc['worst']}",
         f"{summary}: Hill Climbing"],
        [f"temperature {SA['start_temperature']:g}, cools by half a percent each iteration",
         f"start {SA['start_temperature']:g}, multiplied by {SA['cooling_rate']:g}, stop below "
         f"{SA['end_temperature']:g} ({sa['mean_iterations']} iterations)", "`sa_parameters`"],
        [f"{GA['population_size']} orders for {GA['generations']} generations; selection, crossover, mutation",
         f"population {GA['population_size']}, {GA['generations']} generations, tournament size "
         f"{GA['tournament_size']}, crossover {GA['crossover_rate']:g}, mutation {GA['mutation_rate']:g}",
         "`ga_parameters`"],
        [f"{RUNS} fixed seeds; best, average and worst are all {OPT}",
         f"seeds {SEEDS[0]} to {SEEDS[-1]}; SA and GA: {sa['best']} / {sa['mean']:.2f} / {sa['worst']}, "
         f"{sa['optimal_runs']} of {RUNS} runs optimal, with {sa['mean_evaluations']:.0f} and "
         f"{ga['mean_evaluations']:.0f} evaluations per run", f"`seeds`; {summary}"],
        ["random sampling does as well; larger mazes show the difference",
         f"the best of {n(BASE_N)} random orders is optimal in {BASE['optimal_runs']} of {RUNS} runs; with {K_MAX} "
         f"pellets and {n(data['scaling_budget'])} evaluations random sampling ends "
         f"{SCALE[(K_MAX, 'Random sampling')]:.1f}% above the optimum, SA "
         f"{SCALE[(K_MAX, 'Simulated Annealing')]:.1f}%",
         f"{summary}: {data['baseline_label']}; `scaling_methods`"],
        [f"parameters chosen on {TUNE_RUNS} separate seeds (slide 5, table)",
         f"{TUNE_RUNS} runs per setting, seeds {data['tuning_seeds'][0]} to {data['tuning_seeds'][1]}; there the "
         f"chosen settings were optimal in {SA_TUNED['hits']} (SA) and {GA_TUNED['hits']} (GA) of {TUNE_RUNS} runs, "
         "so \"every time\" is not a guarantee",
         "`tuning_runs`, `tuning_seeds`, `tuning_sa`, `tuning_ga`"],
        ["the cheapest method with a guarantee",
         f"A* (h2): {a2['nodes_expanded']} expansions, {a2['time_ms']:.2f} ms, {a2['peak_memory_kib']:.0f} KiB; "
         f"UCS: {n(ucs['nodes_expanded'])}, {ucs['time_ms']:.2f} ms, {ucs['peak_memory_kib']:.0f} KiB",
         "`comparison`: effort, time_ms, peak_memory_kib"],
        ["h2 is close to the true cost",
         f"on average h2 gives {HEUR['h2']['mean_ratio'] * 100:.0f}% of it, h1 "
         f"{HEUR['h1']['mean_ratio'] * 100:.0f}%", "`heuristic_analysis`: mean_ratio"],
    ],
    widths_cm=[6.4, 6.2, 5.6], size=8.5, keep_together=False)
doc.page_numbers()
doc.save(OUT / "Phase2_Video_Script.docx")
print("written", OUT / "Phase2_Video_Script.docx")
