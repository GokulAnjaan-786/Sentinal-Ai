"""
RBAC Manager
==============

Role-Based Access Control management for SentinelAI.

This module provides utilities for managing roles, permissions,
and access control policies within the banking environment.

RBAC Hierarchy:
    super_admin -> Full access to everything
    security_analyst -> Access to alerts, monitoring, threat investigation
    admin -> User management, system configuration
    viewer -> Read-only access to dashboards and reports
    employee -> Standard employee access
    contractor -> Minimal access for external contractors
"""

import logging
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.models.role import Role, Permission, role_permissions
from app.models.user import User

logger = logging.getLogger(__name__)


class RBACManager:
    """
    Role-Based Access Control manager.

    Provides methods for checking permissions, managing roles,
    and enforcing access control policies throughout the application.
    """

    # Default role definitions with their permissions
    DEFAULT_ROLES = {
        "super_admin": {
            "description": "Full system access with all permissions",
            "is_system_role": True,
            "permissions": ["*"],  # Wildcard: all permissions
        },
        "security_analyst": {
            "description": "Monitor threats, investigate alerts, analyze risks",
            "is_system_role": True,
            "permissions": [
                "alerts.view", "alerts.create", "alerts.update", "alerts.acknowledge",
                "activities.view", "activities.export",
                "risk_scores.view", "risk_scores.assess",
                "threats.view", "threats.investigate",
                "users.view", "users.view_risk",
                "dashboard.view", "dashboard.advanced",
                "reports.view", "reports.generate",
            ],
        },
        "admin": {
            "description": "Manage users and system configuration",
            "is_system_role": True,
            "permissions": [
                "users.view", "users.create", "users.update", "users.delete",
                "roles.view", "roles.manage",
                "departments.view", "departments.manage",
                "system.config", "system.audit_logs",
                "dashboard.view",
            ],
        },
        "viewer": {
            "description": "Read-only access to dashboards and reports",
            "is_system_role": False,
            "permissions": [
                "dashboard.view",
                "reports.view",
                "users.view",
            ],
        },
        "employee": {
            "description": "Standard bank employee access",
            "is_system_role": False,
            "permissions": [
                "dashboard.view",
            ],
        },
        "contractor": {
            "description": "External contractor with minimal access",
            "is_system_role": False,
            "permissions": [
                "dashboard.view",
            ],
        },
    }

    @staticmethod
    async def initialize_roles(db: AsyncSession) -> None:
        """
        Initialize default roles and permissions in the database.

        Creates all default roles and their associated permissions.
        Existing roles are not modified. This should be called on
        application startup or during database seeding.

        Args:
            db: Async database session.
        """
        for role_name, role_config in RBACManager.DEFAULT_ROLES.items():
            # Check if role already exists
            result = await db.execute(
                select(Role).where(Role.name == role_name)
            )
            existing_role = result.scalar_one_or_none()

            if existing_role is None:
                # Create the role
                new_role = Role(
                    name=role_name,
                    description=role_config["description"],
                    is_system_role=role_config["is_system_role"],
                )
                db.add(new_role)
                await db.flush()

                # Create permissions for this role
                for perm_name in role_config["permissions"]:
                    if perm_name == "*":
                        continue  # Skip wildcard

                    # Parse permission name into resource.action format
                    parts = perm_name.split(".")
                    resource = parts[0] if len(parts) > 0 else "unknown"
                    action = parts[1] if len(parts) > 1 else "unknown"

                    # Check if permission already exists
                    perm_result = await db.execute(
                        select(Permission).where(Permission.name == perm_name)
                    )
                    existing_perm = perm_result.scalar_one_or_none()

                    if existing_perm is None:
                        new_perm = Permission(
                            name=perm_name,
                            resource=resource,
                            action=action,
                            description=f"Permission to {action} {resource}",
                        )
                        db.add(new_perm)
                        await db.flush()
                    else:
                        new_perm = existing_perm

                    # Link permission to role via association table directly
                    await db.execute(
                        insert(role_permissions).values(
                            role_id=new_role.id,
                            permission_id=new_perm.id
                        )
                    )

                logger.info(f"Created role: {role_name}")
            else:
                logger.debug(f"Role already exists: {role_name}")

        logger.info("Role initialization complete")

    @staticmethod
    def check_permission(user: User, permission_name: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user: The user to check permissions for.
            permission_name: The permission to check (e.g., 'alerts.view').

        Returns:
            True if the user has the permission, False otherwise.
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True

        if not user.role:
            return False

        # Check for wildcard permission
        if any(p.name == "*" for p in user.role.permissions):
            return True

        return user.role.has_permission(permission_name)

    @staticmethod
    def get_user_permissions(user: User) -> Set[str]:
        """
        Get all permissions for a user.

        Args:
            user: The user to get permissions for.

        Returns:
            Set of permission name strings.
        """
        if user.is_superuser:
            return {"*"}

        if not user.role:
            return set()

        return {p.name for p in user.role.permissions}

    @staticmethod
    def has_elevated_access(user: User) -> bool:
        """
        Check if a user has elevated (administrative) access.

        Elevated access users can perform sensitive operations like
        modifying security configurations, accessing audit logs,
        and managing other users.

        Args:
            user: The user to check.

        Returns:
            True if the user has elevated access.
        """
        if user.is_superuser:
            return True

        elevated_roles = {"super_admin", "security_analyst", "admin"}
        return user.role is not None and user.role.name in elevated_roles
