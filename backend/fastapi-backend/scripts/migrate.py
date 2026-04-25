#!/usr/bin/env python3
"""
Database migration script
Runs Alembic migrations before application startup
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from app.core.config import settings
from app.core.database import check_db_connection
from loguru import logger


def wait_for_database(max_retries=5, retry_interval=1):
    """
    Wait for database to be available
    
    Args:
        max_retries: Maximum number of retry attempts (reduced for faster startup)
        retry_interval: Seconds between retries (reduced for faster startup)
    
    Returns:
        bool: True if database is available, False otherwise
    """
    print("=" * 50)
    print("Checking database connection...")
    print(f"DATABASE_URL: {settings.DATABASE_URL.split('@')[0]}@***")  # Hide password
    print("=" * 50)
    logger.info("Checking database connection...")
    
    # First attempt - immediate check (database is usually already available on restart)
    if check_db_connection():
        print("✓ Database connection established!")
        logger.info("✓ Database connection established")
        return True
    
    # If first attempt fails, retry with shorter intervals
    for attempt in range(1, max_retries + 1):
        print(f"Attempt {attempt}/{max_retries}: Checking database connection...")
        if check_db_connection():
            print("✓ Database connection established!")
            logger.info("✓ Database connection established")
            return True
        
        print(f"✗ Database not ready, retrying in {retry_interval}s...")
        logger.warning(f"Database not ready (attempt {attempt}/{max_retries}), retrying in {retry_interval}s...")
        time.sleep(retry_interval)
    
    print("✗ Database connection failed after all retries")
    logger.error("✗ Database connection failed after all retries")
    return False


def run_migrations():
    """
    Run Alembic migrations (only if needed)
    
    Returns:
        bool: True if migrations succeeded or not needed, False otherwise
    """
    try:
        print("=" * 50)
        print("Checking database migrations...")
        print("=" * 50)
        logger.info("Checking database migrations...")
        
        # Get Alembic config
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        # Override sqlalchemy.url if not set
        if not alembic_cfg.get_main_option("sqlalchemy.url"):
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # Check current migration version
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            script = ScriptDirectory.from_config(alembic_cfg)
            head_rev = script.get_current_head()
            
            if current_rev == head_rev:
                print("✓ Database is up to date - no migrations needed")
                logger.info("✓ Database is up to date - no migrations needed")
                return True
        
        # Migrations are needed
        print("Running database migrations...")
        logger.info("Running database migrations...")
        
        # Run migrations
        print("Executing: alembic upgrade head")
        command.upgrade(alembic_cfg, "head")
        
        print("=" * 50)
        print("✓ Migrations completed successfully")
        print("=" * 50)
        logger.info("=" * 50)
        logger.info("✓ Migrations completed successfully")
        logger.info("=" * 50)
        return True
    
    except Exception as e:
        print("=" * 50)
        print(f"✗ Migration failed: {str(e)}")
        print("=" * 50)
        logger.error("=" * 50)
        logger.error(f"✗ Migration failed: {str(e)}")
        logger.error("=" * 50)
        logger.exception("Migration error details:")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    try:
        # Wait for database
        if not wait_for_database():
            logger.error("Cannot proceed without database connection")
            logger.error("Please ensure database is running and DATABASE_URL is correct")
            logger.error("Container will continue to start - run migrations manually later")
            sys.exit(1)  # Exit with error but entrypoint will continue
        
        # Run migrations
        if not run_migrations():
            logger.error("Migration failed - check logs above for details")
            logger.error("Container will continue to start - run migrations manually later")
            sys.exit(1)  # Exit with error but entrypoint will continue
        
        logger.info("Migration script completed successfully")
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error in migration script: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

