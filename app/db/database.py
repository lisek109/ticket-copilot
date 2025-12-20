from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# NOTE: SQLite is used for MVP. 
DATABASE_URL = "sqlite:///./ticket_copilot.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite-specific setting
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass
