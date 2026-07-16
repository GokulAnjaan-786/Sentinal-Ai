"""
Password Utilities
===================

Provides secure password hashing and verification using bcrypt.

Bcrypt is an adaptive hashing function designed to be computationally
expensive, making brute force attacks impractical. The work factor
(rounds) can be increased as hardware improves.

Current Configuration:
    - Algorithm: bcrypt
    - Rounds: 12 (configurable via settings)
    - Time to hash: ~250ms on modern hardware
    - Time to verify: ~250ms (same as hashing)

Password Policy (enforced during registration and password change):
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Not in common password list
"""

import re
import logging
from typing import Optional

import bcrypt

from app.core.config import settings

logger = logging.getLogger(__name__)

"""
List of commonly used passwords that should be rejected.
This is a subset - in production, use a comprehensive dictionary.
"""
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "monkey", "master", "dragon", "login", "princess",
    "football", "shadow", "sunshine", "trustno1", "iloveyou",
    "batman", "access", "hello", "charlie", "letmein",
    "password1", "password123", "admin", "administrator",
}


class PasswordManager:
    """
    Password hashing and verification manager.

    Provides static methods for securely hashing passwords,
    verifying passwords against their hashes, and validating
    password strength against security policies.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password using bcrypt.

        This method generates a salt and hashes the password with the
        configured number of bcrypt rounds. The resulting hash includes
        the salt, so no separate salt storage is needed.

        Args:
            password: The plaintext password to hash.

        Returns:
            Bcrypt hash string (includes algorithm, rounds, salt, and hash).
        """
        # Generate salt with configured rounds
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)

        # Hash the password
        password_bytes = password.encode("utf-8")
        hash_bytes = bcrypt.hashpw(password_bytes, salt)

        return hash_bytes.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a bcrypt hash.

        This method is timing-safe - it takes the same amount of time
        regardless of where the password differs from the hash, preventing
        timing-based side channel attacks.

        Args:
            password: The plaintext password to verify.
            hashed_password: The stored bcrypt hash to verify against.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validate a password against the security policy.

        Checks the password against multiple strength requirements and
        returns detailed feedback about which requirements are not met.

        Args:
            password: The password to validate.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
            If is_valid is True, the error list is empty.
        """
        errors = []

        # Minimum length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        # Maximum length check (prevent DoS with very long passwords)
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")

        # Uppercase letter check
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # Lowercase letter check
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # Digit check
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        # Special character check
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\;'/`~]", password):
            errors.append("Password must contain at least one special character")

        # Common password check
        if password.lower() in COMMON_PASSWORDS:
            errors.append("This password is too common. Choose a more unique password")

        # Sequential character check
        if re.search(r"(.)\1{2,}", password):
            errors.append("Password must not contain 3 or more repeated characters")

        return (len(errors) == 0, errors)

    @staticmethod
    def generate_password_hash_info(password: str) -> dict:
        """
        Generate hash and metadata for a password (for admin display).

        Args:
            password: The password to hash.

        Returns:
            Dictionary with hash and metadata (never includes the password).
        """
        hashed = PasswordManager.hash_password(password)
        return {
            "hash": hashed,
            "algorithm": "bcrypt",
            "rounds": settings.BCRYPT_ROUNDS,
        }
