# schemas/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

# Esquema para a criação de um usuário
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    game: Optional[str] = None

# Esquema para atualizar dados do usuário
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    game: Optional[str] = None

# Esquema para ler/retornar dados do usuário (sem a senha!)
class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    game: Optional[str] = None

    class Config:
        from_attributes = True # Antigo orm_mode = True

