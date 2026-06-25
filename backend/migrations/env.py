"""
VoiceCare AI — Alembic environment configuration.
Reads DATABASE_URL from environment / app config and supports async migrations.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ------------------------------------------------------------------
# Alembic config object
# ------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------------
# Import all models so Alembic autogenerate picks them up
# ------------------------------------------------------------------
from app.db.models import Base  # noqa: E402 — must be after sys.path setup
target_metadata = Base.metadata

# ------------------------------------------------------------------
# Resolve database URL from environment (overrides alembic.ini)
# ------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

# Convert postgres:// → postgresql+asyncpg:// for async driver
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


# ------------------------------------------------------------------
# Offline migrations (generate SQL without a live DB connection)
# ------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------------
# Online migrations (async)
# ------------------------------------------------------------------
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create async engine and run migrations."""
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (connected) migration."""
    asyncio.run(run_async_migrations())


# ------------------------------------------------------------------
# Dispatch
# ------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
