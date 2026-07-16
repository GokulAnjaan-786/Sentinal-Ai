"""
Database Seed Script
=====================

Seeds the SentinelAI database with initial data including:
- Default roles and permissions
- Admin user account
- Sample departments
- Sample users for demonstration
- Synthetic activity data for ML training

Usage:
    python -m scripts.seed_database
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database.connection import async_session_factory, async_engine
from app.database.connection import Base
from app.models import (
    User, Role, Permission, Department, Activity, Alert,
    RiskScore, Device, UserSession
)
from app.auth.password_utils import PasswordManager
from app.auth.rbac import RBACManager
from app.core.config import settings
from app.logging_config.setup import setup_logging

import logging
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def seed_roles_and_permissions(db):
    """Seed default roles and permissions."""
    await RBACManager.initialize_roles(db)
    logger.info("Roles and permissions seeded")


async def seed_departments(db):
    """Seed organizational departments."""
    departments = [
        {"name": "Information Technology", "code": "IT", "description": "IT Infrastructure and Operations"},
        {"name": "Security Operations", "code": "SEC", "description": "Cybersecurity and SOC"},
        {"name": "Finance", "code": "FIN", "description": "Financial Operations"},
        {"name": "Human Resources", "code": "HR", "description": "Human Resources Management"},
        {"name": "Retail Banking", "code": "RB", "description": "Retail Banking Operations"},
        {"name": "Corporate Banking", "code": "CB", "description": "Corporate Banking Services"},
        {"name": "Risk Management", "code": "RM", "description": "Enterprise Risk Management"},
        {"name": "Compliance", "code": "CMP", "description": "Regulatory Compliance"},
        {"name": "Fraud Prevention", "code": "FP", "description": "Fraud Detection and Prevention"},
        {"name": "External IT Services", "code": "EXT", "description": "External IT Contractors"},
    ]

    dept_objects = {}
    for dept_data in departments:
        existing = (await db.execute(
            select(Department).where(Department.code == dept_data["code"])
        )).scalar_one_or_none()
        if existing is None:
            dept = Department(**dept_data)
            db.add(dept)
            await db.flush()
            dept_objects[dept_data["code"]] = dept
            logger.info(f"Created department: {dept_data['name']}")
        else:
            dept_objects[dept_data["code"]] = existing

    return dept_objects


async def seed_users(db, departments):
    """Seed sample users."""
    users_data = [
        {
            "username": "admin",
            "email": "admin@sentinelai.bank",
            "password": "Admin@12345!",
            "full_name": "System Administrator",
            "role_name": "super_admin",
            "department_code": "IT",
            "employee_id": "EMP001",
        },
        {
            "username": "soc_analyst_1",
            "email": "analyst1@sentinelai.bank",
            "password": "Analyst@123!",
            "full_name": "Sarah Chen",
            "role_name": "security_analyst",
            "department_code": "SEC",
            "employee_id": "EMP002",
        },
        {
            "username": "soc_analyst_2",
            "email": "analyst2@sentinelai.bank",
            "password": "Analyst@123!",
            "full_name": "James Rodriguez",
            "role_name": "security_analyst",
            "department_code": "SEC",
            "employee_id": "EMP003",
        },
        {
            "username": "it_admin_1",
            "email": "itadmin1@sentinelai.bank",
            "password": "Admin@123!",
            "full_name": "Michael Zhang",
            "role_name": "admin",
            "department_code": "IT",
            "employee_id": "EMP004",
        },
        {
            "username": "finance_user",
            "email": "finance@sentinelai.bank",
            "password": "Finance@123!",
            "full_name": "Emily Watson",
            "role_name": "employee",
            "department_code": "FIN",
            "employee_id": "EMP005",
        },
        {
            "username": "viewer_1",
            "email": "viewer@sentinelai.bank",
            "password": "Viewer@123!",
            "full_name": "David Kim",
            "role_name": "viewer",
            "department_code": "HR",
            "employee_id": "EMP006",
        },
    ]

    for user_data in users_data:
        # Check if user exists
        existing = await db.execute(
            select(User).where(User.username == user_data["username"])
        )
        if existing.scalar_one_or_none() is not None:
            logger.debug(f"User {user_data['username']} already exists, skipping")
            continue

        # Get role
        role_result = await db.execute(
            select(Role).where(Role.name == user_data["role_name"])
        )
        role = role_result.scalar_one_or_none()

        # Get department
        dept = departments.get(user_data["department_code"])

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=PasswordManager.hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role_id=role.id if role else None,
            department_id=dept.id if dept else None,
            employee_id=user_data["employee_id"],
            is_active=True,
            is_superuser=(user_data["role_name"] == "super_admin"),
            last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
        )
        db.add(user)
        await db.flush()
        logger.info(f"Created user: {user_data['username']} ({user_data['role_name']})")


async def seed_synthetic_activities(db, users):
    """Seed synthetic activity data for ML training."""
    from app.ml.synthetic.generator import SyntheticDataGenerator

    logger.info("Generating synthetic activity data...")
    generator = SyntheticDataGenerator(seed=42)
    activities_df, user_profiles = generator.generate_dataset(days=30)

    # Insert a sample of activities into the database
    sample_size = min(500, len(activities_df))
    sample = activities_df.sample(n=sample_size, random_state=42)

    for _, row in sample.iterrows():
        created = row.get("created_at", datetime.utcnow())
        if hasattr(created, "item"):
            created = datetime.utcfromtimestamp(int(created.item()))
        elif isinstance(created, (int, float)):
            created = datetime.utcfromtimestamp(int(created))
        elif hasattr(created, "to_pydatetime"):
            created = created.to_pydatetime().replace(tzinfo=None)
        if created.tzinfo is None:
            from datetime import timezone
            created = created.replace(tzinfo=timezone.utc)
        activity = Activity(
            user_id=users[0].id if users else uuid.uuid4(),
            activity_type=row.get("activity_type", "unknown"),
            description=row.get("description", ""),
            ip_address=f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
            device_id=row.get("device_id", "dev_0001"),
            location=row.get("location", "New York, NY"),
            severity=row.get("severity", "info"),
            risk_contribution=float(row.get("risk_contribution", 0.0)),
            status=row.get("status", "success"),
            created_at=created,
        )
        db.add(activity)

    logger.info(f"Seeded {sample_size} synthetic activities")


async def main():
    """Main seeding function."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("SentinelAI Database Seeding")
    logger.info("=" * 60)

    # Create tables
    await create_tables()

    # Seed data
    async with async_session_factory() as db:
        try:
            await seed_roles_and_permissions(db)
            departments = await seed_departments(db)
            await seed_users(db, departments)

            # Get seeded users for activity generation
            result = await db.execute(select(User).limit(10))
            users = result.scalars().all()

            await seed_synthetic_activities(db, users)

            await db.commit()
            logger.info("Database seeding completed successfully!")

        except Exception as e:
            await db.rollback()
            logger.error(f"Seeding failed: {str(e)}")
            raise
        finally:
            await db.close()

    # Cleanup
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
