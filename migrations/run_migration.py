#!/usr/bin/env python3
"""
Database Migration Runner
Run this script to apply database migrations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration(migration_file: str):
    """Run a single migration file"""
    migration_path = Path(__file__).parent / migration_file

    if not migration_path.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    logger.info(f"Running migration: {migration_file}")

    try:
        with open(migration_path, 'r') as f:
            sql = f.read()

        with engine.connect() as conn:
            # Split by semicolons and execute each statement
            statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

            for statement in statements:
                logger.info(f"Executing: {statement[:100]}...")
                conn.execute(text(statement))
                conn.commit()

        logger.info(f"✓ Migration {migration_file} completed successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False


def run_all_migrations():
    """Run all migration files in order"""
    migrations_dir = Path(__file__).parent
    migration_files = sorted([f.name for f in migrations_dir.glob("*.sql")])

    if not migration_files:
        logger.info("No migrations to run")
        return

    logger.info(f"Found {len(migration_files)} migration(s) to run")

    success_count = 0
    for migration_file in migration_files:
        if run_migration(migration_file):
            success_count += 1

    logger.info(f"Completed {success_count}/{len(migration_files)} migrations")


if __name__ == "__main__":
    logger.info("Starting database migrations...")
    run_all_migrations()
    logger.info("Migration process completed")
