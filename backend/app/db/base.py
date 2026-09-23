from sqlalchemy.orm import declarative_base

# Base is the parent class every ORM model (Phase 5 onward) will inherit from.
# Alembic also uses this to auto-detect model changes.
Base = declarative_base()