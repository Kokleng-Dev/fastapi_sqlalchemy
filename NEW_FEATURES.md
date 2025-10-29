# New Features Summary

## What Was Added

### 1. Dynamic Schema Switching (PostgreSQL)

**File**: `fastapi_sqlalchemy/connection.py`

Added support for switching PostgreSQL schemas dynamically per request:

```python
# Usage
async with connection_manager.session(schema="tenant_001") as session:
    db = DB(session)
    users = await db.table(User).all()
```

**How it works**:
- Sessions accept a `schema` parameter
- When provided, executes `SET search_path TO {schema}` for PostgreSQL
- Enables multi-tenant applications where each tenant uses a different schema

### 2. ORM Loading Strategies

**File**: `fastapi_sqlalchemy/table_query.py`

Added SQLAlchemy ORM features to the query builder:

**New Methods**:
- `with_orm(enabled=True)` - Enable ORM mode (returns SQLAlchemy objects)
- `options(*load_strategies)` - Add SQLAlchemy loading options
- `load_only(*columns)` - Load only specific columns
- `select_related(*relationships)` - Django-like eager loading

**Usage**:
```python
# Load relationships eagerly
from sqlalchemy.orm import joinedload
users = await db.table(User).options(joinedload(User.posts)).all()

# Load only specific columns
users = await db.table(User).load_only(User.id, User.name).all()

# ORM mode returns SQLAlchemy objects
user = await db.table(User).with_orm().find(1)
```

### 3. Eloquent-Style Models (Laravel-like ORM)

**File**: `fastapi_sqlalchemy/base_model.py`

Created a `BaseModel` class that allows models to have static methods like Laravel Eloquent:

**Features**:
- Static methods: `User.all()`, `User.find(1)`, `User.first()`, etc.
- Query builder: `User.where(User.active == True).all()`
- CRUD operations: `User.create()`, `User.update_by_id()`, `User.delete_by_id()`
- Schema switching per request
- Multi-connection support

**Usage**:
```python
from fastapi_sqlalchemy import BaseModel
from sqlalchemy import Column, Integer, String, Boolean

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    email = Column(String(255))
    active = Column(Boolean, default=True)

# Use like Laravel
users = await User.all()
user = await User.find(1)
user = await User.create({"username": "john", "email": "john@example.com"})
```

### 4. Examples

**File**: `examples/advanced_usage.py`

Created comprehensive examples showing:
- Schema switching per request
- Eloquent-style model usage
- ORM loading strategies
- Multi-tenant applications
- Decorators with models
- Complete FastAPI integration

### 5. Updated Documentation

**Files**: `README.md`

Added sections for:
- Dynamic schema switching
- ORM loading strategies
- Eloquent-style models
- Multi-tenancy examples
- Decorator usage with models

## Changes Made to Existing Files

### `fastapi_sqlalchemy/connection.py`
- Added `schema` parameter to `session()` method
- Executes PostgreSQL `SET search_path` for schema switching

### `fastapi_sqlalchemy/table_query.py`
- Added `_load_options` for ORM loading strategies
- Added `_enable_orm` flag for ORM mode
- Added methods: `with_orm()`, `options()`, `load_only()`, `select_related()`

### `fastapi_sqlalchemy/__init__.py`
- Exported new classes: `BaseModel`, `Base`, `create_model`, `setup_model_session`

## Usage Examples

### Schema Switching

```python
@app.get("/users")
async def list_users(schema: str = "public"):
    async with connection_manager.session(schema=schema) as session:
        db = DB(session)
        users = await db.table(User).all()
        return users

# Multi-tenant
@app.get("/tenants/{tenant_id}/users")
async def get_tenant_users(tenant_id: str):
    async with connection_manager.session(schema=f"tenant_{tenant_id}") as session:
        db = DB(session)
        users = await db.table(User).all()
        return users
```

### ORM Loading

```python
from sqlalchemy.orm import joinedload, selectinload

# Eager load relationships
users = await db.table(User)\
    .options(joinedload(User.posts))\
    .all()

# Load specific columns
users = await db.table(User)\
    .load_only(User.id, User.username)\
    .all()
```

### Eloquent-Style Models

```python
# Setup session (in middleware or dependency)
async with connection_manager.session() as session:
    User.set_session(session)
    
    # Use models directly
    users = await User.all()
    user = await User.find(1)
    user = await User.create({"username": "john"})
```

## Benefits

1. **Schema Switching**: Perfect for multi-tenant applications
2. **ORM Features**: Better performance with eager loading
3. **Eloquent-Style**: Familiar API for Laravel developers
4. **Flexibility**: Mix query builder and ORM as needed

## Migration Guide

### For Existing Users

No breaking changes! All existing code continues to work.

**To use new features**:

1. **Schema switching**: Just add `schema` parameter to `connection_manager.session()`
2. **ORM features**: Add `.options()`, `.load_only()`, etc. to existing queries
3. **Eloquent models**: Inherit from `BaseModel` instead of SQLAlchemy's `Base`

```python
# Before
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class User(Base):
    ...

# After
from fastapi_sqlalchemy import BaseModel
class User(BaseModel):
    ...
    # Now can use User.all(), User.find(1), etc.
```

## Testing

To test the new features:

```bash
# Install dependencies
pip install -r requirements.txt

# Run examples
cd examples
python advanced_usage.py
```

## Next Steps

1. Add support for MySQL and SQLite schema switching
2. Add more ORM loading strategies (subqueryload, etc.)
3. Add relationship helpers to BaseModel
4. Add model factories for testing
5. Add migration support

