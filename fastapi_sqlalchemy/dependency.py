from .connection import connection_manager

async def get_db_session():
    """FastAPI dependency for database session."""
    async with connection_manager.session() as session:  # Auto-closes
        yield session
