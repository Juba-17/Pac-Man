"""Small helper around python-pptx for the project's video slide decks (16:9).

One visual system for every deck: white surface, dark-blue titles, one orange accent that
is used only for the take-away line. Every slide can carry
    speaker   shown at the top right ("who talks here, and when")
    takeaway  one sentence in the bar at the bottom of the slide (the message to remember)
    note      the spoken text, stored in the speaker notes

    deck = Deck("CSAI 301  |  Pac-Man Food Collection  |  Phase I")
    deck.title_slide(...); deck.bullets_slide(...); deck.figure_slide(...)
    deck.two_figures_slide(...); deck.table_slide(...); deck.takeaways_slide(...)
    deck.save("deck.pptx")
"""
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

INK = RGBColor(0x1A, 0x1A, 0x1A)
SOFT = RGBColor(0x52, 0x51, 0x4E)
ACCENT = RGBColor(0x1C, 0x4E, 0x8A)        # titles
BLUE = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xEB, 0x68, 0x34)        # take-away bar only
PALE = RGBColor(0xEE, 0xF3, 0xFA)          # panels, table header
STRIPE = RGBColor(0xF6, 0xF8, 0xFB)
RULE = RGBColor(0xC9, 0xD3, 0xE0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

W, H = 13.333, 7.5                         # slide size in inches
LEFT, RIGHT = 0.6, 0.6                     # side margins
TOP_BODY = 1.45                            # where the body starts (below the title)
BOTTOM_BODY = 6.25                         # where the body ends when there is a take-away bar


class Deck:
    def __init__(self, footer):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(W), Inches(H)
        self.footer = footer
        self.blank = self.prs.slide_layouts[6]

    # ------------------------------------------------------------------ low-level pieces
    def _text(self, slide, left, top, width, height, text, size=18, bold=False, color=INK,
              align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = Inches(0.04)
        frame.margin_top = frame.margin_bottom = Inches(0.02)
        frame.vertical_anchor = anchor
        paragraph = frame.paragraphs[0]
        paragraph.alignment = align
        self._run(paragraph, text, size, bold, color, italic)
        return box

    def _run(self, paragraph, text, size, bold=False, color=INK, italic=False):
        """Adds text to a paragraph; **double stars** switch bold on and off."""
        for index, piece in enumerate(text.split("**")):
            if not piece:
                continue
            run = paragraph.add_run()
            run.text = piece
            run.font.name = FONT
            run.font.size = Pt(size)
            run.font.bold = bold or index % 2 == 1
            run.font.italic = italic
            run.font.color.rgb = color

    def _rect(self, slide, left, top, width, height, fill, line=None):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
        if line is None:
            shape.line.fill.background()
        else:
            shape.line.color.rgb = line
            shape.line.width = Pt(0.75)
        shape.shadow.inherit = False
        return shape

    def _picture(self, slide, path, left, top, width, height):
        """Place a picture inside the box (left, top, width, height), centred, keeping its shape."""
        with Image.open(path) as image:
            pixel_w, pixel_h = image.size
        scale = min(width / pixel_w, height / pixel_h)
        w, h = pixel_w * scale, pixel_h * scale
        return slide.shapes.add_picture(str(path), Inches(left + (width - w) / 2), Inches(top + (height - h) / 2),
                                        Inches(w), Inches(h))

    def _frame(self, title, speaker=None, takeaway=None, note=""):
        """A slide with the title, the speaker tag, the footer and (optionally) the take-away bar."""
        slide = self.prs.slides.add_slide(self.blank)
        self._rect(slide, 0, 0, 0.22, H, ACCENT)                                   # coloured edge
        self._text(slide, LEFT, 0.38, W - LEFT - RIGHT - 3.4, 0.9, title, size=30, bold=True, color=ACCENT,
                   anchor=MSO_ANCHOR.MIDDLE)
        if speaker:
            self._text(slide, W - RIGHT - 3.4, 0.45, 3.4, 0.6, speaker, size=13, color=SOFT, align=PP_ALIGN.RIGHT,
                       anchor=MSO_ANCHOR.MIDDLE)
        line = self._rect(slide, LEFT, 1.3, W - LEFT - RIGHT, 0.02, RULE)
        line.name = "title rule"
        number = len(self.prs.slides)
        self._text(slide, LEFT, H - 0.42, 8.0, 0.3, self.footer, size=10.5, color=SOFT)
        self._text(slide, W - RIGHT - 1.0, H - 0.42, 1.0, 0.3, str(number), size=10.5, color=SOFT, align=PP_ALIGN.RIGHT)
        if takeaway:
            self._rect(slide, LEFT, 6.38, 0.09, 0.56, ORANGE)
            self._rect(slide, LEFT + 0.09, 6.38, W - LEFT - RIGHT - 0.09, 0.56, PALE)
            self._text(slide, LEFT + 0.25, 6.38, W - LEFT - RIGHT - 0.4, 0.56, takeaway, size=16, bold=True,
                       anchor=MSO_ANCHOR.MIDDLE)
        if note:
            slide.notes_slide.notes_text_frame.text = note
        return slide

    def _bullets(self, slide, left, top, width, height, bullets, size=20):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.word_wrap = True
        first = True
        for item in bullets:
            level = 1 if item.startswith("- ") else 0
            text = item[2:] if level else item
            paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
            first = False
            paragraph.space_after = Pt(9 if level == 0 else 5)
            self._run(paragraph, ("•  " if level == 0 else "–  ") + text, size if level == 0 else size - 3,
                      color=INK if level == 0 else SOFT)
            if level:
                paragraph.level = 1
        return box

    # ------------------------------------------------------------------ slide types
    def title_slide(self, title, subtitle, lines, note=""):
        slide = self.prs.slides.add_slide(self.blank)
        self._rect(slide, 0, 0, W, 2.9, ACCENT)
        self._text(slide, 0.9, 0.75, W - 1.8, 1.2, title, size=40, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        self._text(slide, 0.9, 1.95, W - 1.8, 0.6, subtitle, size=20, color=WHITE)
        top = 3.35
        for line in lines:
            self._text(slide, 0.9, top, W - 1.8, 0.45, line, size=17, color=INK if top < 3.4 else SOFT)
            top += 0.47
        if note:
            slide.notes_slide.notes_text_frame.text = note
        return slide

    def bullets_slide(self, title, bullets, speaker=None, takeaway=None, note="", image=None, image_share=0.45,
                      size=20):
        """Bullets on the left; an optional picture on the right (image_share = its part of the width)."""
        slide = self._frame(title, speaker, takeaway, note)
        bottom = BOTTOM_BODY if takeaway else 6.9
        body_w = W - LEFT - RIGHT
        if image:
            image_w = body_w * image_share
            self._bullets(slide, LEFT, TOP_BODY + 0.1, body_w - image_w - 0.3, bottom - TOP_BODY - 0.1, bullets, size)
            self._picture(slide, image, W - RIGHT - image_w, TOP_BODY + 0.05, image_w, bottom - TOP_BODY - 0.1)
        else:
            self._bullets(slide, LEFT, TOP_BODY + 0.1, body_w, bottom - TOP_BODY - 0.1, bullets, size)
        return slide

    def figure_slide(self, title, image, caption=None, speaker=None, takeaway=None, note=""):
        """One large picture, with an optional small caption under it."""
        slide = self._frame(title, speaker, takeaway, note)
        bottom = BOTTOM_BODY if takeaway else 6.9
        caption_h = 0.35 if caption else 0.0
        self._picture(slide, image, LEFT, TOP_BODY, W - LEFT - RIGHT, bottom - TOP_BODY - caption_h)
        if caption:
            self._text(slide, LEFT, bottom - caption_h, W - LEFT - RIGHT, caption_h, caption, size=13, color=SOFT,
                       align=PP_ALIGN.CENTER)
        return slide

    def two_figures_slide(self, title, images, captions=None, speaker=None, takeaway=None, note="", shares=None):
        """Two (or three) pictures side by side, each with an optional caption."""
        slide = self._frame(title, speaker, takeaway, note)
        bottom = BOTTOM_BODY if takeaway else 6.9
        gap = 0.3
        total = W - LEFT - RIGHT - gap * (len(images) - 1)
        shares = shares or [1 / len(images)] * len(images)
        caption_h = 0.4 if captions else 0.0
        left = LEFT
        for index, image in enumerate(images):
            width = total * shares[index]
            self._picture(slide, image, left, TOP_BODY, width, bottom - TOP_BODY - caption_h)
            if captions:
                self._text(slide, left, bottom - caption_h, width, caption_h, captions[index], size=13, color=SOFT,
                           align=PP_ALIGN.CENTER)
            left += width + gap
        return slide

    def table_slide(self, title, headers, rows, speaker=None, takeaway=None, note="", col_widths=None,
                    highlight_rows=(), size=15, row_height=0.42, bullets=None):
        """A table (first column left-aligned, the others centred); highlight_rows are drawn bold.
        `bullets` adds a few lines of text under the table."""
        slide = self._frame(title, speaker, takeaway, note)
        width = W - LEFT - RIGHT
        shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(LEFT), Inches(TOP_BODY + 0.1),
                                       Inches(width), Inches(row_height * (len(rows) + 1)))
        table = shape.table
        shape._element.graphic.graphicData.tbl[0][-1].text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # plain grid
        col_widths = col_widths or [1.0] * len(headers)
        for index, share in enumerate(col_widths):
            table.columns[index].width = Emu(int(Inches(width) * share / sum(col_widths)))
        for r in range(len(rows) + 1):
            table.rows[r].height = Inches(row_height)
            for c in range(len(headers)):
                cell = table.cell(r, c)
                text = headers[c] if r == 0 else str(rows[r - 1][c])
                cell.text = ""
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = cell.margin_right = Inches(0.08)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                paragraph = cell.text_frame.paragraphs[0]
                paragraph.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
                bold = r == 0 or (r - 1) in highlight_rows
                self._run(paragraph, text, size, bold=bold, color=ACCENT if r == 0 else INK)
                cell.fill.solid()
                cell.fill.fore_color.rgb = PALE if r == 0 else (STRIPE if r % 2 == 0 else WHITE)
        if bullets:
            top = TOP_BODY + 0.1 + row_height * (len(rows) + 1) + 0.25
            bottom = BOTTOM_BODY if takeaway else 6.9
            self._bullets(slide, LEFT, top, width, bottom - top, bullets, size=17)
        return slide

    def takeaways_slide(self, title, items, speaker=None, note=""):
        """Numbered take-away messages, one panel each."""
        slide = self._frame(title, speaker, None, note)
        count = len(items)
        gap = 0.18
        height = min(1.15, (6.75 - TOP_BODY - gap * (count - 1)) / count)
        top = TOP_BODY + 0.15
        for index, item in enumerate(items, start=1):
            self._rect(slide, LEFT, top, 0.09, height, ORANGE)
            self._rect(slide, LEFT + 0.09, top, W - LEFT - RIGHT - 0.09, height, PALE)
            self._text(slide, LEFT + 0.3, top, 0.6, height, str(index), size=28, bold=True, color=ACCENT,
                       anchor=MSO_ANCHOR.MIDDLE)
            self._text(slide, LEFT + 0.95, top, W - LEFT - RIGHT - 1.2, height, item, size=19, anchor=MSO_ANCHOR.MIDDLE)
            top += height + gap
        return slide

    def save(self, path):
        self.prs.core_properties.author = "CSAI 301 project team"
        self.prs.save(str(path))
        return path
