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

# these exports are the only ones under the Apache License as explained in
# the LICENSE file. No permission over Core or related is granted.

from collections.abc import Callable
from functools import partial
from typing import Any, overload

from PikiBot.Core.bot import PikiBot
from PikiBot.Core.command import (
    PikiAppCommand,
    PikiAppGroup,
    PikiCommand,
    PikiCommandTree,
    PikiContextMenu,
    PikiGroup,
    PikiHybridCommand,
    PikiHybridGroup,
    app_command,
    app_group,
    command,
    group,
    hybrid_command,
    hybrid_group,
)
from PikiBot.Core.context import Context
from PikiBot.Core.database import BaseModel, Database
from PikiBot.Core.extension import (
    AuthorInfo,
    Dependency,
    EntryPointLocation,
    Extension,
    ExtensionInfo,
)
from PikiBot.Core.help import (
    PikiDefaultHelpCommand,
    PikiHelpCommand,
    PikiMinimalHelpCommand,
)
from PikiBot.Core.i18n import Translator

type Bot = PikiBot
"""An alias for :class:`PikiBot`."""

__all__ = (
    "AuthorInfo",
    "BaseModel",
    "Bot",
    "Context",
    "Database",
    "Dependency",
    "EntryPointLocation",
    "Extension",
    "ExtensionInfo",
    "PikiAppCommand",
    "PikiAppGroup",
    "PikiBot",
    "PikiCommand",
    "PikiCommandTree",
    "PikiContextMenu",
    "PikiDefaultHelpCommand",
    "PikiGroup",
    "PikiHelpCommand",
    "PikiHybridCommand",
    "PikiHybridGroup",
    "PikiMinimalHelpCommand",
    "Translator",
    "app_command",
    "app_group",
    "command",
    "group",
    "hybrid_command",
    "hybrid_group",
)


@overload
def database_model[T](cls: type[T]) -> type[T]: ...


@overload
def database_model[T](
    cls: None = None,
    *,
    table_name: str | None = None,
    abstract: bool = False,
) -> Callable[[type[T]], type[T]]: ...


def database_model[T](
    cls: type[T] | None = None,
    *,
    table_name: str | None = None,
    abstract: bool = False,
) -> Any:
    """A decorator that generates a :class:`BaseModel` subclass automatically and assigns it
    to the decorated class.

    This is just a shortcut for doing ::

        class MyModel(BaseModel):
            __tablename__ = table_name or cls.__name__.lower()
            __abstract__ = abstract

    Parameters
    ----------
    table_name: :class:`str` | :data:`None`
        The table name to assign to this model. If ``None``, defaults to the lowered class name.
    abstract: :class:`bool`
        Whether the model should be flagged as abstract.
    """
    if cls is None:
        kwgs = {}
        if table_name is not None:
            kwgs["__tablename__"] = table_name
        if abstract:
            kwgs["__abstract__"] = True
        func = partial(_convert_cls, **kwgs)
        return func
    else:
        return _convert_cls(cls)


def _convert_cls[T](cls: type[T], **options: Any) -> type[T]:
    ns = {
        key: value
        for key, value in vars(cls).items()
        if key not in ("__dict__", "__weakref__")
    }
    ns["__module__"] = cls.__module__
    ns.update(options)
    return type(  # type: ignore
        cls.__name__,
        (BaseModel,),
        ns,
    )
