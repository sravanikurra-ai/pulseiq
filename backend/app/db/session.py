from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# The Engine manages the actual connection pool to Postgres.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is a factory: calling SessionLocal() gives us a new
# database "workspace" (session) for a single request/operation.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency: provides a DB session to a route, and guarantees
    it's closed afterward, even if the request raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()