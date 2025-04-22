from sqlalchemy.orm import Session

from app.src.user.model import User


def find_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    db.refresh(user)
    return user
