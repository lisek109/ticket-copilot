from app.db.database import engine, Base
from app.db import models  # noqa: F401  (ensures models are registered)

def init():
    """Create all tables (MVP only). We'll add Alembic migrations next."""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init()
