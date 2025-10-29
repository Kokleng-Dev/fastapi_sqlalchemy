from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import StaticPool, QueuePool


class DBConfig:
    """
    Database configuration container.
    Similar to Laravel's config/database.php
    """
    
    def __init__(
        self,
        driver: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        charset: str = "utf8mb4",
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        echo_pool: bool = False,
        pool_pre_ping: bool = True,
        connect_args: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize database configuration."""
        self.driver = driver
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.charset = charset
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.echo_pool = echo_pool
        self.pool_pre_ping = pool_pre_ping
        self.connect_args = connect_args or {}
        self.extra = kwargs

    def get_url(self) -> str:
        """Build database URL from config."""
        if self.driver == "sqlite":
            return f"sqlite+aiosqlite:///{self.database}"
        elif self.driver == "postgresql":
            return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.driver == "mysql":
            return f"mysql+aiomysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
        else:
            raise ValueError(f"Unsupported driver: {self.driver}")

    def get_pool_class(self):
        """Get appropriate pool class based on driver."""
        if self.driver == "sqlite":
            return StaticPool
        return QueuePool

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "DBConfig":
        """Create DBConfig from dictionary."""
        return cls(**config)


class db_settings:
    """Database configuration settings manager."""
    
    _connections: Dict[str, Dict[str, Any]] = {}
    _default_connection: str = "default"
    _engines: Dict[str, AsyncEngine] = {}
    
    @classmethod
    def load_from_dict(cls, connections: Dict[str, Dict[str, Any]], default: str = "default"):
        """Load connections from dictionary."""
        cls._connections = connections
        cls._default_connection = default
    
    @classmethod
    def get_config(cls, connection_name: str = None) -> DBConfig:
        """Get database configuration."""
        name = connection_name or cls._default_connection
        if name not in cls._connections:
            raise ValueError(f"Connection '{name}' not found")
        return DBConfig.from_dict(cls._connections[name])
    
    @classmethod
    def switch(cls, connection_name: str):
        """Switch default connection."""
        if connection_name not in cls._connections:
            raise ValueError(f"Connection '{connection_name}' not found")
        cls._default_connection = connection_name


