from sqlalchemy import and_, or_
from typing import Any, List

class DBQuerySetting:
    """Utility class for query building logic."""
    
    @staticmethod
    def apply_join(stmt, join_type: str, model, onclause):
        """Apply a single join to statement."""
        if join_type == "right":
            return stmt.join(model, onclause, isouter=True, full=False)
        elif join_type == "full":
            return stmt.join(model, onclause, isouter=True, full=True)
        else:
            return stmt.join(model, onclause, isouter=(join_type == "left"))

    @staticmethod
    def apply_where(stmt, where_conditions: list, or_conditions: list):
        """Apply WHERE and OR WHERE conditions to statement."""
        if not where_conditions and not or_conditions:
            return stmt

        conditions = []
        
        if where_conditions:
            if len(where_conditions) == 1:
                conditions.append(where_conditions[0])
            else:
                conditions.append(and_(*where_conditions))
        
        if or_conditions:
            if len(or_conditions) == 1:
                conditions.append(or_conditions[0])
            else:
                conditions.append(or_(*or_conditions))
        
        if len(conditions) == 1:
            return stmt.where(conditions[0])
        else:
            return stmt.where(and_(*conditions))

    @staticmethod
    def build_filter_expression(column, op: str, value: Any):
        """Build a single filter expression based on operator."""
        if op == "eq":
            return column == value
        elif op in ("ne", "neq"):
            return column != value
        elif op == "gt":
            return column > value
        elif op == "gte":
            return column >= value
        elif op == "lt":
            return column < value
        elif op == "lte":
            return column <= value
        elif op in ("like", "icontains"):
            return column.ilike(f"%{value}%")
        elif op == "in":
            return column.in_(value if isinstance(value, list) else [value])
        elif op == "notin":
            return column.notin_(value if isinstance(value, list) else [value])
        elif op == "is":
            return column.is_(value)
        elif op == "not":
            return column.is_not(value)
        elif op == "isnull":
            return column.is_(None)
        elif op == "notnull":
            return column.is_not(None)
        elif op == "startswith":
            return column.startswith(value)
        elif op == "endswith":
            return column.endswith(value)
        elif op == "contains":
            return column.contains(value)
        elif op == "regexp":
            return column.regexp_match(value)
        elif op == "between":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("'between' requires [min, max] values")
            return column.between(value[0], value[1])
        elif op == "not_between":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("'not_between' requires [min, max] values")
            return ~column.between(value[0], value[1])
        elif op == "isnot":
            return column.is_not(value)
        else:
            raise ValueError(f"Unsupported operator: '{op}'")

    @staticmethod
    def get_column_from_model(base_table, joins: list, table_name: str, column_name: str):
        """Get a column from base table or any joined table."""
        model = None
        
        if base_table:
            table_name_lower = table_name.lower()
            base_table_name = getattr(base_table, '__tablename__', 'unknown').lower()
            base_model_name = getattr(base_table, '__name__', 'unknown').lower()
            
            if table_name_lower == base_table_name or table_name_lower == base_model_name:
                model = base_table
        
        if not model:
            for _, join_model, _ in joins:
                table_name_lower = table_name.lower()
                
                model_table_name = getattr(join_model, '__tablename__', None)
                if model_table_name:
                    model_table_name = model_table_name.lower()
                
                model_name = getattr(join_model, '__name__', None)
                if model_name:
                    model_name = model_name.lower()
                
                alias_name = getattr(join_model, 'name', None)
                if alias_name:
                    alias_name = alias_name.lower()
                
                if (table_name_lower == model_table_name or 
                    table_name_lower == model_name or 
                    table_name_lower == alias_name):
                    model = join_model
                    break
        
        if not model:
            available = DBQuerySetting.get_available_tables(base_table, joins)
            raise ValueError(f"Unknown table/model '{table_name}'. Available: {available}")
        
        if not hasattr(model, column_name):
            raise ValueError(f"Column '{column_name}' not found in '{table_name}'.")
        
        return getattr(model, column_name)

    @staticmethod
    def get_available_tables(base_table, joins: list) -> str:
        """Get list of available table names for error messages."""
        tables = []
        
        if base_table:
            table_name = getattr(base_table, '__tablename__', 'unknown')
            model_name = getattr(base_table, '__name__', 'unknown')
            tables.append(f"{model_name}({table_name})")
        
        for _, join_model, _ in joins:
            table_name = getattr(join_model, '__tablename__', None) or getattr(join_model, 'name', 'unknown')
            model_name = getattr(join_model, '__name__', None)
            
            if model_name:
                tables.append(f"{model_name}({table_name})")
            else:
                tables.append(f"subquery({table_name})")
        
        return ", ".join(tables)



