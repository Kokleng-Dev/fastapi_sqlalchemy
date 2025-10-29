# Modular Migrations - Django-style App-based Migrations

This feature allows you to organize migrations per app/feature, similar to Django's modular migration system.

## Overview

With modular migrations, each app or feature module can have its own migrations folder:

```
project/
├── alembic.ini                    # Main config (shared)
├── apps/
│   ├── users/
│   │   ├── migrations/            # Users app migrations
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       ├── 001_initial.py
│   │   │       └── 002_add_email.py
│   │   ├── models.py              # User models
│   │   └── ...
│   ├── posts/
│   │   ├── migrations/            # Posts app migrations
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       └── 001_initial.py
│   │   ├── models.py              # Post models
│   │   └── ...
│   └── orders/
│       ├── migrations/            # Orders app migrations
│       ├── models.py
│       └── ...
```

## Usage

### 1. Initialize Modular Migrations

For each app/feature, initialize migrations separately:

```bash
# Initialize migrations for users app
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations

# Initialize migrations for posts app
python -m fastapi_sqlalchemy.cli migration init apps/posts/migrations
```

### 2. Create Migrations for Specific App

```bash
# Create migration for users app
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations "Add email field"

# Create migration for posts app
python -m fastapi_sqlalchemy.cli migration makemigrations apps/posts/migrations "Add tags table"
```

### 3. Apply All Migrations

```bash
# Apply all migrations from all apps
python -m fastapi_sqlalchemy.cli migration migrate
```

## Complete Example

### Project Structure

```
my_project/
├── alembic.ini
├── apps/
│   ├── users/
│   │   ├── migrations/
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   ├── models.py
│   │   └── routes.py
│   └── products/
│       ├── migrations/
│       │   ├── env.py
│       │   ├── script.py.mako
│       │   └── versions/
│       ├── models.py
│       └── routes.py
└── main.py
```

### Step 1: Create Models

**apps/users/models.py:**
```python
from fastapi_sqlalchemy import BaseModel
from sqlalchemy import Column, Integer, String

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    email = Column(String(255))
```

**apps/products/models.py:**
```python
from fastapi_sqlalchemy import BaseModel
from sqlalchemy import Column, Integer, String, Float

class Product(BaseModel):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Float)
```

### Step 2: Initialize Migrations

```bash
# Initialize users migrations
python -m fastapi_sqlalchemy.cli migration init apps/users/migrations

# Initialize products migrations
python -m fastapi_sqlalchemy.cli migration init apps/products/migrations
```

### Step 3: Import Models in env.py

**apps/users/migrations/env.py:**
```python
# Add this line to import your models
from apps.users.models import User
```

**apps/products/migrations/env.py:**
```python
# Add this line to import your models
from apps.products.models import Product
```

### Step 4: Create Migrations

```bash
# Create migration for users
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations "Initial users table"

# Create migration for products
python -m fastapi_sqlalchemy.cli migration makemigrations apps/products/migrations "Initial products table"
```

### Step 5: Apply Migrations

```bash
# Apply all migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Benefits of Modular Migrations

### 1. **Better Organization**
Each feature has its own migration history, making it easier to track changes.

### 2. **Team Collaboration**
Different developers can work on different apps without migration conflicts.

### 3. **Modular Deployments**
You can deploy changes from specific apps independently.

### 4. **Clearer History**
Migration history is organized by feature/app rather than chronologically.

### 5. **Reusability**
Apps with their migrations can be easily moved between projects.

## Python API Usage

You can also use the `MigrationManager` directly in Python:

```python
from fastapi_sqlalchemy import MigrationManager

# For users app
user_manager = MigrationManager(migrations_dir="apps/users/migrations")
await user_manager.init()
await user_manager.makemigrations("Add username field")

# For products app
product_manager = MigrationManager(migrations_dir="apps/products/migrations")
await product_manager.init()
await product_manager.makemigrations("Add discount field")
```

## Mixing Centralized and Modular

You can mix both approaches:

```bash
# Centralized migrations (project-wide)
python -m fastapi_sqlalchemy.cli migration makemigrations

# Modular migrations (app-specific)
python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations
```

## Best Practices

1. **Consistent Structure**: Use the same folder structure across all apps
   ```
   apps/{app_name}/migrations/
   ```

2. **App Name Detection**: The system auto-detects app names from paths
   - `apps/users/migrations` → app name: `users`
   - `apps/products/migrations` → app name: `products`

3. **Model Imports**: Always import your models in each app's `env.py`

4. **Descriptive Messages**: Use meaningful migration messages
   ```bash
   python -m fastapi_sqlalchemy.cli migration makemigrations apps/users/migrations "Add email verification"
   ```

5. **One Migration per Change**: Create separate migrations for each logical change

## Comparison

### Centralized Migrations
```
migrations/
├── versions/
│   ├── 001_initial.py       # All models mixed together
│   ├── 002_add_email.py
│   ├── 003_add_products.py
│   └── ...
```

### Modular Migrations (Django-style)
```
apps/
├── users/
│   └── migrations/
│       └── versions/
│           ├── 001_initial.py    # Only user models
│           ├── 002_add_email.py
│           └── ...
├── products/
│   └── migrations/
│       └── versions/
│           ├── 001_initial.py    # Only product models
│           └── ...
```

## Advanced: Multiple Databases

You can also use modular migrations with different database connections:

```python
# Different apps can connect to different databases
db_settings.load_from_dict({
    "main": {
        "driver": "postgresql",
        "host": "localhost",
        "database": "main_db",
    },
    "analytics": {
        "driver": "postgresql",
        "host": "localhost",
        "database": "analytics_db",
    }
})

# Each app manager can use different connections
user_manager = MigrationManager(migrations_dir="apps/users/migrations")
product_manager = MigrationManager(migrations_dir="apps/products/migrations")
```

## Troubleshooting

### Issue: Migrations not found
**Solution**: Make sure you've initialized migrations for each app:
```bash
python -m fastapi_sqlalchemy.cli migration init apps/{app_name}/migrations
```

### Issue: Models not detected
**Solution**: Import your models in the app's `migrations/env.py`:
```python
from apps.{app_name}.models import YourModel, AnotherModel
```

### Issue: App name auto-detection fails
**Solution**: Manually specify the app name:
```python
manager = MigrationManager(
    migrations_dir="apps/users/migrations",
    app_name="users"
)
```

## Summary

Modular migrations provide:
- ✅ One folder per feature/app
- ✅ Django-like organization
- ✅ Better team collaboration
- ✅ Clearer migration history
- ✅ Easy reuse and deployment

This is perfect for larger projects with multiple features or microservices architecture!
