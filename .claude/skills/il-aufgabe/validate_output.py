#!/usr/bin/env python
"""Validate the OUT/ artifacts for one Aufgabe. Exit 0 = clean, 1 = problems.

    python validate_output.py 4-4 --out OUT
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.w3.org/2000/svg}"
WHITE = {"#ffffff", "#fff", "white"}
LINK = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
REQUIRED_HEADINGS = [
    "## Problemstellung",
    "## Zielsetzung",
    "## Gegeben",
    "## Definitionen und Formeln",
    "## Schritt-fuer-Schritt-Loesung",
    "## Verifikation",
    "## Endergebnis",
    "## Haeufige Fehler",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="task number with hyphen, e.g. 4-4")
    ap.add_argument("--out", default="OUT")
    a = ap.parse_args()

    out = Path(a.out)
    errs = []
    checked = 0

    files = {
        "solution": out / f"Aufgabe {a.task}.md",
        "beispiel": out / f"{a.task}--Beispielaufgabe.md",
        "loesung": out / f"{a.task}--Loesung.md",
    }

    for kind, f in files.items():
        if not f.is_file():
            errs.append(f"MISSING {kind}: {f}")
        elif f.stat().st_size < 200:
            errs.append(f"TOO SMALL {f} ({f.stat().st_size} B)")

    sol = files["solution"]
    if sol.is_file():
        txt = sol.read_text(encoding="utf-8")
        for h in REQUIRED_HEADINGS:
            if h not in txt:
                errs.append(f"HEADING MISSING in {sol.name}: {h}")

    for f in files.values():
        if not f.is_file():
            continue
        for target in LINK.findall(f.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "data:")):
                continue
            checked += 1
            p = (f.parent / target).resolve()
            if not p.is_file():
                errs.append(f"BROKEN LINK in {f.name}: {target}")
                continue
            if p.suffix.lower() != ".svg":
                continue
            try:
                root = ET.parse(p).getroot()
            except ET.ParseError as e:
                errs.append(f"BAD SVG {p.name}: {e}")
                continue
            if not any(r.get("fill", "").lower() in WHITE
                       for r in root.iter(f"{NS}rect")):
                errs.append(f"NO WHITE BACKGROUND RECT in {p.name}")

    svgdir = out / "svg" / a.task
    if not svgdir.is_dir():
        errs.append(f"MISSING svg folder: {svgdir}")

    for e in errs:
        print("FAIL:", e)
    print(f"checked {checked} image link(s); {len(errs)} problem(s)")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
