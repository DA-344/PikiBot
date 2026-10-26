# PikiBot

**PikiBot** is a modular Discord bot built in Python.

> ❗ **Project in development**
> PikiBot is still in a development phase. Structure, API, and other parts of the project may change
> before releasing a stable version.

## Project Structure

```
PikiBot/
├── Core/     # Main bot implementations
├── Modules/  # Official modules
├── API/      # Public API for developers
└── Plugins/  # Third-party plugins and extensions
```

### Core

Contains the main implementation of PikiBot and all its components required for it to work.

### Modules

Official modules that provide additional functionalities to the bot.

### API

Public interface for plugins and extensions developers.

API is built to provide an easy-to-use communication with PikiBot without having to modify the
source code directly.

### Plugins

Plugins let you add extra independent functionalities to PikiBot.

Plugins may be developed and distributed by third parties and may use their own terms and licenses,
as log as they keep the original license to PikiBot and do not show more governance over the source
code than the ones expressly specified in [PikiBot's License](./LICENSE.md).

## Installation

> **PyPI installation for developers not yet available**

## Versioning

This project tries to follow [Semantic Versioning](https://semver.org/).

- MAJOR version releases are done only when a breaking change is done.
- MINOR version releases are done when adding new functionalities with backward compatibilities with other ``MINOR`` versions under the same ``MAJOR``.
- PATCH version releases are done only for emergency or important bug fixes.

## License

Original Software of PikiBot is licensed under **PikiBot Noncommercial License 1.1.0**.

This license allows using, modifying, and distributing the Original Software for noncommercial purposes,
subject to the license's terms and conditions.

PikiBot's public API is governed by an independent license.

Plugins and independent contributions may be licensed under other licenses.

Check [`LICENSE.md`](./LICENSE.md) for more information regarding the terms of the license and Original Software.

## Project Status

PikiBot is being constantly developed.

The API, plugins system, and main internal structure may suffer breaking changes.

At the moment, the project may be considered as experimental and does not provide any API stability warranty.
