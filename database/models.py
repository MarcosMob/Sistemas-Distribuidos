# database/models.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    game = Column(String, nullable=True)

# Novo Enum para o status
class MatchStatus(enum.Enum):
    PENDING = "pending"
    MATCHED = "matched"

# Nova tabela para as sessões de match
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    # IDs dos dois usuários envolvidos
    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Status da interação
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING, nullable=False)
    # Timestamp do match
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos (opcional, mas bom para consultas)
    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])

# Nova tabela para rastrear curtidas individuais
class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    # Usuário que curtiu
    liker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Usuário que foi curtido
    liked_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Timestamp da curtida
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    liker = relationship("User", foreign_keys=[liker_id])
    liked = relationship("User", foreign_keys=[liked_id])

# Nova tabela para mensagens de chat
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    # ID do match (sala de chat)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    # Usuário que enviou a mensagem
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Conteúdo da mensagem
    content = Column(String, nullable=False)
    # Timestamp da mensagem
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    match = relationship("Match")
    sender = relationship("User")