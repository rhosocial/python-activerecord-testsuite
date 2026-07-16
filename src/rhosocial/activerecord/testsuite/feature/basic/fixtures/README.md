# Basic Feature Test Fixtures

This directory contains fixture model classes for testing basic ActiveRecord functionality across Python 3.8–3.12.

## Sync/Async Parity

Every model class has both a synchronous (`ActiveRecord`) and an asynchronous (`AsyncActiveRecord`) variant. The two variants define identical fields, validators, and annotations, ensuring test coverage mirrors across sync/async backends.

## Files Overview

| File | Python Version | Key Features |
|------|---------------|--------------|
| `models.py` | 3.8+ | Base version using `Optional[T]` and `Union[T, U]` |
| `models_py310.py` | 3.10+ | `X \| Y` union type syntax |
| `models_py311.py` | 3.11+ | `Self` type for chainable methods |
| `models_py312.py` | 3.12+ | `@override` decorator, type parameter syntax |

## Version-Specific Syntax Features

### Python 3.8+ (`models.py`)

The base version uses traditional typing module syntax:

```python
from typing import Optional, Union

class User(ActiveRecord):
    id: Optional[int] = None
    username: str
    email: Optional[EmailStr] = None
```

### Python 3.10+ (`models_py310.py`)

Uses the new union type syntax (`X | Y`):

```python
class User(ActiveRecord):
    id: int | None = None
    username: str
    email: EmailStr | None = None
```

### Python 3.11+ (`models_py311.py`)

Adds the `Self` type for methods that return instances of the same class:

```python
from typing import Self

class User(ActiveRecord):
    def activate(self) -> Self:
        """Activate user and return self for chaining."""
        self.is_active = True
        return self

    def with_balance(self, new_balance: float) -> Self:
        """Return a new instance with updated balance."""
        new_user = self.clone()
        new_user.balance = new_balance
        return new_user

# Usage: chainable method calls
user = User(username="test", email="test@example.com")
user.activate().with_balance(100.0)
```

### Python 3.12+ (`models_py312.py`)

Adds the `@override` decorator for inheritance safety:

```python
from typing import override

class ValidatedUser(ActiveRecord):
    @field_validator('username')
    @override
    def validate_username(cls, v: str) -> str:
        # Ensures this method correctly overrides parent
        ...
```

Also includes examples of the new type parameter syntax (PEP 695):

```python
# Before (Python 3.8+)
from typing import Generic, TypeVar
T = TypeVar('T')
class Container(Generic[T]): ...

# After (Python 3.12+)
class Container[T]: ...
```

## Usage with Fixture Selector

Use the `select_fixture()` function to automatically select the most appropriate version for your Python environment:

```python
from rhosocial.activerecord.testsuite.utils import select_fixture

# Import all versions
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import User as UserBase
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models_py310 import User as User310
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models_py311 import User as User311
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models_py312 import User as User312

# Select the best version for current environment
User = select_fixture(User312, User311, User310, UserBase)
```

The `select_fixture()` function:
1. Checks each candidate in order (highest version first)
2. Returns the first class whose `__requires_python__` requirement is satisfied
3. Falls back to the last candidate if no match is found

## Requirement Declaration

Each version-specific file declares its Python requirement:

```python
# models_py310.py
__requires_python__ = (3, 10)

# models_py311.py
__requires_python__ = (3, 11)

# models_py312.py
__requires_python__ = (3, 12)
```

## When to Use Which Version

| Scenario | Recommended File |
|----------|------------------|
| Maximum compatibility | `models.py` (Python 3.8+) |
| Cleaner syntax | `models_py310.py` (Python 3.10+) |
| Chainable methods | `models_py311.py` (Python 3.11+) |
| Override safety | `models_py312.py` (Python 3.12+) |

## Model Classes Included

All versions define the same set of model classes:

- **TypeCase** - Model with various data types
- **User** - Standard user model for CRUD testing
- **ValidatedUser** - Model with custom validators
- **TypeAdapterTest** - Model for type adapter testing
- **MappedUser** - Model with custom column mappings
- **MappedPost** - Post model with column mappings
- **MappedComment** - Comment model with column mappings
- **MixedAnnotationModel** - Model combining various annotations


## IDE Type Checking

When viewing these files in an IDE, you may see syntax errors for version-specific features. This is expected because:

1. The project supports Python 3.8+ as the minimum version
2. These files are only imported in compatible Python environments
3. The `select_fixture()` mechanism ensures runtime safety

To suppress these warnings in your IDE, you can:
- Configure the IDE to use a specific Python version for type checking
- Add `# type: ignore` comments for specific lines
- Use `# pyright: reportInvalidTypeForm=false` at the file level
