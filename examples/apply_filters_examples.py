"""
Advanced Examples: Using apply_filters with Laravel-like syntax
"""

from fastapi import FastAPI, Depends, Query
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi_sqlalchemy import BaseModel, connection_manager, DB, with_db
from fastapi_sqlalchemy.config import db_settings

# ============================================================================
# MODELS
# ============================================================================

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    active = Column(Boolean, default=True)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    posts = relationship("Post", back_populates="user")


class Post(BaseModel):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    content = Column(String)
    published = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="posts")


# ============================================================================
# BASIC EXAMPLES - Single Table
# ============================================================================

async def example_1_basic_filters():
    """Basic filters on single table."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Filter by active status
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
        
        # LIKE search
        users = await db.table(User)\
            .apply_filters({"user.email__like": "gmail"})\
            .all()
        
        # IN clause
        users = await db.table(User)\
            .apply_filters({"user.id__in": [1, 2, 3, 4, 5]})\
            .all()
        
        # OR filters
        users = await db.table(User)\
            .apply_filters(
                {
                    "user.username__like": "john",
                    "user.email__like": "john"
                },
                use_or=True
            )\
            .all()
        
        return users


# ============================================================================
# ADVANCED EXAMPLES - With JOINs
# ============================================================================

async def example_2_with_joins():
    """Apply filters with table.column syntax after joins."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Filter users with their published posts
        results = await db.table(User)\
            .left_join(Post, User.id == Post.user_id)\
            .apply_filters({
                "user.active__eq": True,
                "post.published__eq": True
            })\
            .select(User.username, Post.title)\
            .all()
        
        return results


# ============================================================================
# LARAVEL-LIKE DYNAMIC FILTERING FROM REQUEST
# ============================================================================

@app.get("/users")
async def list_users(
    active: Optional[bool] = Query(None),
    age_min: Optional[int] = Query(None),
    age_max: Optional[int] = Query(None),
    email_like: Optional[str] = Query(None),
    ids: Optional[str] = Query(None)
):
    """List users with dynamic filters from query parameters."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Build filters dynamically from request
        filters = {}
        
        if active is not None:
            filters["user.active__eq"] = active
        
        if age_min is not None:
            filters["user.age__gte"] = age_min
        
        if age_max is not None:
            filters["user.age__lte"] = age_max
        
        if email_like:
            filters["user.email__like"] = email_like
        
        if ids:
            id_list = [int(id) for id in ids.split(",")]
            filters["user.id__in"] = id_list
        
        # Apply all filters at once
        users = await db.table(User)\
            .apply_filters(filters)\
            .order_by(User.created_at.desc())\
            .all()
        
        return users


# ============================================================================
# SEARCH AND FILTER API
# ============================================================================

async def build_search_filters(request_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build filters from request parameters dynamically.
    Converts request params to Laravel-like filter syntax.
    """
    filters = {}
    
    # Direct mappings
    if "active" in request_params:
        filters["user.active__eq"] = request_params["active"]
    
    if "age" in request_params:
        filters["user.age__eq"] = request_params["age"]
    
    if "age_min" in request_params:
        filters["user.age__gte"] = request_params["age_min"]
    
    if "age_max" in request_params:
        filters["user.age__lte"] = request_params["age_max"]
    
    # Text search
    if "search" in request_params:
        search = request_params["search"]
        filters["user.username__like"] = search
        # Note: For OR logic, you'd need to call apply_filters separately
    
    if "email_like" in request_params:
        filters["user.email__like"] = request_params["email_like"]
    
    # NULL checks
    if "email_verified" in request_params and request_params["email_verified"]:
        filters["user.email__notnull"] = True
    
    # IN clauses
    if "ids" in request_params:
        ids = request_params["ids"]
        if isinstance(ids, str):
            ids = [int(id) for id in ids.split(",")]
        filters["user.id__in"] = ids
    
    return filters


@app.post("/users/search")
async def search_users(params: Dict[str, Any]):
    """Advanced search with multiple filters."""
    
    # Build filters from request
    filters = await build_search_filters(params)
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Apply all filters
        users = await db.table(User)\
            .apply_filters(filters)\
            .order_by(User.created_at.desc())\
            .limit(params.get("limit", 50))\
            .all()
        
        count = await db.table(User).apply_filters(filters).count()
        
        return {
            "users": users,
            "count": count,
            "filters_applied": filters
        }


# ============================================================================
# COMPLEX QUERIES WITH apply_filters
# ============================================================================

async def example_3_complex_query():
    """Complex query with joins and multiple filters."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Get active users with published posts, ordered by post views
        results = await db.table(User)\
            .left_join(Post, User.id == Post.user_id)\
            .apply_filters({
                "user.active__eq": True,
                "post.published__eq": True,
                "post.views__gte": 100
            })\
            .select(User.username, Post.title, Post.views)\
            .order_by(Post.views.desc())\
            .limit(10)\
            .all()
        
        return results


# ============================================================================
# USING WITH BaseModel
# ============================================================================

async def example_4_with_basemodel():
    """Using apply_filters with Eloquent-style models."""
    
    async with connection_manager.session() as session:
        User.set_session(session)
        
        # Direct model usage with apply_filters
        filters = {
            "user.active__eq": True,
            "user.age__gte": 18
        }
        
        users = await User.query()\
                         .apply_filters(filters)\
                         .all()
        
        return users


# ============================================================================
# ALL AVAILABLE OPERATORS
# ============================================================================

async def example_5_all_operators():
    """Examples of all available operators."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Equals, Not equals
        users = await db.table(User)\
            .apply_filters({"user.active__eq": True})\
            .all()
        
        users = await db.table(User)\
            .apply_filters({"user.active__ne": False})\
            .all()
        
        # Comparison operators
        users = await db.table(User)\
            .apply_filters({
                "user.age__gt": 18,
                "user.age__gte": 18,
                "user.age__lt": 65,
                "user.age__lte": 65
            })\
            .all()
        
        # String matching
        users = await db.table(User)\
            .apply_filters({
                "user.email__like": "gmail",
                "user.username__icontains": "john",
                "user.email__startswith": "admin",
                "user.email__endswith": ".com"
            })\
            .all()
        
        # IN/NOT IN
        users = await db.table(User)\
            .apply_filters({"user.id__in": [1, 2, 3]})\
            .all()
        
        users = await db.table(User)\
            .apply_filters({"user.id__notin": [1, 2, 3]})\
            .all()
        
        # NULL checks
        users = await db.table(User)\
            .apply_filters({"user.email__isnull": True})\
            .all()
        
        users = await db.table(User)\
            .apply_filters({"user.email__notnull": True})\
            .all()
        
        # BETWEEN
        users = await db.table(User)\
            .apply_filters({"user.age__between": [18, 65]})\
            .all()
        
        users = await db.table(User)\
            .apply_filters({"user.age__not_between": [0, 17]})\
            .all()
        
        return users


# ============================================================================
# REAL-WORLD COMPLETE EXAMPLE
# ============================================================================

async def advanced_search_users(search_params: Dict[str, Any]):
    """
    Advanced user search with all features.
    
    Expected params:
    {
        "active": true,
        "age_min": 18,
        "age_max": 65,
        "email": "gmail",
        "ids": [1, 2, 3],
        "search": "john",
        "has_posts": true,
        "order_by": "created_at",
        "order_dir": "desc",
        "page": 1,
        "per_page": 20
    }
    """
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Build base filters
        filters = {}
        
        if search_params.get("active") is not None:
            filters["user.active__eq"] = search_params["active"]
        
        if search_params.get("age_min"):
            filters["user.age__gte"] = search_params["age_min"]
        
        if search_params.get("age_max"):
            filters["user.age__lte"] = search_params["age_max"]
        
        if search_params.get("email"):
            filters["user.email__like"] = search_params["email"]
        
        if search_params.get("ids"):
            filters["user.id__in"] = search_params["ids"]
        
        # Build query
        query = db.table(User)
        
        # Apply filters
        if filters:
            query = query.apply_filters(filters)
        
        # Join posts if needed
        if search_params.get("has_posts"):
            query = query.left_join(Post, User.id == Post.user_id)
            query = query.apply_filters({"post.id__notnull": True})
        
        # Order by
        order_by = search_params.get("order_by", "created_at")
        order_dir = search_params.get("order_dir", "desc")
        
        if order_dir == "desc":
            query = query.order_by(getattr(User, order_by).desc())
        else:
            query = query.order_by(getattr(User, order_by))
        
        # Paginate
        page = search_params.get("page", 1)
        per_page = search_params.get("per_page", 20)
        
        if page and per_page:
            result = await query.paginate(page, per_page)
        else:
            items = await query.all()
            count = await db.table(User).apply_filters(filters).count()
            result = {
                "items": items,
                "pagination": {
                    "total_records": count,
                    "per_page": len(items) if page and per_page else count
                }
            }
        
        return result


# ============================================================================
# USAGE IN FASTAPI
# ============================================================================

app = FastAPI()

@app.get("/api/users/advanced-search")
async def advanced_search_endpoint(
    active: Optional[bool] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    email: Optional[str] = None,
    ids: Optional[str] = None,
    order_by: Optional[str] = "created_at",
    order_dir: Optional[str] = "desc",
    page: int = 1,
    per_page: int = 20
):
    """Advanced search endpoint with apply_filters."""
    
    # Build search params
    search_params = {
        "active": active,
        "age_min": age_min,
        "age_max": age_max,
        "email": email,
        "ids": [int(id) for id in ids.split(",")] if ids else None,
        "order_by": order_by,
        "order_dir": order_dir,
        "page": page,
        "per_page": per_page
    }
    
    # Remove None values
    search_params = {k: v for k, v in search_params.items() if v is not None}
    
    # Execute search
    result = await advanced_search_users(search_params)
    
    return result


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# Example usage:
# GET /api/users/advanced-search?active=true&age_min=18&age_max=65&email=gmail&page=1&per_page=20

# Using in code:
"""
search_params = {
    "active": True,
    "age_min": 18,
    "age_max": 65,
    "email": "gmail",
    "ids": [1, 2, 3],
    "order_by": "age",
    "order_dir": "desc",
    "page": 1,
    "per_page": 20
}

result = await advanced_search_users(search_params)
print(result["items"])
print(result["pagination"])
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

