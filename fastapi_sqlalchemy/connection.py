from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy import text
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import contextvars
from .config import DBConfig, db_settings


class DBConnectionManager:
    """Manages multiple database connections."""
    
    def __init__(self):
        self._connections: Dict[str, DBConfig] = {}
        self._engines: Dict[str, AsyncEngine] = {}
        self._session_makers: Dict[str, async_sessionmaker] = {}
        self._default_connection: str = "default"
        self._initialized: bool = False

    def add_connection(self, name: str, config: DBConfig) -> None:
        """Add a database connection configuration."""
        self._connections[name] = config
        if len(self._connections) == 1:
            self._default_connection = name

    def set_default_connection(self, name: str) -> None:
        """Set the default connection to use."""
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        self._default_connection = name

    def get_default_connection(self) -> str:
        """Get the default connection name."""
        return self._default_connection

    async def initialize(self) -> None:
        """Initialize all database engines and session makers."""
        if self._initialized:
            return

        # If no connections were added directly, hydrate from db_settings
        # This lets projects call db_settings.load_from_dict(...) and then
        # simply run connection_manager.initialize() without extra wiring.
        if not self._connections and getattr(db_settings, "_connections", None):
            # Load all configured connections from db_settings
            for name, cfg in db_settings._connections.items():  # type: ignore[attr-defined]
                self._connections[name] = DBConfig.from_dict(cfg)
            # Set default connection name from db_settings
            if getattr(db_settings, "_default_connection", None):
                self._default_connection = db_settings._default_connection  # type: ignore[attr-defined]

        for name, config in self._connections.items():
            engine = create_async_engine(
                config.get_url(),
                echo=config.echo,
                echo_pool=config.echo_pool,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_recycle=config.pool_recycle,
                pool_pre_ping=config.pool_pre_ping,
                poolclass=config.get_pool_class(),
                connect_args=config.connect_args
            )
            
            self._engines[name] = engine
            self._session_makers[name] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

        self._initialized = True

    async def close_all(self) -> None:
        """Close all database connections."""
        for engine in self._engines.values():
            await engine.dispose()
        
        self._engines.clear()
        self._session_makers.clear()
        self._initialized = False

    def get_engine(self, connection: Optional[str] = None) -> AsyncEngine:
        """Get database engine for a connection."""
        if not self._initialized:
            raise RuntimeError("ConnectionManager not initialized. Call await manager.initialize() first.")
        
        conn_name = connection or self._default_connection
        
        if conn_name not in self._engines:
            raise ValueError(f"Connection '{conn_name}' not found")
        
        return self._engines[conn_name]

    def get_session_maker(self, connection: Optional[str] = None) -> async_sessionmaker:
        """Get session maker for a connection."""
        if not self._initialized:
            raise RuntimeError("ConnectionManager not initialized. Call await manager.initialize() first.")
        
        conn_name = connection or self._default_connection
        
        if conn_name not in self._session_makers:
            raise ValueError(f"Connection '{conn_name}' not found")
        
        return self._session_makers[conn_name]

    @asynccontextmanager
    async def session(self, connection: Optional[str] = None, schema: Optional[str] = None):
        """
        Get a database session as context manager.
        
        Args:
            connection: Connection name to use
            schema: PostgreSQL schema name to use
        """
        session_maker = self.get_session_maker(connection)
        
        async with session_maker() as session:
            # Set schema if provided (PostgreSQL)
            if schema:
                # This works for PostgreSQL
                await session.execute(text(f"SET search_path TO {schema}"))
            
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    def list_connections(self) -> List[str]:
        """Get list of all registered connection names."""
        return list(self._connections.keys())


# Global connection manager instance
connection_manager = DBConnectionManager()
_current_connection = contextvars.ContextVar('db_connection', default='default')
