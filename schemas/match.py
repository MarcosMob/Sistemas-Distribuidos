# schemas/match.py
import enum
from pydantic import BaseModel
from .user import User # Importe o schema do usuário

class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    MATCHED = "matched"

# Schema para retornar um match, incluindo os dados dos usuários
class Match(BaseModel):
    id: int
    user_a: User
    user_b: User
    status: MatchStatus

    class Config:
        from_attributes = True