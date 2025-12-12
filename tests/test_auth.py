"""
Testes para rotas de autenticação
"""
import pytest
from fastapi import status


class TestRegister:
    """Testes para o endpoint de registro"""
    
    def test_register_success(self, client, test_user_data):
        """Testa registro bem-sucedido"""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["game"] == test_user_data["game"]
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data  # Senha não deve ser retornada
    
    def test_register_duplicate_email(self, client, test_user_data):
        """Testa registro com email duplicado"""
        # Primeiro registro
        response1 = client.post("/auth/register", json=test_user_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Segundo registro com mesmo email
        response2 = client.post("/auth/register", json=test_user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response2.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Testa registro com email inválido"""
        invalid_data = {
            "email": "invalid-email",
            "password": "test123",
            "game": "League of Legends"
        }
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_fields(self, client):
        """Testa registro com campos faltando"""
        incomplete_data = {"email": "test@example.com"}
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Testes para o endpoint de login"""
    
    def test_login_success(self, client, test_user_data):
        """Testa login bem-sucedido"""
        # Primeiro registra o usuário
        client.post("/auth/register", json=test_user_data)
        
        # Depois faz login
        response = client.post(
            "/auth/token",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_wrong_password(self, client, test_user_data):
        """Testa login com senha incorreta"""
        # Registra o usuário
        client.post("/auth/register", json=test_user_data)
        
        # Tenta login com senha errada
        response = client.post(
            "/auth/token",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Testa login com usuário que não existe"""
        response = client.post(
            "/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "anypassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_missing_credentials(self, client):
        """Testa login sem credenciais"""
        response = client.post("/auth/token", data={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCurrentUser:
    """Testes para obter dados do usuário atual"""
    
    def test_get_current_user_success(self, client, auth_headers, test_user_data):
        """Testa obter dados do usuário autenticado"""
        response = client.get("/auth/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_get_current_user_unauthorized(self, client):
        """Testa obter dados sem autenticação"""
        response = client.get("/auth/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Testa obter dados com token inválido"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateUser:
    """Testes para atualizar dados do usuário"""
    
    def test_update_user_game(self, client, auth_headers, test_user_data):
        """Testa atualizar o jogo do usuário"""
        # Criar usuário primeiro
        register_response = client.post("/auth/register", json=test_user_data)
        if register_response.status_code != 200:
            # Se já existe, fazer login para obter token
            login_response = client.post(
                "/auth/token",
                data={"username": test_user_data["email"], "password": test_user_data["password"]}
            )
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = auth_headers
        
        new_game = "Valorant"
        response = client.put(
            "/auth/users/me",
            headers=headers,
            json={"game": new_game}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["game"] == new_game
        assert data["email"] == test_user_data["email"]
    
    def test_update_user_email(self, client, auth_headers):
        """Testa atualizar o email do usuário"""
        new_email = "newemail@example.com"
        response = client.put(
            "/auth/users/me",
            headers=auth_headers,
            json={"email": new_email}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == new_email
    
    def test_update_user_duplicate_email(self, client, two_users):
        """Testa atualizar email para um que já existe"""
        # Tenta mudar email do user1 para o email do user2
        response = client.put(
            "/auth/users/me",
            headers=two_users["headers1"],
            json={"email": two_users["user2"]["email"]}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    def test_update_user_unauthorized(self, client):
        """Testa atualizar sem autenticação"""
        response = client.put(
            "/auth/users/me",
            json={"game": "New Game"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetMatches:
    """Testes para buscar usuários com mesmo jogo"""
    
    def test_get_matches_same_game(self, client, two_users):
        """Testa buscar matches quando há usuários com mesmo jogo"""
        response = client.get(
            "/auth/users/match",
            headers=two_users["headers1"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        matches = response.json()
        assert isinstance(matches, list)
        # Deve encontrar o user2 que tem o mesmo jogo
        user_ids = [user["id"] for user in matches]
        assert two_users["user2"]["id"] in user_ids
        # Não deve incluir o próprio usuário
        assert two_users["user1"]["id"] not in user_ids
    
    def test_get_matches_different_game(self, client, test_user_data, test_user3_data):
        """Testa buscar matches quando não há usuários com mesmo jogo"""
        # Criar user1
        client.post("/auth/register", json=test_user_data)
        token1_response = client.post(
            "/auth/token",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        token1 = token1_response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        # Criar user3 com jogo diferente
        client.post("/auth/register", json=test_user3_data)
        
        # Buscar matches do user1
        response = client.get("/auth/users/match", headers=headers1)
        
        assert response.status_code == status.HTTP_200_OK
        matches = response.json()
        # Não deve encontrar user3 porque tem jogo diferente
        user_emails = [user["email"] for user in matches]
        assert test_user3_data["email"] not in user_emails
    
    def test_get_matches_no_game(self, client, auth_headers):
        """Testa buscar matches quando usuário não tem jogo definido"""
        response = client.get("/auth/users/match", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        matches = response.json()
        assert matches == []
    
    def test_get_matches_unauthorized(self, client):
        """Testa buscar matches sem autenticação"""
        response = client.get("/auth/users/match")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

