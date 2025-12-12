"""
Testes para rotas de match
"""
import pytest
from fastapi import status


class TestLikeUser:
    """Testes para curtir um usuário"""
    
    def test_like_user_success(self, client, two_users):
        """Testa curtir um usuário com sucesso"""
        response = client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "LIKED"
        assert "message" in data
    
    def test_like_user_match(self, client, two_users):
        """Testa quando ocorre um match (curtida mútua)"""
        # User1 curte User2
        response1 = client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # User2 curte User1 de volta (deve dar match)
        response2 = client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        
        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()
        assert data["status"] == "MATCHED"
        assert "match_id" in data
    
    def test_like_user_already_liked(self, client, two_users):
        """Testa curtir um usuário que já foi curtido"""
        # Primeira curtida
        response1 = client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Segunda curtida (deve falhar)
        response2 = client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        
        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()
        assert data["status"] == "ALREADY_LIKED"
    
    def test_like_user_self(self, client, auth_headers, created_user):
        """Testa tentar curtir a si mesmo"""
        response = client.post(
            f"/matches/like/{created_user['id']}",
            headers=auth_headers
        )
        
        # Deve retornar erro ou status específico
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST, 
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        # Se retornar 200, deve ter status ERROR
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data.get("status") == "ERROR" or "cannot like yourself" in data.get("message", "").lower()
    
    def test_like_user_nonexistent(self, client, auth_headers):
        """Testa curtir um usuário que não existe"""
        response = client.post(
            "/matches/like/99999",
            headers=auth_headers
        )
        
        # Pode retornar 404 ou erro específico
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK
        ]
    
    def test_like_user_unauthorized(self, client, two_users):
        """Testa curtir sem autenticação"""
        response = client.post(
            f"/matches/like/{two_users['user2']['id']}"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetMyMatches:
    """Testes para obter matches do usuário"""
    
    def test_get_my_matches_empty(self, client, auth_headers):
        """Testa obter matches quando não há nenhum"""
        response = client.get("/matches/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        matches = response.json()
        assert isinstance(matches, list)
        assert len(matches) == 0
    
    def test_get_my_matches_with_match(self, client, two_users):
        """Testa obter matches quando há um match"""
        # Criar match
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        client.post(
            f"/matches/like/{two_users['user1']['id']}",
            headers=two_users["headers2"]
        )
        
        # Buscar matches do user1
        response = client.get("/matches/me", headers=two_users["headers1"])
        
        assert response.status_code == status.HTTP_200_OK
        matches = response.json()
        assert isinstance(matches, list)
        assert len(matches) > 0
        # Verifica que o match contém os dois usuários
        match = matches[0]
        assert match["status"] == "matched"
        assert "user_a" in match
        assert "user_b" in match
    
    def test_get_my_matches_unauthorized(self, client):
        """Testa obter matches sem autenticação"""
        response = client.get("/matches/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetLikesSent:
    """Testes para obter likes enviados"""
    
    def test_get_likes_sent_empty(self, client, auth_headers):
        """Testa obter likes enviados quando não há nenhum"""
        response = client.get("/matches/likes-sent", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        likes = response.json()
        assert isinstance(likes, list)
        assert len(likes) == 0
    
    def test_get_likes_sent_with_likes(self, client, two_users):
        """Testa obter likes enviados quando há likes"""
        # User1 curte User2
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        
        # Buscar likes enviados do user1
        response = client.get("/matches/likes-sent", headers=two_users["headers1"])
        
        assert response.status_code == status.HTTP_200_OK
        likes = response.json()
        assert isinstance(likes, list)
        assert len(likes) > 0
        assert likes[0]["liked_user_id"] == two_users["user2"]["id"]
    
    def test_get_likes_sent_unauthorized(self, client):
        """Testa obter likes enviados sem autenticação"""
        response = client.get("/matches/likes-sent")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetLikesReceived:
    """Testes para obter likes recebidos"""
    
    def test_get_likes_received_empty(self, client, auth_headers):
        """Testa obter likes recebidos quando não há nenhum"""
        response = client.get("/matches/likes-received", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        likes = response.json()
        assert isinstance(likes, list)
        assert len(likes) == 0
    
    def test_get_likes_received_with_likes(self, client, two_users):
        """Testa obter likes recebidos quando há likes"""
        # User1 curte User2
        client.post(
            f"/matches/like/{two_users['user2']['id']}",
            headers=two_users["headers1"]
        )
        
        # Buscar likes recebidos do user2
        response = client.get("/matches/likes-received", headers=two_users["headers2"])
        
        assert response.status_code == status.HTTP_200_OK
        likes = response.json()
        assert isinstance(likes, list)
        assert len(likes) > 0
        assert likes[0]["liker_user_id"] == two_users["user1"]["id"]
    
    def test_get_likes_received_unauthorized(self, client):
        """Testa obter likes recebidos sem autenticação"""
        response = client.get("/matches/likes-received")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

