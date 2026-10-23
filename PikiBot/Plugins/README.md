# Plugins

This folder is meant to store all third-party plugins that can be installed.

All these plugins fall to the specific terms in the ``LICENSE`` which refer to it.

## Structure

All plugins must be a folder that may have any name but must have an ``extension.yml`` (mind the ``yml``)
that defines the properties of each plugin.

This is the table of the keys it must have:

| Field name | Field type | Description |
| :--------: | :--------: | :---------: |
| name | string | The name of the extension |
| description? | ?string | The description of the extension |
| version | string | A PEP440 version identifier representing the version of this extension |
| entrypoint | entrypoint object | Entrypoint metadata |
| author | author object | Author info |
| license? | ?string | The license the plugin is licensed under |
| dependencies? | dict of dependencies | The dependencies that must be installed to use the plugin |
| extras | dict | Extra plugin information |

### Entrypoint object

| Field name | Field type | Description |
| :--------: | :--------: | :---------: |
| module | string | The module where the setup and teardown are located |
| setup | string | The function name following the ``async (bot: PikiBot) -> None`` structure that executes the setup |
| teardown | ?string | The function name following the ``async (bot: PikiBot) -> None`` structure that executes the teardown |

### Author object

| Field name | Field type | Description |
| :--------: | :--------: | :---------: |
| name | string | The author name |
| email? | ?string | The author email |
| extras | dict | Extra author metadata |

### Dependency

| Field name | Field type | Description |
| :--------: | :--------: | :---------: |
| name | string | The canonical name of the package the plugin depends on |
| version | string | The versions the dependency is under, follows pip version specifier (``>=3.0``, ``>3,<4``, etc.) |


## What's the difference between ``Modules`` and ``Plugins``?

``Modules`` are included by default with PikiBot and are made by the maintainers, while ``Plugins`` are third-party installable
extensions made by external authors.

More information on this may be found in the ``LICENSE``.
