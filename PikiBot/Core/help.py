"""
PikiBot NonCommercial License 1.0.0

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, override

import discord
from discord.ext import commands

from .command import LocalizableMixin

if TYPE_CHECKING:
    from discord.ext.commands.help import _HelpCommandOptions
    from typing_extensions import Unpack

    from .context import Context


class PikiHelpCommand(commands.HelpCommand):
    """Base help command that resolves and displays localized command metadata.

    Parameters
    ----------
    **options: :data:`Any`
        Options forwarded to :class:`commands.HelpCommand`.

    Attributes
    ----------
    context: :class:`Context`
        Context of the current help invocation, set by discord.py.

    Notes
    -----
    Localized names and help text are cached before formatting. Subclasses can
    override discord.py's synchronous formatting methods to customize the output.
    """

    if TYPE_CHECKING:
        context: Context

    def __init__(self, **options: Unpack[_HelpCommandOptions]) -> None:
        super().__init__(**options)

    @override
    async def command_callback(
        self, ctx: Context, /, *, command: str | None = None
    ) -> None:
        # Help formatters are synchronous; prepare localized values before they run.
        for item in ctx.bot.walk_commands():
            if isinstance(item, LocalizableMixin):
                await item.cache_localized_help(ctx)

        await self.prepare_help_command(ctx, command)

        bot = ctx.bot
        if command is None:
            return await self.send_bot_help(self.get_bot_mapping())

        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)

        keys = command.split()
        cmd = await self.get_localized_command(ctx, keys[0])
        if cmd is None:
            error = await discord.utils.maybe_coroutine(
                self.command_not_found, self.remove_mentions(keys[0])
            )
            return await self.send_error_message(error)

        for key in keys[1:]:
            if not isinstance(cmd, commands.Group):
                found = None
            else:
                found = await self.get_localized_command(ctx, key, parent=cmd)

            if found is None:
                error = await discord.utils.maybe_coroutine(
                    self.subcommand_not_found, cmd, self.remove_mentions(key)
                )
                return await self.send_error_message(error)
            cmd = found

        if isinstance(cmd, commands.Group):
            return await self.send_group_help(cmd)
        return await self.send_command_help(cmd)

    def _localized_name(self, command: LocalizableMixin, locale: str) -> str:
        return command.translated_names.get(locale, command.name)

    def _command_path(self, command: LocalizableMixin) -> tuple[str, str]:
        locale = command.get_user_locale(self.context)
        parents: list[LocalizableMixin] = []
        parent = command.parent
        while parent is not None:
            parents.append(parent)
            parent = parent.parent

        path_parts: list[str] = []
        for parent in reversed(parents):
            parent_locale = parent.get_user_locale(self.context)
            part = self._localized_name(parent, parent_locale)
            if parent.signature and not parent.invoke_without_command:
                part = f"{part} {parent.signature}"
            path_parts.append(part)

        return " ".join(path_parts), self._localized_name(command, locale)

    def _localized_qualified_name(self, command: LocalizableMixin) -> str:
        locale = command.get_user_locale(self.context)
        parents: list[LocalizableMixin] = []
        parent = command.parent
        while parent is not None:
            parents.append(parent)
            parent = parent.parent

        names = [
            self._localized_name(item, item.get_user_locale(self.context))
            for item in reversed(parents)
        ]
        names.append(self._localized_name(command, locale))
        return " ".join(names)

    def _format_localized_signature(
        self,
        command: LocalizableMixin,
        *,
        include_aliases: bool,
        include_parameters: bool = True,
    ) -> str:
        parent_signature, name = self._command_path(command)
        aliases = tuple(command.original_aliases) if include_aliases else ()
        display_name = f"[{name}|{'|'.join(aliases)}]" if aliases else name
        path = " ".join(part for part in (parent_signature, display_name) if part)
        if include_parameters:
            path = f"{path} {command.signature}".rstrip()
        return f"{self.context.clean_prefix}{path}"

    @override
    def get_command_signature(self, command: commands.Command[Any, ..., Any], /) -> str:
        if not isinstance(command, LocalizableMixin):
            return super().get_command_signature(command)

        return self._format_localized_signature(command, include_aliases=True)

    async def get_localized_command(
        self,
        ctx: Context,
        command_name: str,
        /,
        *,
        parent: commands.Group[Any, ..., Any] | None = None,
    ) -> commands.Command[Any, ..., Any] | None:
        """Resolve source names first, then localized names and aliases."""
        mapping = parent.all_commands if parent is not None else ctx.bot.all_commands
        command = mapping.get(command_name)
        if command is not None:
            return command

        candidates = parent.commands if parent is not None else ctx.bot.commands
        case_insensitive = getattr(
            parent if parent is not None else ctx.bot,
            "case_insensitive",
            False,
        )
        normalized_name = command_name.casefold() if case_insensitive else command_name

        for candidate in candidates:
            if not isinstance(candidate, LocalizableMixin) or not candidate.localize:
                continue
            names = await candidate.get_localized_names(ctx)
            if any(
                (name.casefold() if case_insensitive else name) == normalized_name
                for name in names
            ):
                return candidate
        return None


class PikiDefaultHelpCommand(commands.DefaultHelpCommand, PikiHelpCommand):
    """Default-style help output with localized command and parameter descriptions.

    Parameters
    ----------
    **options: :data:`Any`
        Options forwarded to :class:`commands.DefaultHelpCommand`, such as ``width``,
        ``indent``, ``show_parameter_descriptions``, and paginator settings.
    """

    @override
    def get_command_signature(self, command: commands.Command[Any, ..., Any], /) -> str:
        if not isinstance(command, LocalizableMixin):
            return super().get_command_signature(command)

        parent_signature, name = self._command_path(command)
        aliases = tuple(
            alias for alias in command.original_aliases if alias != command.name
        )
        display_name = f"[{name}|{'|'.join(aliases)}]" if aliases else name
        path = " ".join(part for part in (parent_signature, display_name) if part)
        if not self.show_parameter_descriptions:
            path = f"{path} {command.signature}".rstrip()
        return f"{self.context.clean_prefix}{path}"

    @override
    async def command_callback(
        self, ctx: Context, /, *, command: str | None = None
    ) -> None:
        await super(commands.DefaultHelpCommand, self).command_callback(
            ctx, command=command
        )

    @override
    def add_command_formatting(
        self, command: commands.Command[Any, ..., Any], /
    ) -> None:
        if not isinstance(command, LocalizableMixin):
            return super().add_command_formatting(command)

        locale = command.get_user_locale(self.context)
        description = command.translated_descriptions.get(locale, command.description)
        help_text = command.translated_help.get(locale, command.help)

        if description:
            self.paginator.add_line(description, empty=True)

        self.paginator.add_line(self.get_command_signature(command), empty=True)

        if help_text:
            try:
                self.paginator.add_line(help_text, empty=True)
            except RuntimeError:
                for line in help_text.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

        if self.show_parameter_descriptions:
            self.add_command_arguments(command)

    @override
    def add_indented_commands(
        self,
        commands: Sequence[commands.Command[Any, ..., Any]],
        /,
        *,
        heading: str,
        max_size: int | None = None,
    ) -> None:
        if not commands:
            return

        self.paginator.add_line(heading)
        localized: list[tuple[commands.Command[Any, ..., Any], str, str]] = []
        for command in commands:
            if isinstance(command, LocalizableMixin):
                locale = command.get_user_locale(self.context)
                name = command.translated_names.get(locale, command.name)
                short_doc = command.translated_short_docs.get(locale, command.short_doc)
            else:
                name = command.name
                short_doc = command.short_doc
            localized.append((command, name, short_doc))

        localized_max = max(
            (discord.utils._string_width(name) for _, name, _ in localized),
            default=0,
        )
        max_size = max(max_size or 0, localized_max)

        get_width = discord.utils._string_width
        for _, name, short_doc in localized:
            width = max_size - (get_width(name) - len(name))
            entry = f"{self.indent * ' '}{name:<{width}} {short_doc}"
            self.paginator.add_line(self.shorten_text(entry))

    @override
    def add_command_arguments(
        self, command: commands.Command[Any, ..., Any], /
    ) -> None:
        if not isinstance(command, LocalizableMixin):
            return super().add_command_arguments(command)

        arguments = command.clean_params
        if not arguments:
            return

        self.paginator.add_line(self.arguments_heading)
        max_size = self.get_max_size(list(arguments.values()))  # type: ignore[arg-type]
        locale = (
            command.get_user_locale(self.context)
            if isinstance(command, LocalizableMixin)
            else None
        )
        descriptions = (
            command._translated_parameter_descriptions.get(locale, {})
            if locale is not None
            else {}
        )

        get_width = discord.utils._string_width
        for key, argument in arguments.items():
            name = argument.displayed_name or argument.name
            description = descriptions.get(key, argument.description)
            width = max_size - (get_width(name) - len(name))
            entry = f"{self.indent * ' '}{name:<{width}} {description or self.default_argument_description}"
            entry = self.shorten_text(entry)
            if argument.displayed_default is not None:
                entry += f" (default: {argument.displayed_default})"
            self.paginator.add_line(entry)


class PikiMinimalHelpCommand(commands.MinimalHelpCommand, PikiHelpCommand):
    """Compact help output with localized command names and short descriptions.

    Parameters
    ----------
    **options: :data:`Any`
        Options forwarded to :class:`commands.MinimalHelpCommand`, such as headings,
        sorting, and destination settings.

    Notes
    -----
    Use this with ``PikiBot(help_command=PikiMinimalHelpCommand())``. Parameter
    descriptions are not shown by discord.py's minimal formatter.
    """

    @override
    def get_command_signature(self, command: commands.Command[Any, ..., Any], /) -> str:
        if not isinstance(command, LocalizableMixin):
            return super().get_command_signature(command)
        signature = self._localized_qualified_name(command)
        if command.signature:
            signature = f"{signature} {command.signature}"
        return f"{self.context.clean_prefix}{signature}"

    @override
    async def command_callback(
        self, ctx: Context, /, *, command: str | None = None
    ) -> None:
        await super(commands.MinimalHelpCommand, self).command_callback(
            ctx, command=command
        )

    @override
    def add_bot_commands_formatting(
        self,
        commands: Sequence[commands.Command[Any, ..., Any]],
        heading: str,
        /,
    ) -> None:
        if not commands:
            return

        names: list[str] = []
        for command in commands:
            if isinstance(command, LocalizableMixin):
                locale = command.get_user_locale(self.context)
                names.append(command.translated_names.get(locale, command.name))
            else:
                names.append(command.name)

        self.paginator.add_line(f"__**{heading}**__")
        self.paginator.add_line("\u2002".join(names))

    @override
    def add_subcommand_formatting(
        self, command: commands.Command[Any, ..., Any], /
    ) -> None:
        if isinstance(command, LocalizableMixin):
            locale = command.get_user_locale(self.context)
            qualified_name = self._localized_qualified_name(command)
            short_doc = command.translated_short_docs.get(locale, command.short_doc)
        else:
            qualified_name = command.qualified_name
            short_doc = command.short_doc

        fmt = "{0}{1} \N{EN DASH} {2}" if short_doc else "{0}{1}"
        self.paginator.add_line(
            fmt.format(self.context.clean_prefix, qualified_name, short_doc)
        )

    @override
    def add_aliases_formatting(self, aliases: Sequence[str], /) -> None:
        if aliases:
            self.paginator.add_line(
                f"**{self.aliases_heading}** {', '.join(aliases)}", empty=True
            )

    @override
    def add_command_formatting(
        self, command: commands.Command[Any, ..., Any], /
    ) -> None:
        if not isinstance(command, LocalizableMixin):
            return super().add_command_formatting(command)

        locale = command.get_user_locale(self.context)
        description = command.translated_descriptions.get(locale, command.description)
        help_text = command.translated_help.get(locale, command.help)

        if description:
            self.paginator.add_line(description, empty=True)

        self.paginator.add_line(self.get_command_signature(command))
        aliases = command.original_aliases
        if aliases:
            self.add_aliases_formatting(aliases)
        else:
            self.paginator.add_line()

        if help_text:
            try:
                self.paginator.add_line(help_text, empty=True)
            except RuntimeError:
                for line in help_text.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()
