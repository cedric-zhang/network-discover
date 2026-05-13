from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean
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
