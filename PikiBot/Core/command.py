"""
MIT License

Copyright (c) 2026-present, DA-344
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Coroutine, Generator, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Concatenate, Literal, Self, overload

import discord
from async_lru import alru_cache
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.core import hooked_wrapped_callback

if TYPE_CHECKING:
    from discord.app_commands.transformers import CommandParameter

    from .bot import PikiBot as Bot
    from .context import Context

__all__ = (
    "LocalizableMixin",
    "PikiCommand",
    "PikiGroup",
    "command",
    "group",
)


def localized_key[
    Cls: (
        PikiCommand[Any, ..., Any]
        | PikiGroup[Any, ..., Any]
        | PikiHybridCommand[Any, ..., Any]
        | PikiHybridGroup[Any, ..., Any]
    )
](
    self: Cls,
    context: Context,
) -> tuple[str, type[Cls], str]:
    return (self.qualified_name, type(self), self.get_user_locale(context))


cache = functools.partial(alru_cache, maxsize=512, key=localized_key)


class LocalizableMixin:
    """Mixin class to add localization support to commands and groups.

    Parameters
    ----------
    localize: :class:`bool`
        Whether the command or group should be localized.
    user_locale: :class:`Callable`[[:class:`~.Context`], :class:`str`] | :data:`None`
        A function called automatically to determine a user's locale based on the context.
        If this function is ``None``, the locale is inherited from the parent command,
        then the interaction or guild, and finally the bot's default locale.
    """

    GLOBAL_LOCALIZE: ClassVar[bool | None] = None
    GLOBAL_CATALOG_VALIDATOR: ClassVar[Callable[[str], str] | None] = None
    GLOBAL_DOMAIN_GETTER: ClassVar[
        Callable[[str, app_commands.TranslationContextTypes], str | None] | None
    ] = None

    if TYPE_CHECKING:
        _cog: commands.Cog | None
        _localization_domain: str | None
        original_aliases: tuple[str, ...]
        _translated_names: dict[str, str]
        _translated_aliases: dict[str, tuple[str, ...]]
        _translated_short_docs: dict[str, str]
        _translated_descriptions: dict[str, str]
        _translated_help: dict[str, str | None]
        _translated_parameter_descriptions: dict[str, dict[str, str]]
        name: str
        parent: PikiGroup[Any, ..., Any] | None
        clean_params: dict[str, commands.Parameter]
        short_doc: str | None
        description: str | None
        help: str | None
        signature: str | None
        invoke_without_command: bool

    def __init__(
        self,
        localize: bool = False,
        user_locale: Callable[[Context], str] | None = None,
    ) -> None:
        self._localize: bool = (
            LocalizableMixin.GLOBAL_LOCALIZE
            if LocalizableMixin.GLOBAL_LOCALIZE is not None
            else localize
        )
        self._user_locale: Callable[[Context], str] | None = user_locale

    def _init_localization(
        self,
        *,
        localize: bool,
        user_locale: Callable[[Context], str] | None,
        localization_domain: str | None,
    ) -> None:
        self._localize = (
            LocalizableMixin.GLOBAL_LOCALIZE
            if LocalizableMixin.GLOBAL_LOCALIZE is not None
            else localize
        )
        self._user_locale = user_locale
        self._localization_domain = localization_domain
        self.original_aliases = tuple(getattr(self, "aliases", ()))
        self._translated_names: dict[str, str] = {}
        self._translated_aliases: dict[str, tuple[str, ...]] = {}
        self._translated_short_docs: dict[str, str] = {}
        self._translated_descriptions: dict[str, str] = {}
        self._translated_help: dict[str, str | None] = {}
        self._translated_parameter_descriptions: dict[str, dict[str, str]] = {}

    def get_user_locale(self, context: Context, /) -> str:
        """Get the user locale based on the context.

        Parameters
        ----------
        context: :class:`~.Context`
            The context from which to determine the user's locale.

        Returns
        -------
        :class:`str`
            The normalized catalog locale for the context.
        """
        if self._user_locale is not None:
            locale = self._user_locale(context)
        elif context.interaction is not None:
            locale = context.interaction.locale.value
        elif isinstance(getattr(self, "parent", None), LocalizableMixin):
            assert self.parent is not None
            locale = self.parent.get_user_locale(context)
        elif context.guild is not None:
            guild_locale = context.guild.preferred_locale
            locale: str = guild_locale.value
        else:
            locale = getattr(context.bot.translator, "default_locale", "en")

        validator = LocalizableMixin.GLOBAL_CATALOG_VALIDATOR
        return validator(locale) if validator is not None else locale

    def get_localization_domain(self) -> str | None:
        """Return this command's domain, inheriting it from its parent if needed."""
        if self._localization_domain is not None:
            return self._localization_domain
        parent = getattr(self, "parent", None)
        if isinstance(parent, LocalizableMixin):
            return parent.get_localization_domain()
        return None

    def _preserve_command_state[T: LocalizableMixin](self: T, clone: T, /) -> T:
        """Keep localization settings and Cog binding on a command clone."""
        clone._localize = self._localize
        clone._user_locale = self._user_locale
        clone._localization_domain = self._localization_domain
        clone.original_aliases = self.original_aliases
        clone._translated_names = self._translated_names
        clone._translated_aliases = self._translated_aliases
        clone._translated_short_docs = self._translated_short_docs
        clone._translated_descriptions = self._translated_descriptions
        clone._translated_help = self._translated_help
        clone._translated_parameter_descriptions = (
            self._translated_parameter_descriptions
        )
        clone._cog = self._cog
        return clone

    @property
    def translated_names(self) -> dict[str, str]:
        """Names cached by catalog locale, kept separate from command aliases."""
        return self._translated_names

    @property
    def translated_aliases(self) -> dict[str, tuple[str, ...]]:
        """Translated forms of declared aliases, keyed by catalog locale."""
        return self._translated_aliases

    @property
    def translated_short_docs(self) -> dict[str, str]:
        """Localized ``short_doc`` values, keyed by catalog locale."""
        return self._translated_short_docs

    @property
    def translated_descriptions(self) -> dict[str, str]:
        """Localized command descriptions, keyed by catalog locale."""
        return self._translated_descriptions

    @property
    def translated_help(self) -> dict[str, str | None]:
        """Localized long help text, keyed by catalog locale."""
        return self._translated_help

    @property
    def translated_parameter_descriptions(self) -> dict[str, dict[str, str]]:
        """Localized parameter descriptions, grouped by catalog and parameter name."""
        return self._translated_parameter_descriptions

    async def get_localized_names(self, context: Context, /) -> tuple[str, ...]:
        """Return the localized command name and aliases without cloning the command."""
        locale = self.get_user_locale(context)
        if (
            locale not in self._translated_names
            or locale not in self._translated_aliases
        ):
            domain = self.get_localization_domain()
            name = await context.translate(self.name, target=locale, domain=domain)
            aliases = tuple(
                [
                    await context.translate(alias, target=locale, domain=domain)
                    for alias in self.original_aliases
                ]
            )
            self._translated_names[locale] = name
            self._translated_aliases[locale] = aliases
        return (
            self._translated_names[locale],
            *self._translated_aliases[locale],
        )

    async def cache_localized_help(self, context: Context, /) -> None:
        """Cache help text for this command without making a localized command clone."""
        if not self._localize:
            return

        locale = self.get_user_locale(context)
        if all(
            locale in cache
            for cache in (
                self._translated_short_docs,
                self._translated_descriptions,
                self._translated_help,
                self._translated_parameter_descriptions,
            )
        ):
            return

        await self.get_localized_names(context)
        domain = self.get_localization_domain()

        async def translate(value: str | None) -> str | None:
            if not value:
                return value
            return await context.translate(value, target=locale, domain=domain)

        short_doc = await translate(self.short_doc) or ""
        description = await translate(self.description) or ""
        help_text = await translate(self.help)
        parameter_descriptions = {
            name: await translate(parameter.description) or ""
            for name, parameter in self.clean_params.items()
        }
        self._translated_short_docs[locale] = short_doc
        self._translated_descriptions[locale] = description
        self._translated_help[locale] = help_text
        self._translated_parameter_descriptions[locale] = parameter_descriptions

    @property
    def localize(self) -> bool:
        """Whether the command or group's metadata should be localized."""
        return self._localize

    async def get_localized[S](self: S, context: Context, /) -> S:
        """Return the localized version of this command.

        :meth:`.get_user_locale` is used to determine the user's locale based on
        the context.

        Parameters
        ----------
        context: :class:`~.Context`
            The context from which to determine the user's locale for localization.

        Returns
        -------
        Self
            The localized version of this object.
        """
        raise NotImplementedError("get_localized must be implemented by subclasses.")


class PikiCommand[Cog: commands.Cog | None, **FuncParams, RType](
    commands.Command[Cog, FuncParams, RType], LocalizableMixin
):
    """Prefix command with optional per-catalog names, aliases, and help text.

    Parameters
    ----------
    func: :class:`Callable`
        Async callback invoked by the command.
    localize: :class:`bool`
        Translate the command name and help metadata for the context locale. The bot-wide
        localization setting takes precedence when configured.
    user_locale: :class:`Callable` | :data:`None`
        Callback that returns the catalog locale. By default, the command inherits its
        parent's locale, then uses the guild locale or the bot's default locale.
    localization_domain: :class:`str` | :data:`None`
        Gettext domain for this command. If omitted, the parent domain or translator default is used.
    **kwargs: :data:`Any`
        Other command options forwarded to :class:`commands.Command`.
    """

    if TYPE_CHECKING:
        parent: PikiGroup[Any, ..., Any] | None  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        func: (
            Callable[Concatenate[Cog, Context, FuncParams], Coroutine[Any, Any, RType]]
            | Callable[Concatenate[Context, FuncParams], Coroutine[Any, Any, RType]]
        ),
        /,
        localize: bool = False,
        user_locale: Callable[[Context], str] | None = None,
        localization_domain: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(func, **kwargs)  # pyright: ignore[reportArgumentType]
        self._init_localization(
            localize=localize,
            user_locale=user_locale,
            localization_domain=localization_domain,
        )

    def copy(self) -> Self:
        return self._preserve_command_state(super().copy())

    @cache()
    async def get_localized(self, context: Context, /) -> Self:
        return await self._get_localized(context)

    async def _get_localized(self, context: Context, /) -> Self:
        locale = self.get_user_locale(context)
        trns = functools.partial(
            context.translate,
            target=locale,
            domain=self.get_localization_domain(),
        )
        this = self.copy()
        this.update(
            name=await trns(this.name),
            help=(await trns(this.help)) if this.help else None,
            brief=(await trns(this.brief)) if this.brief else None,
            description=await trns(this.description),
        )
        this.parent = await this.parent.get_localized(context) if this.parent else None

        for param in this.params.values():
            param._displayed_name = await trns(param.displayed_name or param.name)
            param._description = (  # type: ignore
                await trns(param.description) if param.description else param.empty
            )

        return this

    async def invoke(self, ctx: Context, /) -> None:
        cmd = self
        await cmd.prepare(ctx)

        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(cmd, ctx, cmd.callback)  # type: ignore
        await injected(*ctx.args, **ctx.kwargs)  # type: ignore

    async def reinvoke(self, ctx: Context, /, *, call_hooks: bool = False) -> None:
        ctx.command = self
        await self._parse_arguments(ctx)

        if call_hooks:
            await self.call_before_hooks(ctx)

        ctx.invoked_subcommand = None
        try:
            await self.callback(*ctx.args, **ctx.kwargs)  # type: ignore
        except:
            ctx.command_failed = True
            raise
        finally:
            if call_hooks:
                await self.call_after_hooks(ctx)


class PikiGroup[Cog: commands.Cog | None, **FuncParams, RType](
    commands.Group[Cog, FuncParams, RType], LocalizableMixin
):
    """Prefix command group with optional per-catalog names, aliases, and help text.

    Parameters
    ----------
    localize: :class:`bool`
        Translate this group's name and help metadata for the context locale. The bot-wide
        localization setting takes precedence when configured.
    user_locale: :class:`Callable` | :data:`None`
        Callback that returns the catalog locale. By default, the group inherits its
        parent's locale, then uses the guild locale or the bot's default locale.
    localization_domain: :class:`str` | :data:`None`
        Gettext domain for this group and, by default, its children.
    **kwargs: :data:`Any`
        Other group options forwarded to :class:`commands.Group`.
    """

    if TYPE_CHECKING:
        parent: PikiGroup[Any, ..., Any] | None  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        *args: Any,
        localize: bool = False,
        user_locale: Callable[[Context], str] | None = None,
        localization_domain: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._init_localization(
            localize=localize,
            user_locale=user_locale,
            localization_domain=localization_domain,
        )

    def copy(self) -> Self:
        return self._preserve_command_state(super().copy())

    @cache()
    async def get_localized(self, context: Context, /) -> Self:
        return await self._get_localized(context)

    async def _get_localized(self, context: Context, /) -> Self:
        locale = self.get_user_locale(context)
        trns = functools.partial(
            context.translate,
            target=locale,
            domain=self.get_localization_domain(),
        )
        this = self.copy()
        this.update(
            name=await trns(this.name),
            help=(await trns(this.help)) if this.help else None,
            brief=(await trns(this.brief)) if this.brief else None,
            description=await trns(this.description),
        )
        this.parent = await this.parent.get_localized(context) if this.parent else None

        for param in this.params.values():
            param._displayed_name = await trns(param.displayed_name or param.name)
            param._description = (  # type: ignore
                await trns(param.description) if param.description else param.empty
            )

        return this

    def command[C: PikiCommand[Any, ..., Any]](
        self,
        name: str = discord.utils.MISSING,
        cls: type[C] = PikiCommand,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [
            Callable[Concatenate[Cog, Context, FuncParams], Coroutine[Any, Any, RType]]
            | Callable[Concatenate[Context, FuncParams], Coroutine[Any, Any, RType]]
        ],
        C,
    ]:
        return super().command(name=name, cls=cls, *args, **kwargs)

    def group[C: PikiGroup[Any, ..., Any]](
        self,
        name: str = discord.utils.MISSING,
        cls: type[C] = discord.utils.MISSING,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [
            Callable[Concatenate[Context, FuncParams], Coroutine[Any, Any, RType]]
            | Callable[
                Concatenate[Cog, Context, FuncParams], Coroutine[Any, Any, RType]
            ]
        ],
        C,
    ]:
        if cls is discord.utils.MISSING:
            cls = PikiGroup  # type: ignore
        return super().group(name=name, cls=cls, *args, **kwargs)

    async def invoke(self, ctx: Context, /) -> None:
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command

        cmd = self
        if early_invoke:
            await cmd.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = cmd.all_commands.get(trigger, None)
            if ctx.invoked_subcommand is None:
                ctx.invoked_subcommand = await self._find_localized_subcommand(
                    trigger, ctx
                )

        if early_invoke:
            injected = hooked_wrapped_callback(cmd, ctx, cmd.callback)  # type: ignore
            await injected(*ctx.args, **ctx.kwargs)  # type: ignore

        ctx.invoked_parents.append(ctx.invoked_with)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    async def _find_localized_subcommand(
        self, trigger: str, ctx: Context, /
    ) -> commands.Command[Any, ..., Any] | None:
        """Resolve a translated child name while retaining the registered command."""
        for child in self.commands:
            if not isinstance(child, LocalizableMixin) or not child.localize:
                continue
            names = await child.get_localized_names(ctx)
            matches = (
                (lambda name: name.casefold() == trigger.casefold())
                if self.case_insensitive
                else (lambda name: name == trigger)
            )
            if any(matches(name) for name in names):
                return child  # invoke() will localize it for this context
        return None

    def get_localized_command(
        self, name: str, locale: str
    ) -> (
        commands.Command[Any, ..., Any]
        | commands.Group[Any, ..., Any]
        | PikiCommand[Any, ..., Any]
        | PikiGroup[Any, ..., Any]
        | None
    ):
        for cmd in self.commands:
            if cmd.name == name:
                return cmd
            if isinstance(cmd, LocalizableMixin):
                translated = cmd._translated_names.get(locale)
                if translated and translated == name:
                    return cmd
        return None

    async def reinvoke(self, ctx: Context, /, *, call_hooks: bool = False) -> None:
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command

        cmd = self
        if early_invoke:
            ctx.command = cmd
            await cmd._parse_arguments(ctx)

            if call_hooks:
                await cmd.call_before_hooks(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = cmd.all_commands.get(trigger, None)
            if ctx.invoked_subcommand is None:
                ctx.invoked_subcommand = await self._find_localized_subcommand(
                    trigger, ctx
                )

        if early_invoke:
            try:
                await cmd.callback(*ctx.args, **ctx.kwargs)  # type: ignore
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await cmd.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.invoked_with)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)


class PikiHybridCommand[Cog: commands.Cog, **FuncParams, RType](
    commands.HybridCommand[Cog, FuncParams, RType],
    PikiCommand[Cog, FuncParams, RType],
):
    """Command available both as a prefix command and an application command.

    Parameters
    ----------
    func: :class:`Callable`
        Async callback shared by both command interfaces.
    localize: :class:`bool`
        Enable application-command localization and translated prefix-name lookup. Defaults to true.
    user_locale: :class:`Callable` | :data:`None`
        Callback that returns the catalog locale. By default, the command inherits its
        parent's locale, then uses the interaction, guild, or bot default locale.
    localization_domain: :class:`str` | :data:`None`
        Gettext domain for this command. If omitted, the parent domain or translator default is used.
    name: :class:`str` | :class:`app_commands.locale_str`
        Application-command name; defaults to the callback name.
    description: :class:`str` | :class:`app_commands.locale_str`
        Application-command description; defaults to the callback docstring.
    **attrs: :data:`Any`
        Additional hybrid-command options forwarded to discord.py.
    """

    if TYPE_CHECKING:
        parent: PikiHybridGroup[Any, ..., Any] | None  # pyright:  ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        func: (
            Callable[Concatenate[Cog, Context, FuncParams], Coroutine[Any, Any, RType]]
            | Callable[Concatenate[Context, FuncParams], Coroutine[Any, Any, RType]]
        ),
        *,
        localize: bool = True,
        user_locale: Callable[[Context], str] | None = None,
        localization_domain: str | None = None,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        description: str | app_commands.locale_str = discord.utils.MISSING,
        **attrs: Any,
    ) -> None:
        localize = (
            LocalizableMixin.GLOBAL_LOCALIZE
            if LocalizableMixin.GLOBAL_LOCALIZE is not None
            else localize
        )
        parent = attrs.get("parent")
        if localization_domain is None and isinstance(parent, LocalizableMixin):
            localization_domain = parent.get_localization_domain()

        if localize is True:
            if name is not discord.utils.MISSING:
                name = (
                    app_commands.locale_str(name, domain=localization_domain)
                    if not isinstance(name, app_commands.locale_str)
                    else name
                )
            else:
                name = app_commands.locale_str(
                    func.__name__, domain=localization_domain
                )

            if description is not discord.utils.MISSING:
                description = (
                    app_commands.locale_str(description, domain=localization_domain)
                    if not isinstance(description, app_commands.locale_str)
                    else description
                )
            else:
                doc = func.__doc__
                description = (
                    app_commands.locale_str(
                        doc.splitlines()[0],
                        domain=localization_domain,
                    )
                    if doc is not None
                    else "..."
                )
        else:
            name = str(name) if name is not discord.utils.MISSING else func.__name__
            description = (
                str(description)
                if description is not discord.utils.MISSING
                else (func.__doc__ or "...")
            )

        super().__init__(
            func,  # pyright: ignore[reportArgumentType]
            name=name,
            description=description,
            **attrs,
        )
        self._localize = localize
        self._init_localization(
            localize=localize,
            user_locale=user_locale,
            localization_domain=localization_domain,
        )

    def copy(self) -> Self:
        return self._preserve_command_state(super().copy())

    @cache()
    async def get_localized(self, context: Context, /) -> Self:
        # if an interaction is set, it should already be localized by Discord's side
        if context.interaction is not None:
            return self
        return await super(commands.HybridCommand, self)._get_localized(context)

    async def invoke(self, ctx: Context, /) -> None:
        await super(commands.HybridCommand, self).invoke(ctx)

    async def reinvoke(self, ctx: Context, /, *, call_hooks: bool = False) -> None:
        await super(commands.HybridCommand, self).reinvoke(ctx, call_hooks=call_hooks)


class PikiHybridGroup[Cog: commands.Cog, **FuncParams, RType](
    commands.HybridGroup[Cog, FuncParams, RType],
    PikiGroup[Cog, FuncParams, RType],
):
    """Group available as both a prefix-command group and an application-command group.

    Parameters
    ----------
    func: :class:`Callable`
        Async callback for the group and its optional fallback command.
    localize: :class:`bool`
        Enable application-command localization and translated prefix-name lookup. Defaults to true.
    user_locale: :class:`Callable` | :data:`None`
        Callback that returns the catalog locale. By default, the group inherits its
        parent's locale, then uses the interaction, guild, or bot default locale.
    localization_domain: :class:`str` | :data:`None`
        Gettext domain for this group and, by default, its children.
    name: :class:`str` | :class:`app_commands.locale_str`
        Application-command name; defaults to the callback name.
    description: :class:`str` | :class:`app_commands.locale_str`
        Application-command description; defaults to the callback docstring.
    fallback: :class:`str` | :class:`app_commands.locale_str` | :data:`None`
        Application-command fallback name for invoking the group's callback.
    **attrs: :data:`Any`
        Additional hybrid-group options forwarded to discord.py.
    """

    if TYPE_CHECKING:
        parent: PikiGroup[Any, ..., Any] | None  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        func: Callable[..., RType],
        *args: Any,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        description: str | app_commands.locale_str = discord.utils.MISSING,
        fallback: str | app_commands.locale_str | None = None,
        localize: bool = True,
        user_locale: Callable[[Context], str] | None = None,
        localization_domain: str | None = None,
        **attrs: Any,
    ) -> None:
        localize = (
            LocalizableMixin.GLOBAL_LOCALIZE
            if LocalizableMixin.GLOBAL_LOCALIZE is not None
            else localize
        )
        parent = attrs.get("parent")
        if localization_domain is None and isinstance(parent, LocalizableMixin):
            localization_domain = parent.get_localization_domain()

        if localize is True:
            if name is not discord.utils.MISSING:
                name = (
                    app_commands.locale_str(name, domain=localization_domain)
                    if not isinstance(name, app_commands.locale_str)
                    else name
                )
            else:
                name = app_commands.locale_str(
                    func.__name__, domain=localization_domain
                )

            if description is not discord.utils.MISSING:
                description = (
                    app_commands.locale_str(description, domain=localization_domain)
                    if not isinstance(description, app_commands.locale_str)
                    else description
                )
            else:
                doc = func.__doc__
                description = (
                    app_commands.locale_str(
                        doc.splitlines()[0],
                        domain=localization_domain,
                    )
                    if doc is not None
                    else "..."
                )
        else:
            name = str(name) if name is not discord.utils.MISSING else func.__name__
            description = (
                str(description)
                if description is not discord.utils.MISSING
                else (func.__doc__ or "...")
            )

        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            func,
            *args,
            name=name,
            description=description,
            fallback=fallback,
            **attrs,
        )
        self._localize = localize
        self._init_localization(
            localize=localize,
            user_locale=user_locale,
            localization_domain=localization_domain,
        )

    def copy(self) -> Self:
        return self._preserve_command_state(super().copy())

    def command[**CParams, CRType](
        self,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        *args: Any,
        with_app_command: bool = True,
        **kwargs: Any,
    ) -> Callable[
        [
            Callable[Concatenate[Cog, Context, CParams], CRType]
            | Callable[Concatenate[Context, CParams], CRType]
        ],
        PikiHybridCommand[Cog, CParams, CRType],
    ]:
        def decorator(
            func: Callable[Concatenate[Cog, Context, CParams], CRType]
            | Callable[Concatenate[Context, CParams], CRType],
        ) -> PikiHybridCommand[Cog, CParams, CRType]:
            kwargs.setdefault("parent", self)
            result = hybrid_command(
                name=name, *args, with_app_command=with_app_command, **kwargs
            )(func)
            self.add_command(result)
            return result

        return decorator

    def group[**GParams, GRType](
        self,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        *args: Any,
        with_app_command: bool = True,
        **kwargs: Any,
    ) -> Callable[
        [
            Callable[Concatenate[Cog, Context, GParams], GRType]
            | Callable[Concatenate[Context, GParams], GRType]
        ],
        PikiHybridGroup[Cog, GParams, GRType],
    ]:
        def decorator(
            func: Callable[Concatenate[Cog, Context, GParams], GRType]
            | Callable[Concatenate[Context, GParams], GRType],
        ) -> PikiHybridGroup[Cog, GParams, GRType]:
            kwargs.setdefault("parent", self)
            result = hybrid_group(
                name=name, *args, with_app_command=with_app_command, **kwargs
            )(func)
            self.add_command(result)
            return result

        return decorator

    @cache()
    async def get_localized(self, context: Context, /) -> Self:
        if context.interaction is not None:
            return self
        return await super(commands.HybridGroup, self)._get_localized(context)

    async def invoke(self, ctx: Context, /) -> None:
        await super(commands.HybridGroup, self).invoke(ctx)

    async def reinvoke(self, ctx: Context, /, *, call_hooks: bool = False) -> None:
        await super(commands.HybridGroup, self).reinvoke(ctx, call_hooks=call_hooks)


def command[C: PikiCommand[Any, ..., Any]](
    name: str = discord.utils.MISSING,
    cls: type[C] = PikiCommand,
    **kwargs: Any,
) -> Any:
    """A decorator that transforms a function into a :class:`PikiCommand`.

    This is a shortcut for :meth:`discord.ext.commands.command` with ``cls`` as :class:`PikiCommand`
    by default.

    Parameters
    ----------
    localize: :class:`bool`
        Whether the command should be localized on invoke and parameters.
        This means that per each context created, the command and its parameters will be localized
        accordingly based on the command's ``user_locale`` function.
    user_locale: :class:`Callable`[[:class:`~.Context`], :class:`str`] | :data:`None`
        A function called automatically to determine a user's locale based on the context.
        If this function is ``None``, the locale is inherited from the parent command,
        then the interaction or guild, and finally the bot's default locale.
    localization_domain: :class:`str` | :data:`None`
        The localization domain that must be used to translated this command's strings.
    """
    return commands.command(name=name, cls=cls, **kwargs)


def hybrid_command[C: PikiHybridCommand[Any, ..., Any]](
    name: str | app_commands.locale_str = discord.utils.MISSING,
    *,
    with_app_command: bool = True,
    cls: type[C] = PikiHybridCommand,
    **attrs: Any,
) -> Callable[..., C]:
    """A decorator that transforms a function into a :class:`PikiHybridCommand`.

    .. note::

        All locale_str instances can have certain extras the Translator uses to determine the catalog
        and domain used to translate all available strings. This are stored in the locale_str's extras
        and are the following:

        - ``catalog_validator`` a function following ``(discord.Locale.value) -> str`` structure that validates
          a Locale enum member to return the proper catalog name. Defaults to the Enum member value.
        - ```domain_getter`` as a function following ``(catalog_name, app_commands.TranslationContextType) -> str`` structure
          that works as a domain getter.

    Parameters
    ----------
    localize: :class:`bool`
        Whether the command should be localized. For the application command side, this is done by sending
        the translated mappings to Discord. For text commands, translated command names and aliases
        are cached per catalog and used for lookup. Argument parsing continues to use the declared
        parameters.
    user_locale: :class:`Callable`[[:class:`~.Context`], :class:`str`] | :data:`None`
        A function called automatically to determine a user's locale based on the context.
    localization_domain: :class:`str` | :data:`None`
        The localization domain that must be used to translate this command's strings.
    """

    def decorator(func: Callable[..., Any]) -> C:
        if isinstance(func, commands.Command):
            raise TypeError("callback is already a command.")
        return cls(func, name=name, with_app_command=with_app_command, **attrs)

    return decorator


def hybrid_group[G: PikiHybridGroup[Any, ..., Any]](
    name: str | app_commands.locale_str = discord.utils.MISSING,
    *,
    with_app_command: bool = True,
    cls: type[G] = PikiHybridGroup,
    **attrs: Any,
) -> Callable[..., G]:
    """A decorator that transforms a function into a :class:`PikiHybridGroup`.

    .. note::

        All locale_str instances can have certain extras the Translator uses to determine the catalog
        and domain used to translate all available strings. This are stored in the locale_str's extras
        and are the following:

        - ``catalog_validator`` a function following ``(discord.Locale.value) -> str`` structure that validates
          a Locale enum member to return the proper catalog name. Defaults to the Enum member value.
        - ```domain_getter`` as a function following ``(catalog_name, app_commands.TranslationContextType) -> str`` structure
          that works as a domain getter.

    Parameters
    ----------
    localize: :class:`bool`
        Whether the group should be localized. For the application command side, this is done by sending
        the translated mappings to Discord. For text commands, translated command names and aliases
        are cached per catalog and used for lookup. Argument parsing continues to use the declared
        parameters.
    user_locale: :class:`Callable`[[:class:`~.Context`], :class:`str`] | :data:`None`
        A function called automatically to determine a user's locale based on the context.
    localization_domain: :class:`str` | :data:`None`
        The localization domain that must be used to translate this command's strings.
    """

    def decorator(func: Callable[..., Any]) -> G:
        if isinstance(func, commands.Command):
            raise TypeError("callback is already a command.")
        return cls(func, name=name, with_app_command=with_app_command, **attrs)

    return decorator


def group[G: PikiGroup[Any, ..., Any]](
    name: str = discord.utils.MISSING,
    cls: type[G] = PikiGroup,
    **kwargs: Any,
) -> Callable[..., G]:
    """A decorator that transforms a function into a :class:`PikiGroup`.

    This is a shortcut for :meth:`discord.ext.commands.group` with ``cls`` as :class:`PikiGroup`
    by default.

    Parameters
    ----------
    localize: :class:`bool`
        Whether the group should be localized on invoke and parameters.
        This means that per each context created, the group and its parameters will be localized
        accordingly based on the group's ``user_locale`` function.
    user_locale: :class:`Callable`[[:class:`~.Context`], :class:`str`] | :data:`None`
        A function called automatically to determine a user's locale based on the context.
        If this function is ``None``, the locale is inherited from the parent command,
        then the interaction or guild, and finally the bot's default locale.
    localization_domain: :class:`str` | :data:`None`
        The localization domain that must be used to translate this command's strings.
    """
    return commands.group(name=name, cls=cls, **kwargs)


class PikiAppCommand[Group: app_commands.Group | commands.Cog, **FuncParams, RType](
    app_commands.Command[Group, FuncParams, RType]
):
    """Application command that automatically prepares translatable strings.

    Parameters
    ----------
    name: :class:`str` | :class:`app_commands.locale_str`
        Command name shown in Discord.
    description: :class:`str` | :class:`app_commands.locale_str`
        Command description shown in Discord.
    callback: :class:`Callable`
        Async interaction callback.
    nsfw: :class:`bool`
        Restrict the command to age-restricted channels.
    parent: :class:`app_commands.Group` | :class:`commands.Cog` | :data:`None`
        Group or cog that owns the command.
    guild_ids: :class:`list`[:class:`int`] | :data:`None`
        Guilds where the command is registered by default.
    allowed_contexts: :class:`app_commands.AppCommandContext` | :data:`None`
        Interaction contexts where the command can be used.
    allowed_installs: :class:`app_commands.AppInstallationType` | :data:`None`
        Installation contexts where the command can be installed.
    auto_locale_strings: :class:`bool`
        Wrap eligible strings in :class:`app_commands.locale_str` before translation.
    extras: :class:`dict` | :data:`discord.utils.MISSING`
        Application metadata that discord.py does not interpret.
    locale_strings_extras: :class:`dict` | :data:`discord.utils.MISSING`
        Extras attached to generated locale strings, such as catalog or domain selectors.
    """

    if TYPE_CHECKING:
        parent: PikiAppGroup | None  # pyright: ignore[reportIncompatibleVariableOverride]

        @property
        def root_parent(self) -> PikiAppGroup | None: ...

    def __init__(
        self,
        *,
        name: str | app_commands.locale_str,
        description: str | app_commands.locale_str,
        callback: Callable[
            Concatenate[Group, discord.Interaction[Bot], FuncParams],
            RType,
        ]
        | Callable[
            Concatenate[discord.Interaction[Bot], FuncParams],
            RType,
        ],
        nsfw: bool = False,
        parent: PikiAppGroup | None = None,
        guild_ids: list[int] | None = None,
        allowed_contexts: app_commands.AppCommandContext | None = None,
        allowed_installs: app_commands.AppInstallationType | None = None,
        auto_locale_strings: bool = True,
        extras: dict[Any, Any] = discord.utils.MISSING,
        locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
    ) -> None:
        self.locale_strings_extras: dict[Any, Any] = locale_strings_extras or {}
        super().__init__(
            name=name,
            description=description,
            callback=callback,  # pyright: ignore[reportArgumentType]
            nsfw=nsfw,
            parent=parent,
            guild_ids=guild_ids,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            auto_locale_strings=auto_locale_strings,
            extras=extras,
        )

    def _convert_to_locale_strings(self) -> None:
        if self._locale_name is None:
            self._locale_name = app_commands.locale_str(
                self.name, **self.locale_strings_extras
            )
        if self._locale_description is None:
            self._locale_description = app_commands.locale_str(
                self.description, **self.locale_strings_extras
            )

        for param in self._params.values():
            self._translate_param(param)

    def _translate_param(self, param: CommandParameter) -> None:
        if param._rename is discord.utils.MISSING:
            param._rename = app_commands.locale_str(
                param.name, **self.locale_strings_extras
            )
        elif isinstance(param._rename, str):
            param._rename = app_commands.locale_str(
                param._rename, **self.locale_strings_extras
            )

        if isinstance(param.description, str):
            param.description = app_commands.locale_str(
                param.description, **self.locale_strings_extras
            )

        if param.choices:
            for choice in param.choices:
                if choice._locale_name is None:
                    choice._locale_name = app_commands.locale_str(
                        choice.name, **self.locale_strings_extras
                    )


class PikiAppGroup(app_commands.Group):
    """Application-command group with localization-aware command decorators.

    Parameters
    ----------
    name: :class:`str` | :class:`app_commands.locale_str`
        Group name shown in Discord.
    description: :class:`str` | :class:`app_commands.locale_str`
        Group description shown in Discord.
    parent: :class:`app_commands.Group` | :data:`None`
        Parent group, if this is a nested group.
    guild_ids: :class:`list`[:class:`int`] | :data:`None`
        Guilds where the group is registered by default.
    guild_only: :class:`bool`
        Restrict the group to guild interactions.
    allowed_contexts: :class:`app_commands.AppCommandContext` | :data:`None`
        Interaction contexts where the group can be used.
    allowed_installs: :class:`app_commands.AppInstallationType` | :data:`None`
        Installation contexts where the group can be installed.
    nsfw: :class:`bool`
        Restrict the group to age-restricted channels.
    auto_locale_strings: :class:`bool`
        Wrap eligible names and descriptions in :class:`app_commands.locale_str`.
    default_permissions: :class:`discord.Permissions` | :data:`None`
        Default permissions required to use the group.
    extras: :class:`dict` | :data:`discord.utils.MISSING`
        Application metadata that discord.py does not interpret.
    locale_strings_extras: :class:`dict` | :data:`discord.utils.MISSING`
        Extras attached to generated locale strings, such as catalog or domain selectors.
    """

    __discord_app_commands_group_children__: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        list[PikiAppCommand[Any, ..., Any] | PikiAppGroup]
    ] = []
    __discord_app_commands_skip_init_binding__: bool = False
    __discord_app_commands_group_name__: str = discord.utils.MISSING
    __discord_app_commands_group_description__: str = discord.utils.MISSING
    __discord_app_commands_group_locale_name__: app_commands.locale_str | None = None
    __discord_app_commands_group_locale_description__: (
        app_commands.locale_str | None
    ) = None
    __discord_app_commands_group_nsfw__: bool = False
    __discord_app_commands_guild_only__: bool = discord.utils.MISSING
    __discord_app_commands_contexts__: app_commands.AppCommandContext | None = (
        discord.utils.MISSING
    )
    __discord_app_commands_installation_types__: (
        app_commands.AppInstallationType | None
    ) = discord.utils.MISSING
    __discord_app_commands_default_permissions__: discord.Permissions | None = (
        discord.utils.MISSING
    )
    __discord_app_commands_has_module__: bool = False
    __discord_app_commands_error_handler__: (  # pyright: ignore[reportIncompatibleVariableOverride]
        Callable[
            [discord.Interaction[Bot], app_commands.AppCommandError],
            Coroutine[Any, Any, None],
        ]
        | None
    ) = None

    if TYPE_CHECKING:
        parent: PikiAppGroup | None  # pyright: ignore[reportIncompatibleVariableOverride]

        @property
        def root_parent(self) -> PikiAppGroup | None: ...

        @property
        def commands(self) -> list[PikiAppCommand[Any, ..., Any] | PikiAppGroup]: ...

        def walk_commands(
            self,
        ) -> Generator[PikiAppCommand[Any, ..., Any] | PikiAppGroup, None, None]: ...

        def add_command(
            self,
            command: PikiAppCommand[Any, ..., Any] | PikiAppGroup,
            /,
            *,
            override: bool = ...,
        ) -> None: ...

        def remove_command(
            self, name: str, /
        ) -> PikiAppCommand[Any, ..., Any] | PikiAppGroup | None: ...

        def get_command(
            self, name: str, /
        ) -> PikiAppCommand[Any, ..., Any] | PikiAppGroup | None: ...

    def __init_subclass__(
        cls,
        *,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        description: str | app_commands.locale_str = discord.utils.MISSING,
        guild_only: bool = discord.utils.MISSING,
        nsfw: bool = False,
        default_permissions: discord.Permissions | None = discord.utils.MISSING,
    ) -> None:
        super().__init_subclass__(
            name=name,
            description=description,
            guild_only=guild_only,
            nsfw=nsfw,
            default_permissions=default_permissions,
        )

    def __init__(
        self,
        *,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        description: str | app_commands.locale_str = discord.utils.MISSING,
        parent: PikiAppGroup | None = None,
        guild_ids: list[int] | None = None,
        guild_only: bool = discord.utils.MISSING,
        allowed_contexts: app_commands.AppCommandContext | None = discord.utils.MISSING,
        allowed_installs: app_commands.AppInstallationType
        | None = discord.utils.MISSING,
        nsfw: bool = discord.utils.MISSING,
        auto_locale_strings: bool = True,
        default_permissions: discord.Permissions | None = discord.utils.MISSING,
        extras: dict[Any, Any] = discord.utils.MISSING,
        locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
    ) -> None:
        self.locale_strings_extras: dict[Any, Any] = locale_strings_extras or {}
        super().__init__(
            name=name,
            description=description,
            parent=parent,
            guild_ids=guild_ids,
            guild_only=guild_only,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            nsfw=nsfw,
            auto_locale_strings=auto_locale_strings,
            default_permissions=default_permissions,
            extras=extras,
        )

    def _convert_to_locale_strings(self) -> None:
        if self._locale_name is None:
            self._locale_name = app_commands.locale_str(
                self.name, **self.locale_strings_extras
            )
        if self._locale_description is None:
            self._locale_description = app_commands.locale_str(
                self.description, **self.locale_strings_extras
            )

    def command[Cls: PikiAppCommand[Any, ..., Any]](
        self,
        *,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        description: str | app_commands.locale_str = discord.utils.MISSING,
        nsfw: bool = False,
        auto_locale_strings: bool = True,
        extras: dict[Any, Any] = discord.utils.MISSING,
        locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
        cls: type[Cls] = PikiAppCommand,
    ) -> Callable[[Callable[..., Any]], Cls]:
        """A decorator that creates an application command from a regular function under this tree.

        Parameters
        ----------
        name: :class:`str` | :class:`discord.app_commands.locale_str`
            The name of the application command. If not given, it defaults to a lower-case version of the callback
            name.
        description: :class:`str` | :class:`discord.app_commands.locale_str`
            The description of the application command. This shows up in the UI to describe the application command.
            If not given, it defaults to the first line of the docstring of the callback shortened to 100 characters.
        nsfw: :class:`bool`
            Whether this command is NSFW and should only work in NSFW channels. Defaults to ``False``.

            Due to a Discord limitation, this does not work on subcommands.
        guild: :class:`discord.abc.Snowflake` | :data:`None`
            The guild to add the command to. If not given or ``None`` then it becomes a global command
            instead.

            .. note::

                Due to a Discord limitation, this keyword argument cannot be used in conjunction with contexts (e.g.
                :func:`discord.app_commands.allowed_contexts`) or installation types (e.g. :func:`discord.app_commands.allowed_installs`).

        guilds: :class:`list`[:class:`discord.abc.Snowflake`]
            The list of guilds to add the command to. This cannot be mixed with the ``guild`` parameter. If no guilds are
            given at all then it becomes a global command instead.

            .. note::

                Due to a Discord limitation, this keyword argument cannot be used in conjunction with contexts (e.g.
                :func:`discord.app_commands.allowed_contexts`) or installation types (e.g. :func:`discord.app-commands.allowed_installs`).

        auto_locale_strings: :class:`bool`
            If this is set to ``True``, then all translatable strings will implicitly be wrapped into :class:`discord.app_commands.locale_str`
            rather than :class:`str`. This could avoid some repetition and be more ergonomic for certain defaults such as
            default command names, command descriptions, and parameter names.
        extras: :class:`dict`
            Extra metadata. The library will not touch any values or keys within this dictionary.
        locale_strings_extras: :class:`dict`
            Extra metadata passed to automatically converted locale_strs.
        cls: type[:class:`PikiAppCommand`]
            The class type to create the command with.
        """

        def decorator(func: Callable[..., Any]) -> Cls:
            if not inspect.iscoroutinefunction(func):
                raise TypeError("command function must be a coroutine function")

            s_cls: Callable[Concatenate[str, ...], Any] = (
                functools.partial(
                    app_commands.locale_str, **(locale_strings_extras or {})
                )
                if auto_locale_strings
                else lambda s, **attrs: s  # pyright: ignore[reportUnknownLambdaType]
            )

            if description is discord.utils.MISSING:
                if func.__doc__ is None:
                    desc = s_cls("...")
                else:
                    desc = s_cls(discord.utils._shorten(func.__doc__))
            else:
                desc = description

            if name is discord.utils.MISSING:
                nname = s_cls(func.__name__.lower())
            else:
                nname = name

            command = cls(
                name=nname,
                description=desc,
                callback=func,
                nsfw=nsfw,
                parent=None,
                auto_locale_strings=auto_locale_strings,
                extras=extras,
                locale_strings_extras=locale_strings_extras,
            )
            self.add_command(command)
            return command

        return decorator


class PikiContextMenu(app_commands.ContextMenu):
    """Application context-menu command with localization-aware names.

    Parameters
    ----------
    name: :class:`str` | :class:`app_commands.locale_str`
        Context-menu label shown in Discord.
    callback: :class:`Callable`
        Async callback. It receives an interaction and the selected user or message.
    type: :class:`discord.AppCommandType`
        Context-menu target type, inferred from the callback when omitted.
    nsfw: :class:`bool`
        Restrict the menu to age-restricted channels.
    guild_ids: :class:`list`[:class:`int`] | :data:`None`
        Guilds where the menu is registered by default.
    allowed_contexts: :class:`app_commands.AppCommandContext` | :data:`None`
        Interaction contexts where the menu can be used.
    allowed_installs: :class:`app_commands.AppInstallationType` | :data:`None`
        Installation contexts where the menu can be installed.
    auto_locale_strings: :class:`bool`
        Wrap the menu name in :class:`app_commands.locale_str` when enabled.
    extras: :class:`dict` | :data:`discord.utils.MISSING`
        Application metadata that discord.py does not interpret.
    locale_strings_extras: :class:`dict` | :data:`discord.utils.MISSING`
        Extras attached to the generated locale string, such as catalog or domain selectors.
    """

    def __init__(
        self,
        *,
        name: str | app_commands.locale_str,
        callback: (
            Callable[
                [discord.Interaction[Bot], discord.Member], Coroutine[Any, Any, Any]
            ]
            | Callable[
                [discord.Interaction[Bot], discord.User], Coroutine[Any, Any, Any]
            ]
            | Callable[
                [discord.Interaction[Bot], discord.Message], Coroutine[Any, Any, Any]
            ]
            | Callable[
                [discord.Interaction[Bot], discord.Member | discord.User],
                Coroutine[Any, Any, Any],
            ]
        ),
        type: discord.AppCommandType = discord.utils.MISSING,
        nsfw: bool = False,
        guild_ids: list[int] | None = None,
        allowed_contexts: app_commands.AppCommandContext | None = None,
        allowed_installs: app_commands.AppInstallationType | None = None,
        auto_locale_strings: bool = True,
        extras: dict[Any, Any] = discord.utils.MISSING,
        locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
    ) -> None:
        self.locale_strings_extras: dict[Any, Any] = locale_strings_extras or {}
        super().__init__(
            name=name,
            callback=callback,
            type=type,
            nsfw=nsfw,
            guild_ids=guild_ids,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            auto_locale_strings=auto_locale_strings,
            extras=extras,
        )

        if auto_locale_strings:
            if self._locale_name:
                self._locale_name.extras.update(self.locale_strings_extras)
            else:
                self._locale_name = app_commands.locale_str(
                    self.name, **self.locale_strings_extras
                )


class PikiCommandTree[C: Bot](app_commands.CommandTree[C]):
    """Application-command tree that creates PikiBot command classes by default.

    Parameters
    ----------
    client: :class:`PikiBot`
        Bot that owns and dispatches this tree.
    fallback_to_global: :class:`bool`
        Whether guild command lookups can fall back to global commands.
    allowed_contexts: :class:`app_commands.AppCommandContext`
        Default interaction contexts for commands in this tree.
    allowed_installs: :class:`app_commands.AppInstallationType`
        Default installation contexts for commands in this tree.

    Notes
    -----
    :meth:`command` and :meth:`context_menu` use :class:`PikiAppCommand` and
    :class:`PikiContextMenu` unless a different class is supplied.
    """

    if TYPE_CHECKING:

        def add_command(
            self,
            commands: PikiAppCommand[Any, ..., Any] | PikiContextMenu | PikiAppGroup,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            guilds: Sequence[discord.abc.Snowflake] = ...,
            override: bool = False,
        ) -> None: ...

        @overload
        def remove_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.message, discord.AppCommandType.user],
        ) -> PikiContextMenu | None: ...

        @overload
        def remove_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.chat_input] = ...,
        ) -> PikiAppCommand[Any, ..., Any] | PikiAppGroup | None: ...

        @overload
        def remove_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: discord.AppCommandType,
        ) -> PikiAppCommand[Any, ..., Any] | PikiAppGroup | PikiContextMenu | None: ...

        def remove_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = None,
            type: discord.AppCommandType = discord.AppCommandType.chat_input,
        ) -> Any: ...

        @overload
        def get_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.message, discord.AppCommandType.user],
        ) -> PikiContextMenu | None: ...

        @overload
        def get_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.chat_input] = ...,
        ) -> PikiAppCommand[Any, ..., Any] | PikiAppGroup | None: ...

        @overload
        def get_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: discord.AppCommandType,
        ) -> PikiAppCommand[Any, ..., Any] | PikiAppGroup | PikiContextMenu | None: ...

        def get_command(
            self,
            command: str,
            /,
            *,
            guild: discord.abc.Snowflake | None = None,
            type: discord.AppCommandType = discord.AppCommandType.chat_input,
        ) -> Any: ...

        @overload
        def get_commands(  # pyright: ignore[reportOverlappingOverload]
            self,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.message, discord.AppCommandType.user],
        ) -> list[PikiContextMenu]: ...

        @overload
        def get_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.chat_input] = ...,
        ) -> list[PikiAppCommand[Any, ..., Any] | PikiAppGroup]: ...

        @overload
        def get_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: discord.AppCommandType | None = ...,
        ) -> list[PikiAppCommand[Any, ..., Any] | PikiAppGroup | PikiContextMenu]: ...

        def get_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = None,
            type: discord.AppCommandType | None = None,
        ) -> Any: ...

        @overload
        def walk_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.message, discord.AppCommandType.user],
        ) -> Generator[PikiContextMenu]: ...

        @overload
        def walk_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: Literal[discord.AppCommandType.chat_input] = ...,
        ) -> Generator[PikiAppCommand[Any, ..., Any] | PikiAppGroup]: ...

        @overload
        def walk_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = ...,
            type: discord.AppCommandType,
        ) -> Generator[
            PikiAppCommand[Any, ..., Any] | PikiAppGroup | PikiContextMenu
        ]: ...

        def walk_commands(
            self,
            *,
            guild: discord.abc.Snowflake | None = None,
            type: discord.AppCommandType = discord.AppCommandType.chat_input,
        ) -> Any: ...

    def __init__(
        self,
        client: C,
        *,
        fallback_to_global: bool = True,
        allowed_contexts: app_commands.AppCommandContext = discord.utils.MISSING,
        allowed_installs: app_commands.AppInstallationType = discord.utils.MISSING,
    ) -> None:
        super().__init__(
            client,
            fallback_to_global=fallback_to_global,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
        )

    def command[Cls: PikiAppCommand[Any, ..., Any]](
        self,
        *,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        description: str | app_commands.locale_str = discord.utils.MISSING,
        nsfw: bool = False,
        guild: discord.abc.Snowflake | None = discord.utils.MISSING,
        guilds: Sequence[discord.abc.Snowflake] = discord.utils.MISSING,
        auto_locale_strings: bool = True,
        extras: dict[Any, Any] = discord.utils.MISSING,
        locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
        cls: type[Cls] = PikiAppCommand,
    ) -> Callable[[Callable[..., Any]], Cls]:
        """A decorator that creates an application command from a regular function under this tree.

        Parameters
        ----------
        name: :class:`str` | :class:`discord.app_commands.locale_str`
            The name of the application command. If not given, it defaults to a lower-case version of the callback
            name. If the bot has localization enabled, then this string is automatically wrapped around a locale_str
            instance independently of ``auto_locale_strings``.
        description: :class:`str` | :class:`discord.app_commands.locale_str`
            The description of the application command. This shows up in the UI to describe the application command.
            If not given, it defaults to the first line of the docstring of the callback shortened to 100 characters.
            If the bot has localization enabled, then this string is automatically wrapped around a locale_str
            instance independently of ``auto_locale_strings``.
        nsfw: :class:`bool`
            Whether this command is NSFW and should only work in NSFW channels. Defaults to ``False``.

            Due to a Discord limitation, this does not work on subcommands.
        guild: :class:`discord.abc.Snowflake` | :data:`None`
            The guild to add the command to. If not given or ``None`` then it becomes a global command
            instead.

            .. note::

                Due to a Discord limitation, this keyword argument cannot be used in conjunction with contexts (e.g.
                :func:`discord.app_commands.allowed_contexts`) or installation types (e.g. :func:`discord.app_commands.allowed_installs`).

        guilds: :class:`list`[:class:`discord.abc.Snowflake`]
            The list of guilds to add the command to. This cannot be mixed with the ``guild`` parameter. If no guilds are
            given at all then it becomes a global command instead.

            .. note::

                Due to a Discord limitation, this keyword argument cannot be used in conjunction with contexts (e.g.
                :func:`discord.app_commands.allowed_contexts`) or installation types (e.g. :func:`discord.app-commands.allowed_installs`).

        auto_locale_strings: :class:`bool`
            If this is set to ``True``, then all translatable strings will implicitly be wrapped into :class:`discord.app_commands.locale_str`
            rather than :class:`str`. This could avoid some repetition and be more ergonomic for certain defaults such as
            default command names, command descriptions, and parameter names. This will be always treated as ``True`` if the bot
            has localization enabled.
        extras: :class:`dict`
            Extra metadata. The library will not touch any values or keys within this dictionary.
        locale_strings_extras: :class:`dict`
            Extra metadata passed to automatically converted locale_strs.
        cls: type[:class:`PikiAppCommand`]
            The class type to create the command with.
        """

        def decorator(func: Callable[..., Any]) -> Cls:
            if not inspect.iscoroutinefunction(func):
                raise TypeError("command function must be a coroutine function")

            locale_strs = auto_locale_strings

            if self.client.translator:
                locale_strs = True

            s_cls: Callable[Concatenate[str, ...], Any] = (
                functools.partial(
                    app_commands.locale_str, **(locale_strings_extras or {})
                )
                if locale_strs
                else lambda s, **attrs: s  # pyright: ignore[reportUnknownLambdaType]
            )

            if description is discord.utils.MISSING:
                if func.__doc__ is None:
                    desc = s_cls("...")
                else:
                    desc = s_cls(discord.utils._shorten(func.__doc__))
            else:
                desc = description

            if name is discord.utils.MISSING:
                nname = s_cls(func.__name__.lower())
            else:
                nname = name

            command = cls(
                name=nname,
                description=desc,
                callback=func,
                nsfw=nsfw,
                parent=None,
                auto_locale_strings=auto_locale_strings,
                extras=extras,
                locale_strings_extras=locale_strings_extras,
            )
            self.add_command(command, guild=guild, guilds=guilds)
            return command

        return decorator

    def context_menu[Cls: PikiContextMenu](
        self,
        *,
        name: str | app_commands.locale_str = discord.utils.MISSING,
        nsfw: bool = False,
        guild: discord.abc.Snowflake | None = discord.utils.MISSING,
        guilds: Sequence[discord.abc.Snowflake] = discord.utils.MISSING,
        auto_locale_strings: bool = True,
        extras: dict[Any, Any] = discord.utils.MISSING,
        locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
        cls: type[Cls] = PikiContextMenu,
    ) -> Callable[[Callable[..., Any]], Cls]:
        """A decorator that creates an application command context menu from a regular function directly under this tree.

        This function must have a signature of :class:`~discord.Interaction` as its first parameter
        and taking either a :class:`~discord.Member`, :class:`~discord.User`, or :class:`~discord.Message`,
        or a :obj:`typing.Union` of ``Member`` and ``User`` as its second parameter.

        Examples
        --------

        .. code-block:: python3

            @tree.context_menu()
            async def react(interaction: discord.Interaction, message: discord.Message):
                await interaction.response.send_message('Very cool message!', ephemeral=True)

            @tree.context_menu()
            async def ban(interaction: discord.Interaction, user: discord.Member):
                await interaction.response.send_message(f'Should I actually ban {user}...', ephemeral=True)

        Parameters
        ----------
        name: :class:`str` | :class:`discord.app_commands.locale_str`
            The name of the application command. If not given, it defaults to the callback
            name. If the bot has localization enabled, then this string is automatically wrapped around a locale_str
            instance independently of ``auto_locale_strings``.
        nsfw: :class:`bool`
            Whether the command is NSFW and should only work in NSFW channels. Defaults to ``False``.

            Due to a Discord limitation, this does not work on subcommands.
        guild: :class:`discord.abc.Snowflake` | :data:`None`
            The guild to add the command to. If not given or ``None`` then it
            becomes a global command instead.

            .. note ::

                Due to a Discord limitation, this keyword argument cannot be used in conjunction with
                contexts (e.g. :func:`discord.app_commands.allowed_contexts`) or installation types
                (e.g. :func:`discord.app_commands.allowed_installs`).

        guilds: :class:`list`[:class:`discord.abc.Snowflake`]
            The list of guilds to add the command to. This cannot be mixed
            with the ``guild`` parameter. If no guilds are given at all
            then it becomes a global command instead.

            .. note ::

                Due to a Discord limitation, this keyword argument cannot be used in conjunction with
                contexts (e.g. :func:`discord.app_commands.allowed_contexts`) or installation types
                (e.g. :func:`discord.app_commands.allowed_installs`).

        auto_locale_strings: :class:`bool`
            If this is set to ``True``, then all translatable strings will implicitly
            be wrapped into :class:`locale_str` rather than :class:`str`. This could
            avoid some repetition and be more ergonomic for certain defaults such
            as default command names, command descriptions, and parameter names.
            Defaults to ``True``.
        extras: :class:`dict`
            A dictionary that can be used to store extraneous data.
            The library will not touch any values or keys within this dictionary.
        locale_strings_extras: :class:`dict`
            Extra metadata passed to automatically converted locale_strs.
        cls: type[:class:`PikiContextMenu`]
            The class type to create the context menu with.
        """

        def decorator(func: Callable[..., Any]) -> Cls:
            if not inspect.iscoroutinefunction(func):
                raise TypeError("context menu function must be a coroutine function")

            localize = auto_locale_strings
            if self.client.translator:
                localize = True

            s_cls: Callable[Concatenate[str, ...], Any] = (
                functools.partial(
                    app_commands.locale_str, **(locale_strings_extras or {})
                )
                if localize
                else lambda s, **attrs: s  # pyright: ignore[reportUnknownLambdaType]
            )

            if name is not discord.utils.MISSING:
                if isinstance(name, app_commands.locale_str):
                    name.extras.update(locale_strings_extras or {})
                    actual = name
                else:
                    actual = s_cls(name)
            else:
                actual = s_cls(func.__name__.title())

            cm = cls(
                name=actual,
                nsfw=nsfw,
                callback=func,
                auto_locale_strings=auto_locale_strings,
                extras=extras,
                locale_strings_extras=locale_strings_extras,
            )
            self.add_command(cm, guild=guild, guilds=guilds)
            return cm

        return decorator


def app_group[Cls: PikiAppGroup](
    name: str | app_commands.locale_str,
    *,
    description: str | app_commands.locale_str = discord.utils.MISSING,
    parent: PikiAppGroup | None = None,
    guild_ids: list[int] | None = None,
    guild_only: bool = discord.utils.MISSING,
    allowed_contexts: app_commands.AppCommandContext | None = discord.utils.MISSING,
    allowed_installs: app_commands.AppInstallationType | None = discord.utils.MISSING,
    nsfw: bool = discord.utils.MISSING,
    auto_locale_strings: bool = True,
    default_permissions: discord.Permissions | None = discord.utils.MISSING,
    extras: dict[Any, Any] = discord.utils.MISSING,
    locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
    cls: type[Cls] = PikiAppGroup,
) -> Cls:
    """A function to create an application command group."""
    return cls(
        name=name,
        description=description,
        parent=parent,
        guild_ids=guild_ids,
        guild_only=guild_only,
        allowed_contexts=allowed_contexts,
        allowed_installs=allowed_installs,
        nsfw=nsfw,
        auto_locale_strings=auto_locale_strings,
        default_permissions=default_permissions,
        extras=extras,
        locale_strings_extras=locale_strings_extras,
    )


def app_command[Cls: PikiAppCommand[Any, ..., Any]](
    *,
    name: str | app_commands.locale_str = discord.utils.MISSING,
    description: str | app_commands.locale_str = discord.utils.MISSING,
    nsfw: bool = False,
    auto_locale_strings: bool = True,
    extras: dict[Any, Any] = discord.utils.MISSING,
    locale_strings_extras: dict[Any, Any] = discord.utils.MISSING,
    cls: type[Cls] = PikiAppCommand,
) -> Callable[[Callable[..., Any]], Cls]:
    """A decorator to create an application command."""

    def decorator(func: Callable[..., Any]) -> Cls:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("command function must be a coroutine function")

        s_cls: Callable[Concatenate[str, ...], Any] = (
            functools.partial(app_commands.locale_str, **(locale_strings_extras or {}))
            if auto_locale_strings
            else lambda s, **attrs: s  # pyright: ignore[reportUnknownLambdaType]
        )

        if name is not discord.utils.MISSING:
            if isinstance(name, app_commands.locale_str):
                name.extras.update(locale_strings_extras or {})
                actual = name
            else:
                actual = s_cls(name)
        else:
            actual = s_cls(func.__name__.title())

        if description is not discord.utils.MISSING:
            if isinstance(description, app_commands.locale_str):
                description.extras.update(locale_strings_extras or {})
                actual_desc = description
            else:
                actual_desc = s_cls(description)
        else:
            if func.__doc__ is None:
                actual_desc = s_cls("...")
            else:
                actual_desc = s_cls(discord.utils._shorten(func.__doc__))

        cmd = cls(
            name=actual,
            description=actual_desc,
            nsfw=nsfw,
            callback=func,
            auto_locale_strings=auto_locale_strings,
            extras=extras,
            locale_strings_extras=locale_strings_extras,
        )
        return cmd

    return decorator
