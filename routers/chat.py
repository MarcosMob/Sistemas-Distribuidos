# routers/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from database.connection import get_db
from schemas import chat as chat_schema, user as user_schema
from services import chat_service
from routers.auth import get_current_user

# Classe para gerenciar conexões WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int, user_id: int):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        
        # Armazena informações do usuário junto com a conexão
        websocket.user_id = user_id
        self.active_connections[match_id].append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: int):
        if match_id in self.active_connections:
            self.active_connections[match_id] = [
                conn for conn in self.active_connections[match_id] 
                if conn != websocket
            ]

    async def broadcast(self, message_data: dict, match_id: int, exclude_user: int = None):
        """Envia mensagem para todos os usuários conectados no match"""
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                if exclude_user and hasattr(connection, 'user_id') and connection.user_id == exclude_user:
                    continue
                try:
                    await connection.send_text(json.dumps(message_data))
                except:
                    # Remove conexões que falharam
                    self.active_connections[match_id] = [
                        conn for conn in self.active_connections[match_id] 
                        if conn != connection
                    ]

manager = ConnectionManager()
router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/rooms", response_model=List[chat_schema.ChatRoom])
def get_chat_rooms(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Retorna todas as salas de chat do usuário"""
    chats = chat_service.get_user_chats(db, current_user.id)
    
    rooms = []
    for match in chats:
        # Determina qual é o outro usuário
        other_user = match.user_a if match.user_b_id == current_user.id else match.user_b
        
        # Busca a última mensagem
        messages = chat_service.get_chat_messages(db, match.id, current_user.id)
        last_message = messages[-1] if messages else None
        
        room = chat_schema.ChatRoom(
            match_id=match.id,
            other_user=other_user,
            last_message=last_message,
            unread_count=0  # TODO: Implementar contagem de mensagens não lidas
        )
        rooms.append(room)
    
    return rooms

@router.get("/messages/{match_id}", response_model=List[chat_schema.ChatMessage])
def get_chat_messages(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Retorna mensagens de um chat específico"""
    messages = chat_service.get_chat_messages(db, match_id, current_user.id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")
    return messages

@router.post("/messages/{match_id}", response_model=chat_schema.ChatMessage)
def send_message(
    match_id: int,
    message: chat_schema.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """Envia uma mensagem para um chat"""
    saved_message = chat_service.save_chat_message(
        db, match_id, current_user.id, message.content
    )
    if saved_message is None:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")
    
    # Envia via WebSocket para usuários conectados
    message_data = {
        "type": "message",
        "id": saved_message.id,
        "sender_id": saved_message.sender_id,
        "content": saved_message.content,
        "created_at": saved_message.created_at.isoformat(),
        "sender_name": current_user.email
    }
    
    # Broadcast para todos conectados no match (exceto o remetente)
    # Como estamos em uma função síncrona, vamos apenas salvar a mensagem
    # O WebSocket será usado apenas para receber mensagens em tempo real
    
    return saved_message

@router.websocket("/ws/{match_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    match_id: int,
    token: str = None
):
    """WebSocket para chat em tempo real"""
    
    # TODO: Implementar autenticação JWT no WebSocket
    # Por enquanto, vamos aceitar qualquer conexão
    # Em produção, você deveria validar o token JWT aqui
    
    await manager.connect(websocket, match_id, 0)  # user_id temporário
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Broadcast da mensagem para todos os conectados
            await manager.broadcast({
                "type": "message",
                "content": message_data.get("content", ""),
                "sender_name": "Usuário"
            }, match_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)