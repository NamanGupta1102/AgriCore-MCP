"""
conftest.py — Shared pytest fixtures for the AgriCore MCP test suite.

This file is automatically loaded by pytest and makes src/ importable,
replacing the manual sys.path.append() hacks in individual test files.
"""
import os
import sys
import pytest

# ---------------------------------------------------------------------------
# Make `src/` importable from any test without sys.path manipulation
# ---------------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------
from rules_engine import RulesEngine
from rag_engine import RagEngine


@pytest.fixture(scope="session")
def rules_engine():
    """
    Session-scoped RulesEngine fixture pointing at the tests/fixtures/ directory
    so that unit tests evaluate against predictable, non-production mock rules.
    """
    rules_dir = os.path.join(ROOT_DIR, "tests", "fixtures")
    return RulesEngine(rules_dir=rules_dir)


@pytest.fixture(scope="session")
def rag_engine():
    """
    Session-scoped RagEngine fixture pointing at the real data/.lancedb directory.
    Model loading is expensive, so this is initialized once per test session.
    """
    db_dir = os.path.join(ROOT_DIR, "data", ".lancedb")
    return RagEngine(db_dir=db_dir)


@pytest.fixture(scope="session")
def fixtures_dir():
    """Returns the absolute path to tests/fixtures/ for loading test-only data."""
    return os.path.join(ROOT_DIR, "tests", "fixtures")
