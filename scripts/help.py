"""Apache License 2.0

Copyright (c) 2026-present DA-344 (aka Developer Anonymous)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
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