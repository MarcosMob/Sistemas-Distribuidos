# services/chat_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import models
from datetime import datetime

def get_chat_messages(db: Session, match_id: int, user_id: int):
    """Busca mensagens de um chat específico, verificando se o usuário tem acesso"""
    
    # Verifica se o usuário pertence ao match
    match = db.query(models.Match).filter(
        and_(
            models.Match.id == match_id,
            models.Match.status == models.MatchStatus.MATCHED,
            (models.Match.user_a_id == user_id) | (models.Match.user_b_id == user_id)
        )
    ).first()
    
    if not match:
        return None
    
    # Busca as mensagens do chat
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.match_id == match_id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    return messages

def save_chat_message(db: Session, match_id: int, sender_id: int, content: str):
    """Salva uma mensagem no chat"""
    
    # Verifica se o usuário pertence ao match
    match = db.query(models.Match).filter(
        and_(
            models.Match.id == match_id,
            models.Match.status == models.MatchStatus.MATCHED,
            (models.Match.user_a_id == sender_id) | (models.Match.user_b_id == sender_id)
        )
    ).first()
    
    if not match:
        return None
    
    # Cria a mensagem
    message = models.ChatMessage(
        match_id=match_id,
        sender_id=sender_id,
        content=content
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message

def get_user_chats(db: Session, user_id: int):
    """Retorna todos os chats (matches) do usuário"""
    matches = db.query(models.Match).filter(
        and_(
            (models.Match.user_a_id == user_id) | (models.Match.user_b_id == user_id),
            models.Match.status == models.MatchStatus.MATCHED
        )
    ).all()
    
    return matches

def get_match_by_id_and_user(db: Session, match_id: int, user_id: int):
    """
    Verifica se um match existe, está 'MATCHED' e se o usuário 
    especificado faz parte dele.
    """
    return db.query(models.Match).filter(
        models.Match.id == match_id,
        models.Match.status == models.MatchStatus.MATCHED,
        (models.Match.user_a_id == user_id) | (models.Match.user_b_id == user_id)
    ).first()
