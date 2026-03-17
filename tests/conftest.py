# tests/conftest.py
"""
Test configuration for testsuite's own tests.

This conftest configures the Python path to include the src directory
so that tests can import the testsuite modules.
"""
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
