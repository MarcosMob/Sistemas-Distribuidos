# services/user_service.py
from sqlalchemy.orm import Session
from database import models
from schemas import user as user_schema
from auth.utils import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        is_active=True,
        game=user.game
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: user_schema.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    
    # Atualiza apenas os campos fornecidos
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users_with_same_game(db: Session, current_user_id: int, current_user_game: str):
    """Busca usuários que jogam o mesmo jogo, excluindo o usuário atual"""
    if not current_user_game:
        return []
    
    users = db.query(models.User).filter(
        models.User.game == current_user_game,
        models.User.id != current_user_id,
        models.User.is_active == True
    ).all()
    
    return users