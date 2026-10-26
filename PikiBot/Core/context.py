"""
PikiBot Noncommercial License 1.1.0

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

import logging
from typing import Any, overload

import discord
from discord import app_commands
from discord.ext import commands

from .bot import PikiBot as Bot
from .database import Database

_log = logging.getLogger(__name__)

__all__ = ("Context",)


class Context(commands.Context[Bot]):
    """Command invocation context with PikiBot-specific helpers.

    Attributes
    ----------
    database: :class:`type`[:class:`Database`]
        Database facade belonging to the current bot.

    Notes
    -----
    :meth:`translate` uses the bot's translator and accepts a catalog locale and
    optional gettext domain.
    """

    @property
    def database(self) -> type[Database]:
        """Returns the database instance associated with the bot."""
        return self.bot.database

    @overload
    async def translate(
        self, object: discord.Embed, target: str, *, domain: str | None = None
    ) -> discord.Embed: ...

    @overload
    async def translate(
        self,
        object: str | app_commands.locale_str,
        target: str,
        *,
        domain: str | None = None,
    ) -> str: ...

    @overload
    async def translate(
        self,
        object: discord.ui.Item[Any],
        target: str,
        *,
        domain: str | None = None,
    ) -> discord.ui.Item[Any]: ...

    @overload
    async def translate(
        self,
        object: discord.ui.View,
        target: str,
        *,
        domain: str | None = None,
    ) -> discord.ui.View: ...

    @overload
    async def translate(
        self,
        object: discord.ui.LayoutView,
        target: str,
        *,
        domain: str | None = None,
    ) -> discord.ui.LayoutView: ...

    async def translate(
        self, object: Any, target: str, *, domain: str | None = None
    ) -> Any:
        """Translate a text to a target language.

        This is done by using the I18N loaded translations from the bot and gettext.

        Parameters
        ----------
        object: Any
            The object to translate. This MUST be at its final state, otherwise
            changes applied AFTER this call will not be translated.
        target: :class:`str`
            The target language for the translation.
        domain: :class:`str` | :data:`None`
            The catalog domain. If omitted, the translator's default domain is used.

        Returns
        -------
        Any
            The translated object.
        """
        if not self.bot.translator:
            _log.warning("Translator is not available")
            return object
        return await self.bot.translator.translate_object(object, target, domain=domain)
