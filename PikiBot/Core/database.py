"""
MIT License

(c) Copyright 2026-present, DA-344
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar, Protocol

import sqlalchemy
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

_log = logging.getLogger(__name__)


class _ContextManagerProto(Protocol):
    async def __aenter__(self) -> AsyncSession: ...

    async def __aexit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: object | None,
    ) -> bool | None: ...


class BaseModel(DeclarativeBase):
    """SQLAlchemy declarative base for models managed by :class:`Database`.

    Subclass this to declare a table model. When :meth:`Database.connect` is called
    with ``create_tables=True``, its metadata is used to create the registered tables.
    """


def create_engine(
    url: str | sqlalchemy.engine.URL,
    *,
    pool_size: int = 20,
    max_overflow: int = 0,
    **kwargs: Any,
) -> AsyncEngine:
    """Create an AsyncEngine for database management.

    You usually do not need to call this function as it creates a connection different to the Bot's
    main database connection.

    Parameters
    ----------
    url: :class:`str`
        The full resolved URL to connect the database to.
    pool_size: :class:`int`
        The max connections allowed at the same time in the pool.
    max_overflow: :class:`int`
        Maximum overflow allowed by the engine.
    **kwargs: :data:`Any`
        Extra params to provide to the engine creator.

    Returns
    -------
    :class:`AsyncEngine`
        The newly created database async engine.
    """
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        **kwargs,
    )


class Database:
    """Class-level access to the bot's asynchronous SQLAlchemy connection.

    The engine and session factory are shared through class state. Call :meth:`connect`
    once during startup, use :meth:`acquire` for transactional sessions, and call
    :meth:`close` during shutdown.

    Notes
    -----
    This class is not instantiated. Its class methods manage the shared connection state.
    """

    __engine__: ClassVar[AsyncEngine | None] = None
    __session__: ClassVar[async_sessionmaker[AsyncSession] | None] = None

    @classmethod
    def is_initialized(cls) -> bool:
        """Whether the Database is initialized."""
        return cls.__engine__ is not None and cls.__session__ is not None

    @classmethod
    async def connect(
        cls, engine: AsyncEngine, *, create_tables: bool = True
    ) -> type[Database]:
        """Start the database connection of the provided engine.

        Parameters
        ----------
        engine: :class:`sqlalchemy.ext.asyncio.AsyncEngine`
            The engine to start the connection to. This should be created using the
            :meth:`create_engine` method.
        create_tables: :class:`bool`
            Whether to automatically create all tables derived from :class:`BaseModel`.

        Raises
        ------
        RuntimeError
            The database has already be connected.

        Returns
        -------
        type[:class:`Database`]
            The database cls to keep interacting with it.
        """
        if cls.__engine__ is not None:
            raise RuntimeError(f"Database already connected: {cls.__engine__!r}")
        cls.__engine__ = engine
        cls.__session__ = async_sessionmaker(cls.__engine__)

        if create_tables:
            async with engine.begin() as conn:
                try:
                    await conn.run_sync(BaseModel.metadata.create_all)
                except:
                    _log.exception(
                        "An error ocurred while creating the tables of the database, "
                        "not connecting."
                    )
                    cls.__engine__ = None
                    cls.__session__ = None

        return cls

    @classmethod
    def acquire(cls) -> _ContextManagerProto:
        """Acquire a session from the pool to perform an operation through the database.

        The connection creates a transaction, which means that if no exception is found, it is
        automatically ``COMMIT``ed, if an exception was found, then it is automatically ``ROLLBACK``ed.

        Examples
        --------
        Obtaining a connection ::

            async with Database.acquire() as session:
                await session.execute(...)

        Raises
        ------
        RuntimeError
            No session is set.

        Returns
        -------
        An async session context manager, that returns a :class:`sqlalchemy.ext.asyncio.AsyncSession` upon entering.
        """
        if not cls.__session__:
            raise RuntimeError("No session set")
        return cls.__session__.begin()

    @classmethod
    async def close(cls) -> None:
        """Dispose the database engine, and reset the database state.

        If no session is currently active, it does nothing.
        """
        if cls.__engine__:
            await cls.__engine__.dispose(close=True)

        cls.__engine__ = None
        cls.__session__ = None
