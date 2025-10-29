"""
Migration module for Alembic integration with Django-like commands.
Provides CLI commands for managing database migrations.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, List
from alembic import config as alembic_config
from alembic import command as alembic_command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from .connection import connection_manager
from .config import db_settings
from .base_model import Base


class MigrationManager:
    """
    Django-like migration manager using Alembic with modular support.
    
    Supports both centralized and modular migrations (one per app/feature).
    
    Usage:
        # Centralized migrations
        manager = MigrationManager()
        await manager.init()
        await manager.makemigrations()
        
        # Modular migrations (Django-style)
        user_manager = MigrationManager(migrations_dir="apps/users/migrations")
        await user_manager.init()
        await user_manager.makemigrations()
    """
    
    def __init__(self, migrations_dir: Optional[str] = None, app_name: Optional[str] = None):
        """
        Initialize migration manager.
        
        Args:
            migrations_dir: Path to migrations directory (e.g., "apps/users/migrations")
                           Defaults to "migrations" for centralized migrations
            app_name: Name of the app/module (optional, auto-detected from path)
        """
        self.base_dir = Path.cwd()
        
        if migrations_dir is None:
            # Default centralized migrations
            self.migrations_dir = self.base_dir / "migrations"
            self.app_name = None
        else:
            # Modular migrations
            self.migrations_dir = Path(migrations_dir)
            if not self.migrations_dir.is_absolute():
                self.migrations_dir = self.base_dir / self.migrations_dir
            
            # Auto-detect app name from path (e.g., "apps/users/migrations" -> "users")
            if app_name:
                self.app_name = app_name
            else:
                parts = self.migrations_dir.parts
                # Try to extract app name (assuming structure like apps/APP_NAME/migrations)
                if len(parts) >= 3 and parts[-1] == "migrations":
                    self.app_name = parts[-2]
                else:
                    self.app_name = "app"
        self.alembic_ini_path = self.base_dir / "alembic.ini"
        self.alembic_dir = self.migrations_dir / "versions"
        
    async def init(self, app_name: str = None):
        """
        Initialize Alembic in the project.
        
        Args:
            app_name: Name of the app (optional, will use detected name if not provided)
        """
        if self.app_name and app_name is None:
            app_name = self.app_name
        
        # Check for alembic.ini (only needed for centralized migrations)
        if not self.alembic_ini_path.exists() and self.app_name is None:
            print("⚠️  No alembic.ini found. Creating centralized migration system...")
        
        # Create migrations directory
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.alembic_dir.mkdir(parents=True, exist_ok=True)
        
        # Create alembic.ini only for centralized migrations or if it doesn't exist
        if not self.alembic_ini_path.exists():
            self._create_alembic_ini()
        
        # Create alembic env.py
        self._create_env_py(app_name)
        
        # Create script.py.mako
        self._create_script_template()
        
        if self.app_name:
            print(f"✓ Initialized migrations for module '{self.app_name}' in '{self.migrations_dir}'")
        else:
            print(f"✓ Initialized Alembic migrations in '{self.migrations_dir}'")
    
    def _create_alembic_ini(self):
        """Create alembic.ini configuration file."""
        ini_content = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = {script_location}

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; This defaults
# to migrations/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path.
# The path separator used here should be the separator specified by "version_path_separator" below.
# version_locations = %(here)s/bar:%(here)s/bat:migrations/versions

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# If this key is omitted entirely, it falls back to the legacy behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""".format(script_location=str(self.migrations_dir.relative_to(self.base_dir)))
        
        self.alembic_ini_path.write_text(ini_content)
    
    def _create_env_py(self, app_name: str = None):
        """Create alembic env.py for async support."""
        app_name_str = app_name or self.app_name or "app"

        header = f'"""Alembic environment for async migrations - {app_name_str} module."""\n\n'
        body = '''from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import your models and Base
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps"))

# Import your models here to ensure they're registered
# Example for module-specific models:
# from apps.<module>.models import *  # Uncomment and import your models

# Import the BaseModel or Base
try:
    from fastapi_sqlalchemy.base_model import Base
except ImportError:
    Base = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
if Base is not None:
    target_metadata = Base.metadata
else:
    target_metadata = None

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Read database URL from connection manager
    try:
        from fastapi_sqlalchemy.connection import connection_manager
        from fastapi_sqlalchemy.config import db_settings

        # Get default connection URL
        config_instance = db_settings.get_config()
        url = config_instance.get_url()
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
    except Exception as e:
        print(f"Warning: Could not configure URL from connection_manager: {e}")
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    try:
        from fastapi_sqlalchemy.connection import connection_manager
        from fastapi_sqlalchemy.config import db_settings

        # Initialize connection manager if not already initialized
        if not connection_manager._initialized:
            await connection_manager.initialize()

        # Get default connection URL
        config_instance = db_settings.get_config()
        url = config_instance.get_url()

        connectable = async_engine_from_config(
            {"sqlalchemy.url": url},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    except Exception as e:
        print(f"Warning: Could not use connection_manager: {e}")
        configuration = config.get_section(config.config_ini_section, {})
        configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
        connectable = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
'''

        env_py_path = self.migrations_dir / "env.py"
        env_py_path.write_text(header + body)
    
    def _create_script_template(self):
        """Create script.py.mako template."""
        template_content = """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
"""
        
        script_template_path = self.migrations_dir / "script.py.mako"
        script_template_path.write_text(template_content)
    
    async def makemigrations(self, message: str = "", autogenerate: bool = True):
        """Create new migration files (Django-like)."""
        if not self.alembic_ini_path.exists():
            print("❌ Alembic not initialized. Run 'init' first.")
            return
        
        # Get Alembic config
        cfg = Config(str(self.alembic_ini_path))
        
        # Update script location for modular migrations
        if self.app_name:
            cfg.set_main_option("script_location", str(self.migrations_dir.relative_to(self.base_dir)))
        
        # Update the database URL in config
        try:
            await connection_manager.initialize()
            config_instance = db_settings.get_config()
            cfg.set_main_option("sqlalchemy.url", config_instance.get_url())
        except Exception as e:
            print(f"Warning: Could not update database URL: {e}")
        
        # Create migration
        if message:
            alembic_command.revision(cfg, message=message, autogenerate=autogenerate)
        else:
            migration_message = f"Auto-migration for {self.app_name}" if self.app_name else ""
            alembic_command.revision(cfg, autogenerate=autogenerate, message=migration_message)
        
        app_label = f" (module: {self.app_name})" if self.app_name else ""
        print(f"✓ Created new migration files{app_label}")
    
    async def migrate(self, target: str = "head"):
        """Apply migrations (Django-like)."""
        if not self.alembic_ini_path.exists():
            print("❌ Alembic not initialized. Run 'init' first.")
            return
        
        # Initialize connection manager
        await connection_manager.initialize()
        
        # Get Alembic config
        cfg = Config(str(self.alembic_ini_path))
        
        # Update the database URL in config
        try:
            config_instance = db_settings.get_config()
            cfg.set_main_option("sqlalchemy.url", config_instance.get_url())
        except Exception as e:
            print(f"Warning: Could not update database URL: {e}")
        
        # Run migrations
        alembic_command.upgrade(cfg, target)
        
        print(f"✓ Applied migrations to {target}")
    
    async def showmigrations(self):
        """Show migration status (Django-like)."""
        if not self.alembic_ini_path.exists():
            print("❌ Alembic not initialized.")
            return
        
        cfg = Config(str(self.alembic_ini_path))
        
        script = ScriptDirectory.from_config(cfg)
        revisions = list(script.walk_revisions())
        
        if not revisions:
            print("No migrations found.")
            return
        
        print("\\nMigration History:")
        for rev in reversed(revisions):
            print(f"  {rev.revision[:8]} - {rev.doc}")
    
    async def downgrade(self, revision: str = "-1"):
        """Downgrade to a specific revision."""
        if not self.alembic_ini_path.exists():
            print("❌ Alembic not initialized.")
            return
        
        await connection_manager.initialize()
        
        cfg = Config(str(self.alembic_ini_path))
        
        try:
            config_instance = db_settings.get_config()
            cfg.set_main_option("sqlalchemy.url", config_instance.get_url())
        except Exception as e:
            print(f"Warning: Could not update database URL: {e}")
        
        alembic_command.downgrade(cfg, revision)
        
        print(f"✓ Downgraded to {revision}")


async def cli():
    """CLI entry point for migration commands."""
    if len(sys.argv) < 2:
        print("Usage: python -m fastapi_sqlalchemy.migration <command>")
        print("Commands:")
        print("  init              - Initialize Alembic in the project")
        print("  makemigrations    - Create new migration files")
        print("  migrate           - Apply migrations")
        print("  showmigrations    - Show migration status")
        print("  downgrade         - Downgrade database")
        sys.exit(1)
    
    command = sys.argv[1]
    manager = MigrationManager()
    
    if command == "init":
        await manager.init()
    elif command == "makemigrations":
        await manager.makemigrations()
    elif command == "migrate":
        await manager.migrate()
    elif command == "showmigrations":
        await manager.showmigrations()
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        await manager.downgrade(revision)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(cli())
