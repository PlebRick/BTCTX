import bcrypt
from backend.database import SessionLocal
from backend.models.user import User

db = SessionLocal()

def ensure_default_user():
    existing = db.query(User).first()
    if existing:
        print("✅ Default user already exists.")
        return

    user = User(
        username="default",
        password_hash=bcrypt.hashpw(b"btctxdev", bcrypt.gensalt()).decode('utf-8')
    )
    db.add(user)
    db.commit()
    print("✅ Default user created: username=default, password=btctxdev")

if __name__ == "__main__":
    ensure_default_user()
