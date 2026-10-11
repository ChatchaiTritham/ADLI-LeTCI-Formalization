"""Pass A: coordinate-based transcription of the Evaluation Factor Score Summary grids.

For each grid page: column centres come from the six range headers (0-5% ... 90-100%) on the header
line; the "X" marks inside the grid (above the "Guidance:" line) are sorted top-to-bottom and assigned
to factors in printed order (A, D, L, I or Le, T, C, I). The item percentage is read from
"Item k.k Score  NN %". Any grid with != 4 marks is flagged, never repaired.
Usage: python -I extract_passA.py  -> passA.json
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources"
DOCS = {"2007_Share_Food": "2007_Share_Food_Scorebook.pdf",
        "2008_Novel_Connect": "2008_Novel_Connect_Scorebook.pdf",
        "2009_Nightingale": "2009_Nightingale_Scorebook.pdf"}
HDR = [r"^0\W5%$", r"^10\W25%$", r"^30\W45%$", r"^50\W65%$", r"^70\W85%$", r"^90\W100%$"]


def grid(page):
    words = page.get_text("words")                      # x0, y0, x1, y1, text, block, line, wno
    text = page.get_text()
    m = re.search(r"Evaluation Factor Score Summary\W+Item\s*([0-9]\.[0-9])", text)
    if not m:
        return None
    item = m.group(1).rstrip(".:")
    guide = [w[1] for w in words if w[4].startswith("Guidance")]
    y_end = min(guide) if guide else 1e9
    heads = {}
    for w in (w for w in words if w[1] < y_end):
        for k, pat in enumerate(HDR):
            if re.match(pat, w[4]) and k not in heads:
                heads[k] = ((w[0] + w[2]) / 2, w[1])
    if len(heads) != 6:
        return {"item": item, "error": f"headers found {sorted(heads)}"}
    y_head = max(v[1] for v in heads.values())
    marks = [w for w in words if re.fullmatch(r"X+", w[4]) and y_head + 5 < w[1] < y_end]
    marks.sort(key=lambda w: w[1])
    bands = []
    for w in marks:
        xc = (w[0] + w[2]) / 2
        bands.append(min(heads, key=lambda k: abs(heads[k][0] - xc)))
    s = re.search(r"Item\s+[0-9.]+\s+Score\s+(\d+)\s*%"
                  r"|Score\s+(\d+)\s*%", text)
    return {"item": item, "factor_bands": bands, "n_marks": len(marks),
            "consensus_pct": int(s.group(1) or s.group(2)) if s else None, "page": page.number + 1}


def main():
    out = {}
    for case, fn in DOCS.items():
        doc = pymupdf.open(SRC / fn)
        rows = [g for g in (grid(p) for p in doc) if g]
        out[case] = rows
        for r in rows:
            print(case, r)
    (HERE / "passA.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
