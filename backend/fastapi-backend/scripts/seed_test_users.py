#!/usr/bin/env python3
"""Quick seeder for test doctor/patient users."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Clinic
from app.models.auth import Role
from loguru import logger


TEST_USERS = [
    {"email": "doctor@yopmail.com",  "password": "password", "role": "doctor",  "name": "Dr. Test"},
    {"email": "patient@yopmail.com", "password": "password", "role": "patient", "name": "Test Patient"},
    {"email": "staff@yopmail.com",   "password": "password", "role": "staff",   "name": "Test Staff"},
]


def main():
    db = SessionLocal()
    try:
        clinic = db.query(Clinic).filter(Clinic.code == "DEFAULT", Clinic.deleted_at.is_(None)).first()
        if not clinic:
            raise SystemExit("DEFAULT clinic missing — run seed_data.py first")

        for spec in TEST_USERS:
            existing = db.query(User).filter(User.email == spec["email"], User.deleted_at.is_(None)).first()
            if existing:
                existing.role = spec["role"]
                existing.password = get_password_hash(spec["password"])
                existing.is_active = True
                logger.info(f"Updated {spec['email']} (role={spec['role']})")
            else:
                u = User(
                    email=spec["email"],
                    password=get_password_hash(spec["password"]),
                    name=spec["name"],
                    role=spec["role"],
                    clinic_id=clinic.id,
                    is_active=True,
                    is_verified=True,
                )
                db.add(u)
                db.flush()
                role_obj = db.query(Role).filter(Role.name == spec["role"], Role.deleted_at.is_(None)).first()
                if role_obj:
                    u.roles.append(role_obj)
                logger.info(f"Created {spec['email']} (role={spec['role']})")

        db.commit()
        logger.info("Done. Test logins:")
        for s in TEST_USERS:
            logger.info(f"  {s['email']} / {s['password']}  ({s['role']})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
