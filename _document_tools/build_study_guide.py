"""Builds Study_Guide/Oral_Discussion_Study_Guide.docx - the study aid for the oral discussion.

    python build_study_guide.py            build the document (cached runs of the project code are reused)
    python build_study_guide.py --rerun    run every command, session and experiment again first

Run it from this folder (it imports docbuilder, team and the study_guide_* modules), with
PYTHONDONTWRITEBYTECODE=1 so that nothing is written into the project's code folders. Then
export the PDF with export_pdf.ps1.

Where the content comes from
  * every number: the two results.json files, or whatif_results.json (written by
    study_experiments.py, which runs the unchanged project code), or the output of commands and
    interpreter sessions that this script executes - see study_guide_common.py;
  * every code excerpt: read from the source files at build time (study_guide_common.excerpt);
  * every fact the text relies on is asserted next to the sentence that states it.
The experiments script is copied next to the guide as whatif_experiments.py, so that the team can
repeat every experiment.
"""
import shutil
import sys

sys.dont_write_bytecode = True

from docbuilder import ACCENT, SOFT, Doc  # noqa: E402

import study_guide_common as common  # noqa: E402
import study_guide_part1 as part1  # noqa: E402
import study_guide_part2 as part2  # noqa: E402
import study_guide_part3 as part3  # noqa: E402
import study_guide_part4 as part4  # noqa: E402


def main():
    doc = Doc(margins_cm=1.8, body_pt=10)
    doc.doc.styles["Normal"].paragraph_format.line_spacing = 1.06      # a little tighter than the reports

    # ---------------------------------------------------------------- cover block and contents
    doc.para("CSAI 301  |  Search Algorithms Applied to an AI Problem  |  Pac-Man Food Collection", size=10.5,
             color=SOFT, space_before=6, space_after=10)
    doc.para("Oral Discussion Study Guide", size=24, bold=True, color=ACCENT, space_after=4)
    doc.para("How our code works, the theory behind it, and the \"what if\" questions - Phase I and Phase II",
             size=12.5, space_after=10)
    doc.callout([
        "**A study aid for the five team members. It is not part of the submission.**",
        "It follows the final code in `Phase1\\code` and `Phase2\\code` and the two final reports. Every number in "
        "it was read from the submitted result files or produced by running the project code; every code excerpt "
        "was copied from the source files by the script that built this document.",
    ])
    doc.para("Contents", size=13.5, bold=True, color=ACCENT, space_before=8, space_after=4)
    doc.toc("1-3")
    doc.para("21 November 2026", size=9, color=SOFT, space_before=8)
    doc.page_numbers(prefix="Oral discussion study guide - not part of the submission  |  page ")

    # ---------------------------------------------------------------- the seven sections
    part1.build(doc)                                   # 1 how to use + tour, 2 the model
    part2.build(doc)                                   # 3 code walkthrough
    questions, question_refs = part3.build(doc)        # 4 theory questions
    what_ifs = part4.build(doc, question_refs)         # 5 what-if, 6 cheat sheet, 7 who demos what

    common.OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(common.TOOLS / "study_experiments.py", common.COMPANION)
    doc.save(common.OUT)
    print(f"written {common.OUT}")
    print(f"written {common.COMPANION}")
    print(f"{questions} theory questions, {what_ifs} what-if questions")


if __name__ == "__main__":
    main()
