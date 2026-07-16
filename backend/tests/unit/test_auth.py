"""
Unit Tests for Authentication Module
======================================

Tests for JWT token operations, password hashing, and RBAC.
These tests verify the core security components work correctly.
"""

import pytest
from datetime import datetime, timedelta

from app.auth.jwt_handler import JWTHandler
from app.auth.password_utils import PasswordManager
from app.auth.rbac import RBACManager


class TestJWTHandler:
    """Tests for JWT token creation, validation, and management."""

    def test_create_access_token(self):
        """Test that access tokens are created with correct structure."""
        token = JWTHandler.create_access_token(
            user_id="test-user-123",
            role="security_analyst"
        )
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test that refresh tokens are created with correct structure."""
        token = JWTHandler.create_refresh_token(user_id="test-user-123")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test that valid tokens can be verified and decoded."""
        user_id = "test-user-456"
        role = "admin"
        token = JWTHandler.create_access_token(user_id=user_id, role=role)

        payload = JWTHandler.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"

    def test_verify_invalid_token(self):
        """Test that invalid tokens are rejected."""
        result = JWTHandler.verify_token("invalid.token.here")
        assert result is None

    def test_verify_tampered_token(self):
        """Test that tampered tokens are rejected."""
        token = JWTHandler.create_access_token(user_id="test", role="admin")
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        result = JWTHandler.verify_token(tampered)
        assert result is None

    def test_token_type_detection(self):
        """Test that token type can be determined."""
        access_token = JWTHandler.create_access_token(user_id="test", role="admin")
        refresh_token = JWTHandler.create_refresh_token(user_id="test")

        assert JWTHandler.get_token_type(access_token) == "access"
        assert JWTHandler.get_token_type(refresh_token) == "refresh"

    def test_user_id_extraction(self):
        """Test that user ID can be extracted from a valid token."""
        user_id = "user-789"
        token = JWTHandler.create_access_token(user_id=user_id, role="viewer")
        extracted_id = JWTHandler.get_user_id_from_token(token)
        assert extracted_id == user_id

    def test_user_id_extraction_invalid(self):
        """Test that user ID extraction returns None for invalid tokens."""
        result = JWTHandler.get_user_id_from_token("invalid")
        assert result is None

    def test_token_expiry_seconds(self):
        """Test that token expiry seconds matches configuration."""
        expiry = JWTHandler.get_access_token_expiry_seconds()
        assert expiry > 0
        assert expiry == 30 * 60  # 30 minutes in seconds


class TestPasswordManager:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Test that passwords are hashed to bcrypt format."""
        password = "SecurePassword123!"
        hashed = PasswordManager.hash_password(password)

        assert hashed is not None
        assert hashed != password  # Hash should differ from plaintext
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test that correct password is verified."""
        password = "CorrectPassword123!"
        hashed = PasswordManager.hash_password(password)

        assert PasswordManager.verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test that incorrect password is rejected."""
        password = "CorrectPassword123!"
        hashed = PasswordManager.hash_password(password)

        assert PasswordManager.verify_password("WrongPassword!", hashed) is False

    def test_password_strength_valid(self):
        """Test that strong password passes validation."""
        is_valid, errors = PasswordManager.validate_password_strength("StrongP@ss1")
        assert is_valid is True
        assert len(errors) == 0

    def test_password_strength_too_short(self):
        """Test that short password fails validation."""
        is_valid, errors = PasswordManager.validate_password_strength("Ab1!")
        assert is_valid is False
        assert any("8 characters" in e for e in errors)

    def test_password_strength_no_uppercase(self):
        """Test that password without uppercase fails."""
        is_valid, errors = PasswordManager.validate_password_strength("lowercase1!")
        assert is_valid is False
        assert any("uppercase" in e for e in errors)

    def test_password_strength_no_digit(self):
        """Test that password without digits fails."""
        is_valid, errors = PasswordManager.validate_password_strength("NoDigitHere!")
        assert is_valid is False
        assert any("digit" in e for e in errors)

    def test_password_strength_no_special(self):
        """Test that password without special characters fails."""
        is_valid, errors = PasswordManager.validate_password_strength("NoSpecial123")
        assert is_valid is False
        assert any("special" in e for e in errors)

    def test_password_strength_common_password(self):
        """Test that common passwords are rejected."""
        is_valid, errors = PasswordManager.validate_password_strength("password1")
        assert is_valid is False
        assert any("common" in e for e in errors)


class TestRBACManager:
    """Tests for Role-Based Access Control."""

    def test_check_permission_superuser(self):
        """Test that superusers have all permissions."""

        class MockUser:
            is_superuser = True
            role = None

        user = MockUser()
        assert RBACManager.check_permission(user, "any.permission") is True

    def test_check_permission_with_role(self):
        """Test that permission check works with roles."""

        class MockPermission:
            def __init__(self, name):
                self.name = name

        class MockRole:
            name = "security_analyst"
            permissions = [
                MockPermission("alerts.view"),
                MockPermission("alerts.create"),
                MockPermission("dashboard.view"),
            ]

            def has_permission(self, name):
                return any(p.name == name for p in self.permissions)

        class MockUser:
            is_superuser = False
            role = MockRole()

        user = MockUser()
        assert RBACManager.check_permission(user, "alerts.view") is True
        assert RBACManager.check_permission(user, "users.delete") is False

    def test_check_permission_no_role(self):
        """Test that users without roles have no permissions."""

        class MockUser:
            is_superuser = False
            role = None

        user = MockUser()
        assert RBACManager.check_permission(user, "alerts.view") is False

    def test_has_elevated_access(self):
        """Test that elevated access is correctly determined."""

        class MockRole:
            name = "security_analyst"

        class MockUser:
            is_superuser = False
            role = MockRole()

        user = MockUser()
        assert RBACManager.has_elevated_access(user) is True

    def test_has_elevated_access_regular_user(self):
        """Test that regular users do not have elevated access."""

        class MockRole:
            name = "employee"

        class MockUser:
            is_superuser = False
            role = MockRole()

        user = MockUser()
        assert RBACManager.has_elevated_access(user) is False
