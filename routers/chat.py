# routers/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from database.connection import get_db
from schemas import chat as chat_schema, user as user_schema
from services import chat_service
from routers.auth import get_current_user

from database.connection import SessionLocal
from fastapi import status
from auth.utils import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from services import user_service

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


def get_user_from_websocket_token(token: str, db: Session):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = user_service.get_user_by_email(db, email=email)
        return user
    except JWTError:
        return None

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

@router.websocket("/ws/{match_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    match_id: int,
    token: str  # O token virá como query param: .../ws/123?token=XYZ
):

    db = SessionLocal() # Cria uma sessão de banco SÓ para esta conexão
    try:
        # 1. AUTENTICAR
        current_user = get_user_from_websocket_token(token, db)
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 2. AUTORIZAR
        match = chat_service.get_match_by_id_and_user(db, match_id, current_user.id)
        if not match:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Conexão autorizada
        await manager.connect(websocket, match_id, current_user.id)

        while True:
            # Cliente envia: {"content": "Olá!"}
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 3. PERSISTIR
            saved_message = chat_service.save_chat_message(
                db=db,
                match_id=match_id,
                sender_id=current_user.id,
                content=message_data.get("content", "")
            )

            if saved_message:
                # 4. DISTRIBUIR
                # Prepara a mensagem com os dados oficiais do banco
                broadcast_data = {
                    "type": "message",
                    "id": saved_message.id,
                    "sender_id": saved_message.sender_id,
                    "content": saved_message.content,
                    "created_at": saved_message.created_at.isoformat(),
                    "sender_email": current_user.email 
                }

                # Envia para todos na sala (inclusive quem enviou)
                await manager.broadcast(broadcast_data, match_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
    except Exception as e:
        print(f"Erro no WebSocket: {e}") # Bom para debug
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        # Garante que a sessão do banco seja fechada quando o user desconectar
        db.close()