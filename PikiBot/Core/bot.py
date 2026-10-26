"""
PikiBot Noncommercial License 1.1.0

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

import io
import logging
from collections.abc import Callable, Coroutine, Generator, Sequence
from contextlib import redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING, Any, Concatenate, Final, Self

import discord
import tqdm
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncEngine

from .cog import PikiCog
from .command import LocalizableMixin, PikiCommand, PikiCommandTree, PikiGroup
from .database import Database
from .extension import Extension, ExtensionInfo
from .help import PikiDefaultHelpCommand
from .i18n import DPYTranslator, Translator

if TYPE_CHECKING:
    from .context import Context

_log = logging.getLogger(__name__)


class PikiBot(commands.Bot):
    """Discord bot with PikiBot's command, extension, translation, and database support.

    Parameters
    ----------
    command_prefix: :class:`str` | :class:`Callable`
        Prefix, or prefix callback, used to invoke text commands.
    description: :class:`str` | :data:`None`
        Bot description shown by help commands.
    intents: :class:`discord.Intents`
        Gateway events and data the bot requests from Discord.
    auto_load_default_modules: :class:`bool`
        Load built-in modules during :meth:`setup_hook`.
    auto_load_plugins: :class:`bool`
        Load plugins during :meth:`setup_hook`.
    use_i18n: :class:`bool`
        Create a :class:`Translator` and enable command localization.
    default_locale: :class:`str` | :data:`None`
        Fallback catalog locale. Required when ``use_i18n`` is true.
    locales_path: :class:`pathlib.Path` | :data:`None`
        Directory containing compiled locale catalogs. Required when ``use_i18n`` is true.
    available_locales: :class:`Sequence`[:class:`str`] | :data:`None`
        Catalog locales to load. If omitted, locales are discovered from ``locales_path``.
    default_translator_domain: :class:`str`
        Gettext domain used when a command does not specify one.
    auto_load_translator_catalogs: :class:`bool`
        Load discovered catalogs when the translator is created.
    global_catalog_validator: :class:`Callable` | :data:`None`
        Normalize Discord locale values to catalog names.
    global_domain_getter: :class:`Callable` | :data:`None`
        Select a gettext domain from a catalog and Discord translation context.
    tree_cls: :class:`type`
        Application-command tree class passed to :class:`commands.Bot`.
    use_db: :class:`bool`
        Connect the supplied database engine during :meth:`setup_hook`.
    create_db_tables: :class:`bool`
        Create tables declared through :class:`BaseModel` during connection.
    engine: :class:`sqlalchemy.ext.asyncio.AsyncEngine` | :data:`None`
        Async engine to connect when ``use_db`` is true.
    **kwargs: :data:`Any`
        Additional options passed to :class:`commands.Bot`.

    Attributes
    ----------
    translator: :class:`Translator` | :data:`None`
        Configured translator, if ``use_i18n`` is enabled.
    database: :class:`type`[:class:`Database`]
        Database facade used by the bot.
    extensions: :class:`list`[:class:`Extension`]
        Loaded default modules and plugins.
    default_modules: :class:`list`[:class:`Extension`]
        Loaded built-in modules.
    plugins: :class:`list`[:class:`Extension`]
        Loaded third-party extensions.

    Notes
    -----
    Unless ``help_command`` is supplied in ``kwargs``, the bot installs a
    :class:`PikiDefaultHelpCommand`. When ``use_db`` is true, ``engine`` must be
    supplied before :meth:`setup_hook` runs.
    """

    DEFAULT_MODULES_PATH: Final[Path] = Path(__file__).parent.parent / "Modules"
    DEFAULT_PLUGINS_PATH: Final[Path] = Path(__file__).parent.parent / "Plugins"

    if TYPE_CHECKING:

        @property
        def tree(self) -> PikiCommandTree[Self]: ...

        def walk_commands(
            self,
        ) -> Generator[PikiCommand[Any, ..., Any] | PikiGroup[Any, ..., Any]]: ...

    def __init__(
        self,
        *,
        command_prefix: str | Callable[[PikiBot, discord.Message], str],
        description: str | None = None,
        intents: discord.Intents,
        auto_load_default_modules: bool = True,
        auto_load_plugins: bool = True,
        default_locale: str | None = None,
        locales_path: Path | None = None,
        available_locales: Sequence[str] | None = None,
        use_i18n: bool = False,
        default_translator_domain: str = "messages",
        auto_load_translator_catalogs: bool = True,
        global_catalog_validator: Callable[[str], str] | None = None,
        global_domain_getter: Callable[
            [str, discord.app_commands.TranslationContextTypes], str | None
        ]
        | None = None,
        tree_cls: type[PikiCommandTree[Self]] = PikiCommandTree,
        use_db: bool = False,
        create_db_tables: bool = True,
        engine: AsyncEngine | None = None,
        **kwargs: Any,
    ) -> None:
        self.auto_load_default_modules: bool = auto_load_default_modules
        self.auto_load_plugins: bool = auto_load_plugins

        self._translator: Translator | None = None

        LocalizableMixin.GLOBAL_CATALOG_VALIDATOR = global_catalog_validator
        LocalizableMixin.GLOBAL_DOMAIN_GETTER = global_domain_getter
        LocalizableMixin.GLOBAL_LOCALIZE = True if use_i18n else None

        self.use_db: bool = use_db
        self._db_engine: AsyncEngine | None = engine
        self._create_db_tables: bool = create_db_tables

        if use_i18n:
            assert default_locale and locales_path, (
                "i18n requires default_locale, locales_path, and locales_messages_file to be set"
            )
            self._translator = Translator(
                default_locale=default_locale,
                path=locales_path,
                default_domain=default_translator_domain,
                available_locales=available_locales,
                auto_load_catalogs=auto_load_translator_catalogs,
            )

        if "help_command" not in kwargs:
            kwargs["help_command"] = PikiDefaultHelpCommand()

        super().__init__(
            command_prefix,
            description=description,
            intents=intents,
            tree_cls=tree_cls,
            **kwargs,
        )

        # discord.py offers a __extension attr by default, so we need to override it
        self.__extensions: dict[str, Extension] = {}

    @property
    def translator(self) -> Translator | None:
        """Returns the translator instance associated with the bot, if applicable."""
        return self._translator

    @property
    def database(self) -> type[Database]:
        """Returns the database instance associated with the bot."""
        return Database

    @property
    def extensions(self) -> list[Extension]:
        """Returns a list of currently loaded extensions."""
        return list(self.__extensions.values())

    @property
    def default_modules(self) -> list[Extension]:
        """Returns a list of currently loaded default modules."""
        return [ext for ext in self.__extensions.values() if ext.is_default()]

    @property
    def plugins(self) -> list[Extension]:
        """Returns a list of currently loaded plugins."""
        return [ext for ext in self.__extensions.values() if not ext.is_default()]

    async def setup_hook(self) -> None:
        if self.auto_load_default_modules:
            await self.load_default_modules()

        if self.auto_load_plugins:
            await self.load_plugins()

        if self.translator is not None:
            await self.tree.set_translator(DPYTranslator(self.translator))

        if self.use_db:
            if not self._db_engine:
                raise RuntimeError("Database engine not provided.")
            await Database.connect(
                self._db_engine, create_tables=self._create_db_tables
            )

    async def get_context[Ctx: Context](
        self, message: discord.Message, *, cls: type[Ctx] = discord.utils.MISSING
    ) -> Ctx:
        if cls is discord.utils.MISSING:
            from .context import Context

            cls = Context  # pyright: ignore[reportAssignmentType]
        ctx = await super().get_context(message, cls=cls)
        # discord.py resolves prefix commands by their registered (source) names.
        # Once it has consumed the actual prefix, try localized root names too.
        if ctx.command is None and ctx.prefix is not None and ctx.invoked_with:
            for command in self.commands:
                if not isinstance(command, LocalizableMixin) or not command.localize:
                    continue
                names = await command.get_localized_names(ctx)
                if any(
                    name.casefold() == ctx.invoked_with.casefold()
                    if self.case_insensitive
                    else name == ctx.invoked_with
                    for name in names
                ):
                    ctx.command = command
                    break
        return ctx

    def clear_commands_translation_cache(self) -> None:
        """Clear all command's translations cache."""
        for cmd in self.walk_commands():
            if isinstance(cmd, LocalizableMixin):
                cmd.get_localized.cache_clear()
                cmd.translated_names.clear()
                cmd.translated_aliases.clear()
                cmd.translated_short_docs.clear()
                cmd.translated_descriptions.clear()
                cmd.translated_help.clear()
                cmd.translated_parameter_descriptions.clear()
        for cog in self.cogs.values():
            if isinstance(cog, PikiCog):
                cog.clear_localization_cache()

    async def load_default_modules(
        self, *, check: Callable[[ExtensionInfo], bool] | None = None
    ) -> None:
        """Load the default modules into the bot.

        Parameters
        ----------
        check: Callable[[:class:`ExtensionInfo`], :class:`bool`] | :data:`None`
            A callable that is called per extension and may return a truthy or falsey value denoting
            whether the extension should be loaded. This is useful to load extensions that only meet
            certain criteria.

        Raises
        ------
        FileNotFoundError
            If the default modules path does not exist.
        """
        path = self.DEFAULT_MODULES_PATH

        if not path.exists():
            raise FileNotFoundError(f"Default Modules path {path!r} does not exist.")

        objs = [obj for obj in path.iterdir() if obj.is_dir()]

        with tqdm.tqdm(
            total=len(objs),
            desc="Loading default modules",
            unit="module",
        ) as pbar:
            for obj in objs:
                pbar.set_postfix_str(f"Loading {obj.name}")

                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    await self.load_extension(obj, check=check)

                output = buffer.getvalue()
                pbar.write(output)
                pbar.update(1)

    async def load_plugins(
        self, *, check: Callable[[ExtensionInfo], bool] | None = None
    ) -> None:
        """Load the third-party plugins into the bot.

        Parameters
        ----------
        check: Callable[[:class:`ExtensionInfo`], :class:`bool`] | :data:`None`
            A callable that is called per extension and may return a truthy or falsey value denoting
            whether the extension should be loaded. This is useful to load extensions that only meet
            certain criteria.

        Raises
        ------
        FileNotFoundError
            If the plugins path does not exist.
        """
        path = self.DEFAULT_PLUGINS_PATH

        if not path.exists():
            raise FileNotFoundError(f"Plugins path {path!r} does not exist.")

        objs = [obj for obj in path.iterdir() if obj.is_dir()]

        with tqdm.tqdm(
            total=len(objs),
            desc="Loading plugins",
            unit="plugin",
        ) as pbar:
            for obj in objs:
                pbar.set_postfix_str(f"Loading {obj.name}")

                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    await self.load_extension(obj, check=check)

                output = buffer.getvalue()
                pbar.write(output)
                pbar.update(1)

    async def load_extension(
        self, path: Path, *, check: Callable[[ExtensionInfo], bool] | None = None
    ) -> None:
        """Load an extension from the given path.

        This path should point to a folder with a valid ``extension.yml`` file present
        at its root.

        Parameters
        ----------
        path: :class:`pathlib.Path`
            The path to the extension folder.

        Raises
        ------
        FileNotFoundError
            If the extension folder does not contain an ``extension.yml`` file.
        """
        dist_info = path / "extension.yml"

        if not dist_info.exists():
            raise FileNotFoundError(f"Extension file {dist_info!r} does not exist.")

        extension = Extension(bot=self, ext_path=path, dist_info="extension.yml")
        if check and not check(extension.info):
            _log.info(
                f"Extension {extension.info.name!r} at {path!r} was skipped because it did not meet the check."
            )
            return

        try:
            await extension.load()
        except Exception as e:
            raise ImportError(
                f"Failed to load extension {extension.info.name!r} at {path!r}"
            ) from e
        else:
            self.__extensions[extension.info.name] = extension

    async def unload_extension(self, name: str) -> None:
        """Unload an extension by its name.

        Parameters
        ----------
        name: :class:`str`
            The name of the extension to unload.
        """
        extension = self.__extensions.pop(name, None)
        if extension is None:
            return

        try:
            await extension.unload()
        except Exception as e:
            _log.error(f"Failed to unload extension {name!r}", exc_info=e)

    def command[C: PikiCommand[Any, Any, Any], ContextT: Context, **FuncParams, RType](
        self,
        name: str = discord.utils.MISSING,
        cls: type[C] = PikiCommand,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [Callable[Concatenate[ContextT, FuncParams], Coroutine[Any, Any, RType]]],  # pyright: ignore[reportInvalidTypeVarUse]
        C,
    ]:
        return super().command(name=name, cls=cls, *args, **kwargs)

    def group[C: PikiGroup[Any, Any, Any], ContextT: Context, **FuncParams, RType](
        self,
        name: str = discord.utils.MISSING,
        cls: type[C] = PikiGroup,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [Callable[Concatenate[ContextT, FuncParams], Coroutine[Any, Any, RType]]],  # pyright: ignore[reportInvalidTypeVarUse]
        C,
    ]:
        return super().group(name=name, cls=cls, *args, **kwargs)
