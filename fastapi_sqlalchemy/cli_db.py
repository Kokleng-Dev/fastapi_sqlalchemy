# fastgo/cli/migration.py
"""
Migration management CLI commands using Typer
Supports modular migrations per folder with nested modules
Multiple models per module in models/ folder
"""

import os
import subprocess
import typer
import re
from pathlib import Path
from typing import Optional
import importlib.util
import sys

from fastgo.core.config import get_settings

cli = typer.Typer(help="Manage database migrations")

class MigrationManager:
    """Manages migrations for each module"""

    def __init__(self, app_dir: str = "app"):
        self.app_dir = app_dir
        self.app_path = Path(app_dir)

    def resolve_module_path(self, module_path: str) -> Optional[Path]:
        """
        Resolve module path (e.g., 'users' or 'users/mobile')
        Returns the path if it exists, None otherwise
        """
        target_path = self.app_path / module_path

        if not target_path.exists():
            return None

        return target_path

    def has_models(self, module_path: Path) -> bool:
        """Check if module has models folder or models.py file"""
        models_folder = module_path / "models"
        models_file = module_path / "models.py"

        return models_folder.is_dir() or models_file.is_file()

    def get_modules_with_models(self, parent_path: Optional[Path] = None):
        """
        Recursively find all modules with models
        Returns dict with nested module paths as keys
        """
        modules = {}
        search_path = parent_path or self.app_path

        if not search_path.exists():
            return modules

        for item in search_path.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                if self.has_models(item):
                    # Get relative path from app_dir
                    rel_path = item.relative_to(self.app_path).as_posix()
                    modules[rel_path] = {
                        "path": item,
                        "models_dir": item / "models",
                        "models_file": item / "models.py",
                        "migrations": item / "migrations",
                        "has_migrations": (item / "migrations").exists()
                    }

                # Recursively search in subdirectories
                sub_modules = self.get_modules_with_models(item)
                modules.update(sub_modules)

        return modules

    def get_base_model_class(self, module_path: Path):
        """Import and get Base model class from module"""
        try:
            # Try models folder first
            models_dir = module_path / "models"
            if models_dir.exists():
                init_file = models_dir / "__init__.py"
                if init_file.exists():
                    spec = importlib.util.spec_from_file_location("models", init_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "Base"):
                        return module.Base

            # Try models.py file
            models_file = module_path / "models.py"
            if models_file.exists():
                spec = importlib.util.spec_from_file_location("models", models_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "Base"):
                    return module.Base
        except Exception as e:
            typer.echo(f"⚠️  Could not load Base model: {e}", err=True)

        return None

    def init_module_migration(self, module_name: str):
        """Initialize Alembic for a module"""
        module_path = self.resolve_module_path(module_name)

        if not module_path:
            typer.echo(f"❌ Module '{module_name}' not found", err=True)
            return False

        if not self.has_models(module_path):
            typer.echo(f"❌ Module '{module_name}' has no models folder or models.py", err=True)
            return False

        migrations_dir = module_path / "migrations"

        if migrations_dir.exists():
            typer.echo(f"⚠️  Migrations already initialized for '{module_name}'")
            return True

        try:
            # Create migrations directory structure
            migrations_dir.mkdir(exist_ok=True)
            (migrations_dir / "versions").mkdir(exist_ok=True)

            # Create alembic.ini for this module
            alembic_ini = module_path / "alembic.ini"
            self._create_alembic_ini(module_name, alembic_ini)

            # Create env.py
            env_py = migrations_dir / "env.py"
            self._create_env_py(module_name, env_py)

            # Create script.py.mako
            script_py_mako = migrations_dir / "script.py.mako"
            self._create_script_mako(script_py_mako)

            # Create __init__.py files
            (migrations_dir / "__init__.py").touch()
            (migrations_dir / "versions" / "__init__.py").touch()

            typer.echo(f"✅ Alembic initialized for module '{module_name}'")
            return True

        except Exception as e:
            typer.echo(f"❌ Error initializing migrations: {e}", err=True)
            return False

    def create_migration(self, module_name: Optional[str] = None, message: str = "auto migration"):
        """Create a new migration (always for default schema)"""
        if module_name:
            module_path = self.resolve_module_path(module_name)
            if not module_path:
                typer.echo(f"❌ Module '{module_name}' not found", err=True)
                return

            modules = {module_name: {
                "path": module_path,
                "has_migrations": (module_path / "migrations").exists()
            }}
        else:
            modules = self.get_modules_with_models()

        if not modules:
            typer.echo("❌ No modules found with models", err=True)
            return

        for mod_name, mod_info in modules.items():
            if not mod_info.get("has_migrations"):
                typer.echo(f"⚠️  Skipping '{mod_name}' - migrations not initialized (run: fastgo db init --module {mod_name})")
                continue

            try:
                alembic_ini = self.app_path / mod_name / "alembic.ini"

                cmd = [
                    sys.executable, "-m", "alembic",
                    "-c", str(alembic_ini),
                    "revision",
                    "--autogenerate",
                    "-m", message
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    typer.echo(f"✅ Migration created for '{mod_name}': {message}")
                    if result.stdout.strip():
                        typer.echo(result.stdout)
                else:
                    typer.echo(f"❌ Error creating migration for '{mod_name}':", err=True)
                    if result.stderr:
                        typer.echo(result.stderr, err=True)
                    if result.stdout:
                        typer.echo(result.stdout, err=True)

            except Exception as e:
                typer.echo(f"❌ Error: {e}", err=True)

    def migrate(self, module_name: Optional[str] = None, revision: str = "head", schema: Optional[str] = None):
        """Apply migrations"""
        if module_name:
            module_path = self.resolve_module_path(module_name)
            if not module_path:
                typer.echo(f"❌ Module '{module_name}' not found", err=True)
                return

            modules = {module_name: {
                "path": module_path,
                "has_migrations": (module_path / "migrations").exists()
            }}
        else:
            modules = self.get_modules_with_models()

        if not modules:
            typer.echo("❌ No modules found", err=True)
            return

        for mod_name, mod_info in modules.items():
            if not mod_info.get("has_migrations"):
                typer.echo(f"⚠️  Skipping '{mod_name}' - no migrations initialized")
                continue

            # Check if there are actual migration files
            migrations_dir = self.app_path / mod_name / "migrations" / "versions"
            migration_files = list(migrations_dir.glob("*.py"))
            migration_files = [f for f in migration_files if not f.name.startswith("__")]

            if not migration_files:
                typer.echo(f"⚠️  Skipping '{mod_name}' - no migration files")
                continue

            try:
                alembic_ini = self.app_path / mod_name / "alembic.ini"

                # Update alembic.ini with schema if provided
                if schema:
                    self._update_alembic_ini_schema(alembic_ini, schema)

                cmd = [
                    sys.executable, "-m", "alembic",
                    "-c", str(alembic_ini),
                    "upgrade",
                    revision
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                schema_info = f" (schema: {schema})" if schema else ""
                if result.returncode == 0:
                    typer.echo(f"✅ Migrated '{mod_name}'{schema_info} to {revision}")
                else:
                    typer.echo(f"❌ Error migrating '{mod_name}':", err=True)
                    typer.echo(result.stderr, err=True)

            except Exception as e:
                typer.echo(f"❌ Error: {e}", err=True)

    def rollback(self, module_name: Optional[str] = None, steps: Optional[int] = None, revision: Optional[str] = None, schema: Optional[str] = None):
        """Rollback migrations"""
        if module_name:
            module_path = self.resolve_module_path(module_name)
            if not module_path:
                typer.echo(f"❌ Module '{module_name}' not found", err=True)
                return

            modules = {module_name: {
                "path": module_path,
                "has_migrations": (module_path / "migrations").exists()
            }}
        else:
            modules = self.get_modules_with_models()

        if not modules:
            typer.echo("❌ No modules found", err=True)
            return

        for mod_name, mod_info in modules.items():
            if not mod_info.get("has_migrations"):
                typer.echo(f"⚠️  Skipping '{mod_name}' - no migrations")
                continue

            try:
                alembic_ini = self.app_path / mod_name / "alembic.ini"

                # Update alembic.ini with schema if provided
                if schema:
                    self._update_alembic_ini_schema(alembic_ini, schema)

                # Determine target revision
                if revision:
                    target_revision = revision
                elif steps:
                    target_revision = f"-{steps}"
                else:
                    target_revision = "-1"

                cmd = [
                    sys.executable, "-m", "alembic",
                    "-c", str(alembic_ini),
                    "downgrade",
                    target_revision
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                schema_info = f" (schema: {schema})" if schema else ""
                if result.returncode == 0:
                    if steps:
                        typer.echo(f"✅ Rolled back '{mod_name}'{schema_info} by {steps} step(s)")
                    elif revision:
                        typer.echo(f"✅ Rolled back '{mod_name}'{schema_info} to {revision}")
                else:
                    typer.echo(f"❌ Error rolling back '{mod_name}':", err=True)
                    typer.echo(result.stderr, err=True)

            except Exception as e:
                typer.echo(f"❌ Error: {e}", err=True)

    def _create_alembic_ini(self, module_name: str, path: Path):
        """Create alembic.ini for module"""
        from fastgo.core.db.sql.config import get_db_config

        config = get_db_config()
        default_conn = config.get("default", "postgresql")
        connection_config = config["connections"][default_conn]

        # Build connection string from config
        driver = connection_config.get("driver", "postgresql+asyncpg")
        username = connection_config.get("username", "user")
        password = connection_config.get("password", "pass")
        host = connection_config.get("host", "localhost")
        port = connection_config.get("port", 5432)
        database = connection_config.get("database", "app")

        db_url = f"{driver}://{username}:{password}@{host}:{port}/{database}"

        # Create unique version table per module
        version_table = f"alembic_version_{module_name.replace('/', '_')}"

        content = f"""[alembic]
sqlalchemy.url = {db_url}
script_location = {self.app_dir}/{module_name}/migrations
version_table = {version_table}

[loggers]
keys = root,sqlalchemy

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

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        path.write_text(content)

    def _create_env_py(self, module_name: str, path: Path):
        """Create env.py for module"""
        # Each module only tracks its OWN models
        module_import_path = module_name.replace("/", ".")
        import_statement = f'''# Import models from this module ONLY
# This ensures each module only tracks its own tables
from app.{module_import_path}.models import *
'''

        content = f'''"""Alembic environment"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import re
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import Base from framework
from fastgo.core.db.sql.base import Base

{import_statement}

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use Base metadata - only contains models imported above
target_metadata = Base.metadata

def get_sync_url(async_url: str) -> str:
    """Convert async database URL to sync URL for Alembic"""
    # postgresql+asyncpg:// -> postgresql://
    sync_url = re.sub(r'\\+asyncpg', '', async_url)
    # mysql+aiomysql:// -> mysql+pymysql://
    sync_url = re.sub(r'\\+aiomysql', '+pymysql', sync_url)
    # sqlite+aiosqlite:// -> sqlite://
    sync_url = re.sub(r'\\+aiosqlite', '', sync_url)
    return sync_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode"""
    url = config.get_main_option("sqlalchemy.url")
    url = get_sync_url(url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    url = config.get_main_option("sqlalchemy.url")
    url = get_sync_url(url)

    # Get version table from config
    version_table = config.get_main_option("version_table", "alembic_version")

    configuration = config.get_section(config.config_ini_section, {{}})
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    def include_object(object, name, type_, reflected, compare_to):
        """Only track tables from this module"""
        if type_ == "table" and name.startswith("alembic_version"):
            return False
        return True

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=version_table,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        path.write_text(content)

    def _create_script_mako(self, path: Path):
        """Create script.py.mako for Alembic"""
        content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
        path.write_text(content)

    def _create_alembic_ini_with_branches(self, module_name: str, path: Path):
        """Create alembic.ini for module with branch labels"""
        from fastgo.core.db.sql.config import get_db_config

        config = get_db_config()
        default_conn = config.get("default", "postgresql")
        connection_config = config["connections"][default_conn]

        # Build connection string
        driver = connection_config.get("driver", "postgresql+asyncpg")
        username = connection_config.get("username", "user")
        password = connection_config.get("password", "pass")
        host = connection_config.get("host", "localhost")
        port = connection_config.get("port", 5432)
        database = connection_config.get("database", "app")

        db_url = f"{driver}://{username}:{password}@{host}:{port}/{database}"

        # Determine script location based on module
        if module_name == ".":
            # Shared migrations in app root
            script_location = f"{self.app_dir}/migrations"
        else:
            # Individual module migrations
            script_location = f"{self.app_dir}/{module_name}/migrations"

        content = f"""[alembic]
sqlalchemy.url = {db_url}
script_location = {script_location}

[loggers]
keys = root,sqlalchemy

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

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        path.write_text(content)

    def _update_alembic_ini_schema(self, alembic_ini: Path, schema: str):
        """Update alembic.ini with target schema (PostgreSQL)"""
        content = alembic_ini.read_text()

        # Add or update schema comment in sqlalchemy.url
        if "?options=" in content:
            # Replace existing options
            content = re.sub(
                r'\?options=[^\n]*',
                f'?options=-c%20search_path%3D{schema}',
                content
            )
        else:
            # Add options to url
            content = re.sub(
                r'(sqlalchemy\.url = [^\n]*)',
                rf'\1?options=-c%20search_path%3D{schema}',
                content
            )

        alembic_ini.write_text(content)

    def show_history(self, module_name: Optional[str] = None, schema: Optional[str] = None):
        """Show migration history"""
        if module_name:
            module_path = self.resolve_module_path(module_name)
            if not module_path:
                typer.echo(f"❌ Module '{module_name}' not found", err=True)
                return

            modules = {module_name: {
                "path": module_path,
                "has_migrations": (module_path / "migrations").exists()
            }}
        else:
            modules = self.get_modules_with_models()

        if not modules:
            typer.echo("❌ No modules found", err=True)
            return

        for mod_name, mod_info in modules.items():
            if not mod_info.get("has_migrations"):
                typer.echo(f"⚠️  Skipping '{mod_name}' - no migrations")
                continue

            try:
                alembic_ini = self.app_path / mod_name / "alembic.ini"

                # Update alembic.ini with schema if provided
                if schema:
                    self._update_alembic_ini_schema(alembic_ini, schema)

                cmd = [
                    sys.executable, "-m", "alembic",
                    "-c", str(alembic_ini),
                    "history",
                    "--verbose"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                schema_info = f" (schema: {schema})" if schema else ""
                typer.echo(f"\n📜 Migration history for '{mod_name}'{schema_info}:")
                typer.echo("─" * 80)

                if result.returncode == 0:
                    if result.stdout:
                        typer.echo(result.stdout)
                    else:
                        typer.echo("No migrations found")
                else:
                    typer.echo(f"❌ Error showing history:", err=True)
                    typer.echo(result.stderr, err=True)

            except Exception as e:
                typer.echo(f"❌ Error: {e}", err=True)


# CLI Commands using Typer
@cli.command()
def init(
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Module path (e.g., users or users/mobile)"),
):
    """Initialize Alembic for modules"""
    settings = get_settings()
    manager = MigrationManager(settings.APP_DIR)

    if module:
        manager.init_module_migration(module)
    else:
        modules = manager.get_modules_with_models()
        if not modules:
            typer.echo("❌ No modules found with models", err=True)
            return

        for mod_name in modules.keys():
            manager.init_module_migration(mod_name)

@cli.command()
def makemigrations(
    module: str = typer.Option(..., "--module", "-m", help="Module path (required - specify which module to migrate)"),
    message: str = typer.Option("auto migration", "--message", "-msg", help="Migration message"),
):
    """Create migrations for a specific module"""
    settings = get_settings()
    manager = MigrationManager(settings.APP_DIR)
    manager.create_migration(module, message)

@cli.command()
def migrate(
    module: str = typer.Option(..., "--module", "-m", help="Module path (required - specify which module to migrate)"),
    revision: str = typer.Option("head", "--revision", "-r", help="Target revision"),
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Target schema (PostgreSQL only)"),
):
    """Apply migrations for a specific module"""
    settings = get_settings()
    manager = MigrationManager(settings.APP_DIR)
    manager.migrate(module, revision, schema)

@cli.command()
def rollback(
    module: str = typer.Option(..., "--module", "-m", help="Module path (required - specify which module to rollback)"),
    steps: Optional[int] = typer.Option(None, "--steps", "-st", help="Number of steps to rollback"),
    revision: Optional[str] = typer.Option(None, "--revision", "-r", help="Target revision ID or 'base'"),
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Target schema (PostgreSQL only)"),
):
    """Rollback migrations for a specific module"""
    settings = get_settings()
    manager = MigrationManager(settings.APP_DIR)

    # Default to 1 step if no revision specified
    if steps is None and revision is None:
        steps = 1

    manager.rollback(module, steps, revision, schema)

@cli.command()
def history(
    module: str = typer.Option(..., "--module", "-m", help="Module path (required - specify which module to show history for)"),
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Target schema (PostgreSQL only)"),
):
    """Show migration history for a specific module"""
    settings = get_settings()
    manager = MigrationManager(settings.APP_DIR)
    manager.show_history(module, schema)
