from functools import wraps
from typing import Callable, Optional
from .db import DB
from .connection import connection_manager

def with_db(connection: Optional[str] = None):
    """Decorator that injects DB instance."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with connection_manager.session(connection) as session:
                db = DB(session, connection or connection_manager.get_default_connection())
                return await func(db, *args, **kwargs)
        return wrapper
    return decorator


def with_session(connection: Optional[str] = None):
    """Decorator that injects AsyncSession."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with connection_manager.session(connection) as session:
                return await func(session, *args, **kwargs)
        return wrapper
    return decorator


def with_transaction(connection: Optional[str] = None):
    """Decorator that wraps function in transaction."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with connection_manager.session(connection) as session:
                db = DB(session, connection or connection_manager.get_default_connection())
                try:
                    result = await func(db, *args, **kwargs)
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise
        return wrapper
    return decorator
