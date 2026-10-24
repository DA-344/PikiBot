"""
PikiBot NonCommercial License 1.0.0

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from .command import LocalizableMixin

if TYPE_CHECKING:
    from .context import Context

__all__ = ("PikiCog", "PikiCogMeta")


class PikiCogMeta(commands.CogMeta):
    """Cog metaclass that stores localization options without changing CogMeta options."""

    def __new__(
        cls,
        *args: Any,
        localize: bool = discord.utils.MISSING,
        user_locale: Callable[[Context], str] | None = discord.utils.MISSING,
        localization_domain: str | None = discord.utils.MISSING,
        **kwargs: Any,
    ) -> PikiCogMeta:
        attrs = args[2]
        if localize is not discord.utils.MISSING:
            attrs["__piki_localize__"] = localize
        if user_locale is not discord.utils.MISSING:
            attrs["__piki_user_locale__"] = user_locale
        if localization_domain is not discord.utils.MISSING:
            attrs["__piki_localization_domain__"] = localization_domain
        return super().__new__(cls, *args, **kwargs)  # pyright: ignore[reportReturnType]


class PikiCog(commands.Cog, LocalizableMixin, metaclass=PikiCogMeta):
    """A discord.py Cog whose name and description can be localized in help output.

    Parameters
    ----------
    localize: :class:`bool`
        Whether to translate this Cog's name and description. Defaults to ``False``;
        ``PikiBot``'s global localization setting takes precedence when configured.
    user_locale: :class:`Callable`[[:class:`~.Context`], :class:`str`] | :data:`None`
        Optional callback that chooses the catalog for a help invocation. Otherwise,
        the interaction locale, guild locale, or translator default is used.
    localization_domain: :class:`str` | :data:`None`
        Translation catalog domain for the Cog metadata. If omitted, the translator's
        default domain is used.

    Notes
    -----
    Set these options in the class declaration alongside discord.py Cog options::

        class Music(PikiCog, name="Music", localize=True, localization_domain="music"):
            \"\"\"Music commands.\"\"\"

    Cog constructors do not need to call ``super().__init__``. Translations are cached
    on the Cog instance when a help command prepares its output.
    """

    __piki_localize__: bool = False
    __piki_user_locale__: Callable[[Context], str] | None = None
    __piki_localization_domain__: str | None = None

    @property
    def localize(self) -> bool:
        """Whether this Cog's help metadata should be localized."""
        global_localize = LocalizableMixin.GLOBAL_LOCALIZE
        if global_localize is not None:
            return global_localize
        return type(self).__piki_localize__

    def get_user_locale(self, context: Context, /) -> str:
        """Return the validated locale selected for this help invocation."""
        callback = type(self).__piki_user_locale__
        if callback is not None:
            locale = callback(context)
        elif context.interaction is not None:
            locale = context.interaction.locale.value
        elif context.guild is not None:
            locale = context.guild.preferred_locale.value
        else:
            locale = getattr(context.bot.translator, "default_locale", "en")

        validator = LocalizableMixin.GLOBAL_CATALOG_VALIDATOR
        return validator(locale) if validator is not None else locale

    def get_localization_domain(self) -> str | None:
        """Return this Cog's translation domain, if one was configured."""
        return type(self).__piki_localization_domain__

    @property
    def translated_names(self) -> dict[str, str]:
        """Localized Cog names keyed by catalog locale."""
        return self.__dict__.setdefault("_piki_translated_names", {})  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def translated_descriptions(self) -> dict[str, str]:
        """Localized Cog descriptions keyed by catalog locale."""
        return self.__dict__.setdefault("_piki_translated_descriptions", {})  # pyright: ignore[reportAttributeAccessIssue]

    async def cache_localized_help(self, context: Context, /) -> None:
        """Cache this Cog's translated name and description for the context locale."""
        if not self.localize:
            return

        locale = self.get_user_locale(context)
        if locale in self.translated_names and locale in self.translated_descriptions:
            return

        domain = self.get_localization_domain()
        self.translated_names[locale] = await context.translate(
            self.qualified_name, target=locale, domain=domain
        )
        self.translated_descriptions[locale] = await context.translate(
            self.description, target=locale, domain=domain
        )

    def clear_localization_cache(self) -> None:
        """Clear cached Cog names and descriptions for every locale."""
        self.translated_names.clear()
        self.translated_descriptions.clear()
