import bcrypt
from sqlalchemy.orm import Session
from db import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_user(db: Session, username: str, password: str) -> str:
    if db.query(User).filter(User.username == username).first():
        return "Username already exists"
    hashed = hash_password(password)
    db.add(User(username=username, hashed_password=hashed))
    db.commit()
    return "Account created!"

def login_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

