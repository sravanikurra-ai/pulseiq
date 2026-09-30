from fastapi import Query


def pagination_params(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Shared pagination dependency. Caps limit at 200 so nobody can request the whole table in one call."""
    return {"limit": limit, "offset": offset}