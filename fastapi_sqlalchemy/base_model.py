"""
Base Model Class - Laravel Eloquent-style ORM
Allows models to have static methods like User.all(), User.find(1), etc.
"""

from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from typing import Type, Optional, Any, Dict, List
from fastapi_sqlalchemy.connection import connection_manager
from fastapi_sqlalchemy.table_query import TableQuery
from fastapi_sqlalchemy.db import DB

Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with Eloquent-style static methods.
    
    All TableQuery methods are accessible through the model either:
    1. As direct model methods (e.g., User.where(), User.join())
    2. Via User.query() which returns a full TableQuery instance
    
    Usage:
        class User(BaseModel):
            __tablename__ = "users"
            
            id = Column(Integer, primary_key=True)
            name = Column(String(255))
            
        # Direct methods
        users = await User.all()
        user = await User.find(1)
        
        # Query builder chaining (returns TableQuery)
        users = await User.where(User.active == True)\
                          .order_by(User.name)\
                          .limit(10)\
                          .all()
        
        # Full access via query() method
        users = await User.query()\
                          .where_in(User.id, [1, 2, 3])\
                          .join(Post, User.id == Post.user_id)\
                          .options(joinedload(User.profile))\
                          .all()
    """
    
    __abstract__ = True
    _session: Optional[AsyncSession] = None
    
    @classmethod
    def get_session(cls) -> AsyncSession:
        """Get the current database session."""
        if cls._session is None:
            raise RuntimeError(
                "No session available. Use User.set_session(session) or "
                "User.use_connection('connection_name') first"
            )
        return cls._session
    
    @classmethod
    def set_session(cls, session: AsyncSession):
        """Set the database session for this model class."""
        cls._session = session
    
    @classmethod
    async def use_connection(cls, connection_name: str):
        """Use a specific database connection."""
        async with connection_manager.session(connection_name) as session:
            cls._session = session
    
    @classmethod
    def query(cls) -> TableQuery:
        """
        Get a fresh query builder for this model.
        
        Returns a TableQuery instance with FULL access to all query methods.
        This is the recommended way to access advanced query features.
        
        Example:
            # Access any TableQuery method
            users = await User.query()\
                .where_in(User.id, [1, 2,  Ness)\
                .join(Post, User.id == Post.user_id)\
                .options(joinedload(User.profile))\
                .distinct_by(User.id)\
                .all()
        """
        session = cls.get_session()
        return TableQuery(session).table(cls)
    
    @classmethod
    async def all(cls) -> List[Dict[str, Any]]:
        """Get all records for this model."""
        return await cls.query().all()
    
    @classmethod
    async def find(cls, id: Any) -> Optional[Dict[str, Any]]:
        """Find a record by primary key."""
        return await cls.query().find(id)
    
    @classmethod
    async def find_or_fail(cls, id: Any) -> Dict[str, Any]:
        """Find a record by ID or raise exception."""
        return await cls.query().find_or_fail(id)
    
    @classmethod
    async def first(cls) -> Optional[Dict[str, Any]]:
        """Get the first record."""
        return await cls.query().first()
    
    @classmethod
    async def count(cls) -> int:
        """Count all records."""
        return await cls.query().count()
    
    # ============================================================
    # Query Builder Chainable Methods
    # All these methods return TableQuery for chaining
    # ============================================================
    
    @classmethod
    def where(cls, *conditions) -> TableQuery:
        """Add WHERE conditions. Returns TableQuery for chaining."""
        return cls.query().where(*conditions)
    
    @classmethod
    def select(cls, *columns) -> TableQuery:
        """Select specific columns. Returns TableQuery for chaining."""
        return cls.query().select(*columns)
    
    @classmethod
    def join(cls, model, onclause) -> TableQuery:
        """Add INNER JOIN. Returns TableQuery for chaining."""
        return cls.query().join(model, onclause)
    
    @classmethod
    def left_join(cls, model, onclause) -> TableQuery:
        """Add LEFT JOIN. Returns TableQuery for chaining."""
        return cls.query().left_join(model, onclause)
    
    @classmethod
    def order_by(cls, *columns) -> TableQuery:
        """Add ORDER BY. Returns TableQuery for chaining."""
        return cls.query().order_by(*columns)
    
    @classmethod
    def group_by(cls, *columns) -> TableQuery:
        """Add GROUP BY. Returns TableQuery for chaining."""
        return cls.query().group_by(*columns)
    
    @classmethod
    def limit(cls, value: int) -> TableQuery:
        """Add LIMIT. Returns TableQuery for chaining."""
        return cls.query().limit(value)
    
    @classmethod
    def offset(cls, value: int) -> TableQuery:
        """Add OFFSET. Returns TableQuery for chaining."""
        return cls.query().offset(value)
    
    @classmethod
    def with_orm(cls, enabled: bool = True) -> TableQuery:
        """Enable ORM mode. Returns TableQuery for chaining."""
        return cls.query().with_orm(enabled)
    
    @classmethod
    def options(cls, *load_strategies) -> TableQuery:
        """Add SQLAlchemy loading options. Returns TableQuery for chaining."""
        return cls.query().options(*load_strategies)
    
    @classmethod
    def load_only(cls, *columns) -> TableQuery:
        """Load only specific columns. Returns TableQuery for chaining."""
        return cls.query().load_only(*columns)
    
    @classmethod
    def schema(cls, schema_name: str) -> TableQuery:
        """Set schema. Returns TableQuery for chaining."""
        return cls.query().schema(schema_name)
    
    @classmethod
    def having(cls, *conditions) -> TableQuery:
        """Add HAVING clause. Returns TableQuery for chaining."""
        return cls.query().having(*conditions)
    
    @classmethod
    def where_in(cls, column, values: list) -> TableQuery:
        """Add WHERE column IN (values). Returns TableQuery for chaining."""
        return cls.query().where_in(column, values)
    
    @classmethod
    def where_not_in(cls, column, values: list) -> TableQuery:
        """Add WHERE column NOT IN (values). Returns TableQuery for chaining."""
        return cls.query().where_not_in(column, values)
    
    @classmethod
    def where_null(cls, column) -> TableQuery:
        """Add WHERE column IS NULL. Returns TableQuery for chaining."""
        return cls.query().where_null(column)
    
    @classmethod
    def where_not_null(cls, column) -> TableQuery:
        """Add WHERE column IS NOT NULL. Returns TableQuery for chaining."""
        return cls.query().where_not_null(column)
    
    @classmethod
    def where_between(cls, column, values: list) -> TableQuery:
        """Add WHERE column BETWEEN. Returns TableQuery for chaining."""
        return cls.query().where_between(column, values)
    
    @classmethod
    def where_like(cls, column, pattern: str) -> TableQuery:
        """Add WHERE column LIKE pattern. Returns TableQuery for chaining."""
        return cls.query().where_like(column, pattern)
    
    @classmethod
    def apply_filters(cls, filters: Dict[str, Any], use_or: bool = False) -> TableQuery:
        """
        Apply filters dynamically with Laravel-like syntax.
        
        Supports table.column__operator syntax.
        
        Examples:
            # Basic filters
            users = await User.apply_filters({
                "user.active__eq": True,
                "user.age__gte": 18
            }).all()
            
            # With joins
            users = await User.left_join(Post, User.id == Post.user_id)\
                             .apply_filters({
                                 "user.active__eq": True,
                                 "post.published__eq": True
                             })\
                             .all()
        
        Available operators:
        - eq, ne, neq - Equal, not equal
        - gt, gte, lt, lte - Comparison
        - like, icontains - Pattern matching
        - in, notin - In/not in lists
        - startswith, endswith - String matching
        - between, not_between - Range queries
        - isnull, notnull - NULL checks
        """
        return cls.query().apply_filters(filters, use_or=use_or)
    
    @classmethod
    async def paginate(cls, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get paginated results."""
        return await cls.query().paginate(page, per_page)
    
    @classmethod
    async def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        return await cls.query().create(data)
    
    @classmethod
    async def create_many(cls, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple records."""
        return await cls.query().create_many(data_list)
    
    @classmethod
    async def update_by_id(cls, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record by ID."""
        return await cls.query().update_by_id(id, data)
    
    @classmethod
    async def delete_by_id(cls, id: Any) -> int:
        """Delete a record by ID."""
        return await cls.query().delete_by_id(id)
    
    @classmethod
    def with_schema(cls, schema_name: str) -> TableQuery:
        """Query with a specific schema."""
        return cls.query().schema(schema_name)
    
    @classmethod
    def with_connection(cls, connection_name: str):
        """Get a query builder for a specific connection."""
        class _ModelWithConnection:
            async def __aenter__(self):
                await cls.use_connection(connection_name)
                return cls
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return _ModelWithConnection()


# Convenience function to create models with Eloquent-style methods
def create_model(tablename: str, **columns) -> Type[BaseModel]:
    """
    Create a model dynamically.
    
    Usage:
        User = create_model(
            "users",
            id=Column(Integer, primary_key=True),
            name=Column(String(255))
        )
    """
    return type(tablename.capitalize(), (BaseModel,), {
        '__tablename__': tablename,
        **columns
    })


# FastAPI Dependency to inject session into models
async def setup_model_session():
    """Context manager to setup model sessions."""
    async with connection_manager.session() as session:
        # Set session for all model classes
        for model_class in BaseModel.__subclasses__():
            model_class.set_session(session)
        yield
