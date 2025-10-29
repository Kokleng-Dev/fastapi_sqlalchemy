# BaseModel Usage Guide

## Accessing TableQuery Methods from BaseModel

Yes! BaseModel can use ALL methods from TableQuery in two ways:

## Method 1: Direct Model Methods (Recommended for Common Operations)

Common query operations are available as direct methods on the model:

```python
from fastapi_sqlalchemy import BaseModel
from sqlalchemy import Column, Integer, String, Boolean

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    email = Column(String(255))
    active = Column(Boolean, default=True)

# All direct model methods return TableQuery for chaining
users = await User.where(User.active == True)\
                  .order_by(User.username)\
                  .limit(10)\
                  .all()

# JOIN operations
users = await User.left_join(Post, User.id == Post.user_id)\
                  .select(User.username, Post.title)\
                  .all()

# ORM loading strategies
from sqlalchemy.orm import joinedload
users = await User.options(joinedload(User.profile))\
                  .load_only(User.id, User.username)\
                  .all()

# Schema switching
users = await User.schema("tenant_001")\
                  .where(User.active == True)\
                  .all()
```

## Method 2: Via query() Method (For All Advanced Features)

For complete access to ALL TableQuery methods, use the `query()` method:

```python
# Access any TableQuery method
users = await User.query()\
                  .where_in(User.id, [1, 2, 3])\
                  .where_not_null(User.email)\
                  .where_between(User.created_at, [start_date, end_date])\
                  .distinct_by(User.username)\
                  .group_by(User.status)\
                  .having(func.count(User.id) > 5)\
                  .union(User.query().where(User.role == "admin"))\
                  .all()
```

## Complete Examples

### 1. Basic Query Building

```python
# Simple queries
users = await User.all()
user = await User.find(1)
active_users = await User.where(User.active == True).all()
```

### 2. Chaining Methods

```python
# Chain multiple methods
users = await User\
    .where(User.active == True)\
    .where_not_null(User.email)\
    .order_by(User.username)\
    .limit(10)\
    .offset(20)\
    .all()
```

### 3. Joins

```python
# Inner join
posts = await User\
    .join(Post, User.id == Post.user_id)\
    .select(User.username, Post.title)\
    .all()

# Left join
users = await User\
    .left_join(Post, User.id == Post.user_id)\
    .select(User.username, Post.title)\
    .all()
```

### 4. ORM Features

```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func

# Eager load relationships
users = await User\
    .options(joinedload(User.posts), selectinload(User.comments))\
    .all()

# Load only specific columns
users = await User.load_only(User.id, User.username, User.email).all()

# ORM mode - returns SQLAlchemy objects
users = await User.with_orm().where(User.active == True).all()
```

### 5. Advanced Queries with query() Method

```python
# Use any TableQuery method
result = await User.query()\
    .where_in(User.id, [1, 2, 3, 4, 5])\
    .where_not_in(User.status, ["banned", "suspended"])\
    .where_between(User.created_at, [start_date, end_date])\
    .where_like(User.email, "gmail")\
    .distinct_by(User.username)\
    .group_by(User.status)\
    .having(func.count(User.id) > 10)\
    .order_by(func.count(User.id).desc())\
    .all()
```

### 6. Subqueries

```python
# From subquery
subquery = User.query()\
    .select(User.id, func.count(Post.id).label('post_count'))\
    .join(Post, User.id == Post.user_id)\
    .group_by(User.id)\
    .build_subquery()

users = await User.query()\
    .from_subquery("user_stats", subquery)\
    .where("user_stats.post_count > 5")\
    .all()
```

### 7. Schema Switching

```python
# Switch schema per request
users = await User.schema("tenant_001").where(User.active == True).all()

# Or use with query()
users = await User.query().schema("tenant_002").all()
```

### 8. Pagination

```python
# Paginate
result = await User.where(User.active == True)\
                   .order_by(User.username)\
                   .paginate(page=1, per_page=20)

items = result["items"]
pagination = result["pagination"]
```

### 9. Aggregates

```python
from sqlalchemy import func

# Count
total = await User.count()

# With query() method
total_active = await User.query()\
                        .where(User.active == True)\
                        .count()

# Sum, Avg, Min, Max
from fastapi_sqlalchemy import DB

async with connection_manager.session() as session:
    db = DB(session)
    avg_age = await db.table(User).avg(User.age)
```

### 10. Transactions

```python
from fastapi_sqlalchemy import with_transaction

@with_transaction()
async def create_user_complete(db: DB):
    User.set_session(db.session)
    
    user = await User.create({"username": "john", "email": "john@example.com"})
    
    # Use with Post model
    post = await Post.create({"user_id": user["id"], "title": "Hello"})
    
    return user, post
```

### 11. Complete Real-World Example

```python
from fastapi import FastAPI, Depends
from fastapi_sqlalchemy import BaseModel, connection_manager
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, joinedload

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    email = Column(String(255))
    active = Column(Boolean, default=True)
    
    posts = relationship("Post", back_populates="user")


class Post(BaseModel):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    content = Column(String)
    
    user = relationship("User", back_populates="posts")


app = FastAPI()


@app.get("/users/{user_id}")
async def get_user_with_posts(user_id: int):
    """Get user with their posts using all features."""
    
    async with connection_manager.session() as session:
        User.set_session(session)
        
        # Use query() for full access
        user = await User.query()\
                        .where(User.id == user_id)\
                        .options(joinedload(User.posts))\
                        .with_orm()\
                        .first()
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "posts": [
                {"id": post.id, "title": post.title}
                for post in user.posts
            ]
        }


@app.get("/users")
async def list_users_with_stats():
    """List users with statistics."""
    
    async with connection_manager.session() as session:
        User.set_session(session)
        
        # Complex query using all features
        result = await User.query()\
                          .where(User.active == True)\
                          .select(
                              User.id,
                              User.username,
                              User.email,
                              func.count(Post.id).label('post_count')
                          )\
                          .left_join(Post, User.id == Post.user_id)\
                          .group_by(User.id)\
                          .having(func.count(Post.id) > 0)\
                          .order_by(func.count(Post.id).desc())\
                          .limit(10)\
                          .all()
        
        return result
```

## Summary

**BaseModel supports ALL TableQuery methods** through:

1. **Direct methods** - For common operations like `where()`, `join()`, `order_by()`, etc.
2. **query() method** - For full access to ALL 100+ TableQuery methods

Any method that returns a `TableQuery` instance can be chained with any other TableQuery method. This gives you complete flexibility and power!

