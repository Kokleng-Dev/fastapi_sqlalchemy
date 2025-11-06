"""
Atomic transaction decorator - Django-like atomic() for SQLAlchemy
Supports nested transactions via savepoints
"""

import functools
import contextvars
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

# Context variables for async per-request/session management
_transaction_ctx = contextvars.ContextVar("transaction_stack", default=None)


class TransactionStack:
    """Manages nested transactions with savepoints"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.depth = 0
        self.savepoints: List[str] = []

    async def begin(self):
        """Start transaction or savepoint"""
        if self.depth == 0:
            # Start actual transaction
            self.transaction = await self.db.begin()
        else:
            # Create savepoint for nested transaction
            savepoint = await self.db.begin_nested()
            self.savepoints.append(savepoint)

        self.depth += 1

    async def commit(self):
        """Commit transaction or release savepoint"""
        self.depth -= 1

        if self.depth == 0:
            # Commit actual transaction
            await self.db.commit()
            self.transaction = None
        # Savepoints are auto-released on success

    async def rollback(self):
        """Rollback transaction or savepoint"""
        self.depth -= 1

        if self.depth == 0:
            # Rollback actual transaction
            await self.db.rollback()
            self.transaction = None
        else:
            # Rollback last savepoint
            if self.savepoints:
                await self.savepoints.pop().rollback()


def _get_db_from_args_kwargs(*args, **kwargs) -> AsyncSession:
    """Extract AsyncSession from args or kwargs (by type, not name)"""
    # Check positional args first
    for arg in args:
        if isinstance(arg, AsyncSession):
            return arg

    # Check kwargs for any AsyncSession parameter (any name)
    for value in kwargs.values():
        if isinstance(value, AsyncSession):
            return value

    raise ValueError("No AsyncSession found in arguments")


def atomic(func=None, *, standalone=False):
    """
    Decorator to wrap a function with atomic transaction

    Args:
        standalone: If True, service has its own transaction (failures don't affect parent)
                   If False (default), uses parent transaction or creates new one (all-or-nothing)

    Usage:
        # Default - all changes rollback together
        @atomic
        async def create_user(db: AsyncSession, data: dict):
            user = User(**data)
            db.add(user)
            return user

        # Standalone - failures don't affect parent transaction
        @atomic(standalone=True)
        async def send_email(db: AsyncSession, email: str):
            await EmailService.send(db, email)

        @atomic
        async def register_user(db: AsyncSession, user_data: dict):
            # This is atomic with parent
            user = await create_user(db, user_data)

            # This is standalone - if email fails, user still created
            try:
                await send_email(db, user_data.email)
            except:
                pass  # Email failure doesn't rollback user creation

            return user
    """
    if func is None:
        return functools.partial(atomic, standalone=standalone)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        db = _get_db_from_args_kwargs(*args, **kwargs)

        if standalone:
            # Standalone: Create independent transaction
            txn_stack = TransactionStack(db)
            try:
                await txn_stack.begin()
                result = await func(*args, **kwargs)
                await txn_stack.commit()
                return result
            except Exception as e:
                await txn_stack.rollback()
                raise
        else:
            # Shared: Use parent transaction or create new one
            txn_stack: Optional[TransactionStack] = _transaction_ctx.get()

            if txn_stack is None:
                # First level transaction
                txn_stack = TransactionStack(db)
                token = _transaction_ctx.set(txn_stack)
            else:
                token = None

            try:
                await txn_stack.begin()
                result = await func(*args, **kwargs)
                await txn_stack.commit()
                return result
            except Exception as e:
                await txn_stack.rollback()
                raise e
            finally:
                # Reset context if we created it
                if token is not None:
                    _transaction_ctx.reset(token)

    return wrapper
