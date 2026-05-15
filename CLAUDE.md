# Project Overview: rhosocial-activerecord-testsuite

## Project Identification

- **Repository Name**: python-activerecord-testsuite
- **Python Package Name**: rhosocial-activerecord-testsuite
- **Version**: 1.0.0.dev* (tracks core package for API compatibility)

## Project Purpose

This project is a standardized test suite for the `rhosocial-activerecord` Python package. It provides contracts for features, real-world scenarios, and benchmarks to validate backend implementations.

## Dependencies

- **Core Package**: `rhosocial-activerecord>=1.0.0,<2.0.0`
- **Testing Framework**: pytest, pytest-asyncio
- **Python Version**: 3.8+ (same as core package)

## Agent Guidelines

### Primary Rules

All agent work MUST follow the rules defined in the core project:

| Rule | Path |
|------|------|
| Architecture | `../python-activerecord/.claude/architecture.md` |
| Code Style | `../python-activerecord/.claude/code_style.md` |
| Testing | `../python-activerecord/.claude/testing.md` |
| Version Control | `../python-activerecord/.claude/version_control.md` |

### Path Assumptions

These guidelines assume:
- `python-activerecord/` and `python-activerecord-testsuite/` are sibling directories

## Key Design Principles

1. **Backend-Agnostic**: Only handles test logic and fixture definitions
2. **Provider Interface Pattern**: Defines contracts backends must implement
3. **Multi-Fixture Support**: Accommodates tests requiring multiple fixture classes
4. **Standardized Testing**: Ensures consistent validation across backend implementations
5. **Capability-based Testing**: Tests use `@requires_capability` for optional features

## Test Structure

```
src/rhosocial/activerecord/testsuite/
├── feature/      # Core feature tests
├── realworld/    # Complex, real-world application scenarios
└── benchmark/    # Performance and load tests
```

## Documentation

The project includes comprehensive documentation:
- `docs/en_US/` - English documentation (authoritative)
- `docs/zh_CN/` - Chinese documentation

## Development Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests (IMPORTANT: Tests MUST run serially - do NOT use pytest -n auto)
PYTHONPATH=src pytest tests/ -v

# Run specific test categories
PYTHONPATH=src pytest tests/ -m "feature"
PYTHONPATH=src pytest tests/ -m "realworld"
PYTHONPATH=src pytest tests/ -m "benchmark"

# Type checking
mypy src/rhosocial/activerecord --ignore-missing-imports

# Linting
ruff check src/ && ruff format --check src/
```

## Version Control and Changelog

This project adheres to the same standards as the main `python-activerecord` project:

See: `../python-activerecord/.claude/rules/version_control.md`

## Getting Help

1. Review `../python-activerecord/.claude/testing.md`
2. Check `docs/en_US/` for detailed documentation
3. Review provider interface examples in `tests/`