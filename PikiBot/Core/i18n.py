"""
PikiBot Noncommercial License 1.1.0

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

import copy
import gettext
import logging
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, overload

import discord
from discord import app_commands

from .command import LocalizableMixin

_log = logging.getLogger(__name__)

__all__ = ("Translator",)


class Translator:
    """Loads gettext catalogs and translates strings and supported Discord UI objects.

    Parameters
    ----------
    path: :class:`pathlib.Path`
        Root directory of compiled catalogs, arranged as
        ``<path>/<locale>/LC_MESSAGES/<domain>.mo``.
    default_locale: :class:`str`
        Locale used as the fallback for untranslated messages.
    default_domain: :class:`str`
        Domain used when a translation call does not specify one. The ``.mo`` suffix is optional.
    available_locales: :class:`Sequence`[:class:`str`] | :data:`None`
        Locales to load. If omitted, locales are discovered under ``path``.
    auto_load_catalogs: :class:`bool`
        Load discovered locale/domain catalogs during initialization.

    Attributes
    ----------
    available_locales: :class:`tuple`[:class:`str`, ...]
        Locales configured for this translator.
    available_domains: :class:`tuple`[:class:`str`, ...]
        Domains found in the configured compiled catalogs.

    Notes
    -----
    Catalogs are cached by locale and domain. Non-default locales fall back to
    ``default_locale`` when a message is missing.
    """

    def __init__(
        self,
        *,
        path: Path,
        default_locale: str,
        default_domain: str = "messages",
        available_locales: Sequence[str] | None = None,
        auto_load_catalogs: bool = True,
    ) -> None:
        self.path: Path = path
        self.default_locale: str = default_locale
        self.default_domain: str = default_domain.removesuffix(".mo")
        self.available_locales: tuple[str, ...]

        if available_locales is None:
            self.available_locales = tuple(
                directory.name
                for directory in path.iterdir()
                if directory.is_dir() and (directory / "LC_MESSAGES").is_dir()
            )
        else:
            self.available_locales = tuple(available_locales)

        self._locale_catalog: dict[str, tuple[str, ...]] = {
            locale: tuple(
                catalog.stem
                for catalog in (self.path / locale / "LC_MESSAGES").glob("*.mo")
            )
            for locale in self.available_locales
        }

        # unlike _locale_catalog, this registers all catalogs that were at least
        # seen once in any locale.
        self.available_domains: tuple[str, ...] = tuple(
            sorted(
                {
                    domain
                    for domains in self._locale_catalog.values()
                    for domain in domains
                }
            )
        )

        if auto_load_catalogs:
            self.load_catalogs()

    def get_locale_domains(self, locale: str) -> tuple[str, ...]:
        """Return all available domains for the specified locale."""
        return self._locale_catalog.get(locale, ())

    def load_catalogs(self) -> None:
        """Load every available locale/domain."""
        _log.debug("Loading all catalogs")
        for locale in self.available_locales:
            _log.debug("Loading locale %s", locale)
            for domain in self.get_locale_domains(locale):
                _log.debug("Loading locale %s domain %s", locale, domain)
                self.load_catalog(locale, domain)

    @lru_cache(maxsize=None)
    def load_catalog(
        self, locale: str, domain: str
    ) -> gettext.GNUTranslations | gettext.NullTranslations:
        """Load the translation catalog for the specified locale.

        Parameters
        ----------
        locale: :class:`str`
            The locale for which to load the catalog.
        domain: :class:`str`
            The domain (messages file) for which to load the catalog.

        Returns
        -------
        :class:`gettext.GNUTranslations` | :class:`gettext.NullTranslations`
            The loaded translation catalog for the specified locale and domain.
        """
        domain = domain.removesuffix(".mo")
        catalog = gettext.translation(
            domain=domain,
            localedir=str(self.path),
            languages=[locale],
            fallback=True,
        )
        if locale != self.default_locale:
            catalog.add_fallback(self.load_catalog(self.default_locale, domain))
        return catalog

    def default_catalog(
        self, domain: str
    ) -> gettext.GNUTranslations | gettext.NullTranslations:
        """Alias for :meth:`load_catalog` with ``locale`` as :attr:`default_locale`."""
        return self.load_catalog(self.default_locale, domain)

    async def translate(
        self, message: str, locale: str, *, domain: str | None = None
    ) -> str:
        """Translate ``message`` into ``locale`` using the specified domain, or the default
        Translator one.

        Parameters
        ----------
        message: :class:`str`
            The message to translate.
        locale: :class:`str`
            The target locale for the translation.
        domain: :class:`str` | :data:`None`
            The domain to use for the translation. If ``None``, the default domain is used.

        Returns
        -------
        :class:`str`
            The translated message, or the original message if no translation is found.
        """
        domain = domain or self.default_domain
        catalog = self.load_catalog(locale, domain)
        # we do not need to call default_catalog as it is used as a fallback in load_catalog
        return catalog.gettext(message)

    async def _translate_item(
        self, item: discord.ui.Item[Any], target: str, domain: str | None = None
    ) -> discord.ui.Item[Any]:
        if isinstance(item, discord.ui.Select):
            if item.placeholder:
                item.placeholder = await self.translate_object(
                    item.placeholder, target, domain=domain
                )

            for option in item.options:
                option.label = await self.translate_object(
                    option.label, target, domain=domain
                )
                if option.description:
                    option.description = await self.translate_object(
                        option.description, target, domain=domain
                    )
        elif isinstance(
            item,
            (
                discord.ui.RoleSelect,
                discord.ui.ChannelSelect,
                discord.ui.MentionableSelect,
                discord.ui.UserSelect,
            ),
        ):
            if item.placeholder:
                item.placeholder = await self.translate_object(
                    item.placeholder, target, domain=domain
                )
        elif isinstance(item, discord.ui.Button):
            if item.label:
                item.label = await self.translate_object(
                    item.label, target, domain=domain
                )
        elif isinstance(item, discord.ui.TextInput):
            if item.label:
                item.label = await self.translate_object(
                    item.label, target, domain=domain
                )
            if item.placeholder:
                item.placeholder = await self.translate_object(
                    item.placeholder, target, domain=domain
                )
        elif isinstance(item, (discord.ui.Container, discord.ui.ActionRow)):
            for child in item.children:
                await self._translate_item(child, target, domain)
        elif isinstance(item, discord.ui.Label):
            await self._translate_item(item.component, target, domain)
            if item.description:
                item.description = await self.translate_object(
                    item.description, target, domain=domain
                )
            item.text = await self.translate_object(item.text, target, domain=domain)
        elif isinstance(item, discord.ui.Section):
            for child in item.children:
                await self._translate_item(child, target, domain)
            await self._translate_item(item.accessory, target, domain)
        elif isinstance(item, discord.ui.TextDisplay):
            item.content = await self.translate_object(
                item.content, target, domain=domain
            )
        elif isinstance(item, discord.ui.Thumbnail):
            if item.description:
                item.description = await self.translate_object(
                    item.description, target, domain=domain
                )
        elif isinstance(item, (discord.ui.RadioGroup, discord.ui.CheckboxGroup)):
            for option in item.options:
                option.label = await self.translate_object(
                    option.label, target, domain=domain
                )
                if option.description:
                    option.description = await self.translate_object(
                        option.description, target, domain=domain
                    )
        else:
            pass

        return item

    async def _translate_embed(
        self, object: discord.Embed, target: str, domain: str | None = None
    ) -> discord.Embed:
        if object.title:
            object.title = await self.translate_object(
                object.title, target, domain=domain
            )
        if object.description:
            object.description = await self.translate_object(
                object.description, target, domain=domain
            )

        _fields: list[dict[str, Any]] = []
        for field in object.fields:
            pd: dict[str, Any] = {
                "inline": field.inline,
            }

            if field.name:
                pd["name"] = await self.translate_object(
                    field.name, target, domain=domain
                )
            if field.value:
                pd["value"] = await self.translate_object(
                    field.value, target, domain=domain
                )

            if not len(pd) >= 3:
                # field is not valid, as it must have both name and value
                continue

            _fields.append(pd)

        setattr(object, "_fields", _fields)

        if object.author:
            # author objects at least have a name attribute
            assert object.author.name
            pd: dict[str, Any] = {
                "icon_url": object.author.icon_url,
                "url": object.author.url,
                "name": await self.translate(object.author.name, target, domain=domain),
            }
            setattr(
                object,
                "_author",
                pd,
            )

        if object.footer:
            pd: dict[str, Any] = {
                "icon_url": object.footer.icon_url,
            }
            if object.footer.text:
                pd["text"] = await self.translate_object(
                    object.footer.text, target, domain=domain
                )
            setattr(
                object,
                "_footer",
                pd,
            )

        return object

    @overload
    async def translate_object(
        self, object: discord.Embed, locale: str, *, domain: str | None = None
    ) -> discord.Embed: ...

    @overload
    async def translate_object(
        self,
        object: str | app_commands.locale_str,
        locale: str,
        *,
        domain: str | None = None,
    ) -> str: ...

    @overload
    async def translate_object(
        self, object: discord.ui.Item[Any], locale: str, *, domain: str | None = None
    ) -> discord.ui.Item[Any]: ...

    @overload
    async def translate_object(
        self, object: discord.ui.View, locale: str, *, domain: str | None = None
    ) -> discord.ui.View: ...

    @overload
    async def translate_object(
        self,
        object: discord.ui.LayoutView,
        locale: str,
        *,
        domain: str | None = None,
    ) -> discord.ui.LayoutView: ...

    async def translate_object(
        self,
        object: Any,
        locale: str,
        *,
        copy_object: bool = False,
        domain: str | None = None,
    ) -> Any:
        """Translate an object to the specified locale.

        .. warning::
            By default, translations mutates the object in place (except for strings). It is recommended
            to use ``copy_object`` for static objects which may be used multiple times, or if you do not
            want to mutate the original object.

        Parameters
        ----------
        object: Any
            The object to translate. This MUST be at its final state, otherwise
            changes applied AFTER this call will not be translated.
        locale: :class:`str`
            The target locale for the translation.
        copy_object: :class:`bool`
            Whether to create a deep copy of the object before translating it. This is useful
            if you want to preserve the original object and avoid modifying it in place.

            .. warning::
                Deep copying can be expensive for large objects, so use this option judiciously.
        domain: :class:`str` | :data:`None`
            The catalog domain to use for all text in the object.

        Returns
        -------
        Any
            The translated object.
        """
        valid_obj_types = (
            str,
            discord.Embed,
            discord.ui.Item,
            discord.ui.View,
            discord.ui.LayoutView,
            app_commands.locale_str,
        )

        if not isinstance(object, valid_obj_types):
            raise TypeError(f"Unsupported object type: {type(object).__name__}")

        if copy_object:
            object = copy.deepcopy(object)

        if isinstance(object, (str, app_commands.locale_str)):
            value = str(object)
            return await self.translate(value, locale, domain=domain)
        elif isinstance(object, discord.Embed):
            return await self._translate_embed(object, locale, domain)
        elif isinstance(object, discord.ui.Item):
            return await self._translate_item(object, locale, domain)
        elif isinstance(object, (discord.ui.View, discord.ui.LayoutView)):
            for child in object.children:
                await self._translate_item(child, locale, domain)
        return object

    def reload_automatic_available_locales(self) -> None:
        """Reload the list of automatically available locales."""
        self.available_locales = tuple(
            directory.name
            for directory in self.path.iterdir()
            if directory.is_dir() and (directory / "LC_MESSAGES").is_dir()
        )
        self._reload_locale_catalog()

    def reload_automatic_available_domains(self) -> None:
        """Reload the list of automatically available domains."""
        self.available_domains = tuple(
            sorted(
                {
                    domain
                    for domains in self._locale_catalog.values()
                    for domain in domains
                }
            )
        )

    def _reload_locale_catalog(self) -> None:
        self._locale_catalog = {
            locale: tuple(
                catalog.stem
                for catalog in (self.path / locale / "LC_MESSAGES").glob("*.mo")
            )
            for locale in self.available_locales
        }

    def clear_cache(self) -> None:
        """Clear the catalogs cache.

        This means that whenever a translation is requested after clearing the cache,
        the catalogs will be reloaded from disk.
        """
        self.load_catalog.cache_clear()

    def reload(self) -> None:
        """Reload the whole translator.

        This clears the cache, and reloads all available locales and domains.
        """
        self.clear_cache()
        self.reload_automatic_available_locales()
        self.reload_automatic_available_domains()


class DPYTranslator(app_commands.Translator):
    """Custom translator that implements :class:`~.Translator`."""

    def __init__(self, translator: Translator) -> None:
        self._underlying: Translator = translator
        super().__init__()

    async def load(self) -> None:
        # we can call it here, because if it was already called it'd be cached
        self._underlying.load_catalogs()

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContextTypes,
    ) -> str | None:
        catalog_name = locale.value
        catalog_validator = (
            string.extras.get("catalog_validator")
            or LocalizableMixin.GLOBAL_CATALOG_VALIDATOR
        )
        if catalog_validator:
            catalog_name = catalog_validator(catalog_name)

        explicit_domain = string.extras.get("domain")
        domain_getter = string.extras.get("domain_getter")
        if domain_getter is not None:
            domain = domain_getter(catalog_name, context)
        elif explicit_domain is not None:
            domain = explicit_domain
        elif LocalizableMixin.GLOBAL_DOMAIN_GETTER is not None:
            domain = LocalizableMixin.GLOBAL_DOMAIN_GETTER(catalog_name, context)
        else:
            domain = None

        domain = domain or self._underlying.default_domain
        catalog = self._underlying.load_catalog(locale=catalog_name, domain=domain)
        return catalog.gettext(string.message)
