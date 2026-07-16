"""
Role & Permission Models
==========================

Defines the Role-Based Access Control (RBAC) models for SentinelAI.

RBAC is a critical security component that controls what actions users
can perform within the system. In a banking environment, this ensures
that only authorized personnel can access sensitive data and operations.

Roles:
    - super_admin: Full system access
    - security_analyst: Monitor threats, view alerts, investigate incidents
    - admin: Manage users and system configuration
    - viewer: Read-only access to dashboards and reports
    - employee: Standard employee with limited access
    - contractor: External contractor with minimal access

Database Tables: roles, permissions, role_permissions
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base


# Association table for the many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to the roles table"
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to the permissions table"
    ),
    comment="Junction table linking roles to their granted permissions"
)


class Role(Base):
    """
    Role model for RBAC.

    Each role represents a set of privileges within the system. Users are
    assigned roles, and roles are granted permissions. This two-level
    indirection allows flexible permission management without modifying
    individual user access.

    Attributes:
        id: Primary key (UUID)
        name: Unique role name
        description: Human-readable description of the role
        is_active: Whether this role can be assigned to users
        is_system_role: System roles cannot be deleted
        created_at: Role creation timestamp
        updated_at: Last modification timestamp
    """
    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique role identifier"
    )
    name = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique role name (e.g., security_analyst)"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of what this role provides"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this role can be assigned to users"
    )
    is_system_role = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="System roles (super_admin, admin) cannot be deleted"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    # Many-to-many: A role can have many permissions, and a permission can belong to many roles
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    # One-to-many: A role can be assigned to many users
    users = relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if this role has a specific permission.

        Args:
            permission_name: The name of the permission to check.

        Returns:
            True if the role has the permission, False otherwise.
        """
        return any(p.name == permission_name for p in self.permissions)


class Permission(Base):
    """
    Permission model representing individual system capabilities.

    Permissions are granular access controls that define specific actions
    a user can perform (e.g., "view_alerts", "manage_users", "export_data").

    Attributes:
        id: Primary key (UUID)
        name: Unique permission name (dot-notation: resource.action)
        description: Human-readable description
        resource: The system resource this permission applies to
        action: The action allowed on the resource
        is_active: Whether this permission is currently active
    """
    __tablename__ = "permissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique permission identifier"
    )
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique permission name using dot-notation (e.g., alerts.view)"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of this permission"
    )
    resource = Column(
        String(50),
        nullable=False,
        comment="System resource this permission controls (e.g., alerts, users)"
    )
    action = Column(
        String(50),
        nullable=False,
        comment="Action allowed on the resource (e.g., view, create, delete)"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this permission is currently active"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"


class RolePermission(Base):
    """
    Explicit junction model for role-permission mapping.
    Provides additional metadata about when and how permissions were granted.

    This is an optional explicit model that adds audit capability
    to the role-permission relationship.
    """
    __tablename__ = "role_permission_audit"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False
    )
    granted_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
