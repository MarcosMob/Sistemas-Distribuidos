"""
Testes para rotas de chat
"""
import pytest
from fastapi import status


class TestGetChatRooms:
    """Testes para obter salas de chat"""
    
    def test_get_chat_rooms_empty(self, client, auth_headers):
        """Testa obter salas quando não há nenhuma"""
        response = client.get("/chat/rooms", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        rooms = response.json()
        assert isinstance(rooms, list)
        assert len(rooms) == 0
    
    def test_get_chat_rooms_with_match(self, client, two_users):
        """Testa obter salas quando há um match"""
        # Criar match
        like1 = client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like2 = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        
        # Buscar salas do user1
        response = client.get("/chat/rooms", headers=two_users["headers1"])
        
        assert response.status_code == status.HTTP_200_OK
        rooms = response.json()
        assert isinstance(rooms, list)
        assert len(rooms) > 0
        room = rooms[0]
        assert "match_id" in room
        assert "other_user" in room
        assert room["other_user"]["id"] == two_users["user2"]["id"]
    
    def test_get_chat_rooms_unauthorized(self, client):
        """Testa obter salas sem autenticação"""
        response = client.get("/chat/rooms")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetChatMessages:
    """Testes para obter mensagens de um chat"""
    
    def test_get_chat_messages_empty(self, client, two_users):
        """Testa obter mensagens quando não há nenhuma"""
        # Criar match primeiro
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Buscar mensagens
        response = client.get(
            f"/chat/messages/{match_id}",
            headers=two_users["headers1"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        messages = response.json()
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    def test_get_chat_messages_nonexistent_match(self, client, auth_headers):
        """Testa obter mensagens de um match que não existe"""
        response = client.get(
            "/chat/messages/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_chat_messages_unauthorized(self, client, two_users):
        """Testa obter mensagens sem autenticação"""
        # Criar match
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Tentar buscar sem autenticação
        response = client.get(f"/chat/messages/{match_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_chat_messages_access_denied(self, client, two_users, test_user3_data):
        """Testa obter mensagens de um match que não pertence ao usuário"""
        # Criar match entre user1 e user2
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Criar user3 e tentar acessar o match
        user3_response = client.post("/auth/register", json=test_user3_data)
        token3_response = client.post(
            "/auth/token",
            data={"username": test_user3_data["email"], "password": test_user3_data["password"]}
        )
        token3 = token3_response.json()["access_token"]
        headers3 = {"Authorization": f"Bearer {token3}"}
        
        # User3 não deve conseguir acessar o match entre user1 e user2
        response = client.get(
            f"/chat/messages/{match_id}",
            headers=headers3
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestWebSocket:
    """Testes para WebSocket de chat"""
    
    def test_websocket_connection_success(self, client, two_users):
        """Testa conexão WebSocket bem-sucedida"""
        # Criar match
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Conectar via WebSocket
        with client.websocket_connect(
            f"/chat/ws/{match_id}?token={two_users['token1']}"
        ) as websocket:
            # Se chegou aqui, a conexão foi aceita
            assert websocket is not None
    
    def test_websocket_invalid_token(self, client, two_users):
        """Testa conexão WebSocket com token inválido"""
        # Criar match
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Tentar conectar com token inválido
        with pytest.raises(Exception):  # WebSocket deve fechar
            with client.websocket_connect(
                f"/chat/ws/{match_id}?token=invalid_token"
            ) as websocket:
                pass
    
    def test_websocket_no_match_access(self, client, two_users, test_user3_data):
        """Testa conexão WebSocket para match que não pertence ao usuário"""
        # Criar match entre user1 e user2
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Criar user3 e tentar conectar ao match
        client.post("/auth/register", json=test_user3_data)
        token3_response = client.post(
            "/auth/token",
            data={"username": test_user3_data["email"], "password": test_user3_data["password"]}
        )
        token3 = token3_response.json()["access_token"]
        
        # User3 não deve conseguir conectar
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/chat/ws/{match_id}?token={token3}"
            ) as websocket:
                pass
    
    def test_websocket_send_message(self, client, two_users):
        """Testa enviar mensagem via WebSocket"""
        # Criar match
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        like_response = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        match_id = like_response.json()["match_id"]
        
        # Conectar e enviar mensagem
        with client.websocket_connect(
            f"/chat/ws/{match_id}?token={two_users['token1']}"
        ) as websocket:
            # Enviar mensagem
            websocket.send_json({"content": "Hello, World!"})
            
            # Receber resposta (a mensagem deve ser broadcastada)
            data = websocket.receive_json()
            assert data["type"] == "message"
            assert data["content"] == "Hello, World!"
            assert "sender_id" in data
            assert "created_at" in data

