# Modular Migrations Feature - Summary

## What Was Added

You can now create migrations in specific folders for each feature/app, just like Django!

## Quick Reference

### Basic Commands

**Centralized migrations (default):**
```bash
python -m fastapi_sqlalchemy.cli migration init
python -m fastapi_sqlalchemy.cli migration makemigrations
python -m fastapi_sqlalchemy.cli migration migrate
```

**Modular migrations (Django-style):**
```bash
# Initialize for specific app
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations

# Create migrations for specific app
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations "Message"

# Apply all migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Project Structure Example

```
my_project/
├── alembic.ini
├── apps/
│   ├── users/
│   │   ├── migrations/          # Users-specific migrations
│   │   │   ├── env.py
│   │   │   ├── versions/
│   │   │   │   ├── 001_initial.py
│   │   │   │   └── 002_add_email.py
│   │   ├── models.py
│   │   └── routes.py
│   ├── products/
│   │   ├── migrations/          # Products-specific migrations
│   │   │   ├── env.py
│   │   │   ├── versions/
│   │   │   │   └── 001_initial.py
│   │   ├── models.py
│   │   └── routes.py
│   └── orders/
│       ├── migrations/          # Orders-specific migrations
│       ├── models.py
│       └── routes.py
└── main.py
```

## How It Works

1. **Auto-detects app name** from path
   - `apps/users/migrations` → app name: `users`
   - `apps/products/migrations` → app name: `products`

2. **Creates isolated migrations** per app
   - Each app has its own `migrations/versions/` folder
   - Each app tracks its own migration history

3. **Shared alembic.ini** for all apps
   - One configuration file
   - Multiple migration directories

4. **Apply all at once**
   - Run `migrate` to apply all migrations from all apps
   - Or apply specific app migrations using the manager

## Usage Examples

### Example 1: Simple Modular Setup

```bash
# Step 1: Create app structure
mkdir -p apps/users/migrations/versions
mkdir -p apps/products/migrations/versions

# Step 2: Initialize migrations for each app
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations
python -m fastapi_sqlalchemy.cli migration init apps/products/migrations

# Step 3: Create models
# apps/users/models.py
# apps/products/models.py

# Step 4: Edit env.py in each app to import models
# In apps/users/migrations/env.py:
# from apps.users.models import User

# In apps/products/migrations/env.py:
# from apps.products.models import Product

# Step 5: Create migrations
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations
python -m fastapi_sqlalchemy.cli migration makemigrations apps/products/migrations

# Step 6: Apply all migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

### Example 2: Using MigrationManager in Code

```python
from fastapi_sqlalchemy import MigrationManager

# Users app migrations
user_manager = MigrationManager(migrations_dir="apps/users/migrations")
await user_manager.init()
await user_manager.makemigrations("Add email verification")

# Products app migrations  
product_manager = MigrationManager(migrations_dir="apps/products/migrations")
await product_manager.init()
await product_manager.makemigrations("Add discount field")
```

## Benefits

✅ **Better Organization** - One folder per feature  
✅ **Team Collaboration** - No migration conflicts  
✅ **Clear History** - See which app changed what  
✅ **Modular Deployments** - Deploy app-specific changes  
✅ **Reusable Apps** - Move apps with migrations between projects  

## Key Features

1. **Path-based detection**
   - Automatically detects app name from migrations directory path
   - `apps/{app_name}/migrations` format

2. **Custom app naming**
   - Auto-detection or manual specification
   ```python
   MigrationManager(migrations_dir="apps/users/migrations", app_name="custom_name")
   ```

3. **Flexible CLI**
   - Supports both centralized and modular in same project
   - Smart path detection

4. **Shared configuration**
   - One alembic.ini for all apps
   - Consistent database connection

## Files Modified

- ✅ `fastapi_sqlalchemy/migration.py` - Added modular support
- ✅ `fastapi_sqlalchemy/cli.py` - Enhanced CLI for modular paths
- ✅ `README.md` - Added modular migration section
- ✅ `MODULAR_MIGRATIONS.md` - Complete guide
- ✅ `MODULAR_MIGRATION_SUMMARY.md` - This file

## Testing

To test modular migrations:

```bash
# 1. Create test structure
mkdir -p test_app/users/migrations/versions
mkdir -p test_app/products/migrations/versions

# 2. Initialize
python -m fastapi_sqlalchemy.cli migration init test_app/users/migrations
python -m fastapi_sqlalchemy.cli migration init test_app/products/migrations

# 3. Create test models in each app

# 4. Generate migrations
python -m fastapi_sqlalchemy.cli migration makemigrations test_app/users/migrations

# 5. Apply
python -m fastapi_sqlalchemy.cli migration migrate
```

## See Also

- [MODULAR_MIGRATIONS.md](./MODULAR_MIGRATIONS.md) - Complete guide
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - General migration guide
- [README.md](./README.md) - Main documentation
