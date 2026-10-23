"""
The MIT License (MIT)

Copyright (c) 2026-present DA-344 (aka Developer Anonymous)

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

from pathlib import Path
import re

MAKEFILE = Path(__file__).resolve().parent.parent / "Makefile"
TARGET_PATTERN = re.compile(r"^([a-zA-Z0-9_-]+)\s*:")

bright = "\033[1m"
white = "\033[0m"


def main() -> None:
    lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    targets: list[tuple[str, list[str]]] = []
    comments: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("##"):
            comments.append(stripped.removeprefix("##").strip())
            continue

        if not stripped:
            continue

        match = TARGET_PATTERN.match(line)

        if match:
            targets.append((match.group(1), comments.copy()))

        comments.clear()

    for target, description in targets:
        if description:
            print(f"\n{bright}{target}{white}")
            for comment in description:
                print(f"  {comment}")


if __name__ == "__main__":
    main()