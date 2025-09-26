# routers/auth.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from schemas import user as user_schema, token as token_schema
from services import user_service
from auth import utils as auth_utils
from database.connection import get_db # Importe sua dependência get_db

router = APIRouter(
    prefix="/auth", # Adicionar um prefixo é uma boa prática
    tags=["Authentication"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Função de dependência para obter o usuário atual
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = token_schema.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = user_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# Endpoint de Registro
@router.post("/register", response_model=user_schema.User)
def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create_user(db=db, user=user)

# Endpoint de Login (Token)
@router.post("/token", response_model=token_schema.Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = user_service.get_user_by_email(db, email=form_data.username)
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint Protegido - Obter dados do usuário atual
@router.get("/users/me", response_model=user_schema.User)
def read_users_me(current_user: Annotated[user_schema.User, Depends(get_current_user)]):
    return current_user

# Endpoint Protegido - Atualizar dados do usuário atual
@router.put("/users/me", response_model=user_schema.User)
def update_user_me(
    user_update: user_schema.UserUpdate,
    current_user: Annotated[user_schema.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    # Verifica se o email já existe em outro usuário (se estiver sendo alterado)
    if user_update.email and user_update.email != current_user.email:
        existing_user = user_service.get_user_by_email(db, email=user_update.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    updated_user = user_service.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

# Endpoint Protegido - Buscar usuários com mesmo jogo (matches)
@router.get("/users/match", response_model=list[user_schema.User])
def get_matches(
    current_user: Annotated[user_schema.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Busca usuários que jogam o mesmo jogo que o usuário logado"""
    matches = user_service.get_users_with_same_game(
        db, 
        current_user.id, 
        current_user.game
    )
    return matches