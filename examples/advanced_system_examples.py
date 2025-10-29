"""
Advanced System Examples: Joins, Subqueries, CTEs, Unions, and Complex Queries
Demonstrates all advanced query builder features
"""

from fastapi import FastAPI, Depends
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, 
    Float, func, case, literal, text
)
from sqlalchemy.orm import relationship, joinedload, selectinload
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio

from fastapi_sqlalchemy import (
    BaseModel, connection_manager, DB, with_db, with_transaction
)
from fastapi_sqlalchemy.config import db_settings

# ============================================================================
# COMPLEX DATA MODEL
# ============================================================================

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    active = Column(Boolean, default=True)
    role = Column(String(50), default="user")
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="user")
    orders = relationship("Order", back_populates="user")
    profile = relationship("Profile", back_populates="user", uselist=False)


class Profile(BaseModel):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bio = Column(String(500))
    avatar_url = Column(String(500))
    location = Column(String(100))
    website = Column(String(200))
    
    user = relationship("User", back_populates="profile")


class Post(BaseModel):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    content = Column(String)
    published = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(BaseModel):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="comments")


class Category(BaseModel):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    slug = Column(String(100), unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)


class Order(BaseModel):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")


class OrderItem(BaseModel):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_name = Column(String(255))
    quantity = Column(Integer)
    price = Column(Float)


# ============================================================================
# 1. COMPLEX JOINS
# ============================================================================

async def example_1_multiple_joins():
    """Multiple joins to get related data."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Get users with their profiles, posts, and post comments
        results = await db.table(User)\
            .left_join(Profile, User.id == Profile.user_id)\
            .left_join(Post, User.id == Post.user_id)\
            .left_join(Comment, Post.id == Comment.post_id)\
            .select(
                User.username,
                User.email,
                Profile.bio,
                Post.title.label("post_title"),
                Comment.content.label("comment_content")
            )\
            .where(User.active == True)\
            .all()
        
        return results


async def example_2_filter_joined_tables():
    """Filter on joined tables."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Users with published posts
        users = await db.table(User)\
            .join(Post, User.id == Post.user_id)\
            .apply_filters({
                "user.active__eq": True,
                "post.published__eq": True,
                "post.views__gte": 100
            })\
            .select(User.username, Post.title, Post.views)\
            .all()
        
        return users


# ============================================================================
# 2. SUBQUERIES
# ============================================================================

async def example_3_where_in_subquery():
    """Use subquery in WHERE IN clause."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Users who have published posts
        users = await db.table(User)\
            .where_in_subquery(
                User.id,
                lambda: db.query()\
                      .table(Post)\
                      .select(Post.user_id)\
                      .where(Post.published == True)\
                      .distinct(Post.user_id)
            )\
            .all()
        
        return users


async def example_4_subquery_as_table():
    """Use subquery as a table (FROM subquery)."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Get user stats from subquery
        stats = await db.table(User)\
            .from_subquery(
                "user_stats",
                lambda: db.query()\
                      .table(User)\
                      .select(
                          User.id,
                          User.username,
                          func.count(Post.id).label("post_count"),
                          func.sum(Post.views).label("total_views")
                      )\
                      .left_join(Post, User.id == Post.user_id)\
                      .group_by(User.id)
            )\
            .all()
        
        return stats


# ============================================================================
# 3. COMPLEX AGGREGATIONS
# ============================================================================

async def example_5_user_statistics():
    """Calculate complex user statistics."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Users with post and comment counts
        stats = await db.table(User)\
            .select(
                User.id,
                User.username,
                User.email,
                func.count(Post.id.distinct()).label("post_count"),
                func.count(Comment.id.distinct()).label("comment_count"),
                func.sum(Post.views).label("total_views"),
                func.sum(Post.likes).label("total_likes")
            )\
            .left_join(Post, User.id == Post.user_id)\
            .left_join(Comment, Post.id == Comment.post_id)\
            .group_by(User.id)\
            .order_by(func.count(Post.id).desc())\
            .limit(10)\
            .all()
        
        return stats


async def example_6_time_based_aggregations():
    """Aggregate data by time periods."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Posts grouped by month
        monthly_posts = await db.table(Post)\
            .select(
                func.date_trunc('month', Post.created_at).label("month"),
                func.count(Post.id).label("post_count"),
                func.avg(Post.views).label("avg_views"),
                func.sum(Post.likes).label("total_likes")
            )\
            .where(Post.published == True)\
            .group_by(func.date_trunc('month', Post.created_at))\
            .order_by(func.date_trunc('month', Post.created_at).desc())\
            .all()
        
        return monthly_posts


# ============================================================================
# 4. UNION & UNION ALL
# ============================================================================

async def example_7_union_queries():
    """Combine multiple queries with UNION."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Get top users and top posts
        q1 = db.table(User)\
               .select(User.id, User.username, func.count(Post.id).label("count"))\
               .left_join(Post, User.id == Post.user_id)\
               .group_by(User.id)\
               .order_by(func.count(Post.id).desc())\
               .limit(5)
        
        q2 = db.table(Post)\
               .select(Post.id, Post.title, Post.views.label("count"))\
               .where(Post.published == True)\
               .order_by(Post.views.desc())\
               .limit(5)
        
        # Union results
        results = await db.query()\
            .table(q1)\
            .union(q2)\
            .all()
        
        return results


async def example_8_union_all():
    """Combine queries with UNION ALL (keeps duplicates)."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Active users and published posts (with duplicates if any)
        q1 = db.table(User)\
               .select(User.username)\
               .where(User.active == True)
        
        q2 = db.table(Post)\
               .select(Post.title)\
               .where(Post.published == True)
        
        results = await db.query()\
            .table(q1)\
            .union_all(q2)\
            .all()
        
        return results


# ============================================================================
# 5. WINDOW FUNCTIONS
# ============================================================================

async def example_9_window_functions():
    """Use SQL window functions."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Rank posts by views within each user
        ranked_posts = await db.table(Post)\
            .select(
                Post.id,
                Post.user_id,
                Post.title,
                Post.views,
                func.rank().over(
                    partition_by=Post.user_id,
                    order_by=Post.views.desc()
                ).label("rank")
            )\
            .all()
        
        return ranked_posts


# ============================================================================
# 6. CASE STATEMENTS
# ============================================================================

async def example_10_case_statements():
    """Use SQL CASE statements."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Categorize users by post count
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
        
        return categorized


# ============================================================================
# 7. RECURSIVE QUERIES (Hierarchical Data)
# ============================================================================

async def example_11_hierarchical_categories():
    """Query hierarchical category data."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Note: This requires a raw SQL query for true recursion
        # But we can build category trees with joins
        
        # Get categories with their parent
        categories = await db.table(Category)\
            .left_join(Category, Category.parent_id == Category.id)\
            .select(
                Category.id,
                Category.name,
                Category.parent_id,
                Category.parent_id.label("parent_name")
            )\
            .all()
        
        return categories


# ============================================================================
# 8. COMPLEX FILTERING WITH SUBQUERIES
# ============================================================================

async def example_12_exists_subquery():
    """Use EXISTS subquery for filtering."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Users who have any comments
        users = await db.table(User)\
            .where_exists_subquery(
                lambda: db.query()\
                      .table(Comment)\
                      .where(Comment.user_id == User.id)
            )\
            .all()
        
        return users


async def example_13_not_exists_subquery():
    """Use NOT EXISTS subquery."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Users who have never posted
        users = await db.table(User)\
            .where_not_exists_subquery(
                lambda: db.query()\
                      .table(Post)\
                      .where(Post.user_id == User.id)
            )\
            .all()
        
        return users


# ============================================================================
# 9. PERFORMANCE OPTIMIZATION WITH SELECTIVE LOADING
# ============================================================================

async def example_14_eager_loading():
    """Optimize queries with eager loading strategies."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Load users with posts and comments in single query
        users = await db.table(User)\
            .with_orm()\
            .options(
                joinedload(User.posts),
                selectinload(User.profile)
            )\
            .where(User.active == True)\
            .all()
        
        return users


async def example_15_load_only_columns():
    """Load only specific columns for performance."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Load only needed columns
        users = await db.table(User)\
            .load_only(User.id, User.username, User.email)\
            .apply_filters({
                "user.active__eq": True
            })\
            .all()
        
        return users


# ============================================================================
# 10. COMPLEX BUSINESS LOGIC
# ============================================================================

@with_transaction()
async def example_16_create_user_with_data(db: DB):
    """Create user with related data in transaction."""
    
    # Create user
    user = await db.table(User).create({
        "username": "john",
        "email": "john@example.com",
        "active": True,
        "role": "author"
    })
    
    # Create profile
    await db.table(Profile).create({
        "user_id": user["id"],
        "bio": "Software Developer",
        "location": "San Francisco"
    })
    
    # Create posts
    posts_data = [
        {"user_id": user["id"], "title": "First Post", "content": "Hello", "published": True},
        {"user_id": user["id"], "title": "Second Post", "content": "World", "published": True}
    ]
    await db.table(Post).create_many(posts_data)
    
    return user


# ============================================================================
# 11. ANALYTICS AND REPORTING
# ============================================================================

async def example_17_analytics_dashboard():
    """Build analytics dashboard data."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Today's stats
        today = datetime.now().date()
        stats = await db.table(User)\
            .select(
                func.count(User.id.distinct()).label("total_users"),
                func.count(Post.id.distinct()).label("total_posts"),
                func.count(Comment.id.distinct()).label("total_comments"),
                func.sum(Post.views).label("total_views")
            )\
            .left_join(Post, User.id == Post.user_id)\
            .left_join(Comment, Post.id == Comment.post_id)\
            .where(func.date(User.created_at) == today)\
            .all()
        
        # Active users this week
        week_ago = datetime.now() - timedelta(days=7)
        active_users = await db.table(User)\
            .select(User.id, User.username)\
            .where(User.created_at >= week_ago)\
            .where(User.active == True)\
            .count()
        
        return {
            "today_stats": stats[0] if stats else {},
            "active_this_week": active_users
        }


# ============================================================================
# 12. MULTI-TENANT SYSTEM WITH SCHEMAS
# ============================================================================

async def example_18_multi_tenant_query(schema_name: str):
    """Query data from specific tenant schema."""
    
    # Query from tenant's schema
    async with connection_manager.session(schema=schema_name) as session:
        db = DB(session)
        User.set_session(session)
        
        # All queries automatically use the tenant's schema
        users = await User.where(User.active == True).all()
        posts = await db.table(Post).apply_filters({"post.published__eq": True}).all()
        
        return {"users": users, "posts": posts}


# ============================================================================
# 13. COMPLETE REAL-WORLD EXAMPLE
# ============================================================================

async def example_19_complete_social_media_feed():
    """Build a social media feed with all related data."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Complex feed query
        feed = await db.table(Post)\
            .join(User, Post.user_id == User.id)\
            .left_join(Profile, User.id == Profile.user_id)\
            .left_join(
                # Subquery for comment count
                db.query()\
                  .table(Comment)\
                  .select(
                      Comment.post_id,
                      func.count(Comment.id).label("comment_count")
                  )\
                  .group_by(Comment.post_id)\
                  .build_subquery().alias("comment_stats"),
                Post.id == text("comment_stats.post_id")
            )\
            .select(
                Post.id,
                Post.title,
                Post.content,
                Post.views,
                Post.likes,
                User.username,
                User.email,
                Profile.avatar_url,
                Comment.content.label("comment_content"),
                text("comment_stats.comment_count").label("comment_count")
            )\
            .apply_filters({
                "post.published__eq": True
            })\
            .order_by(Post.created_at.desc())\
            .limit(20)\
            .all()
        
        return feed


# ============================================================================
# 14. FASTAPI INTEGRATION
# ============================================================================

app = FastAPI()

@app.get("/api/users/with-stats")
async def get_users_with_stats():
    """Get users with their statistics."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        stats = await db.table(User)\
            .select(
                User.id,
                User.username,
                User.email,
                func.count(Post.id.distinct()).label("post_count"),
                func.sum(Post.views).label("total_views"),
                func.avg(Post.views).label("avg_views"),
                func.max(Post.created_at).label("last_post_date")
            )\
            .left_join(Post, User.id == Post.user_id)\
            .group_by(User.id)\
            .having(func.count(Post.id) > 0)\
            .order_by(func.count(Post.id).desc())\
            .all()
        
        return stats


@app.get("/api/posts/popular")
async def get_popular_posts(period: str = "week"):
    """Get popular posts based on views and likes."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        # Calculate popularity score
        cutoff_date = datetime.now() - timedelta(days=7 if period == "week" else 30)
        
        popular_posts = await db.table(Post)\
            .join(User, Post.user_id == User.id)\
            .select(
                Post.id,
                Post.title,
                Post.views,
                Post.likes,
                (Post.views * 0.3 + Post.likes * 0.7).label("popularity_score"),
                User.username
            )\
            .where(Post.published == True)\
            .where(Post.created_at >= cutoff_date)\
            .order_by((Post.views * 0.3 + Post.likes * 0.7).desc())\
            .limit(10)\
            .all()
        
        return popular_posts


@app.post("/api/users/create-complete")
@with_transaction()
async def create_complete_user(db: DB, user_data: dict):
    """Create user with all related data."""
    
    User.set_session(db.session)
    
    # Create user
    user = await User.create({
        "username": user_data["username"],
        "email": user_data["email"],
        "active": True
    })
    
    # Create profile
    if "profile" in user_data:
        await db.table(Profile).create({
            "user_id": user["id"],
            **user_data["profile"]
        })
    
    return user


# ============================================================================
# 15. ADVANCED PATTERNS
# ============================================================================

async def example_20_pagination_with_totals():
    """Paginate with calculated fields."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        result = await db.table(User)\
            .select(
                User.id,
                User.username,
                func.count(Post.id).label("post_count")
            )\
            .left_join(Post, User.id == Post.user_id)\
            .group_by(User.id)\
            .having(func.count(Post.id) > 0)\
            .order_by(func.count(Post.id).desc())\
            .paginate(page=1, per_page=20)
        
        return result


async def example_21_dynamic_complex_query(params: dict):
    """Build complex query dynamically from parameters."""
    
    async with connection_manager.session() as session:
        db = DB(session)
        
        query = db.table(User)
        
        # Add joins if needed
        if params.get("include_posts"):
            query = query.left_join(Post, User.id == Post.user_id)
        
        if params.get("include_profile"):
            query = query.left_join(Profile, User.id == Profile.user_id)
        
        # Apply filters
        filters = {}
        if params.get("active"):
            filters["user.active__eq"] = params["active"]
        if params.get("role"):
            filters["user.role__eq"] = params["role"]
        if params.get("min_age"):
            filters["user.age__gte"] = params["min_age"]
        
        if filters:
            query = query.apply_filters(filters)
        
        # Order by
        if params.get("order_by"):
            if params.get("order_dir") == "desc":
                query = query.order_by(getattr(User, params["order_by"]).desc())
            else:
                query = query.order_by(getattr(User, params["order_by"]))
        
        # Paginate
        if params.get("paginate"):
            result = await query.paginate(
                params.get("page", 1),
                params.get("per_page", 20)
            )
        else:
            items = await query.all()
            result = {"items": items}
        
        return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

