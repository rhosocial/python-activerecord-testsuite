# src/rhosocial/activerecord/testsuite/feature/relation/conftest.py
"""
Pytest configuration for relation tests.
"""
import pytest
from typing import Type, Tuple

from rhosocial.activerecord import ActiveRecord


def pytest_configure(config):
    """Configure pytest for relation tests."""
    config.addinivalue_line(
        "markers", "feature_relation: Tests for relation functionality"
    )


@pytest.fixture
def employee_department_fixtures(request) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
    """
    Provide employee and department models for relation tests.
    
    Returns:
        Tuple of (Employee, Department) model classes
    """
    scenario = request.config.getoption("--scenario", default="memory")
    provider_registry_path = request.config.getoption(
        "--provider-registry",
        default="providers.registry:provider_registry"
    )
    
    # Import the provider registry
    import importlib
    module_path, obj_name = provider_registry_path.split(':')
    module = importlib.import_module(module_path)
    provider_registry = getattr(module, obj_name)
    
    provider = provider_registry.get_provider('relation')
    return provider.setup_employee_department_fixtures(scenario)


@pytest.fixture
def author_book_fixtures(request) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
    """
    Provide author, book, chapter, and profile models for relation tests.
    
    Returns:
        Tuple of (Author, Book, Chapter, Profile) model classes
    """
    scenario = request.config.getoption("--scenario", default="memory")
    provider_registry_path = request.config.getoption(
        "--provider-registry",
        default="providers.registry:provider_registry"
    )
    
    # Import the provider registry
    import importlib
    module_path, obj_name = provider_registry_path.split(':')
    module = importlib.import_module(module_path)
    provider_registry = getattr(module, obj_name)
    
    provider = provider_registry.get_provider('relation')
    return provider.setup_author_book_fixtures(scenario)


@pytest.fixture
def employee(employee_department_fixtures):
    """
    Provide an employee instance using the employee model from fixtures.
    """
    Employee, _ = employee_department_fixtures
    return Employee(username='john_doe', department_id=1)


@pytest.fixture
def department(employee_department_fixtures):
    """
    Provide a department instance using the department model from fixtures.
    """
    _, Department = employee_department_fixtures
    return Department(name='Engineering', description='Engineering Department')


@pytest.fixture
def author(author_book_fixtures):
    """
    Provide an author instance using the author model from fixtures.
    """
    Author, _, _, _ = author_book_fixtures
    return Author(name='Test Author')


@pytest.fixture
def book(author_book_fixtures):
    """
    Provide a book instance using the book model from fixtures.
    """
    _, Book, _, _ = author_book_fixtures
    return Book(title='Test Book', author_id=1)


@pytest.fixture
def chapter(author_book_fixtures):
    """
    Provide a chapter instance using the chapter model from fixtures.
    """
    _, _, Chapter, _ = author_book_fixtures
    return Chapter(title='Test Chapter', book_id=1)


@pytest.fixture
def profile(author_book_fixtures):
    """
    Provide a profile instance using the profile model from fixtures.
    """
    _, _, _, Profile = author_book_fixtures
    return Profile(bio='Test Bio', author_id=1)