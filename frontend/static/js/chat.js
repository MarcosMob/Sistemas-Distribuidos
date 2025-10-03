document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const backButton = document.getElementById('back-button');

    const API_URL = 'http://127.0.0.1:8000';
    const token = localStorage.getItem('accessToken');
    
    if (!token) {
        window.location.href = '/';
        return;
    }

    // Obter o match_id da URL
    const pathParts = window.location.pathname.split('/');
    const matchId = pathParts[pathParts.length - 1];

    if (!matchId || isNaN(matchId)) {
        alert('ID de match inválido');
        window.location.href = '/recommendations';
        return;
    }

    let websocket;
    let currentUser = null;

    // Buscar dados do usuário atual
    async function fetchCurrentUser() {
        try {
            const response = await fetch(`${API_URL}/auth/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user data');
            }

            currentUser = await response.json();
            return currentUser;
        } catch (error) {
            console.error(error);
            localStorage.removeItem('accessToken');
            window.location.href = '/';
        }
    }

    // Carregar mensagens existentes
    async function loadMessages() {
        try {
            const response = await fetch(`${API_URL}/chat/messages/${matchId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to load messages');
            }

            const messages = await response.json();
            messages.forEach(message => {
                const isOwn = message.sender_id === currentUser.id;
                addMessage(message.content, isOwn ? 'own' : 'other', message.created_at);
            });
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    // Conectar ao WebSocket
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/chat/ws/${matchId}`;
        
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
            console.log('Conectado ao chat');
            addSystemMessage('Conectado ao chat!');
        };
        
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    const isOwn = data.sender_id === currentUser.id;
                    addMessage(data.content, isOwn ? 'own' : 'other', data.created_at);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        websocket.onclose = () => {
            console.log('Conexão fechada');
            addSystemMessage('Conexão perdida. Tentando reconectar...');
            setTimeout(connectWebSocket, 3000);
        };
        
        websocket.onerror = (error) => {
            console.error('Erro no WebSocket:', error);
            addSystemMessage('Erro na conexão');
        };
    }

    function addMessage(text, type, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-time">${timeStr}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addSystemMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.style.textAlign = 'center';
        messageDiv.style.fontStyle = 'italic';
        messageDiv.style.color = '#666';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        
        if (!message) {
            return;
        }

        try {
            const response = await fetch(`${API_URL}/chat/messages/${matchId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: message }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Erro da API:', errorText);
                throw new Error('Failed to send message');
            }

            const savedMessage = await response.json();
            addMessage(savedMessage.content, 'own', savedMessage.created_at);
            messageInput.value = '';
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Erro ao enviar mensagem: ' + error.message);
        }
    }

    sendButton.addEventListener('click', () => {
        sendMessage();
    });
    
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    backButton.addEventListener('click', () => {
        window.location.href = '/recommendations';
    });

    // Inicializar chat
    async function initChat() {
        await fetchCurrentUser();
        await loadMessages();
        connectWebSocket();
    }

    initChat();
});
