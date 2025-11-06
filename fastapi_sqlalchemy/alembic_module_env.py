def include_object(object, name, type_, reflected, compare_to):
    """
    Determine whether to include an object in the migration.

    - reflected=True: object exists in database
    - reflected=False: object exists in model
    - compare_to is None when object only exists in one place
    """
    if type_ == "table":
        # Always include the version table
        if name == version_table:
            return True

        # For tables in our metadata, always include them
        if not reflected and object in target_metadata.tables.values():
            return True

        # For reflected tables (in DB), check if they're in our metadata
        if reflected:
            return name in target_metadata.tables

        return False

    elif type_ == "column":
        # Get the table this column belongs to
        table = object.table if hasattr(object, 'table') else None

        # If column is from our models
        if not reflected and table is not None:
            return table in target_metadata.tables.values()

        # If column is reflected from DB
        if reflected and table is not None:
            return table.name in target_metadata.tables

        return False

    elif type_ == "index":
        # Include indexes for our tables
        if hasattr(object, 'table'):
            table = object.table
            if not reflected and table in target_metadata.tables.values():
                return True
            if reflected and table.name in target_metadata.tables:
                return True
        return False

    elif type_ == "unique_constraint":
        # Include unique constraints for our tables
        if hasattr(object, 'table'):
            table = object.table
            if not reflected and table in target_metadata.tables.values():
                return True
            if reflected and table.name in target_metadata.tables:
                return True
        return False

    elif type_ == "foreign_key_constraint":
        # Include foreign keys for our tables
        if hasattr(object, 'table'):
            table = object.table
            if not reflected and table in target_metadata.tables.values():
                return True
            if reflected and table.name in target_metadata.tables:
                return True
        return False

    # For other types, include them
    return True
