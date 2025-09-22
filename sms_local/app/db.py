# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

# For SQLite only; harmless for others
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Models import this Base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Import all model modules *inside* this function to avoid circular imports.
    Then create tables.
    """
    # IMPORTANT: keep these imports INSIDE the function
    from .models import (
        student,
        guardian,
        enrollment,
        attendance,
        fees,
        expenditure,
        stationery,   # <- stationery (replacing old inventory)
    )  # noqa: F401

    Base.metadata.create_all(bind=engine)
