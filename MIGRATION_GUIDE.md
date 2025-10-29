# Migration Guide - Django-like Migrations with Alembic

This guide explains how to use the migration system in FastAPI SQLAlchemy, which provides Django-like migration commands powered by Alembic.

## Overview

The migration system allows you to:
- Create migration files from model changes (autogenerate)
- Apply migrations to update your database schema
- Track migration history
- Rollback (downgrade) migrations
- Work with multiple databases

## Quick Start

### 1. Initialize Migrations

First, initialize Alembic in your project:

```bash
python -m fastapi_sqlalchemy.cli migration init
```

This creates:
- `alembic.ini` - Alembic configuration file
- `migrations/` directory - Where migration files are stored
- `migrations/versions/` - Migration version files
- `migrations/env.py` - Migration environment configuration
- `migrations/script.py.mako` - Migration template

### 2. Create Your Models

Define your SQLAlchemy models in your project:

```python
from fastapi_sqlalchemy import BaseModel
from sqlalchemy import Column, Integer, String

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    email = Column(String(255))
```

### 3. Create Migration Files

Generate migration files from your model changes:

```bash
python -m fastapi_sqlalchemy.cli migration makemigrations
```

Or with a custom message:

```bash
python -m fastapi_sqlalchemy.cli migration makemigrations "Add users table"
```

This creates a new migration file in `migrations/versions/` with:
- Auto-detected schema changes
- Upgrade and downgrade functions
- Timestamp and revision ID

### 4. Apply Migrations

Apply migrations to update your database:

```bash
python -m fastapi_sqlalchemy.cli migration migrate
```

This executes all pending migrations and updates your database schema.

### 5. Check Migration Status

View migration history:

```bash
python -m fastapi_sqlalchemy.cli migration showmigrations
```

### 6. Downgrade (Rollback)

Rollback to a previous migration:

```bash
# Rollback one migration
python -m fastapi_sqlalchemy.cli migration downgrade -1

# Rollback to specific revision
python -m fastapi_sqlalchemy.cli migration downgrade abc123def456
```

## Configuration

### Database Connection

Migrations automatically use the connection configured in `db_settings`:

```python
from fastapi_sqlalchemy import db_settings

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
```

### Import Your Models

Update `migrations/env.py` to import all your models:

```python
# In migrations/env.py, add your model imports:

from your_app.models import User, Post, Comment
from fastapi_sqlalchemy.base_model import Base

# This ensures models are registered with Alembic's autogenerate
```

## Advanced Usage

### Manual Migration Files

You can create migrations manually by editing the generated files:

```python
# In a migration file
def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
```

### Multiple Database Connections

For projects with multiple databases:

```python
from fastapi_sqlalchemy import MigrationManager

# Create migrations for specific connection
manager = MigrationManager()
await manager.init()

# The manager will use the default connection from db_settings
await manager.makemigrations()
await manager.migrate()
```

### Custom Alembic Configuration

Edit `alembic.ini` to customize:

- File template
- Migration location
- Database URL (overridden by connection_manager)
- Logging configuration

## Common Workflows

### Adding a New Model

1. Create the model class
2. Run `makemigrations`
3. Review the generated migration
4. Run `migrate`

### Modifying an Existing Model

1. Update the model class
2. Run `makemigrations`
3. Review the changes
4. Run `migrate`

### Adding a Column

```python
# In your model
class User(BaseModel):
    __tablename__ = "users"
    # ... existing columns ...
    age = Column(Integer)  # New column
```

```bash
python -m fastapi_sqlalchemy.cli migration makemigrations "Add age column"
python -m fastapi_sqlalchemy.cli migration migrate
```

### Removing a Column

```python
# Remove the column from model
class User(BaseModel):
    __tablename__ = "users"
    # age column removed
```

```bash
python -m fastapi_sqlalchemy.cli migration makemigrations "Remove age column"
python -m fastapi_sqlalchemy.cli migration migrate
```

## Troubleshooting

### Autogenerate Not Detecting Changes

1. Make sure your models are imported in `migrations/env.py`
2. Check that models inherit from `BaseModel` or `Base`
3. Verify the model is properly defined with `__tablename__`

### Migration Conflicts

If multiple developers create migrations:

1. Pull latest changes
2. Check for conflicts with `showmigrations`
3. Merge branches if necessary
4. Generate a merge migration if needed

### Database Out of Sync

If database is out of sync with migrations:

1. Check current revision: `showmigrations`
2. Manually fix database schema
3. Stamp the database: Update alembic_version table

### Rollback Issues

If rollback fails:

1. Check the downgrade function in the migration file
2. Manually fix any data inconsistencies
3. Ensure all foreign keys are properly handled

## Best Practices

1. **Review Generated Migrations**: Always review autogenerated migrations before applying
2. **Use Descriptive Messages**: Provide meaningful messages when creating migrations
3. **Test Migrations**: Test migrations in development before production
4. **Backup Database**: Always backup production database before migrations
5. **Atomic Migrations**: Keep migrations small and focused
6. **Version Control**: Commit migration files to version control
7. **Migration Order**: Apply migrations in order on all environments

## Command Reference

```bash
# Initialize Alembic
python -m fastapi_sqlalchemy.cli migration init

# Create migration files
python -m fastapi_sqlalchemy.cli migration makemigrations [message]

# Apply migrations
python -m fastapi_sqlalchemy.cli migration migrate [revision]

# Show migration history
python -m fastapi_sqlalchemy.cli migration showmigrations

# Downgrade migrations
python -m fastapi_sqlalchemy.cli migration downgrade [revision]
```

## Integration with FastAPI

```python
from fastapi import FastAPI
from fastapi_sqlalchemy import db_settings, connection_manager

app = FastAPI()

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
    # Migrations are run manually via CLI
```

## Example Project Structure

```
my_project/
├── alembic.ini
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 2024_01_15_1200-abc123_add_users_table.py
│       └── 2024_01_16_1400-def456_add_posts_table.py
├── my_app/
│   ├── models.py          # Your models
│   └── main.py           # FastAPI app
└── main.py
```

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Base Model Usage](./BASE_MODEL_USAGE.md)
- [README](./README.md)
