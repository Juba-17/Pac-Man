"""Team details and shared front-matter helpers for the generated documents."""
from docbuilder import ACCENT, SOFT

UNIVERSITY = "University of Science and Technology at Zewail City"
COURSE = "CSAI 301"
PROJECT = "Search Algorithms Applied to an AI Problem"
PROBLEM_TITLE = "Pac-Man Food Collection as a Search Problem"

# (name, student id, e-mail) in the order given by the team
TEAM = [
    ("Almoatasembellah Aboubakr", "202400993", "s-almoatasembellah.gafer@zewailcity.edu.eg"),
    ("Rabie Al Sayed Mosa", "202400113", "s-rabie.mosa@zewailcity.edu.eg"),
    ("Amir Elsamahy", "202401724", "s-amir.elsamahy@zewailcity.edu.eg"),
    ("Ebrahim Mohamed Rabia", "202401474", "s-ebrahim.rabia@zewailcity.edu.eg"),
    ("Ahmed Mostafa", "202401612", "s-ahmed.ayman@zewailcity.edu.eg"),
]
LEADER = TEAM[0][0]


def title_page(doc, phase_line, subtitle, date_text):
    """Cover page: university, course, title, team table, date."""
    doc.para(UNIVERSITY, size=12, color=SOFT, align="center", space_before=40, space_after=2)
    doc.para(f"{COURSE}  |  Project: {PROJECT}", size=12, color=SOFT, align="center", space_after=70)
    doc.para(PROBLEM_TITLE, size=26, bold=True, color=ACCENT, align="center", space_after=10)
    doc.para(phase_line, size=16, bold=True, align="center", space_after=6)
    doc.para(subtitle, size=12, color=SOFT, align="center", space_after=60)
    doc.para("Team members", size=11, bold=True, align="center", space_after=4)
    rows = [[name + ("  (team leader)" if name == LEADER else ""), student_id, mail]
            for name, student_id, mail in TEAM]
    doc.table(["Name", "Student ID", "University e-mail"], rows, widths_cm=[6.0, 2.8, 7.4],
              align=["l", "c", "l"], size=10, stripe=False)
    doc.para(date_text, size=11, color=SOFT, align="center", space_before=40)
    doc.page_break()
