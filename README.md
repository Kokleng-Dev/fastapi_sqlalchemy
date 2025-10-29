# FastAPI SQLAlchemy - Laravel-style Query Builder

A powerful, fluent query builder for FastAPI and SQLAlchemy inspired by Laravel's Eloquent ORM. Build clean, readable database queries with a chainable API.

## Features

- 🚀 **Fluent Query Builder** - Chain methods like Laravel's query builder
- 🔄 **Async/Await Support** - Built for FastAPI's async ecosystem  
- 🎯 **Type-Safe** - Full type hints for better IDE support
- 🔌 **Multiple Connections** - Support for multiple databases
- 🎨 **Clean API** - Similar to Laravel's Eloquent syntax
- 📝 **Auto SQL Debugging** - See generated SQL queries
- 🔐 **Transaction Support** - Easy transaction handling
- 📊 **Paginated Results** - Built-in pagination support
- 🗂️ **Dynamic Schema Switching** - Switch PostgreSQL schemas per request
- 🔍 **ORM Loading Strategies** - Eager loading, lazy loading, selective loading
- 🎯 **Eloquent-Style Models** - Use models like `User.all()`, `User.find(1)`

## Installation

```bash
pip install fastapi-sqlalchemy
```

Or using `uv`:

```bash
uv add fastapi-sqlalchemy
```

### Migration Support

This package includes Alembic-based migration support (similar to Django migrations):

```bash
# Initialize migrations
python -m fastapi_sqlalchemy.cli migration init

# Create migration files
python -m fastapi_sqlalchemy.cli migration makemigrations

# Apply migrations
python -m fastapi_sqlalchemy.cli migration migrate

# Check migration status
python -m fastapi_sqlalchemy.cli migration showmigrations
```

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for complete migration documentation.

### Modular Migrations (Django-style)

Organize migrations per app/feature module:

```bash
# Initialize migrations for specific app
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations

# Create migrations for specific app
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations "Add users table"

# Apply all migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

See [MODULAR_MIGRATIONS.md](./MODULAR_MIGRATIONS.md) for modular migration documentation.

## Quick Start

### 1. Configure Database Connection

```python
from fastapi import FastAPI
from fastapi_sqlalchemy import db_settings, connection_manager, DB

app = FastAPI()

# Load database configurations
db_settings.load_from_dict({
    "default": {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "myapp",
        "username": "postgres",
        "password": "secret",
        "pool_size": 10,
        "max_overflow": 20,
    },
    "analytics": {
        "driver": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "analytics",
        "username": "analytics_user",
        "password": "analytics_pass",
    }
}, default="default")

# Initialize connections on startup
@app.on_event("startup")
async def startup():
    await connection_manager.initialize()

@app.on_event("shutdown")
async def shutdown():
    await connection_manager.close_all()
```

### 2. Define Your Models

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3. Use in Your Routes

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_sqlalchemy import DB, connection_manager

async def get_db() -> DB:
    async with connection_manager.session() as session:
        yield DB(session)

@app.get("/users")
async def list_users(db: DB = Depends(get_db)):
    users = await db.table(User).where(User.active == True).all()
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: DB = Depends(get_db)):
    user = await db.table(User).find(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users")
async def create_user(user_data: dict, db: DB = Depends(get_db)):
    user = await db.table(User).create(user_data)
    return user
```

## API Reference

### Configuration

#### db_settings

Configuration manager for database connections.

```python
from fastapi_sqlalchemy import db_settings

# Load configurations
db_settings.load_from_dict({
    "default": {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "myapp",
        "username": "postgres",
        "password": "secret"
    }
}, default="default")

# Get config
config = db_settings.get_config("default")

# Switch default connection
db_settings.switch("analytics")
```

### Query Builder

#### SELECT Operations

##### all() - Get all records

```python
users = await db.table(User).all()
# Returns: List[Dict[str, Any]]

users = await db.table(User).where(User.active == True).all()
```

##### first() - Get first record

```python
user = await db.table(User).first()
# Returns: Optional[Dict[str, Any]]

user = await db.table(User).where(User.email == "test@example.com").first()
```

##### find(id) - Find by primary key

```python
user = await db.table(User).find(1)
# Returns: Optional[Dict[str, Any]]

if user:
    print(user["name"])
```

##### find_or_fail(id) - Find by ID or raise error

```python
user = await db.table(User).find_or_fail(1)
# Returns: Dict[str, Any]
# Raises: ValueError if not found
```

##### paginate(page, per_page) - Paginated results

```python
result = await db.table(User).paginate(page=1, per_page=20)
# Returns: {"items": [...], "pagination": {...}}

items = result["items"]
pagination = result["pagination"]
print(pagination["total_records"])
print(pagination["total_pages"])
```

#### WHERE Conditions

##### where() - AND conditions

```python
users = await db.table(User)\
    .where(User.active == True)\
    .where(User.age > 18)\
    .all()
```

##### or_where() - OR conditions

```python
users = await db.table(User)\
    .where(User.role == "admin")\
    .or_where(User.role == "moderator")\
    .all()
```

##### where_in() - IN clause

```python
users = await db.table(User).where_in(User.id, [1, 2, 3]).all()
```

##### where_not_in() - NOT IN clause

```python
users = await db.table(User)\
    .where_not_in(User.status, ["banned", "suspended"])\
    .all()
```

##### where_null() / where_not_null() - NULL checks

```python
users = await db.table(User).where_null(User.deleted_at).all()
users = await db.table(User).where_not_null(User.email_verified_at).all()
```

##### where_between() - Range queries

```python
posts = await db.table(Post)\
    .where_between(Post.views, [100, 1000])\
    .all()
```

##### where_like() - Pattern matching

```python
users = await db.table(User)\
    .where_like(User.email, "gmail")\
    .all()
# SQL: WHERE email ILIKE '%gmail%'
```

##### apply_filters() - Dynamic filters with Laravel-like syntax

**NEW!** Apply multiple filters dynamically with `table.column__operator` syntax:

```python
# Basic filters on single table
users = await db.table(User)\
    .apply_filters({
        "user.active__eq": True,
        "user.age__gte": 18,
        "user.age__lte": 65
    })\
    .all()

# Text search (LIKE)
users = await db.table(User)\
    .apply_filters({"user.email__like": "gmail"})\
    .all()

# IN clause
users = await db.table(User)\
    .apply_filters({"user.id__in": [1, 2, 3, 4, 5]})\
    .all()

# With joins - filter multiple tables
results = await db.table(User)\
    .left_join(Post, User.id == Post.user_id)\
    .apply_filters({
        "user.active__eq": True,
        "post.published__eq": True
    })\
    .all()

# OR logic
users = await db.table(User)\
    .apply_filters(
        {"user.role__eq": "admin"},
        use_or=True
    )\
    .apply_filters(
        {"user.role__eq": "moderator"},
        use_or=True
    )\
    .all()
```

**Available operators:**
- `eq`, `ne`, `neq` - Equal, not equal
- `gt`, `gte`, `lt`, `lte` - Comparison
- `like`, `icontains` - Pattern matching
- `in`, `notin` - In/not in lists
- `startswith`, `endswith` - String matching
- `between`, `not_between` - Range queries
- `isnull`, `notnull` - NULL checks

**Dynamic filtering from request:**

```python
@app.get("/users")
async def list_users(
    active: bool = None,
    age_min: int = None,
    age_max: int = None,
    search: str = None
):
    filters = {}
    if active is not None:
        filters["user.active__eq"] = active
    if age_min:
        filters["user.age__gte"] = age_min
    if age_max:
        filters["user.age__lte"] = age_max
    if search:
        filters["user.email__like"] = search
    
    users = await db.table(User)\
        .apply_filters(filters)\
        .all()
    
    return users
```

#### JOIN Operations

##### join() / inner_join() - INNER JOIN

```python
posts = await db.table(Post)\
    .join(User, Post.user_id == User.id)\
    .select(Post.title, User.name)\
    .all()
```

##### left_join() - LEFT OUTER JOIN

```python
users = await db.table(User)\
    .left_join(Post, User.id == Post.user_id)\
    .select(User.name, Post.title)\
    .all()
```

##### right_join() / full_join() - RIGHT/FULL OUTER JOIN

```python
results = await db.table(User).right_join(Post, User.id == Post.user_id).all()
results = await db.table(User).full_join(Post, User.id == Post.user_id).all()
```

#### CREATE Operations

##### create(data) - Insert single record

```python
user = await db.table(User).create({
    "name": "John Doe",
    "email": "john@example.com",
    "active": True
})
print(user["id"])  # Access the generated ID
```

##### create_many(data_list) - Insert multiple records

```python
users = await db.table(User).create_many([
    {"name": "John", "email": "john@example.com"},
    {"name": "Jane", "email": "jane@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
])
```

#### UPDATE Operations

##### update(data) - Update with WHERE clause

```python
updated = await db.table(User)\
    .where(User.id == 1)\
    .update({"name": "Jane", "active": False})

print(updated[0]["name"])
```

##### update_by_id(id, data) - Update by ID

```python
user = await db.table(User).update_by_id(1, {
    "name": "Jane",
    "active": False
})
```

#### DELETE Operations

##### delete() - Delete with WHERE clause

```python
deleted_count = await db.table(User)\
    .where(User.active == False)\
    .delete()

print(f"Deleted {deleted_count} users")
```

##### delete_by_id(id) - Delete by ID

```python
deleted = await db.table(User).delete_by_id(1)
```

#### Aggregates

```python
# Count
total = await db.table(User).count()
active = await db.table(User).where(User.active == True).count()

# Sum, Avg, Min, Max
total_views = await db.table(Post).sum(Post.views)
avg_score = await db.table(Post).avg(Post.score)
min_price = await db.table(Product).min(Product.price)
max_price = await db.table(Product).max(Product.price)

# Exists
has_active = await db.table(User).where(User.active == True).exists()
```

#### Ordering & Limiting

```python
users = await db.table(User)\
    .order_by(User.created_at.desc())\
    .limit(10)\
    .offset(20)\
    .all()

# Or use aliases
users = await db.table(User)\
    .order_by(User.name)\
    .take(10)\
    .skip(20)\
    .all()
```

#### GROUP BY & HAVING

```python
stats = await db.table(Post)\
    .select(Post.user_id, func.count(Post.id).label('post_count'))\
    .group_by(Post.user_id)\
    .having(func.count(Post.id) > 5)\
    .all()
```

### Transactions

#### Context Manager

```python
async with db.transaction():
    user = await db.table(User).create({"name": "John"})
    post = await db.table(Post).create({
        "user_id": user["id"],
        "title": "Hello"
    })
    # Auto-commits on success, auto-rollback on error
```

#### Manual Control

```python
await db.begin_transaction()
try:
    user = await db.table(User).create({"name": "John"})
    await db.commit()
except Exception:
    await db.rollback()
```

### Decorators

Use decorators for automatic session management:

```python
from fastapi_sqlalchemy import with_db, with_transaction

@with_db()
async def process_users(db: DB):
    users = await db.table(User).all()
    return users

@with_transaction()
async def create_user_with_posts(db: DB, user_data: dict):
    user = await db.table(User).create(user_data)
    posts = await db.table(Post).create_many(posts_data)
    return user
```

### SQL Debugging

View generated SQL queries:

```python
query = db.table(User)\
    .left_join(Post, User.id == Post.user_id)\
    .where(User.active == True)\
    .order_by(User.name)

# Print SQL
query.print_sql()
query.print_formatted_sql()

# Get SQL as string
sql = query.to_sql()
```

## Complete Examples

### FastAPI Service Layer

```python
class UserService:
    def __init__(self, db: DB):
        self.db = db

    async def get_all(self, page: int = 1, per_page: int = 20):
        return await self.db.table(User)\
            .where(User.active == True)\
            .order_by(User.created_at.desc())\
            .paginate(page=page, per_page=per_page)

    async def get_by_email(self, email: str):
        return await self.db.table(User)\
            .where(User.email == email)\
            .first()

    async def create(self, data: dict):
        return await self.db.table(User).create(data)

    async def update(self, user_id: int, data: dict):
        return await self.db.table(User)\
            .where(User.id == user_id)\
            .update(data)

    async def delete(self, user_id: int):
        return await self.db.table(User)\
            .where(User.id == user_id)\
            .delete()
```

### FastAPI Routes

```python
@app.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: DB = Depends(get_db)
):
    service = UserService(db)
    result = await service.get_all(page=page, per_page=per_page)
    return result

@app.post("/users")
async def create_user(user_data: UserCreate, db: DB = Depends(get_db)):
    service = UserService(db)
    return await service.create(user_data.dict())

@app.put("/users/{user_id}")
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: DB = Depends(get_db)
):
    service = UserService(db)
    updated = await service.update(user_id, user_data.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated[0]

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: DB = Depends(get_db)):
    service = UserService(db)
    deleted = await service.delete(user_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}
```

## Best Practices

1. **Always use transactions for related operations**
   ```python
   async with db.transaction():
       user = await db.table(User).create(user_data)
       await db.table(Profile).create({"user_id": user["id"]})
   ```

2. **Use pagination for large datasets**
   ```python
   result = await db.table(User).paginate(page=1, per_page=20)
   ```

3. **Validate database exists before use**
   ```python
   if not connection_manager._initialized:
       await connection_manager.initialize()
   ```

4. **Use connection pooling in production**
   ```python
   config = {
       "pool_size": 20,
       "max_overflow": 40,
       "pool_pre_ping": True
   }
   ```

5. **Handle errors gracefully**
   ```python
   try:
       user = await db.table(User).find_or_fail(999)
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   ```

## Advanced Features

### Dynamic Schema Switching (PostgreSQL)

Switch PostgreSQL schemas per request dynamically:

```python
from fastapi import Header
from typing import Optional

async def get_schema_from_header(x_schema: Optional[str] = Header(None)):
    return x_schema or "public"

@app.get("/users")
async def list_users(schema: str = Depends(get_schema_from_header)):
    # Use specific schema for this request
    async with connection_manager.session(schema=schema) as session:
        db = DB(session)
        users = await db.table(User).all()
        return users

# Usage:
# curl http://localhost:8000/users
# curl -H "X-Schema: tenant_001" http://localhost:8000/users
```

### ORM Loading Strategies

Use SQLAlchemy ORM features for performance:

```python
from sqlalchemy.orm import joinedload, selectinload

# Load relationships eagerly
users = await db.table(User)\
    .options(joinedload(User.posts))\
    .all()

# Load specific columns only
users = await db.table(User)\
    .load_only(User.id, User.username, User.email)\
    .all()

# Multiple loading strategies
users = await db.table(User)\
    .options(
        joinedload(User.posts),
        selectinload(User.comments)
    )\
    .all()
```

### Eloquent-Style Models

Create models that work like Laravel Eloquent. **BaseModel has access to ALL TableQuery methods!**

```python
from fastapi_sqlalchemy import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship, joinedload

class User(BaseModel):
    """Eloquent-style model with static methods."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    active = Column(Boolean, default=True)
    
    # Relationships
    posts = relationship("Post", back_populates="user")

# Direct model methods (common operations)
users = await User.all()           # Get all users
user = await User.find(1)           # Find by ID
user = await User.first()           # Get first user
count = await User.count()         # Count records

# Query builder chaining
users = await User.where(User.active == True)\
                  .order_by(User.username)\
                  .limit(10)\
                  .all()

# JOIN operations
users = await User.left_join(Post, User.id == Post.user_id)\
                  .select(User.username, Post.title)\
                  .all()

# ORM loading strategies
users = await User.options(joinedload(User.posts))\
                  .load_only(User.id, User.username)\
                  .all()

# Access ALL TableQuery methods via query()
users = await User.query()\
                  .where_in(User.id, [1, 2, 3])\
                  .where_between(User.created_at, [start, end])\
                  .distinct_by(User.username)\
                  .group_by(User.status)\
                  .having(func.count(User.id) > 5)\
                  .all()

# Dynamic filters with apply_filters (Laravel-like)
users = await User.apply_filters({
    "user.active__eq": True,
    "user.age__gte": 18,
    "user.email__like": "gmail"
}).all()

# With joins
users = await User.left_join(Post, User.id == Post.user_id)\
                  .apply_filters({
                      "user.active__eq": True,
                      "post.published__eq": True
                  })\
                  .all()

# CRUD operations
user = await User.create({"username": "john", "email": "john@example.com"})
user = await User.update_by_id(1, {"active": False})
deleted = await User.delete_by_id(1)

# Pagination
result = await User.where(User.active == True).paginate(page=1, per_page=20)
```

**Note**: All methods that return `TableQuery` can be chained with any other TableQuery method. Use `User.query()` for full access to ALL 100+ query builder methods.

### Using Decorators with Models

```python
from fastapi_sqlalchemy import with_transaction

@with_transaction()
async def create_user_complete(db: DB):
    # Auto session management
    User.set_session(db.session)
    
    user = await User.create({"username": "john", "email": "john@example.com"})
    post = await db.table(Post).create({"user_id": user["id"], "title": "Hello"})
    return user
```

### Multi-Tenancy with Schema Switching

```python
@app.get("/tenants/{tenant_id}/users")
async def get_tenant_users(tenant_id: str):
    """Get users from tenant's schema."""
    tenant_schema = f"tenant_{tenant_id}"
    
    async with connection_manager.session(schema=tenant_schema) as session:
        db = DB(session)
        User.set_session(session)
        
        users = await User.all()
        return users
```

## Supported Databases

- ✅ PostgreSQL (via asyncpg)
- ✅ MySQL (via aiomysql)
- ✅ SQLite (via aiosqlite)

## Examples

See the examples directory for complete examples:

- **`examples/advanced_usage.py`** - Schema switching, Eloquent-style models, ORM strategies, Multi-tenancy
- **`examples/apply_filters_examples.py`** - Complete guide to using `apply_filters()` with Laravel-like syntax
- **`examples/advanced_system_examples.py`** - Complete guide with joins, subqueries, CTEs, unions, and complex queries

### Quick Examples

#### apply_filters - Dynamic Filtering

```python
# Single table
users = await User.apply_filters({
    "user.active__eq": True,
    "user.age__gte": 18,
    "user.email__like": "gmail"
}).all()

# With joins - filter multiple tables
users = await User.left_join(Post, User.id == Post.user_id)\
                  .apply_filters({
                      "user.active__eq": True,
                      "post.published__eq": True
                  })\
                  .all()
```

#### Complex Joins and Subqueries

```python
# Multiple joins
results = await User\
    .left_join(Profile, User.id == Profile.user_id)\
    .left_join(Post, User.id == Post.user_id)\
    .left_join(Comment, Post.id == Comment.post_id)\
    .select(User.username, Profile.bio, Post.title)\
    .all()

# Subquery in WHERE IN
users = await User.where_in_subquery(
    User.id,
    lambda: db.query()
              .table(Post)
              .select(Post.user_id)
              .where(Post.published == True)
).all()

# EXISTS subquery
users = await User.where_exists_subquery(
    lambda: db.query()
              .table(Post)
              .where(Post.user_id == User.id)
).all()

# Use subquery as table (CTE-like)
stats = await db.table(User)\
    .from_subquery(
        "user_stats",
        lambda: db.query()
              .table(User)
              .select(User.id, func.count(Post.id).label("post_count"))
              .left_join(Post, User.id == Post.user_id)
              .group_by(User.id)
    )\
    .all()
```

#### Complex Aggregations

```python
# User statistics with multiple aggregates
stats = await db.table(User)\
    .select(
        User.id,
        User.username,
        func.count(Post.id.distinct()).label("post_count"),
        func.count(Comment.id.distinct()).label("comment_count"),
        func.sum(Post.views).label("total_views")
    )\
    .left_join(Post, User.id == Post.user_id)\
    .left_join(Comment, Post.id == Comment.post_id)\
    .group_by(User.id)\
    .order_by(func.count(Post.id).desc())\
    .all()
```

#### UNION Queries

```python
# Combine queries with UNION
q1 = db.table(User).select(User.username).where(User.active == True)
q2 = db.table(Post).select(Post.title).where(Post.published == True)

results = await db.query().table(q1).union(q2).all()
```

See `examples/advanced_system_examples.py` for 20+ complete examples of:
- Multiple joins
- Subqueries (IN, EXISTS, FROM)
- CTEs and Common Table Expressions
- Complex aggregations
- Window functions
- CASE statements
- Hierarchical queries
- Performance optimization
- Real-world business logic

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
