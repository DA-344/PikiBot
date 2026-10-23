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

import argparse
import subprocess
from pathlib import Path

try:
    import babel
except ImportError:
    raise ModuleNotFoundError("Babel is a required dependency that must be installed to compile i18n files")


def get_domains(locale_dir: Path) -> set[str]:
    if not locale_dir.is_dir():
        raise ValueError(
            f"Translations directory does not exist: {locale_dir}",
        )

    domains: set[str] = set()

    for locale in locale_dir.iterdir():
        if not locale.is_dir():
            continue

        messages_dir = locale / "LC_MESSAGES"
        
        if not messages_dir.is_dir():
            raise ValueError(
                f"Invalid locale structure: {locale}"
            )

        for catalog in messages_dir.iterdir():
            if catalog.suffix not in (".po", ".mo"):
                continue
            
            if not catalog.is_file():
                continue
            
            domains.add(catalog.stem)

    if not domains:
        raise ValueError(
            f"No translation catalogs found in {locale_dir}"
        )
    return domains


blue = "\033[96m"
white = "\033[0m"
magenta = "\033[35m"
bright = "\033[1m"
red = "\033[91m"


def main() -> None:
    print(blue, "[INFO]", white, "Using", bright, "Babel", magenta, babel.__version__, white, "for I18N compile...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--locale-dir", required=True)
    parser.add_argument("--domains", default="")

    args = parser.parse_args()

    if not args.locale_dir:
        raise SyntaxError("LOCALE_DIR is required parameter that is missing")

    args.locale_dir = Path(args.locale_dir)

    try:
        available = get_domains(args.locale_dir)
        requested = {
            domain.strip()
            for domain in args.domains.split(",")
            if domain.strip()
        }
        domains = requested or available

        unknown = domains - available
        if unknown:
            raise ValueError(
                f"Unknown domains: {', '.join(unknown)}",
            )

        subprocess.run(
            [
                "pybabel",
                "compile",
                "-d", str(args.locale_dir),
                "-D", " ".join(domains),
            ],
            check=True,
        )
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{red}{bright}Error:{white} {magenta}{error}{white}\n")


if __name__ == "__main__":
    main()
