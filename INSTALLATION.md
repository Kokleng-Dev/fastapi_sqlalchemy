# Installation Guide

## For Users (After Publishing to PyPI)

```bash
# Install from PyPI
pip install fastapi-sqlalchemy

# Or with uv
uv add fastapi-sqlalchemy

# Or add to pyproject.toml
[project]
dependencies = [
    "fastapi-sqlalchemy>=0.1.0",
]
```

## For Developers (Local Development)

```bash
# Clone the repository
git clone <repository-url>
cd fastapi-sqlalchemy

# Install in editable mode
pip install -e .

# Or with uv
uv pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

## Verification

After installation, verify it works:

```bash
# Check CLI
python -m fastapi_sqlalchemy.cli --help

# Test imports
python -c "from fastapi_sqlalchemy import BaseModel, DB; print('Success!')"

# Check version
python -c "import fastapi_sqlalchemy; print(fastapi_sqlalchemy.__version__)"
```

That's it! You're ready to use the library.
