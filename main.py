#!/usr/bin/env python3
"""news-image-20261120: one image summing up the world news of
Friday 20 November 2026.

The image (entry.png) was drawn by renderer.py from stories.json: 50
stories, every one verified to have happened or been first reported on
20 November 2026, across 7 regions and 14 topics. Layout: giant date,
UTC timeline, 16 featured stories with flat vector pictograms, a world
map with numbered pins, an ALSO ON list, a DATE CHECK bar naming the
tempting wrong-date stories left out on purpose, and a footer.

This program is pure standard library: it only copies the finished
image to /output/entry.png, so it runs in the judging container, which
has nothing installed beyond the standard library. Deterministic: the
same entry.png is copied every run, byte for byte.
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    if Path(out_dir).is_dir():
        out = Path(out_dir) / "entry.png"
    else:
        out = HERE / "out" / "entry.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "entry.png", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
