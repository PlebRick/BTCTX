from backend.database import SessionLocal
from backend.models.user import User
from backend.services.user import create_user
from passlib.hash import bcrypt

db = SessionLocal()

def ensure_default_user():
    existing = db.query(User).first()
    if existing:
        print("✅ Default user already exists.")
        return

    user = User(
        username="default",
        password_hash=bcrypt.hash("btctxdev")
    )
    db.add(user)
    db.commit()
    print("✅ Default user created: username=default, password=btctxdev")

if __name__ == "__main__":
    ensure_default_user()
