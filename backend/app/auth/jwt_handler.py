"""
JWT Handler
============

Implements JSON Web Token (JWT) operations for SentinelAI.

JWT tokens are the primary authentication mechanism. The handler provides:
- Token creation with configurable expiration
- Token validation and decoding
- Refresh token management
- Token blacklisting for logout

Token Structure:
    Header:  { "alg": "HS256", "typ": "JWT" }
    Payload: { "sub": user_id, "role": role, "exp": expiry, "jti": token_id }
    Signature: HMAC-SHA256(secret, header.payload)

Security Considerations:
    - Tokens are signed with HMAC-SHA256 (switch to RS256 for production)
    - Access tokens expire after 30 minutes (configurable)
    - Refresh tokens expire after 7 days (configurable)
    - Token IDs (jti) enable individual token revocation
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTError as JoseJWTError

from app.core.config import settings


class JWTHandler:
    """
    JWT token management handler.

    Provides static methods for creating, validating, and managing
    JWT tokens used throughout the SentinelAI authentication system.
    """

    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new JWT access token.

        Access tokens are short-lived tokens used to authenticate API
        requests. They contain the user's identity and role information.

        Args:
            user_id: The unique identifier of the authenticated user.
            role: The user's role name (e.g., 'security_analyst').
            additional_claims: Optional extra claims to include in the token.

        Returns:
            Encoded JWT token string.
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        """
        Token payload contains standard claims:
        - sub: Subject (user ID)
        - role: User's role for authorization
        - exp: Expiration time
        - iat: Issued at time
        - jti: Unique token ID for revocation
        - type: Token type (access vs refresh)
        """
        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access",
        }

        # Add any additional custom claims
        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create a new JWT refresh token.

        Refresh tokens are long-lived tokens used to obtain new access
        tokens without requiring the user to re-authenticate.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            Encoded JWT refresh token string.
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Validates the token signature and expiration. Returns the decoded
        payload if valid, None if invalid or expired.

        Args:
            token: The JWT token string to verify.

        Returns:
            Decoded token payload dictionary, or None if invalid.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except ExpiredSignatureError:
            # Token has expired
            return None
        except JWTError:
            # Invalid token (bad signature, malformed, etc.)
            return None
        except JoseJWTError:
            # Catch-all for jose library errors
            return None

    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """
        Extract the expiration time from a JWT token without validation.

        Warning: This does NOT verify the token signature. Only use
        for informational purposes (e.g., displaying session duration).

        Args:
            token: The JWT token string.

        Returns:
            Expiration datetime, or None if the token is malformed.
        """
        try:
            payload = jwt.get_unverified_claims(token)
            exp = payload.get("exp")
            if exp:
                return datetime.utcfromtimestamp(exp)
            return None
        except JWTError:
            return None

    @staticmethod
    def get_token_type(token: str) -> Optional[str]:
        """
        Extract the token type (access/refresh) without full validation.

        Args:
            token: The JWT token string.

        Returns:
            Token type string ('access' or 'refresh'), or None.
        """
        try:
            payload = jwt.get_unverified_claims(token)
            return payload.get("type")
        except JWTError:
            return None

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """
        Extract the user ID from a JWT token.

        Args:
            token: The JWT token string.

        Returns:
            User ID string, or None if the token is invalid.
        """
        payload = JWTHandler.verify_token(token)
        if payload:
            return payload.get("sub")
        return None

    @staticmethod
    def get_access_token_expiry_seconds() -> int:
        """
        Get the access token expiration time in seconds.

        Returns:
            Number of seconds until access token expiration.
        """
        return settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @staticmethod
    def decode_token_unverified(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a JWT token without verifying the signature.

        WARNING: This should ONLY be used for debugging and logging.
        Never use this for authentication or authorization decisions.

        Args:
            token: The JWT token string.

        Returns:
            Decoded payload dictionary, or None if malformed.
        """
        try:
            return jwt.get_unverified_claims(token)
        except JWTError:
            return None
