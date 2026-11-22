"""Builds the one-page contribution statements of both phases.

The allocation below is a PROPOSAL (areas of responsibility); the team has to confirm or edit
it before submitting, so that it describes what each member really did.
"""
from pathlib import Path

from docbuilder import ACCENT, SOFT, Doc
from team import COURSE, PROBLEM_TITLE, TEAM, UNIVERSITY

PROJECT = Path(__file__).resolve().parent.parent

PHASES = {
    1: {
        "title": "Phase I - Problem Modeling and Uninformed Search",
        "date": "21 November 2026",
        "roles": [
            ("Problem model and maze layouts; size of the state space; coordination and submission (team leader)",
             "`problem.py`, `layouts.py`; report Sections 1-2", "Part 1: the problem and the model"),
            ("Breadth-first and depth-first search; the node and counter classes shared by all algorithms",
             "`search_core.py`, BFS and DFS in `uninformed.py`; report Sections 3 and 6.1", "Part 2: BFS and DFS"),
            ("Uniform-cost search and iterative deepening (both versions); fewest steps versus lowest cost",
             "UCS and IDS in `uninformed.py`, `step_cost_tradeoff`; report Sections 5.2, 5.3 and 6.2",
             "Part 3: UCS and IDS"),
            ("Experiments and measurements: timing, memory, result tables, comparison with the theory",
             "`experiments.py`, `run_phase1.py`, `tests/`; report Sections 4, 5.1, 6.3 and 6.4",
             "Part 4: measurements, theory versus results"),
            ("Visualization: explored states, search trees, charts and animations; command-line program and README",
             "`visualize.py`, `main.py`, `README.md`; report Section 7 and all figures",
             "Part 5: visualization and take-away messages"),
        ],
    },
    2: {
        "title": "Phase II - Heuristic Search, Local Search and Comparison",
        "date": "December 2026",
        "roles": [
            ("The two heuristics: design, proofs of admissibility and consistency, check on every state; changes "
             "since Phase I; coordination and submission (team leader)",
             "`heuristics.py`; report Sections 1-2", "Part 1: the two heuristics"),
            ("Greedy Best-First Search and A*; the informed-search experiments",
             "`informed.py`, tests of the informed algorithms; report Section 3", "Part 2: Greedy and A*"),
            ("Local-search formulation (pellet order, objective, neighbours); Hill Climbing with restarts and "
             "sideways moves; analysis of the landscape",
             "`TourProblem` and `hill_climbing` in `local_search.py`, `analyse_landscape`; report Sections 4.1-4.3",
             "Part 3: local search and Hill Climbing"),
            ("Simulated Annealing and the Genetic Algorithm; parameter study with the random-sampling baseline; "
             "the seeded runs",
             "`simulated_annealing`, `genetic_algorithm` and `random_sampling` in `local_search.py`, "
             "`tuning_study`; report Sections 4.4-4.5", "Part 4: SA and GA"),
            ("Comparison of all nine algorithms; experiment on larger mazes; Phase II figures and summary chart; "
             "command-line program and README",
             "`visualize_phase2.py`, `run_phase2.py`, `scaling.py`, `main.py`, `README.md`; report Sections 4.6, "
             "5 and 6",
             "Part 5: comparison and take-away messages"),
        ],
    },
}


def build(phase):
    info = PHASES[phase]
    doc = Doc(margins_cm=2.0, body_pt=10.5)
    doc.para(f"{UNIVERSITY}  |  {COURSE}", size=10, color=SOFT, align="center", space_after=2)
    doc.para("Contribution Statement", size=20, bold=True, color=ACCENT, align="center", space_after=2)
    doc.para(info["title"], size=13, bold=True, align="center", space_after=2)
    doc.para(f"Project: {PROBLEM_TITLE}  |  {info['date']}", size=10, color=SOFT, align="center", space_after=10)
    doc.para(
        "The table lists the part of the project each member was responsible for. Every member is expected to "
        "explain the whole project; the listed part is the one that member owns, has checked and presents in "
        "the video.",
        size=10, align="justify", space_after=6)
    rows = []
    for (name, student_id, _), (role, files, video) in zip(TEAM, info["roles"]):
        rows.append([f"**{name}**  ({student_id})", role, files, video])
    doc.table(["Member", "Responsible for", "Code files and report sections", "Video"], rows,
              widths_cm=[3.3, 5.3, 5.4, 3.0], size=9, stripe=False)
    doc.para(
        "**Shared by all members:** agreeing on the problem model, reviewing the report and the code before "
        "submission, rehearsing and recording the video, and preparing for the oral discussion.",
        size=10, align="justify", space_after=4)
    doc.para(
        "**Use of AI tools:** an AI assistant (Claude, by Anthropic) was used to help write and test the code, "
        "to produce the figures and to draft the documents, as acknowledged in the report. The members listed "
        "above are responsible for their parts and for the submission as a whole.",
        size=10, align="justify", space_after=10)
    doc.para("We confirm that this statement describes our contributions accurately.", size=10, space_after=4)
    doc.table(["Name", "Signature", "Date"], [[name, "", ""] for name, _, _ in TEAM],
              widths_cm=[7.0, 6.0, 4.0], size=9.5, stripe=False)
    out = PROJECT / f"Phase{phase}" / "contribution" / f"Phase{phase}_Contribution_Statement.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    print("written", out)


for number in PHASES:
    build(number)
