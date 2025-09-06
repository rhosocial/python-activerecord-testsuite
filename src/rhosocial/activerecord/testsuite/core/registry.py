# src/rhosocial/activerecord/testsuite/core/registry.py
"""
This file defines the core mechanism for decoupling the generic testsuite from
specific backend implementations. It provides a `ProviderRegistry` class that
backend test suites can use to register their concrete provider classes.
"""
import os
import importlib
from typing import Optional, Type, Dict

class ProviderRegistry:
    """
    A simple registry that maps an interface's import path (as a string)
    to a concrete provider class that implements it.
    """

    def __init__(self):
        self._providers: Dict[str, Type] = {}

    def register(self, interface_path: str, provider_class: Type) -> None:
        """Registers a provider class for a given interface path."""
        self._providers[interface_path] = provider_class

    def get_provider(self, interface_path: str) -> Optional[Type]:
        """Retrieves a provider class for a given interface path."""
        return self._providers.get(interface_path)

# A global singleton to hold the registry instance.
_registry_instance = None

def get_provider_registry() -> ProviderRegistry:
    """
    Finds and returns the backend's provider registry instance.

    It discovers the registry by reading the `TESTSUITE_PROVIDER_REGISTRY`
    environment variable, which should contain the Python import path to the
    registry instance (e.g., 'my_project.tests.providers:provider_registry').
    This allows the testsuite to dynamically load the correct providers at runtime.
    """
    global _registry_instance
    if _registry_instance:
        return _registry_instance

    registry_path = os.environ.get('TESTSUITE_PROVIDER_REGISTRY')
    if not registry_path:
        raise RuntimeError(
            "The TESTSUITE_PROVIDER_REGISTRY environment variable is not set.\n"
            "Please set it to the import path of your provider registry instance, e.g.,\n"
            "export TESTSUITE_PROVIDER_REGISTRY='tests.providers.registry:provider_registry'"
        )

    try:
        module_path, obj_name = registry_path.rsplit(':', 1)
        module = importlib.import_module(module_path)
        _registry_instance = getattr(module, obj_name)
        return _registry_instance
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Failed to load ProviderRegistry from '{registry_path}': {e}")
