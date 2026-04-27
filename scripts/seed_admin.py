#!/usr/bin/env python3
"""
Seed script to create initial admin user.

Usage:
    python scripts/seed_admin.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import AdminUser
from app.utils.security import hash_password
from app.config import settings


def seed_admin():
    """Create admin user if it doesn't exist."""
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(AdminUser).filter(
            AdminUser.email == settings.ADMIN_EMAIL
        ).first()

        if existing_admin:
            print(f"❌ Admin user already exists: {settings.ADMIN_EMAIL}")
            return

        # Create admin user
        admin = AdminUser(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            name=settings.ADMIN_NAME
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin.email}")
        print(f"   Name: {admin.name}")
        print(f"   ID: {admin.id}")
        print(f"\n🔐 Use these credentials to login:")
        print(f"   Email: {settings.ADMIN_EMAIL}")
        print(f"   Password: {settings.ADMIN_PASSWORD}")

    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding admin user...")
    seed_admin()
