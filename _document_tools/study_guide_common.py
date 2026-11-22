"""Shared data and helpers for build_study_guide.py.

Every number used in the study guide is read here from one of three places:
  * results.json of the Phase I and Phase II result folders (the submitted results),
  * whatif_results.json, written by study_experiments.py (our own extra runs of the project code),
  * the output of commands / interpreter sessions that are executed with the project code.
Command outputs, sessions and experiments are cached in the scratch folder; `--rerun` on the
builder's command line refreshes them all.
"""
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

sys.dont_write_bytecode = True

TOOLS = Path(__file__).resolve().parent
WORK = TOOLS / "_cache"
PROJECT = Path(__file__).resolve().parent.parent
CODE1 = PROJECT / "Phase1" / "code"
CODE2 = PROJECT / "Phase2" / "code"
OUT_DIR = PROJECT / "Study_Guide"
OUT = OUT_DIR / "Oral_Discussion_Study_Guide.docx"
COMPANION = OUT_DIR / "whatif_experiments.py"
PYTHON = sys.executable
RERUN = "--rerun" in sys.argv
CODE_WIDTH = 104                 # characters that fit on one line of a code block (Consolas 8 pt)

WORK.mkdir(parents=True, exist_ok=True)
P1 = json.loads((CODE1 / "results" / "phase1" / "results.json").read_text(encoding="utf-8"))
P2 = json.loads((CODE2 / "results" / "phase2" / "results.json").read_text(encoding="utf-8"))

LAYOUTS = ["small", "medium", "large"]
L = "large"
UNINFORMED = ["BFS", "DFS", "UCS", "IDS"]
INFORMED = ["Greedy (h1)", "Greedy (h2)", "A* (h1)", "A* (h2)"]
LOCALS = ["Hill Climbing", "Simulated Annealing", "Genetic Algorithm"]
HC_RR = f"Hill Climbing ({P2['hc_restarts']} restarts)"

M1 = {(r["layout"], r["algorithm"]): r for r in P1["metrics"]}
SIZE = {r["layout"]: r for r in P1["state_space"]}
TRADE = {r["layout"]: r for r in P1["tradeoff"]}
VARIANT = {(r["layout"], r["variant"]): r for r in P1["ids_variants"]}
IDS_ITER = {name: [r for r in P1["ids_iterations"] if r["layout"] == name] for name in LAYOUTS}
S2 = {(r["layout"], r["algorithm"]): r for r in P2["search_metrics"]}
LOC = {(r["layout"], r["algorithm"]): r for r in P2["local_search_summary"]}
RUNS = {}
for _row in P2["local_search_runs"]:
    RUNS.setdefault((_row["layout"], _row["algorithm"]), []).append(_row)
HEUR = {(r["layout"], r["heuristic"]): r for r in P2["heuristic_analysis"]}
LAND = {r["layout"]: r for r in P2["landscape"]}
COMP = {(r["layout"], r["algorithm"]): r for r in P2["comparison"]}
TSA = {(r["start_temperature"], r["cooling_rate"]): r for r in P2["tuning_sa"]}
TGA = {(r["population_size"], r["mutation_rate"]): r for r in P2["tuning_ga"]}
ONE = {(r["algorithm"], r["parameter"], r["value"]): r for r in P2["tuning_one_at_a_time"]}
OPT = P2["optimum"]
SA, GA = P2["sa_parameters"], P2["ga_parameters"]
N_SEEDS = len(P2["seeds"])
TUNE_RUNS = P2["tuning_runs"]
TEXTBOOK, MEMO = "IDS (textbook)", "IDS with memo table"


def n(value, digits=0):
    """Number with thousands separators, rounded to `digits` decimals (0 = a whole number)."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return f"{value:,.{digits}f}"


def ms(value):
    """A running time in milliseconds with about three significant digits."""
    if value < 1:
        return f"{value:.3f}"
    if value < 10:
        return f"{value:.2f}"
    if value < 100:
        return f"{value:.1f}"
    return f"{value:,.0f}"


def pct(part, whole, digits=0):
    return f"{100 * part / whole:.{digits}f}%"


def s2(layout, algorithm, key):
    return S2[(layout, algorithm)][key]


def loc(layout, algorithm, key):
    return LOC[(layout, algorithm)][key]


def keep_header_with_first_row(table):
    """A table that may run over a page break never leaves its header row alone at the foot of a page."""
    for cell in table.rows[0].cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.keep_with_next = True
    return table


def effective_branching_factor(generated, depth):
    """b* such that 1 + b* + b*^2 + ... + b*^depth = generated + 1 (bisection), as in the Phase II report."""
    low, high = 1.0000001, 4.0
    for _ in range(80):
        mid = (low + high) / 2
        total = (mid ** (depth + 1) - 1) / (mid - 1)
        if total < generated + 1:
            low = mid
        else:
            high = mid
    return (low + high) / 2


# --------------------------------------------------------------------------------------
# Cached runs of the project code
# --------------------------------------------------------------------------------------
_CACHE_FILE = WORK / "guide_cache.json"
_cache = {} if RERUN or not _CACHE_FILE.exists() else json.loads(_CACHE_FILE.read_text(encoding="utf-8"))


def _cached(key, compute):
    if key not in _cache:
        _cache[key] = compute()
        _CACHE_FILE.write_text(json.dumps(_cache, indent=1), encoding="utf-8")
    return _cache[key]


def run_command(arguments, cwd=None):
    """Run `python -B <arguments>` with the project code and return what it printed (stdout + stderr).

    Nothing is written into the project: bytecode files are switched off and the callers pass an
    --out folder inside the cache folder to the run scripts."""
    def compute():
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        done = subprocess.run([PYTHON, "-B", *[str(a) for a in arguments]], capture_output=True, text=True,
                              cwd=str(cwd or WORK), env=env, timeout=900)
        assert done.returncode == 0, (arguments, done.stderr[-2000:])
        return {"stdout": done.stdout, "stderr": done.stderr}
    return _cached("cmd: " + " ".join(str(a) for a in arguments) + " @ " + str(cwd or WORK), compute)


_SESSION_RUNNER = r'''
import code, contextlib, io, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
blocks = json.loads(sys.stdin.read())
console = code.InteractiveConsole()
result = {}
for name, lines in blocks:
    transcript, more = [], False
    for line in lines:
        buffer = io.StringIO()
        prompt = "... " if more else ">>> "
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            more = console.push(line)
        transcript.append([prompt, line, buffer.getvalue()])
    result[name] = transcript
sys.stdout.write(json.dumps(result))
'''


def run_session(key, blocks):
    """Feed lines to a real Python interpreter session (code.InteractiveConsole) started in the
    Phase II code folder and return, for every block, the transcript [(prompt, line, output), ...].

    `blocks` is a list of (name, [lines]); all blocks share one session, in the given order. An
    empty line ends an indented block, exactly as at the >>> prompt."""
    def compute():
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        done = subprocess.run([PYTHON, "-B", "-c", _SESSION_RUNNER, str(CODE2)], input=json.dumps(blocks),
                              capture_output=True, text=True, cwd=str(WORK), env=env, timeout=900)
        assert done.returncode == 0, done.stderr[-2000:]
        return json.loads(done.stdout)
    return _cached("session: " + key + json.dumps(blocks), compute)


def transcript_text(transcript, drop_time=True):
    """A session transcript as text: '>>> code' lines followed by what Python printed."""
    out = []
    for prompt, line, printed in transcript:
        if line.strip():
            out.append(prompt + line)
        printed = printed.rstrip("\n")
        if not printed:
            continue
        lines = printed.split("\n")
        if lines[0].startswith("Traceback"):               # keep only the error message itself
            lines = [lines[-1]]
        for text in lines:
            if drop_time:
                text = re.sub(r" time=[\d.]+ ms", "", text)
            out.extend(textwrap.wrap(text, CODE_WIDTH, subsequent_indent="    ") or [""])
    for text in out:
        assert len(text) <= CODE_WIDTH, text
    return "\n".join(out)


def excerpt(relative_path, first, last, anchor=None):
    """Lines of a Phase II source file, from the line containing `first` to the line containing
    `last` (the search starts at the line containing `anchor`, if given), without the common
    indentation. The text is read from the file itself, so a quoted excerpt cannot differ from
    the code. Only the run of spaces in front of a trailing comment is shortened when a line
    would not fit on the page."""
    lines = (CODE2 / relative_path).read_text(encoding="utf-8").split("\n")
    start = 0
    if anchor is not None:
        start = next(i for i, line in enumerate(lines) if anchor in line)
    begin = next(i for i in range(start, len(lines)) if first in lines[i])
    end = next(i for i in range(begin, len(lines)) if last in lines[i])
    block = textwrap.dedent("\n".join(lines[begin:end + 1])).split("\n")
    out = []
    for line in block:
        if len(line) > CODE_WIDTH and "  #" in line:
            code, comment = line.split("  #", 1)
            line = code.rstrip() + "  #" + comment
        assert len(line) <= CODE_WIDTH, (relative_path, len(line), line)
        out.append(line)
    return "\n".join(out)


def load_whatif():
    """Results of the extra experiments (study_experiments.py); they are run when missing or with --rerun."""
    path = WORK / "whatif_results.json"
    if RERUN or not path.exists():
        import study_experiments
        path.write_text(json.dumps(study_experiments.run_all(), indent=1), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


W = load_whatif()

# --------------------------------------------------------------------------------------
# Consistency checks: the three sources must tell the same story
# --------------------------------------------------------------------------------------
for _name in LAYOUTS:
    for _alg in UNINFORMED:                      # Phase I numbers were reproduced exactly in the Phase II run
        for _key in ("path_cost", "steps", "nodes_generated", "nodes_expanded", "max_frontier",
                     "max_nodes_in_memory", "solution"):
            assert M1[(_name, _alg)][_key] == S2[(_name, _alg)][_key], (_name, _alg, _key)
    assert OPT[_name] == S2[(_name, "UCS")]["path_cost"] == TRADE[_name]["optimal_cost"]
    for _alg in ("BFS", "DFS", "UCS", "IDS", "Greedy (h2)", "A* (h2)", "A* (h1)"):   # our own runs agree
        _mine = W["action_order"][_name]["original"][_alg]
        _theirs = S2[(_name, _alg)]
        assert (_mine["cost"], _mine["steps"], _mine["expanded"], _mine["generated"], _mine["max_memory"]) == (
            _theirs["path_cost"], _theirs["steps"], _theirs["nodes_expanded"], _theirs["nodes_generated"],
            _theirs["max_nodes_in_memory"]), (_name, _alg)
    for _key in ("free_cells", "pellets", "upper_bound", "valid", "reachable"):
        assert W["model"][_name][_key] == SIZE[_name][_key]
    assert W["model"][_name]["transitions"] == HEUR[(_name, "h1")]["transitions_checked"]
    assert W["decoding"][_name]["orders"] == LAND[_name]["orders"]
    assert W["decoding"][_name]["optimal_orders"] == LAND[_name]["optimal_orders"]
for _label, _key in (("SA final", "Simulated Annealing"), ("GA final", "Genetic Algorithm"), ("HC plain", "Hill Climbing"),
                     ("HC 9 restarts", HC_RR)):
    assert W["local"][_label]["eval"]["hits"] == LOC[(L, _key)]["optimal_runs"], _label
    assert W["local"][_label]["eval"]["mean"] == LOC[(L, _key)]["mean"], _label
assert W["local"]["SA final"]["tuning"]["hits"] == TSA[(SA["start_temperature"], SA["cooling_rate"])]["hits"]
assert W["local"]["SA cooling 0.9"]["tuning"]["hits"] == TSA[(10.0, 0.9)]["hits"]
assert W["local"]["SA start 1"]["tuning"]["hits"] == TSA[(1.0, 0.995)]["hits"]
assert W["local"]["GA no crossover"]["tuning"]["hits"] == ONE[("GA", "crossover_rate", 0.0)]["hits"]
assert W["local"]["HC sideways 20"]["tuning"]["hits"] == ONE[("HC", "max_sideways", 20)]["hits"]
assert W["local"]["HC 9 restarts"]["tuning"]["hits"] == ONE[("HC", "restarts", 9)]["hits"]
assert W["local"]["hc_costs_by_seed"] == [r["cost"] for r in sorted(RUNS[(L, "Hill Climbing")], key=lambda r: r["seed"])]
assert W["restarts"]["p_single_climb"] == LAND[L]["hc_success_probability"]
