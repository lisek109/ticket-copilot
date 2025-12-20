from sqlalchemy.orm import Session
from app.db.database import SessionLocal

def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
