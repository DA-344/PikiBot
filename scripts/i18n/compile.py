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
