"""
Configuração global de testes - fixtures compartilhadas
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configurar variáveis de ambiente para testes ANTES de importar main
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from main import app
from database.connection import Base, get_db
from database import models

# Database de teste em memória (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Cria um banco de dados de teste limpo para cada teste"""
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Cria uma sessão
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Limpa todas as tabelas após o teste
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Cliente HTTP para testes"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Override do get_db para usar o banco de teste
    app.dependency_overrides[get_db] = override_get_db
    
    # Override do SessionLocal para WebSocket também usar o banco de teste
    # O WebSocket usa SessionLocal() diretamente, então precisamos fazer monkey patch
    import database.connection as db_conn
    original_SessionLocal = db_conn.SessionLocal
    
    # Criar uma função que retorna sempre a mesma sessão de teste
    def mock_SessionLocal():
        return db
    
    # Aplicar o monkey patch
    db_conn.SessionLocal = mock_SessionLocal
    
    # Também fazer patch no import do chat.py se necessário
    import routers.chat as chat_module
    chat_module.SessionLocal = mock_SessionLocal
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Restaurar
    app.dependency_overrides.clear()
    db_conn.SessionLocal = original_SessionLocal
    chat_module.SessionLocal = original_SessionLocal


@pytest.fixture
def test_user_data():
    """Dados de um usuário de teste"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "game": "League of Legends"
    }


@pytest.fixture
def test_user2_data():
    """Dados de um segundo usuário de teste"""
    return {
        "email": "test2@example.com",
        "password": "testpassword123",
        "game": "League of Legends"
    }


@pytest.fixture
def test_user3_data():
    """Dados de um terceiro usuário de teste (jogo diferente)"""
    return {
        "email": "test3@example.com",
        "password": "testpassword123",
        "game": "Valorant"
    }


@pytest.fixture
def created_user(client, test_user_data, db):
    """Cria um usuário e retorna os dados"""
    # Limpar qualquer usuário existente primeiro (garantir isolamento)
    from database import models
    db.query(models.User).filter(models.User.email == test_user_data["email"]).delete()
    db.commit()
    
    response = client.post("/auth/register", json=test_user_data)
    if response.status_code != 200:
        # Se falhar, pode ser que já existe - tenta buscar
        from services import user_service
        existing_user = user_service.get_user_by_email(db, test_user_data["email"])
        if existing_user:
            return {
                "id": existing_user.id,
                "email": existing_user.email,
                "game": existing_user.game,
                "is_active": existing_user.is_active
            }
    assert response.status_code == 200, f"Erro ao criar usuário: {response.text}"
    return response.json()


@pytest.fixture
def auth_token(client, test_user_data):
    """Cria um usuário e retorna o token de autenticação"""
    # Registra o usuário
    client.post("/auth/register", json=test_user_data)
    
    # Faz login
    response = client.post(
        "/auth/token",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Headers de autenticação para requisições"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def two_users(client, test_user_data, test_user2_data):
    """Cria dois usuários e retorna seus dados e tokens"""
    # Criar primeiro usuário
    user1_response = client.post("/auth/register", json=test_user_data)
    assert user1_response.status_code == 200
    user1 = user1_response.json()
    
    # Login do primeiro usuário
    token1_response = client.post(
        "/auth/token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token1 = token1_response.json()["access_token"]
    
    # Criar segundo usuário
    user2_response = client.post("/auth/register", json=test_user2_data)
    assert user2_response.status_code == 200
    user2 = user2_response.json()
    
    # Login do segundo usuário
    token2_response = client.post(
        "/auth/token",
        data={"username": test_user2_data["email"], "password": test_user2_data["password"]}
    )
    token2 = token2_response.json()["access_token"]
    
    return {
        "user1": user1,
        "user2": user2,
        "token1": token1,
        "token2": token2,
        "headers1": {"Authorization": f"Bearer {token1}"},
        "headers2": {"Authorization": f"Bearer {token2}"}
    }

