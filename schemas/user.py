# schemas/schemas.py
from pydantic import BaseModel, EmailStr

# Esquema para a criação de um usuário
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Esquema para ler/retornar dados do usuário (sem a senha!)
class User(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True # Antigo orm_mode = True

