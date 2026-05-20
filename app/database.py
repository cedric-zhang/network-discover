from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os

# Using relative path to create database file
DATABASE_PATH = Path(__file__).parent.parent / 'data' / 'network.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Create directory (if it doesn't exist)
DATABASE_PATH.parent.mkdir(exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

def migrate_tables():
    """Auto-add missing columns to existing SQLite tables."""
    import logging
    columns_to_add = {
        "scan_tasks": [
            ("progress", "INTEGER DEFAULT 0"),
            ("current_ip", "TEXT"),
            ("total_ips", "INTEGER"),
            ("elapsed_seconds", "FLOAT"),
        ],
    }
    with engine.connect() as conn:
        for table, columns in columns_to_add.items():
            for col_name, col_type in columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logging.info(f"Migration OK: {table}.{col_name} {col_type}")
                    print(f"  [MIGRATE] Added {table}.{col_name} {col_type}")
                except Exception as e:
                    err = str(e).lower()
                    if "duplicate column" in err or "already exists" in err:
                        print(f"  [SKIP] {table}.{col_name} already exists")
                    else:
                        try:
                            conn.execute(text(f"SELECT {col_name} FROM {table} LIMIT 1"))
                            print(f"  [OK] {table}.{col_name} exists (verified)")
                        except Exception:
                            print(f"  [WARN] {table}.{col_name}: {e}")
    # Ensure any new tables are created
    Base.metadata.create_all(bind=engine)
    print("Migration check complete")

