# apply_filters() - Complete Guide

## Overview

The `apply_filters()` method provides Laravel-like dynamic filtering with `table.column__operator` syntax. It supports filtering single tables and multiple tables with JOINs.

## Syntax

```
{table}.{column}__{operator}
```

**Parts:**
- `table` - Table name (e.g., `user`, `post`, `product`)
- `column` - Column name (e.g., `name`, `email`, `age`)
- `operator` - Operation (e.g., `eq`, `gt`, `like`, `in`)

## Available Operators

### Equality
- `eq` - Equal (default if not specified)
- `ne`, `neq` - Not equal

### Comparison
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal

### String Matching
- `like` - LIKE pattern matching (case-insensitive)
- `icontains` - Contains string (case-insensitive)
- `startswith` - Starts with
- `endswith` - Ends with

### Lists
- `in` - In list
- `notin` - Not in list

### Range
- `between` - Between min and max `[min, max]`
- `not_between` - Not between

### NULL Checks
- `isnull` - IS NULL
- `notnull` - IS NOT NULL

## Usage Examples

### 1. Basic Single Table Filters

```python
from fastapi_sqlalchemy import DB, connection_manager

async with connection_manager.session() as session:
    db = DB(session)
    
    # Single filter
    users = await db.table(User)\
        .apply_filters({"user.active__eq": True})\
        .all()
    
    # Multiple filters (AND by default)
    users = await db.table(User)\
        .apply_filters({
            "user.active__eq": True,
            "user.age__gte": 18,
            "user.age__lte": 65
        })\
        .all()
    
    # Text search
    users = await db.table(User)\
        .apply_filters({"user.email__like": "gmail"})\
        .all()
```

### 2. With JOINs - Multiple Tables

```python
# Filter both tables
results = await db.table(User)\
    .left_join(Post, User.id == Post.user_id)\
    .apply_filters({
        "user.active__eq": True,
        "post.published__eq": True
    })\
    .select(User.username, Post.title)\
    .all()
```

### 3. OR Logic

```python
# Apply OR logic by using use_or=True
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

### 4. With BaseModel

```python
from fastapi_sqlalchemy import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    # ... columns

# Use directly on model
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
```

### 5. From FastAPI Request Parameters

```python
from fastapi import FastAPI, Depends, Query
from typing import Optional

@app.get("/users")
async def list_users(
    active: Optional[bool] = Query(None),
    age_min: Optional[int] = Query(None),
    age_max: Optional[int] = Query(None),
    email_like: Optional[str] = Query(None),
    ids: Optional[str] = Query(None)
):
    # Build filters dynamically
    filters = {}
    
    if active is not None:
        filters["user.active__eq"] = active
    
    if age_min:
        filters["user.age__gte"] = age_min
    
    if age_max:
        filters["user.age__lte"] = age_max
    
    if email_like:
        filters["user.email__like"] = email_like
    
    if ids:
        filters["user.id__in"] = [int(id) for id in ids.split(",")]
    
    # Apply filters
    users = await db.table(User)\
        .apply_filters(filters)\
        .order_by(User.created_at.desc())\
        .all()
    
    return users
```

### 6. Complete Advanced Example

```python
async def advanced_search(search_params: dict):
    """
    Advanced search with multiple filters.
    
    search_params = {
        "active": True,
        "age_min": 18,
        "age_max": 65,
        "email": "gmail",
        "role": "admin",
        "ids": [1, 2, 3]
    }
    """
    
    filters = {}
    
    # Direct mappings
    if "active" in search_params:
        filters["user.active__eq"] = search_params["active"]
    
    if "age_min" in search_params:
        filters["user.age__gte"] = search_params["age_min"]
    
    if "age_max" in search_params:
        filters["user.age__lte"] = search_params["age_max"]
    
    if "email" in search_params:
        filters["user.email__like"] = search_params["email"]
    
    if "ids" in search_params:
        filters["user.id__in"] = search_params["ids"]
    
    # Execute query
    users = await db.table(User)\
        .apply_filters(filters)\
        .order_by(User.created_at.desc())\
        .limit(search_params.get("limit", 20))\
        .all()
    
    return users
```

### 7. All Available Operators

```python
# Equality
{"user.active__eq": True}
{"user.active__ne": False}

# Comparison
{"user.age__gt": 18}
{"user.age__gte": 18}
{"user.age__lt": 65}
{"user.age__lte": 65}

# String matching
{"user.email__like": "gmail"}
{"user.email__icontains": "example"}
{"user.email__startswith": "admin"}
{"user.email__endswith": ".com"}

# IN clauses
{"user.id__in": [1, 2, 3]}
{"user.id__notin": [1, 2, 3]}

# NULL checks
{"user.email__isnull": True}
{"user.email__notnull": True}

# BETWEEN
{"user.age__between": [18, 65]}
{"user.age__not_between": [0, 17]}
```

## Real-World Use Cases

### 1. Dynamic API Search

```python
@app.get("/api/users/search")
async def search_users(
    active: bool = None,
    age_range: str = None,  # "18-65"
    email: str = None,
    role: str = None,
    page: int = 1,
    per_page: int = 20
):
    filters = {}
    
    if active is not None:
        filters["user.active__eq"] = active
    
    if age_range:
        min_age, max_age = age_range.split("-")
        filters["user.age__gte"] = int(min_age)
        filters["user.age__lte"] = int(max_age)
    
    if email:
        filters["user.email__like"] = email
    
    if role:
        filters["user.role__eq"] = role
    
    result = await User.apply_filters(filters)\
                       .paginate(page, per_page)
    
    return result
```

### 2. Multi-Table Filtering

```python
# Filter users with their posts
results = await User.left_join(Post, User.id == Post.user_id)\
                   .apply_filters({
                       "user.active__eq": True,
                       "post.published__eq": True,
                       "post.views__gte": 100
                   })\
                   .select(User.username, Post.title, Post.views)\
                   .order_by(Post.views.desc())\
                   .all()
```

### 3. Complex Business Logic

```python
# Active users in specific age range with verified email
filters = {
    "user.active__eq": True,
    "user.age__gte": 18,
    "user.age__lte": 65,
    "user.email__notnull": True,
    "user.email__like": "@example.com"
}

users = await User.apply_filters(filters)\
                  .where(User.role.in_(["admin", "moderator"]))\
                  .all()
```

## Benefits

1. **Laravel-like syntax** - Familiar syntax for developers coming from Laravel
2. **Type-safe** - Works with SQLAlchemy models
3. **Flexible** - Works with single tables and JOINs
4. **Dynamic** - Perfect for building filters from request parameters
5. **Chainable** - Works with all TableQuery methods
6. **Clean code** - Reduces repetitive where() calls

## Performance Tips

1. **Index columns** you frequently filter on
2. **Use specific operators** when possible (eq vs like)
3. **Combine filters** in a single apply_filters() call
4. **Use load_only()** with apply_filters() to select only needed columns

```python
# Efficient query
users = await User.apply_filters({
    "user.active__eq": True,
    "user.age__gte": 18
})\
.load_only(User.id, User.username, User.email)\
.all()
```

## See Also

- `examples/apply_filters_examples.py` - Complete working examples
- `README.md` - Full API documentation
- `BASE_MODEL_USAGE.md` - Using with Eloquent-style models

