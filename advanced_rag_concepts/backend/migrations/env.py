"""Alembic migration environment: connects to the database and runs migrations."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from rag_app.core.config import get_settings
from rag_app.db.base import Base

# Alembic's config object, built from alembic.ini
config = context.config

# Use DATABASE_URL from .env (same source as the app) instead of a hardcoded URL.
# "%" is doubled because alembic.ini values treat % as special (interpolation).
config.set_main_option("sqlalchemy.url", str(get_settings().database_url).replace("%", "%%"))

# Configure Python logging from the [loggers] sections of alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# All ORM models' tables; lets `alembic revision --autogenerate` detect schema changes
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to the screen instead of executing it (`alembic upgrade head --sql`)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations on an already-open connection, inside one transaction."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Open an async connection and run the (synchronous) migration code through it."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        # No connection pool: migrations are a short one-off script
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        # Alembic's API is synchronous; run_sync bridges our async connection to it
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Connect to the real database and apply migrations."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
