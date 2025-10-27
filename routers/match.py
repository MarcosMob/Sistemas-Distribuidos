# routers/match.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from schemas import match as match_schema, user as user_schema
from services import match_service
from routers.auth import get_current_user # Importa a dependência de usuário logado

router = APIRouter(
    prefix="/matches",
    tags=["Matches"]
)

@router.post("/like/{target_user_id}")
def like_user_endpoint(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Curtir um usuário - sistema atômico de matches"""
    result = match_service.like_user(db, current_user.id, target_user_id)
    return result

@router.get("/me", response_model=List[match_schema.Match])
def get_my_matches(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Retorna apenas matches confirmados"""
    return match_service.get_user_matches(db, current_user.id)

@router.get("/likes-sent")
def get_my_likes_sent(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Retorna usuários que você curtiu (aguardando resposta)"""
    likes = match_service.get_user_likes(db, current_user.id)
    return [{"liked_user_id": like.liked_id, "liked_at": like.created_at} for like in likes]

@router.get("/likes-received")
def get_my_likes_received(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Retorna usuários que curtiram você (você pode curtir de volta)"""
    likes = match_service.get_user_liked_by(db, current_user.id)
    return [{"liker_user_id": like.liker_id, "liked_at": like.created_at} for like in likes]