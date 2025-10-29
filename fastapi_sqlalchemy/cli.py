"""
CLI entry point for FastAPI SQLAlchemy commands.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi_sqlalchemy.migration import MigrationManager


def main_entry():
    """Entry point function for CLI command."""
    asyncio.run(main())

async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("FastAPI SQLAlchemy - Database Management CLI")
        print("\\nAvailable commands:")
        print("  migration")
        print("    init              - Initialize Alembic in the project")
        print("    makemigrations    - Create new migration files")
        print("    migrate           - Apply migrations to database")
        print("    showmigrations    - Show migration status")
        print("    downgrade         - Downgrade database to a specific revision")
        print("\\nUsage: python -m fastapi_sqlalchemy.cli migration <command> [options]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "migration":
        if len(sys.argv) < 3:
            print("Migration commands:")
            print("  init              - Initialize Alembic")
            print("  makemigrations    - Create new migrations")
            print("  migrate           - Apply migrations")
            print("  showmigrations    - Show migration status")
            print("  downgrade         - Downgrade database")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        manager = MigrationManager()
        
        if subcommand == "init":
            # Check if app_name is provided for modular migrations
            app_path = sys.argv[3] if len(sys.argv) > 3 else None
            if app_path:
                manager = MigrationManager(migrations_dir=app_path)
            await manager.init()
        elif subcommand == "makemigrations":
            # Support: makemigrations workspace [message] or makemigrations [message]
            if len(sys.argv) > 3:
                arg = sys.argv[3]
                # Check if it looks like a path (contains slashes)
                if "/" in arg or "\\" in arg or arg.endswith("migrations"):
                    # Modular migration
                    migrations_path = arg
                    message = sys.argv[4] if len(sys.argv) > 4 else ""
                    manager = MigrationManager(migrations_dir=migrations_path)
                    await manager.makemigrations(message=message)
                else:
                    # Centralized migration with message
                    message = arg
                    await manager.makemigrations(message=message)
            else:
                # Centralized migration without message
                await manager.makemigrations()
        elif subcommand == "migrate":
            target = sys.argv[3] if len(sys.argv) > 3 else "head"
            await manager.migrate(target)
        elif subcommand == "showmigrations":
            await manager.showmigrations()
        elif subcommand == "downgrade":
            revision = sys.argv[3] if len(sys.argv) > 3 else "-1"
            await manager.downgrade(revision)
        else:
            print(f"Unknown migration command: {subcommand}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
