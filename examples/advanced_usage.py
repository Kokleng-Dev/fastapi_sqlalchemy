"""
Advanced Usage Examples
Demonstrates schema switching, ORM features, and Eloquent-style models
"""

from fastapi import FastAPI, Depends, Header
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, joinedload, selectinload
from datetime import datetime
from typing import Optional
import asyncio

from fastapi_sqlalchemy import (
    db_settings, 
    connection_manager, 
    DB, 
    BaseModel,
    with_db,
    with_transaction
)

# ============================================================================
# 1. DEFINE MODELS WITH ELOQUENT-STYLE INHERITANCE
# ============================================================================

class User(BaseModel):
    """
    Eloquent-style model with static methods.
    Can be called directly like User.all(), User.find(1), etc.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (will be loaded with ORM features)
    posts = relationship("Post", back_populates="user")
    profile = relationship("Profile", back_populates="user", uselist=False)


class Profile(BaseModel):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    user = relationship("User", back_populates="profile")


class Post(BaseModel):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    published = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    
    user = relationship("User", back_populates="posts")


# ============================================================================
# 2. FASTAPI APP WITH SCHEMA SWITCHING
# ============================================================================

app = FastAPI()

# Configure databases with schemas
db_settings.load_from_dict({
    "default": {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "myapp",
        "username": "postgres",
        "password": "secret"
    },
    "analytics": {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "analytics_db",
        "username": "postgres",
        "password": "secret"
    }
}, default="default")


@app.on_event("startup")
async def startup():
    await connection_manager.initialize()
    
    # Set up default session for models
    async with connection_manager.session() as session:
        User.set_session(session)


@app.on_event("shutdown")
async def shutdown():
    await connection_manager.close_all()


# ============================================================================
# 3. SCHEMA SWITCHING PER REQUEST (DYNAMIC)
# ============================================================================

async def get_schema_from_header(x_schema: Optional[str] = Header(None)):
    """Extract schema from request header."""
    return x_schema or "public"


@app.get("/users")
async def list_users(schema: str = Depends(get_schema_from_header)):
    """
    List users with dynamic schema switching.
    
    Usage:
        curl http://localhost:8000/users
        curl -H "X-Schema: tenant_001" http://localhost:8000/users
    """
    # Use specific schema for this request
    async with connection_manager.session(schema=schema) as session:
        db = DB(session)
        User.set_session(session)
        
        users = await User.where(User.active == True).all()
        return users


@app.get("/tenants/{tenant_id}/users")
async def get_tenant_users(tenant_id: str):
    """Get users for specific tenant using tenant's schema."""
    # Switch to tenant schema dynamically
    tenant_schema = f"tenant_{tenant_id}"
    
    async with connection_manager.session(schema=tenant_schema) as session:
        db = DB(session)
        User.set_session(session)
        
        users = await User.all()
        return users


# ============================================================================
# 4. ELOQUENT-STYLE MODEL USAGE
# ============================================================================

@app.get("/eloquent/users")
async def list_users_eloquent():
    """Use models directly like Laravel Eloquent."""
    
    # All users
    all_users = await User.all()
    
    # Find by ID
    user = await User.find(1)
    
    # Where clause
    active_users = await User.where(User.active == True).all()
    
    # Count
    total = await User.count()
    
    # First
    first_user = await User.first()
    
    return {
        "all_users": all_users,
        "user": user,
        "active_users": active_users,
        "total": total,
        "first_user": first_user
    }


@app.post("/eloquent/users")
async def create_user_eloquent(user_data: dict):
    """Create user using Eloquent-style model."""
    
    user = await User.create({
        "username": user_data["username"],
        "email": user_data["email"],
        "active": True
    })
    
    return user


@app.put("/eloquent/users/{user_id}")
async def update_user_eloquent(user_id: int, user_data: dict):
    """Update user using Eloquent-style model."""
    
    user = await User.update_by_id(user_id, {
        "username": user_data["username"],
        "email": user_data["email"]
    })
    
    return user


# ============================================================================
# 5. ORM FEATURES WITH LOADING STRATEGIES
# ============================================================================

@app.get("/users-with-posts")
async def get_users_with_posts():
    """Get users with their posts using ORM loading strategies."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Using joinedload for eager loading
        from sqlalchemy.orm import joinedload
        
        query = db.table(User).options(
            joinedload(User.posts),
            joinedload(User.profile)
        )
        
        users = await query.all()
        return users


@app.get("/users/{user_id}/posts")
async def get_user_posts(user_id: int):
    """Get user posts with selective loading."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Use with_orm to get SQLAlchemy objects instead of dicts
        query = db.table(User)\
            .where(User.id == user_id)\
            .with_orm()\
            .options(joinedload(User.posts))
        
        result = await query.first()
        
        if result:
            return {
                "user": {
                    "id": result.id,
                    "username": result.username,
                    "email": result.email
                },
                "posts": [
                    {
                        "id": post.id,
                        "title": post.title,
                        "content": post.content
                    }
                    for post in result.posts
                ]
            }
        
        return None


# ============================================================================
# 6. LOAD ONLY SPECIFIC COLUMNS
# ============================================================================

@app.get("/users-lightweight")
async def get_users_lightweight():
    """Load only specific columns for performance."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Only load id, username, and email
        users = await db.table(User)\
            .load_only(User.id, User.username, User.email)\
            .all()
        
        return users


# ============================================================================
# 7. USING DECORATORS
# ============================================================================

@with_db()
async def create_user_with_posts(db: DB, user_data: dict):
    """Auto session management with decorator."""
    
    user = await db.table(User).create(user_data)
    
    posts_data = [
        {"user_id": user["id"], "title": f"Post {i}", "content": f"Content {i}"}
        for i in range(3)
    ]
    
    posts = await db.table(Post).create_many(posts_data)
    
    return {"user": user, "posts": posts}


@with_transaction()
async def create_user_with_profile(db: DB, user_data: dict, profile_data: dict):
    """Transaction with auto-commit/rollback."""
    
    user = await db.table(User).create(user_data)
    profile_data["user_id"] = user["id"]
    profile = await db.table(Profile).create(profile_data)
    
    return {"user": user, "profile": profile}


@app.post("/users/create-batch")
async def create_user_batch():
    """Create user with posts using decorators."""
    return await create_user_with_posts({
        "username": "john",
        "email": "john@example.com",
        "active": True
    })


@app.post("/users/create-complete")
async def create_user_complete():
    """Create user with profile using transaction."""
    return await create_user_with_profile(
        {
            "username": "jane",
            "email": "jane@example.com",
            "active": True
        },
        {
            "bio": "Software Developer",
            "avatar_url": "https://example.com/avatar.jpg"
        }
    )


# ============================================================================
# 8. MULTI-CONNECTION EXAMPLE
# ============================================================================

@app.get("/analytics/user-count")
async def get_analytics_user_count():
    """Query from analytics database."""
    
    # Switch to analytics connection
    async with connection_manager.session("analytics") as session:
        db = DB(session)
        
        # Query from analytics database
        count = await db.table(User).count()
        
        return {"user_count": count}


# ============================================================================
# 9. SCHEMA AWARE QUERIES
# ============================================================================

@app.get("/schema/{schema_name}/users")
async def get_schema_users(schema_name: str):
    """Query from specific schema."""
    
    async with connection_manager.session(schema=schema_name) as session:
        db = DB(session)
        User.set_session(session)
        
        users = await User.all()
        return {"schema": schema_name, "users": users}


# ============================================================================
# 10. COMPLETE EXAMPLE WITH ALL FEATURES
# ============================================================================

@app.get("/complete-example/{user_id}")
async def complete_example(user_id: int):
    """Demonstrates all features together."""
    
    # Use specific schema
    async with connection_manager.session(schema="public") as session:
        db = DB(session)
        User.set_session(session)
        
        # Eloquent-style query with ORM
        user = await User.where(User.id == user_id).first()
        
        # If not found, create one
        if not user:
            user = await User.create({
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "active": True
            })
        
        # Get user's posts using ORM loading
        from sqlalchemy.orm import joinedload
        
        query = db.table(User)\
            .where(User.id == user_id)\
            .with_orm()\
            .options(joinedload(User.posts))
        
        user_with_posts = await query.first()
        
        return {
            "user": user,
            "posts_count": len(user_with_posts.posts) if user_with_posts else 0
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

