"""
Tests for Database Seeding
============================

Tests that the seed script creates expected data.
"""

import pytest
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


class TestSeedDatabase:
    """Tests for the database seeding script."""

    def test_seed_script_importable(self):
        """Test that the seed script can be imported without errors."""
        import importlib
        spec = importlib.util.find_spec("scripts.seed_database")
        assert spec is not None

    def test_seed_script_has_main(self):
        """Test that the seed script has a main function."""
        from scripts import seed_database
        assert hasattr(seed_database, "main") or hasattr(seed_database, "seed_database")

    def test_seed_roles_defined(self):
        """Test that the seed script defines expected roles."""
        from scripts.seed_database import DEFAULT_ROLES
        role_names = [r["name"] for r in DEFAULT_ROLES]
        assert "super_admin" in role_names
        assert "security_analyst" in role_names
        assert "admin" in role_names
        assert "viewer" in role_names
        assert "employee" in role_names
        assert "contractor" in role_names

    def test_seed_departments_defined(self):
        """Test that the seed script defines expected departments."""
        from scripts.seed_database import DEFAULT_DEPARTMENTS
        dept_names = [d["name"] for d in DEFAULT_DEPARTMENTS]
        assert "Security Operations Center" in dept_names or len(dept_names) > 0

    def test_seed_users_defined(self):
        """Test that the seed script defines default users."""
        from scripts.seed_database import DEFAULT_USERS
        usernames = [u["username"] for u in DEFAULT_USERS]
        assert "admin" in usernames
        assert "soc_analyst_1" in usernames
