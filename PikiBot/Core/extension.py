"""
PikiBot NonCommercial License 1.0.0

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import logging
import pathlib
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any

import discord
import yaml
from attr import dataclass, field
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

if TYPE_CHECKING:
    from .bot import PikiBot as Bot

__all__ = (
    "AuthorInfo",
    "Dependency",
    "EntryPointLocation",
    "Extension",
    "ExtensionInfo",
)

_log = logging.getLogger(__name__)


@dataclass(init=True, frozen=True, repr=True, slots=True, kw_only=True)
class EntryPointLocation:
    """Names the module and lifecycle functions used by an extension.

    Attributes
    ----------
    module: :class:`str`
        Dotted import path containing the lifecycle functions.
    setup: :class:`str`
        Function called when the extension loads. It receives the bot as its argument.
    teardown: :class:`str` | :data:`None`
        Optional function called when the extension unloads. It receives the bot as its argument.
    """

    module: str
    setup: str
    teardown: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, str], /) -> EntryPointLocation:
        return EntryPointLocation(
            module=raw["module"],
            setup=raw["setup"],
            teardown=raw.get("teardown"),
        )


@dataclass(init=True, frozen=True, repr=True, slots=True, kw_only=True)
class AuthorInfo:
    """Author metadata declared by an extension.

    Attributes
    ----------
    name: :class:`str`
        Display name of the author.
    email: :class:`str` | :data:`None`
        Optional contact address.
    extras: :class:`dict`[:class:`str`, :data:`Any`]
        Additional metadata not interpreted by PikiBot.
    """

    name: str
    email: str | None = None
    extras: dict[str, Any] = field(factory=dict)

    @classmethod
    def from_raw(cls, data: str | dict[str, Any], /) -> AuthorInfo:
        if isinstance(data, str):
            return AuthorInfo(name=data)
        else:
            return AuthorInfo(
                name=data["name"],
                email=data.get("email"),
                extras=data.get("extras", {}),
            )


@dataclass(init=True, frozen=True, repr=True, slots=True, kw_only=True)
class Dependency:
    """A package requirement that an extension needs to load.

    Attributes
    ----------
    name: :class:`str`
        Canonicalized package name.
    specifier: :class:`packaging.specifiers.SpecifierSet`
        Accepted package versions, using Python version-specifier syntax.

    Notes
    -----
    :meth:`is_satisfied` checks the installed distribution version against ``specifier``.
    """

    name: str
    specifier: SpecifierSet

    def is_satisfied(self) -> bool:
        """Whether the dependency requirement is satisfied.

        This method performs a heavy operation and should not be called by the
        end user but rather the API itself.
        """
        try:
            raw_version = importlib.metadata.version(self.name)
        except importlib.metadata.PackageNotFoundError:
            return False
        return Version(raw_version) in self.specifier

    @classmethod
    def from_data(cls, data: dict[str, str] | None) -> dict[str, Dependency]:
        if data:
            return {
                k: Dependency(
                    name=canonicalize_name(k),
                    specifier=SpecifierSet(v),
                )
                for k, v in data.items()
            }
        return {}


@dataclass(init=True, frozen=True, repr=True, slots=True, kw_only=True)
class ExtensionInfo:
    """Parsed metadata that describes an extension and its entry point.

    Attributes
    ----------
    name: :class:`str`
        Unique extension name.
    description: :class:`str` | :data:`None`
        Optional summary shown in extension listings.
    version: :class:`packaging.version.Version`
        Extension release version.
    entrypoint: :class:`EntryPointLocation`
        Module and lifecycle function names.
    author: :class:`AuthorInfo`
        Author metadata.
    license: :class:`str` | :data:`None`
        Optional license identifier or text.
    dependencies: :class:`dict`[:class:`str`, :class:`Dependency`]
        Package requirements keyed by package name.
    extras: :class:`dict`[:class:`str`, :data:`Any`]
        Additional metadata not interpreted by PikiBot.
    """

    name: str
    description: str | None = None
    version: Version
    entrypoint: EntryPointLocation
    author: AuthorInfo
    license: str | None = None
    dependencies: dict[str, Dependency] = field(factory=dict)
    extras: dict[str, Any] = field(factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], /) -> ExtensionInfo:
        if not isinstance(data, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(
                "Loaded YAML is not a dict. Please make sure it follows the proper definition structure."
            )

        try:
            ret = ExtensionInfo(
                name=data["name"],
                description=data.get("description"),
                version=Version(data["version"]),
                entrypoint=EntryPointLocation.from_dict(data["entrypoint"]),
                author=AuthorInfo.from_raw(data["author"]),
                license=data.get("license"),
                dependencies=Dependency.from_data(data.get("dependencies")),
                extras=data.get("extras", {}),
            )
        except KeyError as e:
            raise KeyError(
                "Missing required key from extension configuration file %r", e.args
            ) from e
        else:
            return ret


class Extension:
    """Loads, unloads, and reloads one module or plugin for a bot.

    Parameters
    ----------
    bot: :class:`PikiBot`
        Bot that owns the extension.
    ext_path: :class:`pathlib.Path`
        Directory containing the extension metadata and Python package.
    dist_info: :class:`str`
        Metadata filename, relative to ``ext_path``.

    Attributes
    ----------
    info: :class:`ExtensionInfo`
        Validated metadata parsed from the extension configuration file.

    Notes
    -----
    Dependencies are checked before the first load. Setup and teardown functions
    are called with the owning bot and may be synchronous or asynchronous.
    """

    def __init__(
        self,
        *,
        bot: Bot,
        ext_path: pathlib.Path,
        dist_info: str,
    ) -> None:
        with (ext_path / dist_info).open(mode="r") as file:
            data = yaml.safe_load(file)

        self._bot: Bot = bot
        self.info: ExtensionInfo = ExtensionInfo.from_dict(data)
        self._module: ModuleType | None = None
        self._resolved_name: str | None = None
        self._dependencies_satisfied: bool | None = None
        self._is_default: bool = ext_path.is_relative_to(bot.DEFAULT_MODULES_PATH)
        self._ext_path: str = (
            ext_path.relative_to(bot.DEFAULT_MODULES_PATH).as_posix().replace("/", ".")
        )
        self._parent: str = "Plugins" if not self._is_default else "Modules"

    def is_default(self) -> bool:
        """Whether the extension is a default module."""
        return self._is_default

    def is_loaded(self) -> bool:
        """Whether the extension has been loaded."""
        return self._module is not None and self._resolved_name is not None

    async def load(self) -> None:
        """Load the module and executes its entrypoint function."""
        await self._load(f"PikiBot.{self._parent}.{self._ext_path}")

    def check_dependencies(self, *, update_state: bool = False) -> bool:
        """Check whether the dependencies requirements are fullfiled.

        This should only be called manually when you want to force recheck the dependencies
        requirements.

        This operation is automatically done when loading the extension for the first time.

        Parameters
        ----------
        update_state: :class:`bool`
            Whether to update the inner state of deps fullfilment. This should be set to ``True`` if
            you want to force reload the state when, for example, you have installed a package that was not
            installed at the time the extension was first loaded.

        Returns
        -------
        :class:`bool`
            Whether the dependencies requirements are satisfied.
        """
        satisfied = True

        for name, dependency in self.info.dependencies.items():
            if not dependency.is_satisfied():
                _log.warning(
                    "Dependency %r (version specifier %r) for extension %r is not satisfied",
                    name,
                    dependency.specifier,
                    self.info.name,
                )
                satisfied = False
                break
            _log.debug(
                "Dependency %r (version version specifier %r) for extension %r SUCCESSFULLY satisfied",
                name,
                dependency.specifier,
                self.info.name,
            )

        if update_state:
            self._dependencies_satisfied = satisfied
        return satisfied

    async def _load(self, path: str, /) -> None:
        if self._dependencies_satisfied is None:
            self.check_dependencies(update_state=True)

        if self._dependencies_satisfied is False:
            raise RuntimeError(
                f"Could not load extension {self.info.name!r} because dependency issues were not resolved."
            )

        self._resolved_name = name = importlib.util.resolve_name(
            f".{self.info.entrypoint.module}", path
        )
        spec = importlib.util.find_spec(name)
        if spec is None:
            self._resolved_name = None
            raise ModuleNotFoundError(f"Extension {name!r} was not found in {path!r}")

        self._module = ext = importlib.util.module_from_spec(spec)
        sys.modules[name] = ext

        try:
            spec.loader.exec_module(ext)  # type: ignore
        except Exception as e:
            self._module = None
            self._resolved_name = None
            del sys.modules[name]
            raise RuntimeError(f"Extension {name!r} could not be loaded") from e

        try:
            setup_func = getattr(ext, self.info.entrypoint.setup)
        except AttributeError:
            self._module = None
            self._resolved_name = None
            del sys.modules[name]
            raise AttributeError(f"Setup function not found for extension {name!r}")

        try:
            await discord.utils.maybe_coroutine(setup_func, self._bot)
        except Exception as e:
            await self._unload()
            raise RuntimeError(
                f"Extension {name!r} failed to load while setting up."
            ) from e

    async def unload(self) -> None:
        """Unloads the module and executes its teardown function."""
        await self._unload()

    async def _unload(self) -> None:
        if not (self._module and self._resolved_name):
            return

        if self.info.entrypoint.teardown:
            try:
                teardown_func = getattr(self._module, self.info.entrypoint.teardown)
            except AttributeError:
                pass
            else:
                try:
                    await discord.utils.maybe_coroutine(teardown_func, self._bot)
                except Exception:
                    _log.exception(
                        "Teardown function in module %r failed", self._resolved_name
                    )

        sys.modules.pop(self._resolved_name, None)
        name = self._module.__name__
        for module in list(sys.modules.keys()):
            if module.startswith((name, name + ".")):
                del sys.modules[module]

        self._module = None
        self._resolved_name = None

    async def reload(self, *, force_dependency_check: bool = False) -> None:
        """Reload the extension.

        Parameters
        ----------
        force_dependency_check: :class:`bool`
            Whether to forcefuly check the dependencies before loading the extension again, updating
            the inner state.
        """
        await self._reload(
            f"PikiBot.{self._parent}.{self._ext_path}",
            check_dependencies=force_dependency_check,
        )

    async def _reload(self, path: str, /, *, check_dependencies: bool) -> None:
        await self._unload()
        if check_dependencies:
            self.check_dependencies(update_state=True)
        await self._load(path)
