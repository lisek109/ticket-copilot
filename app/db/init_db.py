from app.db.database import engine, Base
from app.db import models  # noqa: F401  (ensures models are registered i Base metadata)
# Importing models ensures all ORM tables are registered in Base.metadata

def init():
    """
    Development helper only.

    In production and CI/CD, prefer Alembic migrations:
        alembic upgrade head
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init()
