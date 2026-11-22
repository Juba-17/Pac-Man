# CSAI 301 Project - Pac-Man Food Collection as a Search Problem

Everything for both phases of the project is in this folder.

Team: Almoatasembellah Aboubakr (202400993, team leader), Rabie Al Sayed Mosa (202400113),
Amir Elsamahy (202401724), Ebrahim Mohamed Rabia (202401474), Ahmed Mostafa (202401612).

## What is where

| Folder / file | What it is | Goes into the submission? |
|---|---|---|
| `Phase1/code/` | Phase I code (BFS, DFS, UCS, IDS), its `README.md`, unit tests and the results (`results/phase1/`: tables, figures, animations) | yes |
| `Phase1/report/` | Phase I report (`Phase1_Report.pdf` and the Word file) | yes |
| `Phase1/contribution/` | one-page contribution statement | yes |
| `Phase1/video/` | **put the recorded video here**; `preparation/` holds the slides and the 3-minute script | the video: yes - `preparation/`: no |
| `Phase2/code/` | Phase II code (Greedy, A*, Hill Climbing, Simulated Annealing, Genetic Algorithm) plus the unchanged Phase I code, `README.md`, tests, results (`results/phase2/`) | yes |
| `Phase2/report/` | Phase II report | yes |
| `Phase2/contribution/` | one-page contribution statement | yes |
| `Phase2/video/` | as for Phase I | the video: yes - `preparation/`: no |
| `Study_Guide/` | preparation for the oral discussion: code walkthrough, theory questions, "what if" questions | no (for you) |
| `Project_Description.docx` | the course brief | no |
| `make_phase1_archive.bat`, `make_phase2_archive.bat` | build the single archive that has to be uploaded (they call `make_submission_archive.ps1`) | - |
| `_document_tools/` | the scripts that generated the reports, statements, slides and study guide from the results | no |

## Before you submit Phase I (due 21 November)

1. **Run the code once on your own machine** (from `Phase1/code`):
   `python main.py`, then `python -m unittest discover -s tests` (33 tests must pass).
   The figures need Matplotlib: `pip install -r requirements.txt`.
2. **Read the report** (`Phase1/report/Phase1_Report.pdf`). Everyone must be able to explain every
   section and every part of the code: the oral discussion is individual. Use `Study_Guide/`.
3. **Contribution statement**: open `Phase1/contribution/Phase1_Contribution_Statement.docx`.
   The roles in it are a proposal. Change them until they say what each of you really did,
   sign it, and save it as PDF again (File > Save As > PDF, same file name).
4. **Record the video** (3 minutes, every member appears or speaks). The slides and the script,
   already split into five parts, are in `Phase1/video/preparation/`. Save the recording as
   `Phase1/video/Phase1_Video.mp4`.
5. **Build the archive**: double-click `make_phase1_archive.bat`. It writes
   `CSAI301_PacMan_Phase1.zip` in this folder (video + report + code + contribution statement)
   and warns you if the video is missing.
6. **The team leader uploads** the zip on the course platform.

## Before you submit Phase II (week 12/13)

1. If you got feedback on Phase I that changes the model, make the change and list it in
   Section 1.2 "Changes since Phase I" of the Phase II report (at the moment it says that
   nothing was changed). If the code changes, run `python run_phase2.py` again and update the
   numbers in the report.
2. Set the date on the cover page of the report if you want an exact one.
3. Then the same steps as above with the `Phase2` folders and `make_phase2_archive.bat`
   (74 unit tests must pass: the 33 of Phase I and 41 new ones).

## Where each requirement of the brief is covered

### Phase I

| Requirement | Where |
|---|---|
| State, initial state, goal test, actions, transition model, step costs | report Section 2.1; `pacman_search/problem.py` |
| Size of the state space (1K-10K) and how it was estimated | report Section 2.2; `results/phase1/state_space.csv` |
| Modeling assumptions | report Section 2.3 |
| BFS, DFS, UCS, IDS implemented by the team | `pacman_search/uninformed.py`; report Section 3 |
| Solution path, path cost, nodes generated / expanded, max frontier, running time | report Sections 5.1-5.2 and the Appendix; `results/phase1/metrics.csv`, `solutions.txt` |
| Analysis: time, memory, completeness, optimality - theory and measured | report Section 6; `results/phase1/state_graph.csv` |
| Visualization: explored states, final path, search trees for each algorithm | report Section 7; `results/phase1/figures/`, `results/phase1/animations/` |
| Reflections | report Section 8 |
| README, commented code, fixed and reproducible results | `Phase1/code/README.md` |
| Outside sources and AI tools cited | report: References and "Use of AI tools" |

### Phase II

| Requirement | Where |
|---|---|
| "Changes since Phase I" | report Section 1.2 |
| Two heuristics, why reasonable, admissible? consistent? | report Section 2; `pacman_search/heuristics.py`; `results/phase2/heuristic_analysis.csv` |
| Greedy Best-First and A* with both heuristics, same measurements, effect of each heuristic | report Section 3; `pacman_search/informed.py`; `results/phase2/search_metrics.csv` |
| Local search: representation, objective, neighbours | report Section 4.1; `pacman_search/local_search.py` |
| Hill Climbing, Simulated Annealing (cooling schedule), Genetic Algorithm (all its parts) | report Section 4.3; `pacman_search/local_search.py` |
| Parameter values justified | report Section 4.4 (300 runs per setting, compared with random sampling); `results/phase2/tuning_*.csv` |
| At least 10 seeded runs; best, average, worst | report Section 4.5 (30 seeds); `results/phase2/local_search_summary.csv`, `local_search_runs.csv` |
| One table with all nine algorithms: time, memory, cost, optimality, completeness | report Section 5, Table 12; `results/phase2/comparison_all.csv` |
| Which algorithm suits the problem best; where each one fails | report Sections 5.1-5.2 |
| Extra (not required): local search against random sampling on larger mazes | report Section 4.6; `pacman_search/scaling.py`; `results/phase2/scaling_*.csv` |
| Visualization: explored states and path for Greedy / A*, convergence plots, summary chart | report Figures 2, 8 and 13; `results/phase2/figures/` |
| Code of both phases with README, fixed seeds | `Phase2/code/README.md` |

## Things to know

* **AI use is declared.** Both reports have a section "Use of AI tools" and both contribution
  statements mention it, because the course policy requires AI tools to be cited. The policy
  also requires that you understand what you submit: each member is examined alone on every
  part of the code, including "what if" questions.
* **The numbers are reproducible.** Paths, costs and node counts are the same on every
  machine. Running times are not: yours will differ from the ones in the reports.
* **The documents can be edited directly** in Word (`.docx`) and saved as PDF again. The
  scripts in `_document_tools/` are only needed if you want to regenerate a document from new
  results.
