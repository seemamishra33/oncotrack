"""
connection.py
=============
This file does ONE job: connect Python to your MySQL database.

Everything else in the project (FastAPI routes, Streamlit pages, seed script)
imports from here. You set up the connection once, reuse it everywhere.

CONCEPTS DEMONSTRATED:
    - python-dotenv  : reads secrets from .env file
    - SQLAlchemy     : Python toolkit for talking to databases
    - Generator      : get_db() uses yield to manage session lifecycle
"""

import os                                      # built-in: read environment variables
from dotenv import load_dotenv                 # reads .env file into os.environ
from sqlalchemy import create_engine, text     # create_engine = the connection itself
from sqlalchemy.orm import sessionmaker        # sessionmaker = factory for DB sessions
from sqlalchemy.orm import DeclarativeBase     # base class for all ORM table models
import logging                                 # built-in: write messages to a log file

# ── Logging setup ────────────────────────────────────────────────────────────
# This creates a logger just for this file.
# When something goes wrong with the DB connection, the message will say
# "oncotrack.database" so you know exactly where the error came from.
logger = logging.getLogger("oncotrack.database")


# ── Load environment variables ───────────────────────────────────────────────
# load_dotenv() looks for a .env file in your project root and loads it.
# After this line, os.getenv("DB_PASSWORD") works anywhere in this file.
# If .env doesn't exist it silently does nothing — safe to call always.
load_dotenv()


# ── Build the connection URL ──────────────────────────────────────────────────
# SQLAlchemy needs a URL in this exact format to know:
#   - what database type (mysql)
#   - what driver/connector to use (mysqlconnector)
#   - who is connecting (user:password)
#   - where to connect (host:port)
#   - which database to use (db_name)
#
# Format:  dialect+driver://user:password@host:port/database
#
# Example: mysql+mysqlconnector://root:secret@localhost:3306/oncotrack

DB_USER     = os.getenv("DB_USER",     "root")         # fallback to "root" if not set
DB_PASSWORD = os.getenv("DB_PASSWORD", "")             # fallback to empty string
DB_HOST     = os.getenv("DB_HOST",     "localhost")    # fallback to localhost
DB_PORT     = os.getenv("DB_PORT",     "3306")         # MySQL default port
DB_NAME     = os.getenv("DB_NAME",     "oncotrack")    # our database name

DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# ── Create the Engine ─────────────────────────────────────────────────────────
# The engine is the core connection to MySQL.

# pool_pre_ping=True  →  before using a connection from the pool, SQLAlchemy
#                        sends a quick "are you alive?" ping to MySQL.
#                        This prevents "connection gone away" errors if MySQL
#                        restarted or timed out while your app was idle.
#
# echo=False          →  set to True temporarily if you want to see every SQL
#                        query printed to the terminal (useful for debugging).
#
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)


# ── Session Factory ───────────────────────────────────────────────────────────
# A "session" is one conversation with the database.
# You open a session, run some queries, commit or rollback, then close it.
# sessionmaker() creates a factory (a class) that produces sessions on demand.
#
# autocommit=False  →  changes are NOT saved until you explicitly call commit().
#                      This protects you from partial writes if something errors halfway.
#
# autoflush=False   →  SQLAlchemy won't auto-send pending changes to the DB
#                      before every query. We control this manually.
#
# bind=engine       →  every session created by this factory uses our engine.
#
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Declarative Base ──────────────────────────────────────────────────────────
# This is the parent class for all our ORM models (Patient, LabResult, etc.).
# When a class inherits from Base and defines __tablename__, SQLAlchemy knows
# it represents a database table.
#
# Example (in models/patient.py):
#   class Patient(Base):
#       __tablename__ = "patients"
#       id = Column(Integer, primary_key=True)
#       ...
#
class Base(DeclarativeBase):
    pass


# ── get_db() — the session generator ─────────────────────────────────────────
# This is a Python GENERATOR used as a dependency in FastAPI.
#
# HOW IT WORKS:
#   1. FastAPI calls get_db()
#   2. A new session is created: db = SessionLocal()
#   3. yield db  →  pauses here and gives the session to the route function
#   4. The route function runs its queries using db
#   5. When the route is done, execution returns here
#   6. The finally block closes the session — ALWAYS, even if an error occurred
#
# WHY yield INSTEAD OF return?
#   return would give the session and exit immediately — the finally block
#   would never run and sessions would pile up, eventually crashing MySQL.
#   yield pauses, hands off control, then resumes for cleanup.
#
# USAGE IN FASTAPI:
#   from fastapi import Depends
#   from database.connection import get_db
#
#   @app.get("/patients")
#   def list_patients(db: Session = Depends(get_db)):
#       return db.query(Patient).all()
#
def get_db():
    db = SessionLocal()
    try:
        yield db            # hand the session to whoever called get_db(). return() would immediately exit() and d.close() never run. Unclosed session pile up and resulting in MySL crash.
    except Exception as e:
        db.rollback()       # if anything went wrong, undo any partial changes
        logger.error(f"Database session error: {e}")
        raise               # re-raise so FastAPI returns a proper error response
    finally:
        db.close()          # always close the session, no matter what happened


# ── test_connection() — quick health check ────────────────────────────────────
# Run this file directly to verify your .env settings are correct
# and MySQL is reachable before you build anything on top of it.
#
# Usage:  python database/connection.py
#
def test_connection():
    """Verify database connection and print table counts."""
    try:
        with engine.connect() as conn:
            # text() wraps a raw SQL string so SQLAlchemy can execute it
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"✓  Connected to MySQL {version}")

            # Check each table exists and how many rows it has
            tables = ["users", "patients", "lab_results", "treatments", "visits", "audit_logs"]
            for table in tables:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"✓  {table:<15} {count:>6} rows")
                except Exception:
                    print(f"✗  {table:<15} table not found — run schema.sql first")

    except Exception as e:
        print(f"✗  Connection failed: {e}")
        print("\nCheck your .env file:")
        print(f"  DB_HOST     = {DB_HOST}")
        print(f"  DB_PORT     = {DB_PORT}")
        print(f"  DB_USER     = {DB_USER}")
        print(f"  DB_PASSWORD = {'*' * len(DB_PASSWORD)}")
        print(f"  DB_NAME     = {DB_NAME}")


if __name__ == "__main__":
    test_connection()