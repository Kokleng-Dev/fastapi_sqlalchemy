# Using FastAPI SQLAlchemy in Your Projects

This guide shows you how to use this library in your own FastAPI projects.

## Installation Methods

### Method 1: Install from PyPI (After Publishing)

```bash
pip install fastapi-sqlalchemy
# or with uv
uv add fastapi-sqlalchemy
```

### Method 2: Install from Local Development

If you're developing the library or want to use it locally:

```bash
# From the library root directory
pip install -e .
# or with uv
uv pip install -e .
```

### Method 3: Add as Dependency in pyproject.toml

In your project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "fastapi-sqlalchemy>=0.1.0",
]
```

## Quick Start in Your Project

### 1. Project Structure

```
my_project/
├── pyproject.toml
├── main.py
├── models.py          # Your models
└── apps/
    ├── users/
    │   ├── migrations/
    │   ├── models.py
    │   └── routes.py
    └── products/
        ├── migrations/
        ├── models.py
        └── routes.py
```

### 2. Create Your FastAPI App

**main.py:**
```python
from fastapi import FastAPI
from fastapi_sqlalchemy import db_settings, connection_manager

app = FastAPI()

# Configure database
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

@app.on_event("startup")
async def startup():
    await connection_manager.initialize()
    print("✓ Database initialized")

@app.on_event("shutdown")
async def shutdown():
    await connection_manager.close_all()
```

### 3. Define Your Models

**models.py:**
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from fastapi_sqlalchemy import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)

class Post(BaseModel):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    content = Column(String)
```

### 4. Use in Routes

**routes.py:**
```python
from fastapi import APIRouter, Depends
from fastapi_sqlalchemy import connection_manager, DB
from .models import User

router = APIRouter()

@router.get("/users")
async def get_users():
    async with connection_manager.session() as session:
        db = DB(session)
        users = await db.table(User).all()
        return users

@router.post("/users")
async def create_user(data: dict):
    async with connection_manager.session() as session:
        db = DB(session)
        user = await db.table(User).create(data)
        return user
```

### 5. Set Up Migrations

```bash
# Initialize migrations
python -m fastapi_sqlalchemy.cli migration init

# Or use modular migrations
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations

# Import your models in migrations/env.py
# from models import User, Post

# Create migrations
python -m fastapi_sqlalchemy.cli migration makemigrations

# Apply migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Using Modular Migrations

### Structure for Modular App

```
my_project/
├── pyproject.toml
├── main.py
├── apps/
│   ├── users/
│   │   ├── migrations/
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   ├── models.py
│   │   └── routes.py
│   └── products/
│       This is a structure with explicit migrations directories:
│       └── migrations/
│           └── versions/
│               └── 001_initial.py (created by makemigrations)
```

### Initialize Modular Migrations

```bash
# For users app
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations

# For products app
python -m fastapi_sqlalchemy.cli migration init apps/products/migrations
```

### Import Models in Each App's env.py

**apps/users/migrations/env.py:**
```python
# Add this to your env.py
from apps.users.models import User
```

**apps/products/migrations/env.py:**
```python
# Add this to your env.py
from apps.products.models import Product
```

### Create and Apply Migrations

```bash
# Create migrations for users
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations

# Create migrations for products
python -m fastapi_sqlalchemy.cli migration makemigrations apps/products/migrations

# Apply all migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Example: Complete Project

### Complete Project Structure

```
my_blog/
├── pyproject.toml
├── main.py
├── alembic.ini
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── post.py
│   └── comment.py
├── routes/
│   ├── __init__.py
│   ├── users.py
│   ├── posts.py
│   └── comments.py
└── config/
    └── database.py
```

### database.py

```python
from fastapi_sqlalchemy import db_settings, connection_manager

def setup_database():
    db_settings.load_from_dict({
        "default": {
            "driver": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "myblog",
            "username": "postgres",
            "password": "secret"
        }
    }, default="default")
    
    return connection_manager
```

### models/user.py

```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from fastapi_sqlalchemy import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### routes/users.py

```python
from fastapi import APIRouter, Depends
from fastapi_sqlalchemy import connection_manager, DB, with_db
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def list_users():
    async with connection_manager.session() as session:
        db = DB(session)
        users = await db.table(User).all()
        return users

@router.get("/{user_id}")
async def get_user(user_id: int):
    async with connection_manager.session() as session:
        db = DB(session)
        user = await db.table(User).find(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

@router.post("/")
async def create_user(user_data: dict):
    async with connection_manager.session() as session:
        db = DB(session)
        user = await db.table(User).create(user_data)
        return user

# Using decorator pattern
from fastapi_sqlalchemy import with_transaction

@with_transaction()
async def create_user_with_posts(db: DB, user_data: dict):
    """Auto transaction handling."""
    user = await db.table(User).create(user_data)
    return user
```

### main.py

```python
from fastapi import FastAPI
from config.database import setup_database
from routes import users, posts, comments

app = FastAPI()

# Setup database
db_manager = setup_database()

@app.on_event("startup")
async def startup():
    await db_manager.initialize()
    print("✓ Database initialized")

@app.on_event("shutdown")
async def shutdown():
    await db_manager.close_all()

# Include routers
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Environment Variables

For production, use environment variables:

```python
import os
from fastapi_sqlalchemy import db_settings

db_settings.load_from_dict({
    "default": {
        "driver": os.getenv("DB_DRIVER", "postgresql"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "myapp"),
        "username": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "secret")
    }
}, default="default")
```

## Best Practices

### 1. Separate Models

Keep models in separate files for better organization.

### 2. Use Dependency Injection

```python
from fastapi import Depends
from fastapi_sqlalchemy import connection_manager

async def get_db():
    async with connection_manager.session() as session:
        yield DB(session)

@router.get("/users")
async def get_users(db: DB = Depends(get_db)):
    users = await db.table(User).all()
    return users
```

### 3. Use Decorators for Transactions

```python
from fastapi_sqlalchemy import with_transaction

@with_transaction()
async def create_user_with_posts(db: DB, user_data: dict, posts_data: list):
    user = await db.table(User).create(user_data)
    for post_data in posts_data:
        post_data["user_id"] = user["id"]
    await db.table(Post).create_many(posts_data)
    return user
```

### 4. Environment-Specific Configurations

```python
import os

ENV = os.getenv("ENVIRONMENT", "development")

configs = {
    "development": {
        "host": "localhost",
        "database": "myapp_dev"
    },
    "production": {
        "host": "prod-db.example.com",
        "database": "myapp_prod"
    }
}

db_config = configs[ENV]
```

## CLI Usage in Projects

After installing the library, you can use the CLI:

```bash
# Check if installed correctly
python -m fastapi_sqlalchemy.cli --help

# Initialize migrations
python -m fastapi_sqlalchemy.cli migration init

# Create migrations
python -m fastapi_sqlalchemy.cli migration makemigrations

# Apply migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Troubleshooting

### Import Errors

If you get import errors, make sure the library is installed:

```bash
pip install -e .  # From library directory
```

### Migration Errors

Make sure models are imported in `migrations/env.py`:

```python
# migrations/env.py
from models.user import User
from models.post import Post
from fastapi_sqlalchemy.base_model import Base
```

### Connection Errors

Verify database configuration matches your actual database settings.

## Next Steps

- See [README.md](./README.md) for full documentation
- See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for migration details
- See [MODULAR_MIGRATIONS.md](./MODULAR_MIGRATIONS.md) for modular migrations
