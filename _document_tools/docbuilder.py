"""Small helper around python-docx for building the project documents (reports, statements,
study guide). Inline markup understood by para()/bullets()/table cells:

    **bold**    __italic__    `code`    ^{superscript}    _{subscript}
"""
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

INK = RGBColor(0x1A, 0x1A, 0x1A)
SOFT = RGBColor(0x52, 0x51, 0x4E)
ACCENT = RGBColor(0x1C, 0x4E, 0x8A)
HEADER_FILL = "DCE8F7"
STRIPE_FILL = "F6F8FB"
BODY_FONT = "Calibri"
CODE_FONT = "Consolas"

_TOKEN = re.compile(r"(\*\*.+?\*\*|__.+?__|`.+?`|\^\{.+?\}|_\{.+?\})")


def _set_cell_shading(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    shade = OxmlElement("w:shd")
    shade.set(qn("w:val"), "clear")
    shade.set(qn("w:color"), "auto")
    shade.set(qn("w:fill"), fill)
    props.append(shade)


def _set_cell_margins(table, top=50, bottom=50, left=90, right=90):
    props = table._tbl.tblPr
    margins = OxmlElement("w:tblCellMar")
    for side, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        margins.append(node)
    props.append(margins)


def _add_field(paragraph, instruction):
    """Insert a Word field (e.g. PAGE or TOC) into a paragraph."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for node in (begin, text, separate, placeholder, end):
        run._r.append(node)
    return run


class Doc:
    def __init__(self, margins_cm=2.2, body_pt=11):
        self.doc = Document()
        self.body_pt = body_pt
        self.figure_no = 0
        self.table_no = 0
        section = self.doc.sections[0]
        section.page_width, section.page_height = Cm(21.0), Cm(29.7)        # A4
        for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(section, side, Cm(margins_cm))
        self.text_width_cm = 21.0 - 2 * margins_cm
        self._styles()

    # ------------------------------------------------------------------ styles
    def _styles(self):
        styles = self.doc.styles
        normal = styles["Normal"]
        normal.font.name = BODY_FONT
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        normal.font.size = Pt(self.body_pt)
        normal.font.color.rgb = INK
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.12
        sizes = {"Heading 1": (17, 16, 6), "Heading 2": (13.5, 12, 4), "Heading 3": (11.5, 9, 3)}
        for name, (size, before, after) in sizes.items():
            style = styles[name]
            style.font.name = BODY_FONT
            style.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
            style.element.rPr.rFonts.set(qn("w:ascii"), BODY_FONT)
            style.element.rPr.rFonts.set(qn("w:hAnsi"), BODY_FONT)
            style.font.size = Pt(size)
            style.font.bold = True
            style.font.italic = False
            style.font.color.rgb = ACCENT if name != "Heading 3" else INK
            style.paragraph_format.space_before = Pt(before)
            style.paragraph_format.space_after = Pt(after)
            style.paragraph_format.keep_with_next = True
        for name in ("List Bullet", "List Number"):
            styles[name].font.name = BODY_FONT
            styles[name].font.size = Pt(self.body_pt)
            styles[name].paragraph_format.space_after = Pt(3)
        # Compact styles for the table of contents (Word applies them when it fills the field).
        for level, indent_cm in ((1, 0.0), (2, 0.45), (3, 0.9)):
            style = styles.add_style(f"toc {level}", WD_STYLE_TYPE.PARAGRAPH, builtin=True)
            style.base_style = normal
            style.font.size = Pt(10)
            style.paragraph_format.space_before = Pt(0)
            style.paragraph_format.space_after = Pt(1.5)
            style.paragraph_format.line_spacing = 1.0
            style.paragraph_format.left_indent = Cm(indent_cm)

    # ------------------------------------------------------------------ inline text
    def _runs(self, paragraph, text, size=None, color=None, bold=None, italic=None):
        for piece in _TOKEN.split(text):
            if not piece:
                continue
            if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
                self._runs(paragraph, piece[2:-2], size, color, True, italic)      # markup may nest
                continue
            if piece.startswith("__") and piece.endswith("__") and len(piece) > 4:
                self._runs(paragraph, piece[2:-2], size, color, bold, True)
                continue
            is_code = piece.startswith("`") and piece.endswith("`") and len(piece) > 2
            if is_code:
                run = paragraph.add_run(piece[1:-1])
                run.font.name = CODE_FONT
                run._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CODE_FONT)
                run.font.size = Pt((size or self.body_pt) - 1)
            elif piece.startswith("^{") and piece.endswith("}"):
                run = paragraph.add_run(piece[2:-1])
                run.font.superscript = True
            elif piece.startswith("_{") and piece.endswith("}"):
                run = paragraph.add_run(piece[2:-1])
                run.font.subscript = True
            else:
                run = paragraph.add_run(piece)
            if size and not is_code:
                run.font.size = Pt(size)
            if color is not None:
                run.font.color.rgb = color
            if bold is not None:
                run.bold = bold
            if italic is not None:
                run.italic = italic
        return paragraph

    # ------------------------------------------------------------------ blocks
    def heading(self, text, level=1, new_page=False):
        paragraph = self.doc.add_heading(text, level=level)
        if new_page:                                 # start the heading on a fresh page
            paragraph.paragraph_format.page_break_before = True
        return paragraph

    def para(self, text, size=None, color=None, align=None, bold=None, italic=None,
             space_after=None, space_before=None, keep_with_next=False, indent_cm=None):
        paragraph = self.doc.add_paragraph()
        self._runs(paragraph, text, size=size, color=color, bold=bold, italic=italic)
        if align == "center":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "justify":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif align == "right":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if space_after is not None:
            paragraph.paragraph_format.space_after = Pt(space_after)
        if space_before is not None:
            paragraph.paragraph_format.space_before = Pt(space_before)
        if keep_with_next:
            paragraph.paragraph_format.keep_with_next = True
        if indent_cm is not None:
            paragraph.paragraph_format.left_indent = Cm(indent_cm)
        return paragraph

    def bullets(self, items, size=None):
        for item in items:
            paragraph = self.doc.add_paragraph(style="List Bullet")
            self._runs(paragraph, item, size=size)

    def numbered(self, items, size=None):
        """A numbered list that starts again at 1 (each call gets its own numbering instance)."""
        numbering = self.doc.part.numbering_part.numbering_definitions._numbering
        style_num_id = self.doc.styles["List Number"].element.pPr.numPr.numId.val
        abstract_id = numbering.num_having_numId(style_num_id).abstractNumId.val
        new_num = numbering.add_num(abstract_id)
        new_num.add_lvlOverride(ilvl=0).add_startOverride(1)
        for item in items:
            paragraph = self.doc.add_paragraph(style="List Number")
            num_pr = paragraph._p.get_or_add_pPr().get_or_add_numPr()
            num_pr.get_or_add_ilvl().val = 0
            num_pr.get_or_add_numId().val = new_num.numId
            self._runs(paragraph, item, size=size)

    def code(self, text, size=8.5):
        """Monospaced block (one paragraph per line, light grey background)."""
        lines = text.strip("\n").split("\n")
        for index, line in enumerate(lines):
            paragraph = self.doc.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(0 if index < len(lines) - 1 else 6)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.left_indent = Cm(0.4)
            paragraph.paragraph_format.keep_with_next = index < len(lines) - 1   # keep the block on one page
            run = paragraph.add_run(line if line else " ")
            run.font.name = CODE_FONT
            run._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CODE_FONT)
            run.font.size = Pt(size)
            props = paragraph._p.get_or_add_pPr()
            shade = OxmlElement("w:shd")
            shade.set(qn("w:val"), "clear")
            shade.set(qn("w:color"), "auto")
            shade.set(qn("w:fill"), "F3F3F1")
            props.append(shade)

    def table(self, headers, rows, widths_cm=None, caption=None, size=9, align=None,
              stripe=True, bold_first_col=False, keep_together=None, keep_blocks=None):
        """A table with a shaded header row. `align` = list of 'l'/'c'/'r' per column.
        Short tables (up to 14 rows) are kept on one page unless keep_together=False.
        keep_blocks=N lets the table break across pages, but only between blocks of N rows
        (the header row is repeated on the next page)."""
        if keep_together is None:
            keep_together = len(rows) <= 14 and not keep_blocks
        if caption:
            self.table_no += 1
            self.para(f"**Table {self.table_no}.** {caption}", size=9.5, color=SOFT,
                      space_after=3, space_before=6, keep_with_next=True)
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        _set_cell_margins(table)
        if widths_cm is None:
            widths_cm = [self.text_width_cm / len(headers)] * len(headers)
        align = align or ["l"] * len(headers)
        alignment = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER, "r": WD_ALIGN_PARAGRAPH.RIGHT}

        def fill(cell, text, column, header=False):
            cell.width = Cm(widths_cm[column])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.alignment = alignment["c" if header and align[column] != "l" else align[column]]
            self._runs(paragraph, str(text), size=size,
                       bold=True if header or (bold_first_col and column == 0) else None)

        for column, text in enumerate(headers):
            fill(table.rows[0].cells[column], text, column, header=True)
            _set_cell_shading(table.rows[0].cells[column], HEADER_FILL)
        header_props = table.rows[0]._tr.get_or_add_trPr()
        repeat = OxmlElement("w:tblHeader")
        repeat.set(qn("w:val"), "true")
        header_props.append(repeat)
        for index, row in enumerate(rows):
            cells = table.add_row().cells
            for column, text in enumerate(row):
                fill(cells[column], text, column)
                if stripe and index % 2 == 1:
                    _set_cell_shading(cells[column], STRIPE_FILL)
        for row in table.rows:                       # keep rows from splitting across pages
            props = row._tr.get_or_add_trPr()
            no_split = OxmlElement("w:cantSplit")
            no_split.set(qn("w:val"), "true")
            props.append(no_split)
        if keep_together:                            # "keep with next" on every row but the last
            for row in table.rows[:-1]:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.keep_with_next = True
        elif keep_blocks:                            # breaks allowed only after every N-th data row
            for index, row in enumerate(table.rows[:-1]):          # index 0 = header row
                if index == 0 or index % keep_blocks != 0:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.keep_with_next = True
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)
        spacer.paragraph_format.line_spacing = 0.6
        return table

    def figure(self, path, caption, width_cm=None):
        self.figure_no += 1
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.keep_with_next = True
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.add_run().add_picture(str(path), width=Cm(width_cm or self.text_width_cm))
        self.para(f"**Figure {self.figure_no}.** {caption}", size=9.5, color=SOFT, align="center",
                  space_after=10)
        return self.figure_no

    def figure_row(self, paths, caption, widths_cm=None):
        """Several pictures side by side (borderless table) under one caption."""
        self.figure_no += 1
        count = len(paths)
        widths_cm = widths_cm or [self.text_width_cm / count] * count
        table = self.doc.add_table(rows=1, cols=count)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        for column, (path, width) in enumerate(zip(paths, widths_cm)):
            cell = table.rows[0].cells[column]
            cell.width = Cm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.keep_with_next = True
            paragraph.add_run().add_picture(str(path), width=Cm(width - 0.3))
        self.para(f"**Figure {self.figure_no}.** {caption}", size=9.5, color=SOFT, align="center",
                  space_after=10, space_before=3)
        return self.figure_no

    def callout(self, lines, fill="EEF3FA"):
        """A shaded box with a few lines of text (used for key findings)."""
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        _set_cell_margins(table, top=110, bottom=110, left=180, right=180)
        cell = table.rows[0].cells[0]
        cell.width = Cm(self.text_width_cm)
        _set_cell_shading(cell, fill)
        first = True
        for line in lines:
            paragraph = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            paragraph.paragraph_format.space_after = Pt(3)
            self._runs(paragraph, line, size=self.body_pt - 0.5)
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)
        spacer.paragraph_format.line_spacing = 0.6

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def toc(self, levels="1-2"):
        paragraph = self.doc.add_paragraph()
        _add_field(paragraph, f'TOC \\o "{levels}" \\h \\z \\u')

    def page_numbers(self, prefix=""):
        """Centered 'page N' footer on every page of the last section."""
        footer = self.doc.sections[-1].footer
        footer.is_linked_to_previous = False
        paragraph = footer.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if prefix:
            run = paragraph.add_run(prefix)
            run.font.size = Pt(8.5)
            run.font.color.rgb = SOFT
        field = _add_field(paragraph, "PAGE")
        field.font.size = Pt(8.5)
        field.font.color.rgb = SOFT

    def new_section(self):
        return self.doc.add_section(WD_SECTION.NEW_PAGE)

    def rule(self):
        """Thin horizontal line (paragraph bottom border)."""
        paragraph = self.doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(6)
        props = paragraph._p.get_or_add_pPr()
        borders = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "C3C2B7")
        borders.append(bottom)
        props.append(borders)

    def save(self, path):
        self.doc.core_properties.author = "CSAI 301 project team"
        self.doc.save(str(path))
        return path
