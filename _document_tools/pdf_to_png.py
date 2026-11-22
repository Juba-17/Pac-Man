"""Render PDF pages to PNG images (for visual checks). Usage: pdf_to_png.py file.pdf out_dir [dpi] [montage_cols]

With montage_cols > 0 the pages are also combined into contact sheets of that many columns
(two rows per sheet), which makes it quick to look at a whole document.
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

pdf = Path(sys.argv[1])
out = Path(sys.argv[2])
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 80
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 0
out.mkdir(parents=True, exist_ok=True)
for old in out.glob(f"{pdf.stem}_*.png"):
    old.unlink()

doc = fitz.open(pdf)
pages = []
for index, page in enumerate(doc, start=1):
    pix = page.get_pixmap(dpi=dpi)
    path = out / f"{pdf.stem}_p{index:02d}.png"
    pix.save(path)
    pages.append(path)
print(f"{len(pages)} pages -> {out}")

if cols:
    per_sheet = cols * 2
    for sheet, start in enumerate(range(0, len(pages), per_sheet), start=1):
        images = [Image.open(p).convert("RGB") for p in pages[start:start + per_sheet]]
        w, h = images[0].size
        rows = (len(images) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * w + (cols + 1) * 10, rows * h + (rows + 1) * 10), "#888888")
        for i, image in enumerate(images):
            canvas.paste(image, (10 + (i % cols) * (w + 10), 10 + (i // cols) * (h + 10)))
        target = out / f"{pdf.stem}_sheet{sheet}.png"
        canvas.save(target)
        print("sheet", target)
