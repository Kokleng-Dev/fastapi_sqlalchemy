from sqlalchemy import (
    Subquery, select, func, and_, or_, text, literal_column, insert, update, delete, 
    union, union_all, exists as sql_exists
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects import postgresql, mysql, sqlite
from typing import Any, Dict, List, Optional, Generator
import math
import copy
from .util import DBQuerySetting

class TableQuery:
    """Fluent query builder for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._reset_state()

    def _reset_state(self):
        """Reset all internal state to defaults."""
        self._schema = None
        self._base_table = None
        self._joins = []
        self._where = []
        self._or_where = []
        self._select = []
        self._order = []
        self._group_by = []
        self._having = []
        self._limit = None
        self._offset = None
        self._union_queries = []
        self._union_all = False
        self._load_options = []  # For ORM loading strategies
        self._enable_orm = False  # Whether to use ORM mode

    def _clone(self) -> "TableQuery":
        """Create a deep copy of current query state."""
        cloned = TableQuery(self.session)
        cloned._schema = self._schema
        cloned._base_table = self._base_table
        cloned._joins = copy.deepcopy(self._joins)
        cloned._where = copy.deepcopy(self._where)
        cloned._or_where = copy.deepcopy(self._or_where)
        cloned._select = copy.deepcopy(self._select)
        cloned._order = copy.deepcopy(self._order)
        cloned._group_by = copy.deepcopy(self._group_by)
        cloned._having = copy.deepcopy(self._having)
        cloned._limit = self._limit
        cloned._offset = self._offset
        cloned._union_queries = copy.deepcopy(self._union_queries)
        cloned._union_all = self._union_all
        cloned._load_options = copy.deepcopy(self._load_options)
        cloned._enable_orm = self._enable_orm
        return cloned

    @staticmethod
    def _chunk(data: list, chunk_size: int) -> Generator[List[Any], None, None]:
        """Split list into chunks of specified size."""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def _build_query(self):
        """Build the SQLAlchemy statement from accumulated conditions."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        stmt = select(*self._select or [self._base_table])

        if self._schema:
            stmt = stmt.execution_options(
                schema_translate_map={None: self._schema}
            )

        for join_type, model, onclause in self._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, self._where, self._or_where)
        
        if self._group_by:
            stmt = stmt.group_by(*self._group_by)

        if self._having:
            stmt = stmt.having(and_(*self._having))

        if self._order:
            stmt = stmt.order_by(*self._order)

        if self._limit is not None:
            stmt = stmt.limit(self._limit)
        if self._offset is not None:
            stmt = stmt.offset(self._offset)

        return stmt

    # ========================
    # Chainable Methods
    # ========================
    def new(self) -> "TableQuery":
        """Create a fresh query builder with the same session."""
        fresh_query = TableQuery(self.session)
        fresh_query._schema = self._schema
        return fresh_query

    def schema(self, schema_name: str) -> "TableQuery":
        """Set schema with validation."""
        if not isinstance(schema_name, str) or not schema_name.replace("_", "").isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")
        self._schema = schema_name
        return self

    def table(self, model) -> "TableQuery":
        """Set the base table for the query."""
        self._base_table = model
        return self

    def select(self, *columns) -> "TableQuery":
        """Specify columns to select."""
        self._select.extend(columns)
        return self
    
    def with_orm(self, enabled: bool = True) -> "TableQuery":
        """Enable ORM mode (returns SQLAlchemy objects instead of dicts)."""
        self._enable_orm = enabled
        return self
    
    def options(self, *load_strategies) -> "TableQuery":
        """
        Add SQLAlchemy loading options.
        
        Usage:
            query.options(joinedload(User.posts), selectinload(User.comments))
        """
        self._load_options.extend(load_strategies)
        return self
    
    def load_only(self, *columns) -> "TableQuery":
        """
        Load only specific columns.
        
        Usage:
            query.load_only(User.name, User.email)
        """
        from sqlalchemy.orm import load_only
        self._load_options.append(load_only(*columns))
        return self
    
    # Removed misleading alias `select_related` (Django-like name but wrong behavior).

    def where(self, *conditions) -> "TableQuery":
        """Add AND conditions."""
        self._where.extend(conditions)
        return self

    def or_where(self, *conditions) -> "TableQuery":
        """Add OR conditions."""
        self._or_where.extend(conditions)
        return self

    def where_in(self, column, values: list) -> "TableQuery":
        """Add WHERE column IN (values) condition."""
        if not isinstance(values, (list, tuple)):
            values = [values]
        self._where.append(column.in_(values))
        return self

    def where_not_in(self, column, values: list) -> "TableQuery":
        """Add WHERE column NOT IN (values) condition."""
        if not isinstance(values, (list, tuple)):
            values = [values]
        self._where.append(column.notin_(values))
        return self

    def where_null(self, column) -> "TableQuery":
        """Add WHERE column IS NULL condition."""
        self._where.append(column.is_(None))
        return self

    def where_not_null(self, column) -> "TableQuery":
        """Add WHERE column IS NOT NULL condition."""
        self._where.append(column.is_not(None))
        return self

    def where_between(self, column, values: list) -> "TableQuery":
        """Add WHERE column BETWEEN min AND max condition."""
        if not isinstance(values, (list, tuple)) or len(values) != 2:
            raise ValueError("between requires [min, max] values")
        self._where.append(column.between(values[0], values[1]))
        return self

    def where_not_between(self, column, values: list) -> "TableQuery":
        """Add WHERE column NOT BETWEEN min AND max condition."""
        if not isinstance(values, (list, tuple)) or len(values) != 2:
            raise ValueError("not_between requires [min, max] values")
        self._where.append(~column.between(values[0], values[1]))
        return self

    def where_like(self, column, pattern: str) -> "TableQuery":
        """Add WHERE column LIKE pattern condition."""
        self._where.append(column.ilike(f"%{pattern}%"))
        return self

    def join(self, model, onclause) -> "TableQuery":
        """Add an INNER JOIN."""
        self._joins.append(("inner", model, onclause))
        return self

    def left_join(self, model, onclause) -> "TableQuery":
        """Add a LEFT JOIN."""
        self._joins.append(("left", model, onclause))
        return self

    def inner_join(self, model, onclause) -> "TableQuery":
        """Add an INNER JOIN."""
        self._joins.append(("inner", model, onclause))
        return self

    def right_join(self, model, onclause) -> "TableQuery":
        """Add a RIGHT JOIN."""
        self._joins.append(("right", model, onclause))
        return self

    def full_join(self, model, onclause) -> "TableQuery":
        """Add a FULL OUTER JOIN."""
        self._joins.append(("full", model, onclause))
        return self

    def left_join_subquery(self, subquery, onclause, alias: str = None) -> "TableQuery":
        """Add a LEFT JOIN with a subquery."""
        if callable(subquery):
            subquery = subquery()
        if alias:
            subquery = subquery.alias(alias)
        self._joins.append(("left", subquery, onclause))
        return self

    def inner_join_subquery(self, subquery, onclause, alias: str = None) -> "TableQuery":
        """Add an INNER JOIN with a subquery."""
        if callable(subquery):
            subquery = subquery()
        if alias:
            subquery = subquery.alias(alias)
        self._joins.append(("inner", subquery, onclause))
        return self

    def right_join_subquery(self, subquery, onclause, alias: str = None) -> "TableQuery":
        """Add a RIGHT JOIN with a subquery."""
        if callable(subquery):
            subquery = subquery()
        if alias:
            subquery = subquery.alias(alias)
        self._joins.append(("right", subquery, onclause))
        return self

    def full_join_subquery(self, subquery, onclause, alias: str = None) -> "TableQuery":
        """Add a FULL OUTER JOIN with a subquery."""
        if callable(subquery):
            subquery = subquery()
        if alias:
            subquery = subquery.alias(alias)
        self._joins.append(("full", subquery, onclause))
        return self

    def order_by(self, *columns) -> "TableQuery":
        """Add ORDER BY clause."""
        self._order.extend(columns)
        return self

    def group_by(self, *columns) -> "TableQuery":
        """Add GROUP BY clause."""
        self._group_by.extend(columns)
        return self

    def limit(self, value: int) -> "TableQuery":
        """Set LIMIT."""
        if not isinstance(value, int) or value < 1:
            raise ValueError("Limit must be a positive integer")
        self._limit = value
        return self

    def offset(self, value: int) -> "TableQuery":
        """Set OFFSET."""
        if not isinstance(value, int) or value < 0:
            raise ValueError("Offset must be a non-negative integer")
        self._offset = value
        return self

    def take(self, value: int) -> "TableQuery":
        """Alias for limit()."""
        return self.limit(value)

    def skip(self, value: int) -> "TableQuery":
        """Alias for offset()."""
        return self.offset(value)

    def having(self, *conditions) -> "TableQuery":
        """Add HAVING clause."""
        self._having.extend(conditions)
        return self

    def union(self, *queries: "TableQuery") -> "TableQuery":
        """Combine multiple queries with UNION."""
        for q in queries:
            if not isinstance(q, TableQuery):
                raise ValueError("All arguments must be TableQuery instances")
        self._union_queries = list(queries)
        self._union_all = False
        return self

    def union_all(self, *queries: "TableQuery") -> "TableQuery":
        """Combine multiple queries with UNION ALL."""
        for q in queries:
            if not isinstance(q, TableQuery):
                raise ValueError("All arguments must be TableQuery instances")
        self._union_queries = list(queries)
        self._union_all = True
        return self

    def apply_filters(self, filters: Dict[str, Any], *, use_or: bool = False) -> "TableQuery":
        """
        Apply filters dynamically with Laravel-like syntax.
        
        Supports table.column syntax like Laravel:
        - "user.name" or "user.name__eq" - equals
        - "user.age__gt" - greater than
        - "user.email__like" - LIKE search
        - "user.id__in" - IN clause
        - etc.
        
        Available operators:
        - eq, ne, neq - Equal, not equal
        - gt, gte, lt, lte - Comparison
        - like, icontains - Pattern matching
        - in, notin - In/not in lists
        - startswith, endswith - String matching
        - between, not_between - Range queries
        - isnull, notnull - NULL checks
        
        Examples:
            # Single table filters
            query.apply_filters({"user.active__eq": True})
            query.apply_filters({"user.name__like": "john"})
            query.apply_filters({"user.age__gte": 18, "user.age__lte": 65})
            
            # With joins
            query.left_join(Post, User.id == Post.user_id)\
                 .apply_filters({
                     "user.active__eq": True,
                     "post.published__eq": True
                 })
        
        Args:
            filters: Dict with keys like "table.column__operator" and values
            use_or: Combine filters with OR instead of AND
        """
        expressions = []
        for key, value in filters.items():
            if value is None:
                continue

            parts = key.split("__")
            col_name = "__".join(parts[:-1]) if len(parts) > 1 else parts[0]
            op = parts[-1] if len(parts) > 1 else "eq"

            if "." not in col_name:
                raise ValueError(
                    f"Column must be 'table.column' or 'table.column__operator', got '{col_name}'.\n"
                    f"Examples: 'user.name', 'user.age__gt', 'post.title__like'"
                )

            table_name, column_name = col_name.split(".", 1)
            
            try:
                column = DBQuerySetting.get_column_from_model(
                    self._base_table, self._joins, table_name, column_name
                )
            except ValueError as e:
                raise ValueError(str(e))

            expr = DBQuerySetting.build_filter_expression(column, op, value)
            expressions.append(expr)

        if expressions:
            if use_or:
                combined = or_(*expressions)
                self._or_where.append(combined)
            else:
                combined = and_(*expressions)
                self._where.append(combined)

        return self

    def where_in_subquery(self, column, subquery_builder) -> "TableQuery":
        """Add WHERE ... IN (subquery) condition."""
        subq = subquery_builder()
        if not hasattr(subq, 'select'):
            subq = select(subquery_builder()).subquery()
        self._where.append(column.in_(subq))
        return self

    def where_exists_subquery(self, subquery_builder) -> "TableQuery":
        """Add WHERE EXISTS (subquery) condition."""
        subq = subquery_builder()
        self._where.append(sql_exists(subq))
        return self

    def where_not_exists_subquery(self, subquery_builder) -> "TableQuery":
        """Add WHERE NOT EXISTS (subquery) condition."""
        subq = subquery_builder()
        self._where.append(~sql_exists(subq))
        return self

    def from_subquery(self, subquery_alias: str, subquery_builder) -> "TableQuery":
        """Use a subquery as the base table."""
        subq = subquery_builder()
        self._base_table = subq.alias(subquery_alias)
        self._select = []
        self._joins = []
        self._where = []
        self._or_where = []
        return self

    def build_subquery(self) -> Subquery:
        """Build a subquery from current query."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")
        stmt = self._build_query()
        return stmt.subquery()

    # ========================
    # Execute - SELECT
    # ========================
    async def all(self) -> List[Dict[str, Any]]:
        """Execute query and return all results."""
        cloned = self._clone()
        stmt = cloned._build_query()
        result = await self.session.execute(stmt)
        cloned._reset_state()
        return [dict(row) for row in result.mappings().all()]

    async def get(self) -> List[Dict[str, Any]]:
        """Alias for all()."""
        return await self.all()

    async def first(self) -> Optional[Dict[str, Any]]:
        """Execute query and return first result."""
        cloned = self._clone()
        stmt = cloned._build_query()
        result = await self.session.execute(stmt)
        row = result.first()
        cloned._reset_state()
        return dict(row) if row else None

    async def one_or_fail(self) -> Dict[str, Any]:
        """Get exactly one record or raise exception."""
        cloned = self._clone()
        stmt = cloned._build_query()
        result = await self.session.execute(stmt)
        rows = result.all()
        cloned._reset_state()
        
        if len(rows) == 0:
            raise ValueError(f"No record found in {self._base_table.__tablename__}")
        elif len(rows) > 1:
            raise ValueError(f"Expected exactly one record, got {len(rows)}")
        
        return dict(rows[0])

    async def find(self, id: Any) -> Optional[Dict[str, Any]]:
        """Find record by primary key ID."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")
        if not hasattr(self._base_table, "id"):
            raise ValueError("Base table has no 'id' column")

        cloned = self._clone()
        stmt = cloned._build_query()
        stmt = stmt.where(self._base_table.id == id).limit(1)
        
        result = await self.session.execute(stmt)
        row = result.first()
        cloned._reset_state()
        return dict(row) if row else None

    async def find_or_fail(self, id: Any) -> Dict[str, Any]:
        """Find record by ID or raise exception."""
        result = await self.find(id)
        if not result:
            raise ValueError(f"No record found with id={id}")
        return result

    async def first_or_fail(self) -> Dict[str, Any]:
        """Get first record or raise exception."""
        result = await self.first()
        if result is None:
            raise ValueError(f"No record found in {self._base_table.__tablename__}")
        return result

    async def last(self) -> Optional[Dict[str, Any]]:
        """Get last record."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = cloned._build_query()
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        cloned._reset_state()
        return dict(rows[-1]) if rows else None

    # ========================
    # Aggregates
    # ========================
    async def count(self) -> int:
        """Count total records."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        
        if cloned._group_by:
            pk_col = getattr(cloned._base_table, "id", None)
            count_col = pk_col or (cloned._select[0] if cloned._select else literal_column("1"))
            stmt = select(func.count(func.distinct(count_col)))
        else:
            stmt = select(func.count(func.distinct(cloned._base_table.id)))

        stmt = stmt.select_from(cloned._base_table)

        for join_type, model, onclause in cloned._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, cloned._where, cloned._or_where)

        result = await self.session.execute(stmt)
        cloned._reset_state()
        return result.scalar_one() or 0

    async def max(self, column) -> Any:
        """Get maximum value of column."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = select(func.max(column)).select_from(cloned._base_table)

        for join_type, model, onclause in cloned._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, cloned._where, cloned._or_where)

        result = await self.session.execute(stmt)
        cloned._reset_state()
        return result.scalar_one()

    async def min(self, column) -> Any:
        """Get minimum value of column."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = select(func.min(column)).select_from(cloned._base_table)

        for join_type, model, onclause in cloned._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, cloned._where, cloned._or_where)

        result = await self.session.execute(stmt)
        cloned._reset_state()
        return result.scalar_one()

    async def sum(self, column) -> Any:
        """Get sum of column."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = select(func.sum(column)).select_from(cloned._base_table)

        for join_type, model, onclause in cloned._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, cloned._where, cloned._or_where)

        result = await self.session.execute(stmt)
        cloned._reset_state()
        return result.scalar_one()

    async def avg(self, column) -> Any:
        """Get average of column."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = select(func.avg(column)).select_from(cloned._base_table)

        for join_type, model, onclause in cloned._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, cloned._where, cloned._or_where)

        result = await self.session.execute(stmt)
        cloned._reset_state()
        return result.scalar_one()

    async def exists(self) -> bool:
        """Check if any record matches."""
        count = await self.count()
        return count > 0

    async def distinct(self, *columns) -> List[Dict[str, Any]]:
        """Get distinct records from query."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        
        select_cols = list(columns) if columns else [self._base_table]
        stmt = select(*select_cols).distinct()
        stmt = stmt.select_from(self._base_table)

        if cloned._schema:
            stmt = stmt.execution_options(
                schema_translate_map={None: cloned._schema}
            )

        for join_type, model, onclause in cloned._joins:
            stmt = DBQuerySetting.apply_join(stmt, join_type, model, onclause)

        stmt = DBQuerySetting.apply_where(stmt, cloned._where, cloned._or_where)
        
        if cloned._order:
            stmt = stmt.order_by(*cloned._order)

        if cloned._limit is not None:
            stmt = stmt.limit(cloned._limit)
        if cloned._offset is not None:
            stmt = stmt.offset(cloned._offset)

        result = await self.session.execute(stmt)
        cloned._reset_state()
        return [dict(row) for row in result.mappings().all()]

    async def distinct_by(self, *distinct_columns) -> List[Dict[str, Any]]:
        """Get distinct records by specific columns."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = cloned._build_query()
        result = await self.session.execute(stmt)
        rows = result.all()
        cloned._reset_state()

        if not rows:
            return []

        seen = {}
        distinct_rows = []
        
        for row in rows:
            row_dict = dict(row)
            key = tuple(row_dict.get(col.name) if hasattr(col, 'name') else row_dict.get(str(col)) 
                       for col in distinct_columns)
            
            if key not in seen:
                seen[key] = True
                distinct_rows.append(row_dict)

        return distinct_rows

    async def group_and_deduplicate(self, *group_columns) -> List[Dict[str, Any]]:
        """Group by columns and get first record per group."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        cloned = self._clone()
        stmt = cloned._build_query()
        result = await self.session.execute(stmt)
        rows = result.all()
        cloned._reset_state()

        if not rows:
            return []

        groups = {}
        grouped_rows = []

        for row in rows:
            row_dict = dict(row)
            key = tuple(row_dict.get(col.name) if hasattr(col, 'name') else row_dict.get(str(col)) 
                       for col in group_columns)
            
            if key not in groups:
                groups[key] = True
                grouped_rows.append(row_dict)

        return grouped_rows

    async def paginate(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Return paginated results with metadata."""
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10

        cloned = self._clone()

        # Count
        if cloned._group_by:
            pk_col = getattr(cloned._base_table, "id", None)
            count_col = pk_col or (cloned._select[0] if cloned._select else literal_column("1"))
            count_stmt = select(func.count(func.distinct(count_col)))
        else:
            count_stmt = select(func.count(func.distinct(cloned._base_table.id)))

        count_stmt = count_stmt.select_from(cloned._base_table)

        for join_type, model, onclause in cloned._joins:
            count_stmt = DBQuerySetting.apply_join(count_stmt, join_type, model, onclause)

        count_stmt = DBQuerySetting.apply_where(count_stmt, cloned._where, cloned._or_where)

        total_records = (await self.session.execute(count_stmt)).scalar_one() or 0
        total_pages = math.ceil(total_records / per_page) if total_records else 1
        offset = (page - 1) * per_page
        has_more = page < total_pages

        paginated_stmt = cloned._build_query()
        paginated_stmt = paginated_stmt.limit(per_page).offset(offset)
        
        result = await self.session.execute(paginated_stmt)
        items = [dict(row) for row in result.mappings().all()]

        pagination = {
            "total_records": total_records,
            "limit": per_page,
            "offset": offset,
            "has_more": has_more,
            "total_pages": total_pages,
            "current_page": page,
            "first_page": 1,
            "previous_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if has_more else None,
            "last_page": total_pages,
        }

        self._reset_state()
        return {"items": items, "pagination": pagination}

    # ========================
    # CREATE
    # ========================
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record and return it with ID."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        if not data:
            raise ValueError("Data cannot be empty")

        for key in data.keys():
            if not hasattr(self._base_table, key):
                raise ValueError(f"Column '{key}' does not exist on table '{self._base_table.__tablename__}'")

        stmt = insert(self._base_table).values(**data)
        
        if self._schema:
            stmt = stmt.execution_options(
                schema_translate_map={None: self._schema}
            )

        try:
            stmt_with_returning = stmt.returning(self._base_table)
            result = await self.session.execute(stmt_with_returning)
            await self.session.commit()
            
            row = result.first()
            self._reset_state()
            return dict(row) if row else None
        except Exception:
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            inserted_id = result.lastrowid
            
            select_stmt = select(self._base_table).where(self._base_table.id == inserted_id)
            fetch_result = await self.session.execute(select_stmt)
            row = fetch_result.first()
            
            self._reset_state()
            return dict(row) if row else None

    async def create_many(self, data_list: List[Dict[str, Any]], chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Create multiple records in chunks and return them."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        if not data_list:
            raise ValueError("Data list cannot be empty")

        for data in data_list:
            for key in data.keys():
                if not hasattr(self._base_table, key):
                    raise ValueError(f"Column '{key}' does not exist on table '{self._base_table.__tablename__}'")

        all_results = []
        chunks = self._chunk(data_list, chunk_size)
        
        for chunk in chunks:
            stmt = insert(self._base_table)
            
            if self._schema:
                stmt = stmt.execution_options(
                    schema_translate_map={None: self._schema}
                )

            try:
                stmt_with_returning = stmt.returning(self._base_table)
                result = await self.session.execute(stmt_with_returning, chunk)
                await self.session.commit()
                
                rows = result.all()
                all_results.extend([dict(row) for row in rows])
            except Exception:
                result = await self.session.execute(stmt, chunk)
                await self.session.commit()
                
                select_stmt = select(self._base_table).order_by(self._base_table.id.desc()).limit(len(chunk))
                fetch_result = await self.session.execute(select_stmt)
                rows = fetch_result.all()
                all_results.extend([dict(row) for row in rows])
        
        self._reset_state()
        return all_results

    # ========================
    # UPDATE
    # ========================
    async def update(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update records matching WHERE conditions."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        if not data:
            raise ValueError("Data cannot be empty")

        if not self._where and not self._or_where:
            raise ValueError("WHERE clause required for UPDATE. Use .where() first.")

        for key in data.keys():
            if not hasattr(self._base_table, key):
                raise ValueError(f"Column '{key}' does not exist on table '{self._base_table.__tablename__}'")

        # Get IDs of records to update
        id_stmt = select(self._base_table.id)
        id_stmt = DBQuerySetting.apply_where(id_stmt, self._where, self._or_where)

        id_result = await self.session.execute(id_stmt)
        affected_ids = [row[0] for row in id_result.all()]

        # Update
        stmt = update(self._base_table).values(**data)
        stmt = DBQuerySetting.apply_where(stmt, self._where, self._or_where)

        if self._schema:
            stmt = stmt.execution_options(
                schema_translate_map={None: self._schema}
            )

        await self.session.execute(stmt)
        await self.session.commit()

        # Fetch and return updated records
        select_stmt = select(self._base_table).where(
            self._base_table.id.in_(affected_ids)
        )
        result = await self.session.execute(select_stmt)
        rows = result.all()
        
        self._reset_state()
        return [dict(row) for row in rows]

    async def update_by_id(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record by primary key."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        if not hasattr(self._base_table, "id"):
            raise ValueError("Base table has no 'id' column")

        if not data:
            raise ValueError("Data cannot be empty")

        updated = await self.where(self._base_table.id == id).update(data)
        return updated[0] if updated else None

    # ========================
    # DELETE
    # ========================
    async def delete(self) -> int:
        """Delete records matching WHERE conditions."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        if not self._where and not self._or_where:
            raise ValueError("WHERE clause required for DELETE. Use .where() first.")

        stmt = delete(self._base_table)
        stmt = DBQuerySetting.apply_where(stmt, self._where, self._or_where)

        if self._schema:
            stmt = stmt.execution_options(
                schema_translate_map={None: self._schema}
            )

        result = await self.session.execute(stmt)
        await self.session.commit()
        
        self._reset_state()
        return result.rowcount

    async def delete_by_id(self, id: Any) -> int:
        """Delete a record by primary key."""
        if not self._base_table:
            raise ValueError("Base table not set. Use .table(Model) first.")

        if not hasattr(self._base_table, "id"):
            raise ValueError("Base table has no 'id' column")

        return await self.where(self._base_table.id == id).delete()

    # ========================
    # Transactions
    # ========================
    async def begin_transaction(self):
        """Begin a transaction."""
        await self.session.begin()

    async def commit(self):
        """Commit the transaction."""
        await self.session.commit()

    async def rollback(self):
        """Rollback the transaction."""
        await self.session.rollback()

    def transaction(self):
        """Context manager for transaction."""
        return self.session.begin()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.begin_transaction()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    # ========================
    # SQL Debugging
    # ========================
    def to_sql(self, dialect: str = "postgresql", show_params: bool = False) -> str:
        """Convert query to SQL string."""
        stmt = self._build_query()
        
        dialect_map = {
            'postgresql': postgresql.dialect(),
            'postgres': postgresql.dialect(),
            'mysql': mysql.dialect(),
            'sqlite': sqlite.dialect(),
        }
        
        dialect_obj = dialect_map.get(dialect.lower(), postgresql.dialect())
        
        try:
            compiled = stmt.compile(dialect=dialect_obj, compile_kwargs={"literal_binds": show_params})
        except Exception:
            compiled = stmt.compile(dialect=dialect_obj)
        
        return str(compiled)

    def print_sql(self, dialect: str = "postgresql", show_params: bool = False) -> None:
        """Print query as SQL."""
        sql = self.to_sql(dialect=dialect, show_params=show_params)
        print("\n" + "="*80)
        print(f"SQL Query ({dialect.upper()}):")
        print("="*80)
        print(sql)
        print("="*80 + "\n")

    def format_sql(self, dialect: str = "postgresql", show_params: bool = False, indent: int = 2) -> str:
        """Format SQL with indentation."""
        sql = self.to_sql(dialect=dialect, show_params=show_params)
        
        keywords = ['SELECT', 'FROM', 'WHERE', 'LEFT JOIN', 'INNER JOIN', 'RIGHT JOIN', 'FULL JOIN', 
                   'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT', 'OFFSET', 'UNION', 'UNION ALL',
                   'AND', 'OR', 'ON', 'AS']
        
        formatted = sql
        for keyword in keywords:
            formatted = formatted.replace(f' {keyword} ', f'\n{keyword} ')
            formatted = formatted.replace(f' {keyword}(', f'\n{keyword}(')
        
        lines = formatted.split('\n')
        indented = '\n'.join([(' ' * indent) + line.strip() if line.strip() else line 
                             for line in lines])
        
        return indented

    def print_formatted_sql(self, dialect: str = "postgresql", show_params: bool = False, indent: int = 2) -> None:
        """Print formatted SQL with indentation."""
        formatted = self.format_sql(dialect=dialect, show_params=show_params, indent=indent)
        print("\n" + "="*80)
        print(f"Formatted SQL Query ({dialect.upper()}):")
        print("="*80)
        print(formatted)
        print("="*80 + "\n")
