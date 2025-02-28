from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database.base import Base
from app.database.models import *  # Import all models
from app.config import config  # Import database config

# This is the Alembic Config object, providing access to .ini settings
alembic_config = context.config

# Set the database URLs dynamically from `config.py`
database_url = config.database_url
async_database_url = config.async_database_url

# Apply the database URL to the Alembic configuration
alembic_config.set_main_option("sqlalchemy.url", database_url)

# Configure logging
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Set the target metadata (models for autogenerate support)
target_metadata = Base.metadata  # ✅ Ensure Alembic detects all models

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
