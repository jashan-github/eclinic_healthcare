"""
Alembic migration environment
"""

from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text

from alembic import context

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Base and all models for autogenerate support
from app.models.base import Base
from app.core.config import settings

# Import all models to ensure they're registered with Base
from app.models import user  # noqa: F401
from app.models import auth  # noqa: F401
from app.models import profile  # noqa: F401
from app.models import audit  # noqa: F401
from app.models import notification  # noqa: F401

# Set target metadata for Alembic autogenerate
target_metadata = Base.metadata

# this is the Alembic Config object
config = context.config

# Note: We don't set sqlalchemy.url here to avoid ConfigParser interpolation issues
# with URL-encoded passwords (%40, %23). Instead, we use settings.DATABASE_URL
# directly in run_migrations_offline() and run_migrations_online()

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use DATABASE_URL from settings directly to avoid ConfigParser interpolation issues
    # with URL-encoded passwords
    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    
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
    # Get database URL from settings if not set in alembic.ini
    # This is important for Docker where alembic.ini doesn't have sqlalchemy.url
    configuration = config.get_section(config.config_ini_section, {})
    if "sqlalchemy.url" not in configuration:
        configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Ensure alembic_version table has VARCHAR(255) for version_num
        # This fixes the issue where long revision IDs exceed VARCHAR(32)
        # Run this outside of the transaction to ensure it completes before migrations
        with connection.begin():
            # Create table with correct size if it doesn't exist
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(255) NOT NULL PRIMARY KEY
                );
            """))
            # If table exists with VARCHAR(32), alter it to VARCHAR(255)
            connection.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'alembic_version' 
                        AND column_name = 'version_num' 
                        AND character_maximum_length = 32
                    ) THEN
                        ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);
                    END IF;
                END $$;
            """))
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
