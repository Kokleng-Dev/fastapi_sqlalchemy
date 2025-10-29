# Advanced Features Quick Reference

## Complete Feature List

This library supports all advanced SQLAlchemy features through a fluent, Laravel-like interface.

## 1. Joins

### Multiple Joins
```python
# Chain multiple joins
results = await User\
    .left_join(Profile, User.id == Profile.user_id)\
    .left_join(Post, User.id == Post.user_id)\
    .left_join(Comment, Post.id == Comment.post_id)\
    .select(User.username, Profile.bio, Post.title)\
    .all()

# Join with conditions
users = await User\
    .join(Post, (User.id == Post.user_id) & (Post.published == True))\
    .all()

# Join types
.left_join()    # LEFT OUTER JOIN
.right_join()   # RIGHT OUTER JOIN
.full_join()    # FULL OUTER JOIN
.inner_join()   # INNER JOIN
```

### Join with Subquery
```python
# Join with a subquery (CTE)
stats_subquery = db.query()\
    .table(Post)\
    .select(Post.user_id, func.count(Post.id).label("post_count"))\
    .group_by(Post.user_id)\
    .build_subquery()

users = await db.table(User)\
    .left_join_subquery(stats_subquery, User.id == stats_subquery.c.user_id)\
    .select(User.username, stats_subquery.c.post_count)\
    .all()
```

## 2. Subqueries

### WHERE IN Subquery
```python
# Users who have published posts
users = await User.where_in_subquery(
    User.id,
    lambda: db.query()\
              .table(Post)\
              .select(Post.user_id)\
              .where(Post.published == True)
).all()
```

### EXISTS Subquery
```python
# Users who have any posts
users = await User.where_exists_subquery(
    lambda: db.query()\
              .table(Post)\
              .where(Post.user_id == User.id)
).all()

# Users who have never posted
users = await User.where_not_exists_subquery(
    lambda: db.query()\
              .table(Post)\
              .where(Post.user_id == User.id)
).all()
```

### FROM Subquery (CTE)
```python
# Use subquery as table
stats = await db.table(User)\
    .from_subquery(
        "user_stats",
        lambda: db.query()\
              .table(User)\
              .select(User.id, func.count(Post.id).label("post_count"))\
              .left_join(Post, User.id == Post.user_id)\
              .group_by(User.id)
    )\
    .all()
```

### Build Subquery for Multiple Uses
```python
# Build once, use multiple times
user_stats = lambda: User.query()\
    .select(User.id, func.count(Post.id).label("post_count"))\
    .left_join(Post, User.id == Post.user_id)\
    .group_by(User.id)\
    .build_subquery()

# Use in JOIN
# Use in WHERE IN
# Use in SELECT
```

## 3. Complex Aggregations

### Basic Aggregates
```python
from sqlalchemy import func

# Count, Sum, Avg, Min, Max
await User.count()
await db.table(Post).sum(Post.views)
await db.table(Post).avg(Post.views)
await db.table(User).min(User.age)
await db.table(User).max(User.age)
```

### Advanced Aggregations
```python
# Multiple aggregates with grouping
stats = await db.table(User)\
    .select(
        User.id,
        User.username,
        func.count(Post.id.distinct()).label("post_count"),
        func.count(Comment.id.distinct()).label("comment_count"),
        func.sum(Post.views).label("total_views"),
        func.avg(Post.views).label("avg_views"),
        func.max(Post.created_at).label("last_post_date")
    )\
    .left_join(Post, User.id == Post.user_id)\
    .left_join(Comment, Post.id == Comment.post_id)\
    .group_by(User.id)\
    .having(func.count(Post.id) > 0)\
    .order_by(func.count(Post.id).desc())\
    .all()
```

### Window Functions
```python
# RANK, ROW_NUMBER, etc.
ranked = await db.table(Post)\
    .select(
        Post.id,
        Post.title,
        Post.views,
        func.rank().over(
            partition_by=Post.user_id,
            order_by=Post.views.desc()
        ).label("rank")
    )\
    .all()
```

## 4. UNION Queries

### UNION (removes duplicates)
```python
q1 = db.table(User).select(User.username).where(User.active == True)
q2 = db.table(Post).select(Post.title).where(Post.published == True)

results = await db.query().table(q1).union(q2).all()
```

### UNION ALL (keeps duplicates)
```python
results = await db.query().table(q1).union_all(q2).all()
```

### Multiple Unions
```python
q1 = db.table(User).select(User.username)
q2 = db.table(Post).select(Post.title)
q3 = db.table(Comment).select(Comment.content)

results = await db.query().table(q1).union(q2, q3).all()
```

## 5. CASE Statements

```python
from sqlalchemy import case

# Categorize users
categorized = await db.table(User)\
    .select(
        User.id,
        User.username,
        func.count(Post.id).label("post_count"),
        case(
            (func.count(Post.id) > 10, "Power User"),
            (func.count(Post.id) > 5, "Active User"),
            (func.count(Post.id) > 0, "Regular User"),
            else_="New User"
        ).label("user_type")
    )\
    .left_join(Post, User.id == Post.user_id)\
    .group_by(User.id)\
    .all()
```

## 6. Apply Filters (Dynamic Filtering)

### Single Table
```python
users = await User.apply_filters({
    "user.active__eq": True,
    "user.age__gte": 18,
    "user.email__like": "gmail"
}).all()
```

### With Joins (Multiple Tables)
```python
results = await User\
    .left_join(Post, User.id == Post.user_id)\
    .apply_filters({
        "user.active__eq": True,
        "post.published__eq": True,
        "post.views__gte": 100
    })\
    .all()
```

### Available Operators
```python
# Equality
{"user.active__eq": True}
{"user.active__ne": False}

# Comparison
{"user.age__gt": 18}
{"user.age__gte": 18}
{"user.age__lt": 65}
{"user.age__lte": 65}

# Text
{"user.email__like": "gmail"}
{"user.email__icontains": "example"}
{"user.email__startswith": "admin"}
{"user.email__endswith": ".com"}

# Lists
{"user.id__in": [1, 2, 3]}
{"user.id__notin": [1, 2, 3]}

# NULL
{"user.email__isnull": True}
{"user.email__notnull": True}

# Range
{"user.age__between": [18, 65]}
{"user.age__not_between": [0, 17]}
```

## 7. ORM Loading Strategies

### Eager Loading
```python
from sqlalchemy.orm import joinedload, selectinload

# Load relationships eagerly
users = await db.table(User)\
    .options(
        joinedload(User.posts),
        selectinload(User.comments)
    )\
    .all()

# ORM mode - returns SQLAlchemy objects
user = await db.table(User)\
    .with_orm()\
    .options(joinedload(User.posts))\
    .find(1)
```

### Selective Column Loading
```python
# Load only specific columns
users = await User.load_only(User.id, User.username, User.email).all()
```

## 8. Schema Switching (Multi-Tenancy)

```python
# Switch schema per request
async with connection_manager.session(schema="tenant_001") as session:
    db = DB(session)
    User.set_session(session)
    
    # All queries use tenant_001 schema
    users = await User.all()
```

## 9. Transactions

### Context Manager
```python
async with db.transaction():
    user = await db.table(User).create({"username": "john"})
    await db.table(Post).create({"user_id": user["id"], "title": "Hello"})
    # Auto-commits on success, auto-rollback on error
```

### With Decorator
```python
@with_transaction()
async def create_user_with_data(db: DB, user_data: dict):
    user = await db.table(User).create(user_data)
    await db.table(Profile).create({"user_id": user["id"], ...})
    return user
```

## 10. Complex Business Logic Examples

### Example 1: User Feed with Statistics
```python
feed = await db.table(Post)\
    .join(User, Post.user_id == User.id)\
    .left_join(Profile, User.id == Profile.user_id)\
    .select(
        Post.id,
        Post.title,
        Post.content,
        Post.views,
        User.username,
        Profile.avatar_url,
        func.count(Comment.id).label("comment_count")
    )\
    .left_join(Comment, Post.id == Comment.post_id)\
    .where(Post.published == True)\
    .group_by(Post.id, User.id)\
    .order_by(Post.created_at.desc())\
    .limit(20)\
    .all()
```

### Example 2: Top Contributors
```python
top_contributors = await db.table(User)\
    .select(
        User.id,
        User.username,
        func.count(Post.id).label("post_count"),
        func.sum(Post.views).label("total_views"),
        func.avg(Post.views).label("avg_views")
    )\
    .left_join(Post, User.id == Post.user_id)\
    .group_by(User.id)\
    .having(func.count(Post.id) > 0)\
    .order_by(
        (func.count(Post.id) * 0.4 + func.sum(Post.views) * 0.6).desc()
    )\
    .limit(10)\
    .all()
```

### Example 3: Dynamic Search API
```python
@app.get("/api/users/search")
async def search_users(
    active: bool = None,
    role: str = None,
    age_min: int = None,
    age_max: int = None,
    email_like: str = None
):
    filters = {}
    if active is not None:
        filters["user.active__eq"] = active
    if role:
        filters["user.role__eq"] = role
    if age_min:
        filters["user.age__gte"] = age_min
    if age_max:
        filters["user.age__lte"] = age_max
    if email_like:
        filters["user.email__like"] = email_like
    
    users = await User.apply_filters(filters)\
                     .order_by(User.created_at.desc())\
                     .paginate(page=1, per_page=20)
    
    return users
```

## 11. Performance Tips

### Use load_only() for Large Results
```python
# Only load needed columns
users = await User.load_only(User.id, User.username, User.email)\
                  .apply_filters({"user.active__eq": True})\
                  .all()
```

### Use Pagination for Large Datasets
```python
# Always paginate large datasets
result = await User.where(User.active == True)\
                  .paginate(page=1, per_page=20)
```

### Use Indexes
```python
# Create indexes for frequently queried columns
from sqlalchemy import Index

class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_active_email', 'active', 'email'),
        Index('idx_username', 'username'),
    )
```

### Use Selective Loading
```python
# Load only what you need
users = await db.table(User)\
    .load_only(User.id, User.username)\
    .options(selectinload(User.posts))\
    .all()
```

## 12. Complete Real-World Example

```python
async def get_user_dashboard(user_id: int):
    """
    Get comprehensive user dashboard data with:
    - User profile
    - Statistics
    - Recent posts
    - Popular posts
    - Activity metrics
    """
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Get user with profile
        user = await db.table(User)\
            .options(joinedload(User.profile))\
            .find(user_id)
        
        # Get statistics
        stats = await db.table(User)\
            .select(
                func.count(Post.id).label("post_count"),
                func.sum(Post.views).label("total_views"),
                func.avg(Post.views).label("avg_views"),
                func.count(Comment.id).label("comment_count")
            )\
            .left_join(Post, User.id == Post.user_id)\
            .left_join(Comment, Post.id == Comment.post_id)\
            .where(User.id == user_id)\
            .group_by(User.id)\
            .first()
        
        # Get recent posts
        recent_posts = await db.table(Post)\
            .where(Post.user_id == user_id)\
            .where(Post.published == True)\
            .order_by(Post.created_at.desc())\
            .limit(5)\
            .all()
        
        # Get popular posts
        popular_posts = await db.table(Post)\
            .where(Post.user_id == user_id)\
            .where(Post.published == True)\
            .order_by(Post.views.desc())\
            .limit(5)\
            .all()
        
        return {
            "user": user,
            "statistics": stats,
            "recent_posts": recent_posts,
            "popular_posts": popular_posts
        }
```

## See Also

- `examples/advanced_system_examples.py` - 20+ complete examples
- `examples/apply_filters_examples.py` - Dynamic filtering examples
- `examples/advanced_usage.py` - Schema switching, Eloquent models
- `BASE_MODEL_USAGE.md` - Using BaseModel with all features
- `APPLY_FILTERS_GUIDE.md` - apply_filters() complete guide

