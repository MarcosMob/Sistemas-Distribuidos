# services/match_service.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from database import models
from . import user_service

def like_user(db: Session, current_user_id: int, target_user_id: int):
    """
    Sistema de curtidas atômico:
    1. Usuário A curte Usuário B → Cria Like
    2. Se Usuário B já curtiu Usuário A → Cria Match
    3. Se não há reciprocidade → Apenas Like
    """
    
    # Não pode curtir a si mesmo
    if current_user_id == target_user_id:
        return {"status": "ERROR", "message": "Cannot like yourself"}
    
    # Verifica se já curtiu este usuário
    existing_like = db.query(models.Like).filter(
        models.Like.liker_id == current_user_id,
        models.Like.liked_id == target_user_id
    ).first()
    
    if existing_like:
        return {"status": "ALREADY_LIKED", "message": "You already liked this user"}
    
    # Verifica se o usuário alvo já curtiu o usuário atual (reciprocidade)
    reciprocal_like = db.query(models.Like).filter(
        models.Like.liker_id == target_user_id,
        models.Like.liked_id == current_user_id
    ).first()
    
    # Cria a curtida
    new_like = models.Like(
        liker_id=current_user_id,
        liked_id=target_user_id
    )
    db.add(new_like)
    
    if reciprocal_like:
        # Há reciprocidade! Criar match
        # Garante ordem consistente dos IDs
        user1_id = min(current_user_id, target_user_id)
        user2_id = max(current_user_id, target_user_id)
        
        new_match = models.Match(
            user_a_id=user1_id,
            user_b_id=user2_id,
            status=models.MatchStatus.MATCHED
        )
        db.add(new_match)
        db.commit()
        db.refresh(new_match)
        
        return {
            "status": "MATCHED", 
            "message": "It's a match!",
            "match_id": new_match.id
        }
    else:
        # Apenas curtida, sem reciprocidade
        db.commit()
        db.refresh(new_like)
        
        return {
            "status": "LIKED", 
            "message": "Like sent! Waiting for response.",
            "like_id": new_like.id
        }

def get_user_matches(db: Session, user_id: int):
    """ Retorna apenas os matches confirmados do usuário """
    matches = db.query(models.Match).filter(
        and_(
            or_(models.Match.user_a_id == user_id, models.Match.user_b_id == user_id),
            models.Match.status == models.MatchStatus.MATCHED
        )
    ).all()
    return matches

def get_user_likes(db: Session, user_id: int):
    """ Retorna usuários que o usuário curtiu (mas ainda não deram match) """
    # Busca curtidas que ainda não viraram match
    likes = db.query(models.Like).filter(
        models.Like.liker_id == user_id
    ).all()
    
    # Filtra apenas os que não têm match correspondente
    pending_likes = []
    for like in likes:
        # Verifica se já existe match entre esses usuários
        match_exists = db.query(models.Match).filter(
            or_(
                and_(models.Match.user_a_id == like.liker_id, models.Match.user_b_id == like.liked_id),
                and_(models.Match.user_a_id == like.liked_id, models.Match.user_b_id == like.liker_id)
            )
        ).first()
        
        if not match_exists:
            pending_likes.append(like)
    
    return pending_likes

def get_user_liked_by(db: Session, user_id: int):
    """ Retorna usuários que curtiram o usuário (mas ainda não deram match) """
    # Busca curtidas recebidas que ainda não viraram match
    likes = db.query(models.Like).filter(
        models.Like.liked_id == user_id
    ).all()
    
    # Filtra apenas os que não têm match correspondente
    pending_likes = []
    for like in likes:
        # Verifica se já existe match entre esses usuários
        match_exists = db.query(models.Match).filter(
            or_(
                and_(models.Match.user_a_id == like.liker_id, models.Match.user_b_id == like.liked_id),
                and_(models.Match.user_a_id == like.liked_id, models.Match.user_b_id == like.liker_id)
            )
        ).first()
        
        if not match_exists:
            pending_likes.append(like)
    
    return pending_likes