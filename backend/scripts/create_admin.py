"""
Seeds the three roles and creates the first ADMIN user.
Run from backend/:   python -m scripts.create_admin
Safe to re-run: existing roles and users are left alone.
"""
import getpass

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Role, User

ROLES = ["ADMIN", "ANALYST", "VIEWER"]


def main() -> None:
    db = SessionLocal()
    try:
        for name in ROLES:
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name))
        db.commit()
        print("Roles ready:", ", ".join(ROLES))

        email = input("Admin email: ").strip().lower()
        if db.query(User).filter(User.email == email).first():
            print("That user already exists; nothing to do.")
            return
        password = getpass.getpass("Admin password (min 8 chars, hidden): ")
        if len(password) < 8:
            print("Password too short.")
            return

        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        db.add(User(email=email, hashed_password=hash_password(password),
                    full_name="Administrator", role_id=admin_role.id))
        db.commit()
        print(f"Admin created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()