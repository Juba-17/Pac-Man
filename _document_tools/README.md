# Document tools (not part of the submission)

These scripts generated the reports, contribution statements, video kits and the study guide
from the result files. You only need them if the results change (for example after feedback
on Phase I) and you want to regenerate a document instead of editing the Word file by hand.

Every script reads the numbers from `Phase1/code/results/phase1/results.json` and
`Phase2/code/results/phase2/results.json`, and stops with an `AssertionError` if a sentence in
the document would no longer be true for the new numbers. Read the failing line: it names the
fact that changed, and the text next to it has to be rewritten.

## Setup

    pip install python-docx python-pptx matplotlib pillow pymupdf

Run the scripts from this folder, after `python run_phase1.py` and `python run_phase2.py`
have produced the results.

## Scripts

| Script | Writes |
|---|---|
| `build_phase1_report.py` | `Phase1/report/Phase1_Report.docx` |
| `build_phase2_report.py` | `Phase2/report/Phase2_Report.docx` |
| `build_contributions.py` | both contribution statements (this overwrites your edits and signatures) |
| `build_video_kit_phase1.py`, `build_video_kit_phase2.py` | slides, script and slide pictures in `PhaseN/video/preparation/` |
| `build_study_guide.py` (`--rerun` to repeat its experiments) | `Study_Guide/Oral_Discussion_Study_Guide.docx` |
| `export_pdf.ps1 file.docx file.pptx ...` | the PDF next to each file (needs Microsoft Word / PowerPoint) |
| `pdf_to_png.py file.pdf out_dir` | page images, to check a layout quickly |

Shared modules: `docbuilder.py` (Word layout), `slidebuilder.py` (slides), `team.py` (names,
IDs, title page), `study_guide_*.py` and `study_experiments.py` (content of the study guide).

The team names and the proposed roles are in `team.py` and `build_contributions.py`.
