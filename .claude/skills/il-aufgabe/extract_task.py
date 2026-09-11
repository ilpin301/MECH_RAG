#!/usr/bin/env python
"""Extract one Aufgabe from a PDF: text excerpt + page renders for the figure.

Deterministic, no LLM. Keeps the whole PDF out of the agent's context: later
stages read only task.txt and the PNG.

    python extract_task.py "IN/Aufgabensammlung.pdf" 4.4 --out .scratch/4-4
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

HEADING = r"Aufgabe\s+\d+\.\d+\b"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("task", help="task number as printed, e.g. 4.4")
    ap.add_argument("--out", default=".scratch")
    ap.add_argument("--dpi", type=int, default=170)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(a.pdf)
    pages = [p.get_text() for p in doc]

    (out / "text.txt").write_text(
        "\n".join(f"=== PAGE {i + 1} ===\n{t}" for i, t in enumerate(pages)),
        encoding="utf-8",
    )

    start = re.compile(r"Aufgabe\s+" + re.escape(a.task) + r"\b")
    nxt = re.compile(HEADING)

    hit = None
    for i, t in enumerate(pages):
        m = start.search(t)
        if m:
            hit = (i, m.start())
            break
    if hit is None:
        sys.exit(f"Aufgabe {a.task} not found in {a.pdf}")

    pi, off = hit
    body = pages[pi][off:]
    m2 = nxt.search(body, 1)
    if m2:
        body = body[: m2.start()]
    else:
        tail = pages[pi + 1] if pi + 1 < len(pages) else ""
        m3 = nxt.search(tail)
        body += "\n" + (tail[: m3.start()] if m3 else tail)
    (out / "task.txt").write_text(body.strip(), encoding="utf-8")

    imgs = []
    for p in range(pi, min(pi + 2, doc.page_count)):
        f = out / f"page_{p + 1:02d}.png"
        doc[p].get_pixmap(dpi=a.dpi).save(f)
        imgs.append(str(f))

    print(json.dumps(
        {
            "task": a.task,
            "page": pi + 1,
            "task_txt": str(out / "task.txt"),
            "full_text": str(out / "text.txt"),
            "images": imgs,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
