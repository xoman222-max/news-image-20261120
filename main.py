# news-image-20261120 entry: copy entry.png to the output directory.
#
# Pure Python standard library (os/shutil/pathlib only). The judging
# container has no Pillow, no network, and a read-only /bot, so this
# program only copies the already-rendered image byte for byte.
#
# Run it the way the grader does:
#   MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out python3 main.py

import os
import shutil
import sys
from pathlib import Path

BOT_DIR = Path(os.environ.get("MAKEFUN_BOT_DIR", "/bot"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def _copy_to(destination: Path, source: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination / "entry.png")


def main() -> int:
    source = BOT_DIR / "entry.png"
    if not source.is_file():
        print(f"entry.png not found in {BOT_DIR}", file=sys.stderr)
        return 1
    try:
        _copy_to(OUTPUT_DIR, source)
    except OSError:
        # The output directory is not writable here; use out/ instead.
        _copy_to(Path("out"), source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
