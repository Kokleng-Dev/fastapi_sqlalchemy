# Complete Setup Guide

This guide covers everything from development to publishing.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Using in Your Projects](#using-in-your-projects)
4. [Publishing to PyPI](#publishing-to-pypi)
5. [Common Workflows](#common-workflows)

## Development Setup

### 1. Clone/Setup Repository

```bash
# If using git
git clone <your-repo>
cd fastapi_sqlalchemy

# Or create new project
mkdir fastapi-sqlalchemy
cd fastapi-sqlalchemy
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

### 3. Verify Installation

```bash
# Check CLI works
python -m fastapi_sqlalchemy.cli --help

# Test imports
python -c "from fastapi_sqlalchemy import BaseModel, DB; print('OK')"
```

## Project Structure

```
fastapi-sqlalchemy/
├── README.md                    # Main documentation
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT license
├── MANIFEST.in                  # Extra files to include
├── pyproject.toml               # Project configuration
├── fastapi_sqlalchemy/          # Main package
│   ├── __init__.py              # Package exports
│   ├── base_model.py            # BaseModel class
│   ├── cli.py                   # CLI commands
│   ├── config.py                # Configuration
│   ├── connection.py            # Connection management
│   ├── db.py                    # DB facade
│   ├── decorator.py             # Decorators
│   ├── dependency.py            # Dependencies
│   ├── migration.py             # Migration manager
│   ├── table_query.py           # Query builder
│   └── util.py                  # Utilities
├── examples/                    # Example files
│   ├── advanced_usage.py
│   ├── apply_filters_examples.py
│   └── advanced_system_examples.py
├── docs/                        # Documentation
│   ├── MIGRATION_GUIDE.md
│   ├── MODULAR_MIGRATIONS.md
│   ├── PUBLISH_TO_PYPI.md
│   └── USAGE_IN_PROJECTS.md
└── tests/                       # Tests (optional)
    └── test_*.py
```

## Using in Your Projects

### Installation from Local Development

```bash
# Install in editable mode (for development)
pip install -e .

# Or using uv
uv pip install -e .
```

### Create a New Project

```bash
# Create new directory
mkdir my_project
cd my_project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the library
pip install -e ../fastapi-sqlalchemy  # Or pip install fastapi-sqlalchemy when published
```

### Project Setup

**pyproject.toml:**
```toml
[project]
name = "my-project"
version = "0.1.0"
dependencies = [
    "fastapi-sqlalchemy",
    "fastapi",
]
```

**main.py:**
```python
from fastapi import FastAPI
from fastapi_sqlalchemy import db_settings, connection_manager

app = FastAPI()

db_settings.load_from_dict({
    "default": {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "myapp",
        "username": "postgres",
        "password": "secret"
    }
}, default="default")

@app.on_event("startup")
async def startup():
    await connection_manager.initialize()

@app.on_event("shutdown")
async def shutdown():
    await connection_manager.close_all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Set Up Migrations

```bash
# Initialize migrations
python -m fastapi_sqlalchemy.cli migration init

# Create models
# ... define models in models.py ...

# Import models in migrations/env.py
# from models import User, Post

# Create migrations
python -m fastapi_sqlalchemy.cli migration makemigrations

# Apply migrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Publishing to PyPI

### Step 1: Prepare

```bash
# Update version in pyproject.toml
# version = "0.1.0"

# Add LICENSE file
# Add/update CHANGELOG.md
```

### Step 2: Build

```bash
# Install build tools
pip install build twine

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build
```

### Step 3: Check

```bash
# Check distribution
python -m twine check dist/*
```

### Step 4: Test on TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ fastapi-sqlalchemy
```

### Step 5: Publish

```bash
# Upload to PyPI
python -m twine upload dist/*
```

## Common Workflows

### Adding New Features

1. Create feature branch
2. Make changes
3. Test locally: `pip install -e .`
4. Update documentation
5. Commit and push
6. Create PR

### Updating Version

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create git tag: `git tag v0.2.0`
5. Push tag: `git push origin v0.2.0`
6. Build and publish

### Bug Fixes

1. Create bug fix branch
2. Fix the issue
3. Add test if applicable
4. Test thoroughly
5. Update CHANGELOG
6. Commit and create PR
7. Publish patch version

## Testing the Library

### Manual Testing

```bash
# Test CLI
python -m fastapi_sqlalchemy.cli migration --help

# Test answer. Test imports
python
>>> from fastapi_sqlalchemy import BaseModel, DB
>>> print("OK")
```

### In a Real Project

```bash
# Create test project
mkdir test_project
cd test_project

# Install library
pip install ../fastapi-sqlalchemy/

# Create test app and models
# ... create models ...

# Test migrations
python -m fastapi_sqlalchemy.cli migration init
python -m fastapi_sqlalchemy.cli migration makemigrations
python -m fastapi_sqlalchemy.cli migration migrate
```

## Distribution Files

When you run `python -m build`, it creates:

- `dist/fastapi-sqlalchemy-0.1.0.tar.gz` - Source distribution
- `dist/fastapi_sqlalchemy-0.1.0-py3-none-any.whl` - Wheel distribution

These are what users download when they run `pip install fastapi-sqlalchemy`.

## Package Entry Points

After installation, users can access:

```bash
# CLI command (if script entry point is configured)
fastapi-sqlalchemy migration init

# Or as Python module
python -m fastapi_sqlalchemy.cli migration init
```

## Local Development vs Published Package

### Local Development
```bash
pip install -e .  # Editable mode - changes reflect immediately
```

### Published Package
```bash
pip install fastapi-sqlalchemy  # Install from PyPI
```

## Useful Commands

```bash
# Run code formatter
black fastapi_sqlalchemy/

# Run linter
ruff check fastapi_sqlalchemy/

# Run tests (if added)
pytest

# Check imports
python -c "import fastapi_sqlalchemy; print(fastapi_sqlalchemy.__version__)"

# Build documentation
# ... if using Sphinx or MkDocs ...
```

## Next Steps

1. ✅ Development setup complete
2. ✅ Test in local projects
3. ✅ Add tests (optional)
4. ✅ Publish to TestPyPI
5. ✅ Publish to PyPI
6. ✅ Share with community

## Resources

- [PyPI Packaging Guide](https://packaging.python.org/)
- [Python Package Tutorial](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Support

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions
- Documentation: Read guides and examples
