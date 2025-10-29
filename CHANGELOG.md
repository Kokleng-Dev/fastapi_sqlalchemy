# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2024-01-XX

### Added
- Initial release
- Fluent query builder inspired by Laravel Eloquent
- Eloquent-style BaseModel with static methods
- Async SQLAlchemy support
- Multiple database connection support
- Chainable query methods (where, join, order_by, etc.)
- Dynamic filtering with apply_filters
- Built-in pagination support
- Transaction decorators
- SQL query debugging utilities
- Django-like migration system with Alembic
- Modular migrations (one folder per app/feature)
- CLI commands for migration management
- Comprehensive documentation

### Features
- ✅ `User.all()`, `User.find(1)`, `User.create()` - Eloquent-style syntax
- ✅ Query builder chaining: `.where().order_by().limit()`
- ✅ Multiple JOIN types (inner, left, right, full)
- ✅ Dynamic filters with Laravel-like syntax
- ✅ Automatic schema switching (PostgreSQL)
- ✅ ORM loading strategies (joinedload, selectinload)
- ✅ Migration commands: init, makemigrations, migrate, showmigrations
- ✅ Modular migrations per app/feature

## [Unreleased]

### Planned
- More query builder methods
- Additional database drivers
- Performance optimizations
- More comprehensive examples
- Integration with popular FastAPI extensions

---

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
