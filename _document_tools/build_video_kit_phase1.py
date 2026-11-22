"""Builds the video kit for Phase I (the team records the 3-minute video themselves):

    Phase1_Slides.pptx          8 slides; the exact spoken text of every slide is in its speaker notes
    Phase1_Video_Script.docx    who speaks when, the spoken text slide by slide, the take-away messages
    slide_figures/*.png         slide-sized pictures, drawn with the project's own plotting code

Every number on the slides and in the script is read from results/phase1/results.json or
recomputed with the project code, and the facts the text relies on are asserted, so the kit
cannot silently drift from the data.

Usage (from the tools folder):   python build_video_kit_phase1.py [output_folder]
"""
import inspect
import json
import re
import sys
from pathlib import Path

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from docbuilder import ACCENT as DOC_ACCENT
from docbuilder import SOFT as DOC_SOFT
from docbuilder import Doc
from slidebuilder import ACCENT, FONT, INK, LEFT, ORANGE, PALE, RIGHT, RULE, SOFT, TOP_BODY, WHITE, Deck, W
from team import COURSE, PROBLEM_TITLE, TEAM, UNIVERSITY

CODE = Path(__file__).resolve().parent.parent / "Phase1" / "code"
RESULTS = CODE / "results" / "phase1"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else CODE.parent / "video" / "preparation"
FIGS = OUT / "slide_figures"
GIF = RESULTS / "animations" / "ucs_large.gif"          # the one animated picture of the deck

sys.path.insert(0, str(CODE))
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from pacman_search import visualize as viz  # noqa: E402
from pacman_search.experiments import measure_time  # noqa: E402
from pacman_search.layouts import load_problem  # noqa: E402
from pacman_search.problem import ACTIONS  # noqa: E402
from pacman_search.uninformed import UNINFORMED_ALGORITHMS  # noqa: E402

VIDEO_SECONDS = 180
PART_SECONDS = 36                   # five speakers, the same time for each
WORD_LIMITS = (400, 430)            # total spoken text
SPEAKER_SECONDS = (33, 40)          # allowed length of one part

# ======================================================================================
# 1. Data
# ======================================================================================
data = json.loads((RESULTS / "results.json").read_text(encoding="utf-8"))
metrics = {(r["layout"], r["algorithm"]): r for r in data["metrics"]}
sizes = {s["layout"]: s for s in data["state_space"]}
trade = {t["layout"]: t for t in data["tradeoff"]}
ALGS = ["BFS", "DFS", "UCS", "IDS"]
LAYOUTS = ["small", "medium", "large"]
L = "large"


def m(layout, algorithm, key):
    return metrics[(layout, algorithm)][key]


def n(value):
    """An integer with thousands separators."""
    return f"{value:,.0f}"


def ms(value):
    """A running time in milliseconds with about three significant digits (as in the report)."""
    if value < 1:
        return f"{value:.3f}"
    if value < 10:
        return f"{value:.2f}"
    if value < 100:
        return f"{value:.1f}"
    return f"{value:,.0f}"


def nearest(value, step):
    """Round to the nearest multiple of `step` (used for the numbers that are spoken)."""
    return int(round(value / step) * step)


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
        "sixteen seventeen eighteen nineteen").split()
TENS = "- - twenty thirty forty fifty sixty seventy eighty ninety".split()


def in_words(number):
    """How a whole number is read aloud, e.g. 8600 -> 'eight thousand six hundred'."""
    if number < 20:
        return ONES[number]
    if number < 100:
        return TENS[number // 10] + ("-" + ONES[number % 10] if number % 10 else "")
    if number < 1000:
        return ONES[number // 100] + " hundred" + (" and " + in_words(number % 100) if number % 100 else "")
    return in_words(number // 1000) + " thousand" + (" " + in_words(number % 1000) if number % 1000 else "")


# The searches again, with trace=True, for the pictures (the counts must match results.json).
large, tiny = load_problem(L), load_problem("tiny")
traced = {a: UNINFORMED_ALGORITHMS[a.lower()](large, trace=True) for a in ALGS}
tiny_run = {a: UNINFORMED_ALGORITHMS[a.lower()](tiny, trace=True) for a in ALGS}
for a in ALGS:
    r = traced[a]
    assert (r.path_cost, r.depth, r.nodes_expanded, r.max_nodes_in_memory) == (
        m(L, a, "path_cost"), m(L, a, "steps"), m(L, a, "nodes_expanded"), m(L, a, "max_nodes_in_memory")), a

reach = sizes[L]["reachable"]
opt = m(L, "UCS", "path_cost")
danger = {a: sum(1 for s in traced[a].states[1:] if s.pos in large.danger_cells) for a in ALGS}
ids_ratio = m(L, "IDS", "nodes_expanded") / m(L, "BFS", "nodes_expanded")
memory_share = m(L, "IDS", "max_nodes_in_memory") / m(L, "BFS", "max_nodes_in_memory")
bfs_share = m(L, "BFS", "nodes_expanded") / reach
extra_steps = m(L, "UCS", "steps") - m(L, "BFS", "steps")
masks = 2 ** sizes[L]["pellets"]
tiny_states = tiny.state_space_report()["reachable"]
timing_limit = inspect.signature(measure_time).parameters["max_seconds"].default   # a slow search stops earlier

# numbers that are spoken in rounded form
say_reach_low, say_reach_high = 1000, nearest(reach, 100)
say_bfs_expanded = nearest(m(L, "BFS", "nodes_expanded"), 100)
say_ids_ms = nearest(m(L, "IDS", "time_ms"), 10)
say_ms_low, say_ms_high = sorted(round(m(L, a, "time_ms")) for a in ("BFS", "UCS"))

# ---- facts the slides and the spoken text rely on: fail loudly if the results ever change ----
assert all(r["found"] for r in data["metrics"]) and len(data["metrics"]) == len(LAYOUTS) * len(ALGS)
assert (large.normal_cost, large.danger_cost) == (1, 5) and len(large.ghosts) == 1
assert sizes[L]["upper_bound"] == sizes[L]["free_cells"] * masks
assert say_reach_low <= min(sizes[x]["reachable"] for x in LAYOUTS) < 1100
assert max(sizes[x]["reachable"] for x in LAYOUTS) == reach <= say_reach_high < reach * 1.01
assert [a for a in ALGS if m(L, a, "cost_optimal")] == ["UCS"] and opt == trade[L]["optimal_cost"]
assert m(L, "BFS", "steps") == m(L, "IDS", "steps") == trade[L]["fewest_steps"]
assert m(L, "BFS", "solution") == m(L, "IDS", "solution")
assert m(L, "BFS", "steps") + danger["BFS"] * (large.danger_cost - 1) == m(L, "BFS", "path_cost")
assert danger["BFS"] == 3 and danger["UCS"] == 0 and extra_steps == 2
assert 0.45 < bfs_share < 0.55
assert abs(say_bfs_expanded - m(L, "BFS", "nodes_expanded")) <= 50
assert round(ids_ratio) == 35 and m(L, "IDS", "nodes_expanded") > 30 * m(L, "BFS", "nodes_expanded")
assert m(L, "DFS", "time_ms") == min(m(L, a, "time_ms") for a in ALGS)
assert m(L, "DFS", "nodes_expanded") == min(m(L, a, "nodes_expanded") for a in ALGS)
assert m(L, "DFS", "path_cost") == max(m(L, a, "path_cost") for a in ALGS)
assert m(L, "IDS", "time_ms") == max(m(L, a, "time_ms") for a in ALGS)
assert say_ms_low < say_ms_high < 10 < say_ids_ms
assert min(m(L, "BFS", "max_nodes_in_memory"), m(L, "UCS", "max_nodes_in_memory")) >= 2000
assert m(L, "IDS", "max_nodes_in_memory") < 100 and round(memory_share * 100) == 1
assert sorted({m(L, a, "path_cost") for a in ALGS}) == [opt, m(L, "BFS", "path_cost"), m(L, "DFS", "path_cost")]
assert all(m(L, a, "nodes_expanded") <= reach for a in ("BFS", "DFS", "UCS"))     # graph search: once per state
assert m(L, "IDS", "nodes_expanded") > reach                                          # tree search: repeats states
assert data["timing_repeats"] == 20 and max(m(L, a, "time_runs") for a in ALGS) == 20
assert timing_limit == 2.0 and 3 <= m(L, "IDS", "time_runs") < data["timing_repeats"]   # IDS hit the time limit
assert tiny_run["IDS"].actions == tiny_run["BFS"].actions
assert tiny_run["UCS"].path_cost < tiny_run["BFS"].path_cost < tiny_run["DFS"].path_cost
assert len({node.depth for node in tiny_run["DFS"].expanded_nodes}) == tiny_run["DFS"].nodes_expanded  # one branch

# ======================================================================================
# 2. The spoken text (one entry per slide) and the timing
# ======================================================================================
SLIDES = [
    {"speaker": 0, "title": "Title slide",
     "say": "Hello everyone. We are five students, and our project is Pac-Man food collection as a search "
            "problem."},
    {"speaker": 0, "title": "The problem and our model",
     "say": "Pac-Man must eat every pellet at the lowest total cost. A state is his position plus a food mask, "
            "one bit for each pellet that is left. He can move up, right, down or left. A step costs "
            f"{large.normal_cost}. The ghosts stand still, but entering a cell next to one costs "
            f"{large.danger_cost}. The goal is an empty food mask. Our three layouts have between "
            f"{n(say_reach_low)} and {n(say_reach_high)} reachable states."},
    {"speaker": 1, "title": "BFS and DFS",
     "say": "Breadth-first search expands the shallowest node first, using a queue and a set of reached "
            f"states. On the large layout it expands about {n(say_bfs_expanded)} nodes, half of the state space, "
            f"and returns the fewest steps: {m(L, 'BFS', 'steps')}. But this path enters danger cells "
            f"{in_words(danger['BFS'])} times, so it costs {m(L, 'BFS', 'path_cost')}. Depth-first search expands "
            "the deepest node first, and an explored set stops it from looping forever. It expands only "
            f"{m(L, 'DFS', 'nodes_expanded')} nodes, but its path has {m(L, 'DFS', 'steps')} "
            f"steps and costs {m(L, 'DFS', 'path_cost')}. Neither of them returns the cheapest path."},
    {"speaker": 2, "title": "UCS and IDS",
     "say": "Uniform-cost search always expands the cheapest node. It is the only one that returns the optimal "
            f"path, with cost {opt}. This path has {in_words(extra_steps)} more steps than the BFS path, but it "
            "never enters a danger cell. So the path with the fewest steps is not the cheapest. Iterative "
            "deepening repeats a depth-limited search with a growing limit. It returns the same path as BFS and "
            "keeps only "
            f"{m(L, 'IDS', 'max_nodes_in_memory')} nodes in memory, but it expands {ids_ratio:.0f} times as many "
            "nodes as BFS."},
    {"speaker": 3, "title": "Measured results",
     "say": "Here is what we measured on the large layout. Node counts are exact, and each time is the "
            f"fastest of up to {data['timing_repeats']} runs. DFS is the fastest. IDS is the slowest: about "
            f"{say_ids_ms} milliseconds, against {say_ms_low} to {say_ms_high} for BFS and UCS."},
    {"speaker": 3, "title": "Theory versus measurement",
     "say": "Theory and measurement agree. All four are complete. Only UCS is optimal in cost. "
            "BFS and UCS pay with memory: they store thousands of states. IDS needs almost no memory, but it "
            "pays with time."},
    {"speaker": 4, "title": "Seeing the search",
     "say": "We also drew every search. This animation shows the states UCS explores, then the returned path. "
            "On a tiny layout the whole search tree fits on a slide: BFS grows level by level, DFS follows "
            "one branch, and UCS grows cheapest first."},
    {"speaker": 4, "title": "Take-away messages",
     "say": "First, the state must contain the food mask. Second, when step costs differ, the fewest steps "
            "are not the cheapest, so only UCS is optimal. Third, every algorithm pays somewhere: with memory, "
            "time, or a worse path. Thank you."},
]


def word_count(text):
    """Words as a word processor counts them (a number in digits is one word)."""
    return len(text.split())


def spoken_words(text):
    """The words as they are spoken: numbers written out, hyphenated words split into their parts."""
    words = []
    for token in text.split():
        core = token.strip(".,:;!?()")
        digits = core.replace(",", "")
        words += re.split(r"[-\s]+", in_words(int(digits)) if digits.isdigit() else core)
    return [word for word in words if word]


def spoken_count(text):
    """Word count in which a number in digits counts as the words needed to say it (116 = 4 words)."""
    total = 0
    for token in text.split():
        digits = token.strip(".,:;!?()").replace(",", "")
        total += len(in_words(int(digits)).split()) if digits.isdigit() else 1
    return total


def syllables(word):
    """Rough number of syllables of an English word (groups of vowels, silent final e not counted)."""
    if word.isupper() and len(word) <= 4:              # BFS, DFS, UCS, IDS are spelled out letter by letter
        return len(word)
    word = re.sub(r"[^a-z]", "", word.lower())
    if word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    count = len(re.findall(r"[aeiouy]+", word))
    if count > 1 and word.endswith("e") and not word.endswith(("le", "ee")):
        count -= 1
    if count > 1 and word.endswith("ed") and not word.endswith(("ted", "ded")):
        count -= 1
    return max(count, 1) if word else 0


def speaking_units(text):
    """Estimated speaking effort: syllables, plus a short pause at every comma (1) and sentence end (2).
    Used to check that the five parts take about the same time when they are spoken."""
    units = sum(syllables(word) for word in spoken_words(text))
    return units + 2 * len(re.findall(r"[.!?](?=\s|$)", text)) + len(re.findall(r"[,:;](?=\s)", text))


def clock(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"


for slide in SLIDES:
    slide["words"], slide["spoken"] = word_count(slide["say"]), spoken_count(slide["say"])
    slide["units"] = speaking_units(slide["say"])
    slide["syllables"] = sum(syllables(word) for word in spoken_words(slide["say"]))
total_words = sum(slide["words"] for slide in SLIDES)
total_spoken = sum(slide["spoken"] for slide in SLIDES)
total_units = sum(slide["units"] for slide in SLIDES)
total_syllables = sum(slide["syllables"] for slide in SLIDES)

# Every speaker gets the same window (36 s). A speaker with two slides changes the slide inside the
# window, in proportion to the length of the two texts.
SPEAKERS = []
for index, (name, student_id, _) in enumerate(TEAM):
    own = [i for i, slide in enumerate(SLIDES) if slide["speaker"] == index]
    assert own == list(range(own[0], own[-1] + 1)), "every speaker speaks once"
    speaker = {
        "name": name, "id": student_id, "slides": [i + 1 for i in own],
        "words": sum(SLIDES[i]["words"] for i in own), "spoken": sum(SLIDES[i]["spoken"] for i in own),
        "syllables": sum(SLIDES[i]["syllables"] for i in own), "units": sum(SLIDES[i]["units"] for i in own),
        "start": index * PART_SECONDS, "end": (index + 1) * PART_SECONDS,
    }
    speaker["estimate"] = VIDEO_SECONDS * speaker["units"] / total_units      # from syllables and pauses
    speaker["by_words"] = VIDEO_SECONDS * speaker["words"] / total_words      # from the word count alone
    elapsed = 0
    for i in own:
        SLIDES[i]["start"] = speaker["start"] + round(PART_SECONDS * elapsed / speaker["units"])
        elapsed += SLIDES[i]["units"]
        SLIDES[i]["end"] = speaker["start"] + round(PART_SECONDS * elapsed / speaker["units"])
        SLIDES[i]["window"] = f"{clock(SLIDES[i]['start'])}-{clock(SLIDES[i]['end'])}"
        SLIDES[i]["tag"] = f"{name}  |  {SLIDES[i]['window']}"
    SPEAKERS.append(speaker)

print(f"total: {total_words} words ({total_spoken} counting numbers as spoken), "
      f"{total_words / (VIDEO_SECONDS / 60):.0f} words per minute, about {total_syllables} syllables "
      f"= {total_syllables / VIDEO_SECONDS:.2f} per second")
for speaker in SPEAKERS:
    print(f"  {speaker['name']:<28} slides {speaker['slides']}  {clock(speaker['start'])}-{clock(speaker['end'])}"
          f"  estimated {speaker['estimate']:.1f} s (by words alone {speaker['by_words']:.1f} s)  "
          f"{speaker['words']} words ({speaker['spoken']} spoken, about {speaker['syllables']} syllables)")
for number, slide in enumerate(SLIDES, start=1):
    print(f"  slide {number}: {slide['window']}  {slide['words']} words ({slide['spoken']} spoken)")
assert WORD_LIMITS[0] <= total_words <= WORD_LIMITS[1], total_words
assert WORD_LIMITS[0] <= total_spoken <= WORD_LIMITS[1], total_spoken
assert SLIDES[-1]["end"] == VIDEO_SECONDS and SPEAKER_SECONDS[0] <= PART_SECONDS <= SPEAKER_SECONDS[1]
assert all(abs(s["estimate"] - PART_SECONDS) <= 1.5 for s in SPEAKERS)       # the parts are balanced
assert all(SPEAKER_SECONDS[0] <= s["by_words"] <= SPEAKER_SECONDS[1] for s in SPEAKERS)

TAKEAWAYS = [
    "**The model decides everything.** A state is Pac-Man's position plus the food mask; the mask is what "
    f"makes the state space large ({n(reach)} reachable states on our main layout).",
    f"**Fewest steps is not cheapest.** With step costs of {large.normal_cost} and {large.danger_cost}, BFS and "
    f"IDS return {m(L, 'BFS', 'steps')} steps at cost {m(L, 'BFS', 'path_cost')}. Only UCS returns the optimal "
    f"cost {opt}: it is the right uninformed algorithm here.",
    "**Every algorithm pays somewhere.** BFS and UCS pay with memory, IDS pays with time "
    f"({ids_ratio:.0f} times the node expansions of BFS), DFS pays with a poor path (cost "
    f"{m(L, 'DFS', 'path_cost')}).",
]
NEXT_STEP = (f"Next, in Phase II: heuristic search has to beat the {n(m(L, 'UCS', 'nodes_expanded'))} node "
             "expansions of UCS.")

# What is said in the video -> the exact value -> where it comes from (printed in the script document).
NUMBERS = [
    (f"a step costs {large.normal_cost}; next to a ghost it costs {large.danger_cost}",
     f"STEP_COST = {large.normal_cost}, DANGER_COST = {large.danger_cost}",
     "`pacman_search/problem.py`"),
    (f"between {n(say_reach_low)} and {n(say_reach_high)} reachable states",
     f"small {n(sizes['small']['reachable'])}, medium {n(sizes['medium']['reachable'])}, large {n(reach)}",
     "`state_space`: reachable"),
    (f"about {n(say_bfs_expanded)} nodes, half of the state space",
     f"{n(m(L, 'BFS', 'nodes_expanded'))} of {n(reach)} states = {bfs_share * 100:.0f}%",
     "`metrics`: BFS nodes_expanded"),
    (f"{m(L, 'BFS', 'steps')} steps, danger cells {in_words(danger['BFS'])} times, costs {m(L, 'BFS', 'path_cost')}",
     f"{m(L, 'BFS', 'steps')} + {danger['BFS']} × {large.danger_cost - 1} = {m(L, 'BFS', 'path_cost')}",
     "`metrics`: BFS; path replayed in the model"),
    (f"{m(L, 'DFS', 'nodes_expanded')} nodes, {m(L, 'DFS', 'steps')} steps, costs {m(L, 'DFS', 'path_cost')}",
     f"{m(L, 'DFS', 'nodes_expanded')} expanded, {m(L, 'DFS', 'steps')} steps, cost {m(L, 'DFS', 'path_cost')}",
     "`metrics`: DFS"),
    (f"cost {opt}, {in_words(extra_steps)} more steps, no danger cell",
     f"cost {opt}, {m(L, 'UCS', 'steps')} steps (BFS: {m(L, 'BFS', 'steps')}), {danger['UCS']} danger cells",
     "`metrics`: UCS; path replayed in the model"),
    (f"only {m(L, 'IDS', 'max_nodes_in_memory')} nodes in memory; thousands of states",
     f"IDS {m(L, 'IDS', 'max_nodes_in_memory')}; BFS {n(m(L, 'BFS', 'max_nodes_in_memory'))}, "
     f"UCS {n(m(L, 'UCS', 'max_nodes_in_memory'))}",
     "`metrics`: max_nodes_in_memory"),
    (f"{ids_ratio:.0f} times as many nodes as BFS",
     f"{n(m(L, 'IDS', 'nodes_expanded'))} / {n(m(L, 'BFS', 'nodes_expanded'))} = {ids_ratio:.1f}",
     "`metrics`: nodes_expanded"),
    (f"the fastest of up to {data['timing_repeats']} runs",
     f"{data['timing_repeats']} runs; IDS: {m(L, 'IDS', 'time_runs')} runs ({timing_limit:g}-second limit)",
     "`timing_repeats`; `metrics`: time_runs"),
    (f"about {say_ids_ms} milliseconds, against {say_ms_low} to {say_ms_high}",
     f"IDS {ms(m(L, 'IDS', 'time_ms'))}, BFS {ms(m(L, 'BFS', 'time_ms'))}, UCS {ms(m(L, 'UCS', 'time_ms'))}, "
     f"DFS {ms(m(L, 'DFS', 'time_ms'))} ms",
     "`metrics`: time_ms"),
]

# ======================================================================================
# 3. Slide-sized pictures (the project's own drawing functions, arranged for a 16:9 slide)
# ======================================================================================
CELL = 0.30        # inches per maze cell when drawing; the slide shows the pictures about 1.55 times larger


def save(fig, path):
    fig.savefig(path, dpi=360, facecolor="white")
    plt.close(fig)
    return path


def figure_model(problem, path):
    """Slide 2: the main layout with the project's maze drawing and its symbol legend."""
    viz.apply_style()
    span = (problem.width - 2 * viz.BORDER_CROP) * CELL
    tall = (problem.height - 2 * viz.BORDER_CROP) * CELL
    foot = 0.42
    fig_w, fig_h = span + 0.66, tall + foot
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([(fig_w - span) / 2 / fig_w, foot / fig_h, span / fig_w, tall / fig_h])
    viz.draw_maze(ax, problem)
    fig.legend(handles=viz.symbol_handles(with_path=False), loc="lower center", ncol=3, fontsize=7.2,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.6, columnspacing=1.3, borderaxespad=0.0)
    return save(fig, path)


def figure_explored(problem, results, notes, heat_max, path, legend=True):
    """Explored states and returned path of one or two algorithms, side by side.

    Same drawing as plot_explored() of the project (draw_maze + draw_path, one blue scale for
    all four algorithms), with a header and a legend that are large enough for a slide.
    """
    viz.apply_style()
    panel_w = (problem.width - 2 * viz.BORDER_CROP) * CELL
    panel_h = (problem.height - 2 * viz.BORDER_CROP) * CELL
    gap, side = 0.2, 0.02
    head = 0.25 if notes else 0.02
    foot = 0.46 if legend else 0.02
    fig_w = 2 * side + len(results) * panel_w + (len(results) - 1) * gap
    fig_h = head + panel_h + foot
    fig = plt.figure(figsize=(fig_w, fig_h))
    for index, result in enumerate(results):
        left = side + index * (panel_w + gap)
        ax = fig.add_axes([left / fig_w, foot / fig_h, panel_w / fig_w, panel_h / fig_h])
        viz.draw_maze(ax, problem, heat=viz.expanded_per_cell(result), heat_max=heat_max, label_food=False)
        viz.draw_path(ax, result.states)
        if notes:
            fig.text(left / fig_w, 1 - 0.17 / fig_h, result.algorithm, fontsize=10.5, fontweight="bold",
                     ha="left", va="baseline")
            fig.text((left + 0.42) / fig_w, 1 - 0.17 / fig_h, notes[index], fontsize=8.4, color=viz.INK_SOFT,
                     ha="left", va="baseline")
    if legend:
        bar_ax = fig.add_axes([(side + 0.02) / fig_w, 0.285 / fig_h, 1.2 / fig_w, 0.08 / fig_h])
        bar = fig.colorbar(ScalarMappable(norm=Normalize(0, heat_max), cmap=viz.HEAT), cax=bar_ax,
                           orientation="horizontal")
        bar.outline.set_visible(False)
        bar.set_ticks([])
        fig.text((side + 1.32) / fig_w, 0.325 / fig_h,
                 "distinct states expanded on the cell (white = none, darker = more)",
                 fontsize=7.3, color=viz.INK, ha="left", va="center")
        handles = viz.symbol_handles()                    # ..., danger cell [3], wall, returned path [5]
        fig.legend(handles=[handles[5], handles[3]], loc="lower left", ncol=2, fontsize=7.3,
                   bbox_to_anchor=(side / fig_w, 0.0), handlelength=1.6, columnspacing=1.6, borderaxespad=0.0)
    return save(fig, path)


def figure_trees(problem, results, path, width=4.7, height=4.75, font=8.0, x_gap=1.7):
    """Slide 7: the complete search trees of BFS, DFS and UCS on the tiny layout.

    The trees are laid out and drawn by the project's _layout_tree() and _draw_tree(); only the
    arrangement is new: the leaves get more room sideways and the labels a larger font.
    """
    viz.apply_style()
    normal_gap, viz.TREE_X_GAP = viz.TREE_X_GAP, x_gap
    try:
        trees = [viz._layout_tree(result.expanded_nodes, result.extra.get("goal_node")) for result in results]
    finally:
        viz.TREE_X_GAP = normal_gap
    pad, head, gap = viz.TREE_PAD, 0.36, 0.1
    unit = min((width - gap * (len(trees) - 1)) / sum(tree["width"] + 2 * pad for tree in trees),
               (height - head) / max(tree["height"] + 2 * pad for tree in trees))
    used = sum((tree["width"] + 2 * pad) * unit for tree in trees) + gap * (len(trees) - 1)
    fig = plt.figure(figsize=(width, height))
    x = (width - used) / 2
    for tree, result in zip(trees, results):
        own_w, own_h = (tree["width"] + 2 * pad) * unit, (tree["height"] + 2 * pad) * unit
        ax = fig.add_axes([x / width, 1 - (head + own_h) / height, own_w / width, own_h / height])
        viz._draw_tree(ax, problem, tree, font=font)
        fig.text((x + own_w / 2) / width, 1 - 0.27 / height, result.algorithm, fontsize=14, fontweight="bold",
                 ha="center", va="baseline")
        x += own_w + gap
    steps = viz._tree_fill_steps(problem)                 # the entries of the project's tree legend
    k = problem.num_food
    handles = [Line2D([], [], marker="o", linestyle="none", markersize=8, markerfacecolor=steps[eaten],
                      markeredgecolor=viz.SURFACE,
                      label=f"{k - eaten} pellet{'s' if k - eaten != 1 else ''} left" + (" (goal)" if eaten == k else ""))
               for eaten in range(k + 1)]
    handles.append(Line2D([], [], color=viz.ORANGE, linewidth=2.2, label="solution path"))
    fig.legend(handles=handles, loc="lower left", ncol=1, fontsize=9.5, bbox_to_anchor=(0.0, 0.0),
               labelspacing=0.45, borderaxespad=0.1)
    return save(fig, path)


# ======================================================================================
# 4. The slide deck
# ======================================================================================
SUPERSCRIPT = re.compile(r"\^\{(.+?)\}")
BODY_W = W - LEFT - RIGHT


class KitDeck(Deck):
    """The shared deck style plus the few things this kit needs: ^{superscripts}, a speaker tag
    that is wide enough for the longest name, bullets and take-away panels of a chosen size."""

    def _run(self, paragraph, text, size, bold=False, color=INK, italic=False):
        for index, piece in enumerate(text.split("**")):
            for part_index, part in enumerate(SUPERSCRIPT.split(piece)):
                if not part:
                    continue
                run = paragraph.add_run()
                run.text = part
                run.font.name = FONT
                run.font.size = Pt(size)
                run.font.bold = bold or index % 2 == 1
                run.font.italic = italic
                run.font.color.rgb = color
                if part_index % 2 == 1:
                    run._r.get_or_add_rPr().set("baseline", "30000")

    def _frame(self, title, speaker=None, takeaway=None, note=""):
        slide = super()._frame(title, None, takeaway, note)
        if speaker:
            self._text(slide, W - RIGHT - 4.6, 0.45, 4.6, 0.6, speaker, size=13, color=SOFT, align=PP_ALIGN.RIGHT,
                       anchor=MSO_ANCHOR.MIDDLE)
        return slide

    def bullets_box(self, slide, left, top, width, height, bullets, size=20, sub=18, after=7, before=10):
        """Bullets as in the shared style ("- " starts a sub-point), with chosen sizes and spacing."""
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.word_wrap = True
        for index, item in enumerate(bullets):
            level = 1 if item.startswith("- ") else 0
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.space_after = Pt(after)
            if level == 0 and index:
                paragraph.space_before = Pt(before)
            self._run(paragraph, ("–  " + item[2:]) if level else ("•  " + item), sub if level else size,
                      color=SOFT if level else INK)
            if level:
                paragraph.level = 1
        return box

    def takeaway_panels(self, slide, items, top, height, gap=0.2, size=20):
        """Numbered take-away panels as on the shared take-aways slide, with a chosen height and font."""
        for index, item in enumerate(items, start=1):
            self._rect(slide, LEFT, top, 0.09, height, ORANGE)
            self._rect(slide, LEFT + 0.09, top, BODY_W - 0.09, height, PALE)
            self._text(slide, LEFT + 0.3, top, 0.6, height, str(index), size=28, bold=True, color=ACCENT,
                       anchor=MSO_ANCHOR.MIDDLE)
            self._text(slide, LEFT + 0.95, top, BODY_W - 1.2, height, item, size=size, anchor=MSO_ANCHOR.MIDDLE)
            top += height + gap
        return top


def build_deck():
    FIGS.mkdir(parents=True, exist_ok=True)
    heat_max = max(max(viz.expanded_per_cell(traced[a]).values()) for a in ALGS)     # one blue scale

    def note_of(a):
        return f"{m(L, a, 'steps')} steps, cost {m(L, a, 'path_cost')}"

    fig_cover = figure_explored(large, [traced["UCS"]], None, heat_max, FIGS / "slide1_cheapest_plan_ucs.png",
                                legend=False)
    fig_model = figure_model(large, FIGS / "slide2_large_layout.png")
    fig_bfs_dfs = figure_explored(large, [traced["BFS"], traced["DFS"]], [note_of("BFS"), note_of("DFS")],
                                  heat_max, FIGS / "slide3_explored_bfs_dfs.png")
    fig_ucs_ids = figure_explored(large, [traced["UCS"], traced["IDS"]], [note_of("UCS"), note_of("IDS")],
                                  heat_max, FIGS / "slide4_explored_ucs_ids.png")
    fig_trees = figure_trees(tiny, [tiny_run["BFS"], tiny_run["DFS"], tiny_run["UCS"]],
                             FIGS / "slide7_search_trees_tiny.png")

    deck = KitDeck(f"{COURSE}  |  Pac-Man Food Collection  |  Phase I video")
    s = SLIDES

    # ---- 1: title -------------------------------------------------------------------------
    slide = deck.title_slide(PROBLEM_TITLE, "Phase I: problem modeling and uninformed search (BFS, DFS, UCS, IDS)",
                             [], note=s[0]["say"])
    deck._text(slide, W - RIGHT - 4.6, 0.22, 4.6, 0.35, s[0]["tag"], size=13, color=WHITE, align=PP_ALIGN.RIGHT)
    deck._text(slide, 0.9, 3.25, 8.0, 0.4, f"{COURSE}  |  {UNIVERSITY}", size=16, color=SOFT)
    top = 3.95
    for index, (name, student_id, _) in enumerate(TEAM):
        deck._text(slide, 0.9, top, 5.6, 0.45, name + ("  (team leader)" if index == 0 else ""), size=20)
        deck._text(slide, 6.6, top, 2.0, 0.45, student_id, size=20, color=SOFT)
        top += 0.52
    deck._picture(slide, fig_cover, W - RIGHT - 3.25, 3.2, 3.25, 3.25)
    deck._text(slide, W - RIGHT - 3.6, 6.47, 3.95, 0.32, f"The cheapest plan on our main layout (cost {opt})",
               size=13, color=SOFT, align=PP_ALIGN.CENTER)

    # ---- 2: the problem and the model ----------------------------------------------------
    start_state = f"(({large.start[0]},{large.start[1]}), {large.all_food:0{large.num_food}b})"
    slide = deck._frame(s[1]["title"], s[1]["tag"],
                        f"A state must remember which pellets are left: {sizes[L]['pellets']} pellets give "
                        f"{masks} food combinations for every cell.", s[1]["say"])
    deck.bullets_box(slide, LEFT, TOP_BODY + 0.08, 7.0, 4.7, [
        "**Task**: eat every pellet at the lowest total cost",
        "**State** = (position, food mask), one bit per pellet",
        f"- start state: {start_state}, all {sizes[L]['pellets']} pellets left",
        "**Actions**: up, right, down, left (not into a wall or ghost)",
        f"**Step cost**: {large.normal_cost}, or **{large.danger_cost}** next to a ghost (ghosts stand still)",
        "**Goal**: food mask = 0, every pellet eaten",
        "**State space**: at most (free cells) × 2^{pellets}",
        f"- large layout: {sizes[L]['free_cells']} × 2^{{{sizes[L]['pellets']}}} = {n(sizes[L]['upper_bound'])} "
        f"at most, **{n(reach)}** reachable",
        f"- small: {n(sizes['small']['reachable'])} and medium: {n(sizes['medium']['reachable'])} reachable states",
    ], after=5, before=7)
    deck._picture(slide, fig_model, W - RIGHT - 4.85, TOP_BODY + 0.02, 4.85, 4.3)
    deck._text(slide, W - RIGHT - 4.85, 5.82, 4.85, 0.36,
               f"Large layout (main instance): {sizes[L]['free_cells']} free cells, {sizes[L]['pellets']} pellets",
               size=14, color=SOFT, align=PP_ALIGN.CENTER)

    # ---- 3: BFS and DFS ------------------------------------------------------------------
    slide = deck._frame(s[2]["title"], s[2]["tag"],
                        "BFS finds the fewest steps and DFS answers fastest, but neither returns the cheapest path.",
                        s[2]["say"])
    deck.bullets_box(slide, LEFT, TOP_BODY + 0.1, 4.4, 4.6, [
        "**BFS**: shallowest node first",
        "- queue + set of reached states",
        f"- fewest steps: **{m(L, 'BFS', 'steps')}**, but cost **{m(L, 'BFS', 'path_cost')}**",
        f"- expands {n(m(L, 'BFS', 'nodes_expanded'))} of {n(reach)} states",
        "**DFS**: deepest node first",
        "- stack + explored set (no loops)",
        f"- **{m(L, 'DFS', 'steps')}** steps, cost **{m(L, 'DFS', 'path_cost')}**",
        f"- expands only {n(m(L, 'DFS', 'nodes_expanded'))} states",
    ], before=22)
    deck._picture(slide, fig_bfs_dfs, LEFT + 4.5, TOP_BODY + 0.02, BODY_W - 4.5, 4.76)

    # ---- 4: UCS and IDS ------------------------------------------------------------------
    slide = deck._frame(s[3]["title"], s[3]["tag"],
                        "Fewest steps is not cheapest: only UCS returns the optimal cost; IDS saves memory "
                        "but pays with time.", s[3]["say"])
    deck.bullets_box(slide, LEFT, TOP_BODY + 0.1, 4.4, 4.6, [
        "**UCS**: cheapest node first",
        "- priority queue on the path cost",
        f"- optimal: cost **{opt}** in {m(L, 'UCS', 'steps')} steps",
        f"- expands {n(m(L, 'UCS', 'nodes_expanded'))} states",
        "**IDS**: depth limit 0, 1, 2, ...",
        f"- same path as BFS: cost {m(L, 'IDS', 'path_cost')}",
        f"- only **{m(L, 'IDS', 'max_nodes_in_memory')}** nodes in memory",
        f"- {n(m(L, 'IDS', 'nodes_expanded'))} expansions: {ids_ratio:.0f} × BFS",
    ], before=22)
    deck._picture(slide, fig_ucs_ids, LEFT + 4.5, TOP_BODY + 0.02, BODY_W - 4.5, 4.76)

    # ---- 5: measured results -------------------------------------------------------------
    slide = deck.table_slide(
        s[4]["title"], ["Algorithm", "Path cost", "Steps", "Nodes expanded", "Max nodes in memory", "Time (ms)"],
        [[a, n(m(L, a, "path_cost")), n(m(L, a, "steps")), n(m(L, a, "nodes_expanded")),
          n(m(L, a, "max_nodes_in_memory")), ms(m(L, a, "time_ms"))] for a in ALGS],
        speaker=s[4]["tag"], note=s[4]["say"],
        takeaway=f"Four algorithms, three different answers: path costs {opt}, {m(L, 'BFS', 'path_cost')} and "
                 f"{m(L, 'DFS', 'path_cost')}. Only UCS is optimal.",
        highlight_rows=(ALGS.index("UCS"),), col_widths=[1.5, 1.2, 1.0, 1.8, 2.3, 1.3], size=18, row_height=0.56)
    deck.bullets_box(slide, LEFT, TOP_BODY + 0.1 + 0.56 * 5 + 0.28, BODY_W, 1.6, [
        f"Large layout: {n(reach)} reachable states, optimal cost **{opt}**",
        f"IDS: **{ids_ratio:.0f} ×** the node expansions of BFS, with about {memory_share * 100:.0f}% of its memory",
        f"Node counts are exact; each time is the fastest of up to {data['timing_repeats']} runs",
    ], size=18, after=7, before=0)

    # ---- 6: theory versus measurement ----------------------------------------------------
    slide = deck.table_slide(
        s[5]["title"], ["", "Theory", "Measured on the large layout"],
        [["**Completeness**", "BFS, UCS and IDS are complete. DFS is complete only with its explored set.",
          f"All {len(ALGS)} algorithms find a solution (also on the other {len(LAYOUTS) - 1} layouts)"],
         ["**Optimality**", "UCS: cheapest path. BFS and IDS: fewest steps, cheapest only if all steps cost the same.",
          f"Path cost: UCS {opt} (optimal), BFS and IDS {m(L, 'BFS', 'path_cost')}, DFS {m(L, 'DFS', 'path_cost')}"],
         ["**Time**", "BFS, DFS, UCS expand each state at most once. IDS repeats states: O(b^{d}) node visits.",
          f"Nodes expanded: BFS {n(m(L, 'BFS', 'nodes_expanded'))}, UCS {n(m(L, 'UCS', 'nodes_expanded'))}, "
          f"DFS {n(m(L, 'DFS', 'nodes_expanded'))}, IDS {n(m(L, 'IDS', 'nodes_expanded'))}"],
         ["**Memory**", "BFS and UCS store every reached state, O(b^{d}) for BFS. IDS stores only its path: O(bd).",
          f"Max nodes in memory: BFS {n(m(L, 'BFS', 'max_nodes_in_memory'))}, "
          f"UCS {n(m(L, 'UCS', 'max_nodes_in_memory'))}, IDS {m(L, 'IDS', 'max_nodes_in_memory')}"]],
        speaker=s[5]["tag"], note=s[5]["say"],
        takeaway="The measurements confirm the theory: each algorithm pays with memory, time or path quality.",
        col_widths=[2.05, 5.3, 4.78], size=18, row_height=0.8)
    table = next(shape for shape in slide.shapes if shape.has_table).table
    table.rows[0].height = Inches(0.5)
    for row in range(len(table.rows)):
        for column in (1, 2):
            table.cell(row, column).text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    deck._text(slide, LEFT, TOP_BODY + 0.1 + 0.5 + 4 * 0.8 + 0.12, BODY_W, 0.35,
               f"b = branching factor (at most {len(ACTIONS)} moves),  d = depth of the shallowest solution "
               f"({m(L, 'BFS', 'steps')} steps here)", size=14, color=SOFT)

    # ---- 7: seeing the search -------------------------------------------------------------
    slide = deck._frame(s[6]["title"], s[6]["tag"],
                        "The pictures show each strategy at work: level by level, one deep branch, or cheapest first.",
                        s[6]["say"])
    picture = deck._picture(slide, GIF, LEFT, TOP_BODY + 0.02, 3.8, 4.32)
    picture.line.color.rgb = RULE
    picture.line.width = Pt(0.75)
    deck._text(slide, LEFT, 5.84, 3.8, 0.36, "Animation: UCS on the large layout", size=14, color=SOFT,
               align=PP_ALIGN.CENTER)
    deck._picture(slide, fig_trees, LEFT + 4.0, TOP_BODY + 0.02, 4.7, 4.76)
    deck.bullets_box(slide, LEFT + 8.9, TOP_BODY + 0.1, BODY_W - 8.9, 3.6, [
        "**Search trees**, tiny layout",
        f"- {tiny_states} reachable states",
        "**BFS**: level by level",
        f"- {tiny_run['BFS'].depth} steps, cost {tiny_run['BFS'].path_cost}",
        "**DFS**: one deep branch",
        f"- {tiny_run['DFS'].depth} steps, cost {tiny_run['DFS'].path_cost}",
        "**UCS**: cheapest first",
        f"- {tiny_run['UCS'].depth} steps, cost {tiny_run['UCS'].path_cost}",
    ], size=18, sub=18, after=3, before=9)
    deck._text(slide, LEFT + 8.9, 5.38, BODY_W - 8.9, 0.8,
               "Node = Pac-Man's (row, col); small number = order of expansion; letter = action",
               size=14, color=SOFT)

    # ---- 8: take-away messages -------------------------------------------------------------
    slide = deck._frame(s[7]["title"], s[7]["tag"], None, s[7]["say"])
    bottom = deck.takeaway_panels(slide, TAKEAWAYS, TOP_BODY + 0.15, 1.34)
    deck._text(slide, LEFT, bottom + 0.02, BODY_W, 0.5, NEXT_STEP, size=18, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)

    assert len(deck.prs.slides) == len(SLIDES)
    for slide, record in zip(deck.prs.slides, SLIDES):          # the notes hold exactly the spoken text
        assert slide.notes_slide.notes_text_frame.text == record["say"]
    deck.prs.core_properties.title = f"{PROBLEM_TITLE} - Phase I video slides"
    target = OUT / "Phase1_Slides.pptx"
    deck.save(target)
    print("written", target)


# ======================================================================================
# 5. The script document
# ======================================================================================
def build_script():
    doc = Doc(margins_cm=1.8, body_pt=10)
    doc.para("Phase I video: recording script", size=17, bold=True, color=DOC_ACCENT, space_after=1)
    doc.para(f"{COURSE}  |  {PROBLEM_TITLE}  |  3 minutes, {len(SLIDES)} slides, {len(TEAM)} speakers  |  "
             "use with `Phase1_Slides.pptx`", size=9.5, color=DOC_SOFT, space_after=6)

    topics = ["the problem and our model", "BFS and DFS", "UCS and IDS", "measurements, theory versus measurement",
              "visualization and take-away messages"]
    lines = ["**How to record (one sitting, total 3:00)**",
             f"**Who speaks when.** Five speakers in the team order; each of us speaks once, for {PART_SECONDS} "
             "seconds:"]
    for speaker, topic in zip(SPEAKERS, topics):
        pages = "-".join(str(x) for x in sorted({speaker["slides"][0], speaker["slides"][-1]}))
        lines.append(f"      {clock(speaker['start'])}-{clock(speaker['end'])}   **{speaker['name']}**   "
                     f"slide{'s' if len(speaker['slides']) > 1 else ''} {pages}: {topic}  "
                     f"({speaker['words']} words)")
    lines += [
        "**Everyone appears or speaks.** The brief asks that all team members appear or speak. Each of us reads "
        "the text of our own slides, so all five voices are in the video; switch the camera on as well if the "
        "recording tool offers it.",
        "**One take-away per slide.** The sentence in the bar at the bottom of a slide is the message of that "
        "slide. Read the text as it is written and do not add new points - there is no spare time.",
        "**Recording.** Open `Phase1_Slides.pptx`, start the slide show (F5) and record the screen and the voice "
        "in one go (PowerPoint: Slide Show > Record, or any screen recorder) at 1920 × 1080. The text of every "
        "slide is also in its speaker notes (Presenter View). Change the slide when its text is finished. "
        "Save the video as MP4.",
        "**Slide 7 is animated.** The picture on the left is the animated GIF `animations/ucs_large.gif` from our "
        "results folder. It moves only in slide-show mode; in the PDF it is a still picture.",
        f"**Rehearse once with a timer.** {total_words} words are about "
        f"{total_words / (VIDEO_SECONDS / 60):.0f} words per minute, a calm pace, and the five parts take about "
        "the same time. If you run over 3:00, speak a little faster instead of cutting a sentence.",
    ]
    doc.callout(lines)

    rows = []
    for number, slide in enumerate(SLIDES, start=1):
        rows.append([slide["window"], TEAM[slide["speaker"]][0], f"**{number}**  {slide['title']}",
                     f"{slide['say']}\n__({slide['words']} words)__"])
    doc.table(["Time", "Speaker", "Slide", "What to say (exact spoken text)"], rows,
              widths_cm=[1.8, 3.0, 2.5, 10.1], size=10, keep_together=False)

    doc.para("Take-away messages of the video", size=12, bold=True, color=DOC_ACCENT, space_before=2, space_after=3,
             keep_with_next=True)
    doc.numbered(TAKEAWAYS, size=10)

    doc.para("Where the numbers come from", size=12, bold=True, color=DOC_ACCENT, space_before=8, space_after=2,
             keep_with_next=True)
    doc.para("Every number was checked against `results/phase1/results.json` (large layout unless stated). "
             "Numbers after \"about\" are rounded; the slides show the exact values.", size=9.5,
             color=DOC_SOFT, space_after=3, keep_with_next=True)
    doc.table(["Said in the video", "Exact value", "Source (results.json)"], [list(row) for row in NUMBERS],
              widths_cm=[6.1, 5.9, 5.4], size=9)
    doc.page_numbers()
    doc.doc.core_properties.title = f"{PROBLEM_TITLE} - Phase I video script"
    target = OUT / "Phase1_Video_Script.docx"
    doc.save(target)
    print("written", target)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    build_deck()
    build_script()
