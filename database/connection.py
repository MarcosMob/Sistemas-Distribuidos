# app/database/connection.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import load_secrets # <--- Importe sua função

# --- CORREÇÃO AQUI ---
# Antes de tentar criar a engine, verifique se a URL existe.
# Se não existir (ou for vazia), force o carregamento dos segredos da AWS.
if not os.getenv("DATABASE_URL"):
    load_secrets() 

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Proteção extra: Se ainda assim estiver vazio, avisa o erro
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("A variavel DATABASE_URL esta vazia. Verifique o Secrets Manager.")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()