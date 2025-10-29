from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
from .config import DBConfig
from .util import DBQuerySetting
from .table_query import TableQuery
from .connection import connection_manager, _current_connection, DBConnectionManager

class DB:
    """
    Main database facade - Laravel style.
    Single entry point for all database operations.
    
    Usage:
        db = DB(session)
        
        users = await db.table(User).where(User.active == True).all()
        user = await db.table(User).find(1)
        created = await db.table(User).create({"name": "John"})
        
        async with db.transaction():
            await db.table(User).create({"name": "Jane"})
            await db.table(Post).create({"user_id": 2, "title": "Hello"})
    """
    
    def __init__(self, session: AsyncSession, connection_name: str = "default"):
        """Initialize DB facade with session."""
        self.session = session
        self.connection_name = connection_name

    def table(self, model) -> TableQuery:
        """Get query builder for a table."""
        return TableQuery(self.session).table(model)

    def query(self) -> TableQuery:
        """Get fresh query builder."""
        return TableQuery(self.session)

    async def begin_transaction(self):
        """Begin a transaction."""
        await self.session.begin()

    async def commit(self):
        """Commit the transaction."""
        await self.session.commit()

    async def rollback(self):
        """Rollback the transaction."""
        await self.session.rollback()

    def transaction(self):
        """Context manager for transaction."""
        return self.session.begin()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.begin_transaction()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @staticmethod
    def connection(name: str):
        """Switch to a different connection temporarily."""
        return connection_manager.session(name)

    @staticmethod
    async def use_connection(name: str):
        """Switch default connection for current context."""
        _current_connection.set(name)

    @staticmethod
    def get_current_connection() -> str:
        """Get current connection name."""
        return _current_connection.get()

    @staticmethod
    def config() -> 'DBConfig':
        """Get the configuration manager."""
        return DBConfig

    @staticmethod
    def manager() -> 'DBConnectionManager':
        """Get the connection manager."""
        return connection_manager
