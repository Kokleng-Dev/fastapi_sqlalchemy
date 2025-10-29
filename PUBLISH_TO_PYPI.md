# Publishing to PyPI

This guide shows you how to publish your library to PyPI so others can install it via pip.

## Prerequisites

1. Create accounts on:

   - PyPI (production): https://pypi.org/account/register/
   - TestPyPI (for testing): https://test.pypi.org/account/register/

2. Install build tools:
   ```bash
   pip install build twine
   ```

## Step 1: Update Project Metadata

### Update pyproject.toml

Make sure your `pyproject.toml` is complete:

```toml
[project]
name = "fastapi-sqlalchemy"
version = "0.1.0"
description = "A powerful, fluent query builder for FastAPI and SQLAlchemy"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["fastapi", "sqlalchemy", "orm", "laravel", "eloquent"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]

[project.scripts]
fastapi-sqlalchemy = "fastapi_sqlalchemy.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Add License

Create a `LICENSE` file (MIT example):

```
MIT License

Copyright (c) 2024 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Create MANIFEST.in (Optional)

Create `MANIFEST.in` to include extra files:

```
include README.md
include LICENSE
include pyproject.toml
recursive-include fastapi_sqlalchemy *.py
recursive-exclude * __pycache__
recursive-exclude * *.py[co]
```

## Step 2: Build Distribution Files

```bash
# Build source distribution and wheel
python -m build
```

This creates files in `dist/` directory:

- `fastapi-sqlalchemy-0.1.0.tar.gz` (source distribution)
- `fastapi_sqlalchemy-0.1.0-py3-none-any.whl` (wheel)

## Step 3: Test on TestPyPI

Always test first on TestPyPI:

### Upload to TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

Enter your TestPyPI credentials when prompted.

### Test Installation

```bash
# Install from TestPyPI
pip install -i https://test.pypi.org/simple/ fastapi-sqlalchemy
```

### Verify

```bash
# Test the CLI
python -m fastapi_sqlalchemy.cli --help

# Test imports
python -c "from fastapi_sqlalchemy import BaseModel, DB; print('Success!')"
```

## Step 4: Publish to PyPI

Once tested, publish to production PyPI:

```bash
# Upload to PyPI
python -m twine upload dist/*
```

Enter your PyPI credentials when prompted.

## Step 5: Verify on PyPI

1. Check your package on PyPI: https://pypi.org/project/fastapi-sqlalchemy/
2. Verify it can be installed:
   ```bash
   pip install fastapi-sqlalchemy
   ```

## Automation with Scripts

Create a `publish.sh` script:

```bash
#!/bin/bash
set -e

echo "Cleaning..."
rm -rf dist/ build/ *.egg-info

echo "Building..."
python -m build

echo "Checking..."
python -m twine check dist/*

echo "Uploading to TestPyPI..."
python -m twine upload --repository testpypi dist/*

echo "Done! Test with: pip install -i https://test.pypi.org/simple/ fastapi-sqlalchemy"
```

Or `publish.py`:

```python
#!/usr/bin/env python3
import subprocess
import sys

def run(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=True)
    return result

def main():
    try:
        print("🧹 Cleaning...")
        run("rm -rf dist/ build/ *.egg-info")

        print("📦 Building...")
        run("python -m build")

        print("✅ Checking...")
        run("python -m twine check dist/*")

        print("🚀 Publishing to PyPI...")
        run("python -m twine upload dist/*")

        print("✅ Published successfully!")
        print("📦 Install with: pip install fastapi-sqlalchemy")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Updating Version

### Update Version in pyproject.toml

```toml
[project]
version = "0.2.0"  # Increment version
```

### Build and Upload

```bash
# Clean
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Upload
python -m twine upload dist/*
```

## Using API Tokens

Instead of username/password, use API tokens:

### Create API Token

1. Go to: https://pypi.org/manage/account/token/
2. Create a new token
3. Copy the token

### Use Token

Upload using token:

```bash
python -m twine upload --username __token__ --password <your-token> dist/*
```

Or create `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Then use:

```bash
python -m twine upload dist/*
```

## Project Checklist

Before publishing:

- [ ] Update version number
- [ ] Update CHANGELOG.md (create if doesn't exist)
- [ ] Add LICENSE file
- [ ] Test locally: `pip install -e .`
- [ ] Run tests if you have any
- [ ] Update README.md if needed
- [ ] Check all dependencies are correct
- [ ] Build: `python -m build`
- [ ] Check: `python -m twine check dist/*`
- [ ] Test on TestPyPI first
- [ ] Publish to PyPI

## Version Naming

Follow Semantic Versioning (semver):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

Examples:

- 0.1.0 → 0.2.0 (new features)
- 0.2.0 → 0.2.1 (bug fix)
- 0.2.1 → 1.0.0 (stable release with breaking changes)

## Common Issues

### Issue: Package already exists

**Solution**: You can't upload the same version twice. Increment the version.

### Issue: Authentication failed

**Solution**: Check your username/password or API token.

### Issue: Invalid package metadata

**Solution**: Run `python -m twine check dist/*` to see errors.

### Issue: Missing files

**Solution**: Check `MANIFEST.in` includes all necessary files.

## GitHub Actions (Optional)

Automate publishing with GitHub Actions:

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install build twine

      - name: Build
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*
```

Add `PYPI_API_TOKEN` as a GitHub secret.

## Next Steps

After publishing:

1. Create a GitHub release
2. Update documentation with installation instructions
3. Share on social media / communities
4. Monitor package downloads on PyPI
5. Maintain and update the package

## References

- [PyPI Documentation](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
