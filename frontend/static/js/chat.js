// frontend/static/js/chat.js
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

    const pathParts = window.location.pathname.split('/');
    const matchId = pathParts[pathParts.length - 1];

    if (!matchId || isNaN(matchId)) {
        alert('ID de match inválido');
        window.location.href = '/recommendations';
        return;
    }

    let websocket;
    let currentUser = null;

    async function fetchCurrentUser() {
        try {
            const response = await fetch(`${API_URL}/auth/users/me`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) throw new Error('Failed to fetch user data');
            currentUser = await response.json();
            return currentUser;
        } catch (error) {
            console.error(error);
            localStorage.removeItem('accessToken');
            window.location.href = '/';
        }
    }

    async function loadMessages() {
        try {
            const response = await fetch(`${API_URL}/chat/messages/${matchId}`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) throw new Error('Failed to load messages');
            
            const messages = await response.json();
            messages.forEach(message => {
                const isOwn = message.sender_id === currentUser.id;
                addMessage(message.content, isOwn ? 'own' : 'other', message.created_at);
            });
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    // --- MUDANÇA 1: Passar o token na URL ---
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Adiciona o token como um query parameter para autenticação
        const wsUrl = `${protocol}//${window.location.host}/chat/ws/${matchId}?token=${token}`;
        
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
            console.log('Conectado ao chat');
            addSystemMessage('Conectado!');
        };
        
        // onmessage agora é a *única* fonte de novas mensagens
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    // O servidor nos diz quem enviou, então podemos saber se é nossa
                    const isOwn = data.sender_id === currentUser.id;
                    addMessage(data.content, isOwn ? 'own' : 'other', data.created_at);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        websocket.onclose = (event) => {
            console.log('Conexão fechada:', event.reason);
            addSystemMessage('Conexão perdida. Tentando reconectar...');
            // Tenta reconectar após 3 segundos
            setTimeout(connectWebSocket, 3000);
        };
        
        websocket.onerror = (error) => {
            console.error('Erro no WebSocket:', error);
            addSystemMessage('Erro na conexão.');
        };
    }

    function addMessage(text, type, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-time">${timeStr}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
    }

    function addSystemMessage(text) {
        // ... (função igual à sua, sem mudanças)
    }

    // --- MUDANÇA 2: Enviar via WebSocket, não por fetch ---
    function sendMessage() {
        const message = messageInput.value.trim();
        
        if (!message) {
            return;
        }

        // Verifica se o WebSocket está conectado
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            // Envia a mensagem como um objeto JSON
            websocket.send(JSON.stringify({ content: message }));
            
            // Limpa o input
            messageInput.value = '';
            
            // NÃO adicionamos a mensagem localmente.
            // Esperamos o servidor (broadcast) nos devolver a mensagem
            // para termos a confirmação de que ela foi salva.
        } else {
            alert('Não foi possível enviar a mensagem. Verifique sua conexão.');
        }
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    backButton.addEventListener('click', () => {
        window.location.href = '/recommendations'; // Ou /matches
    });

    async function initChat() {
        await fetchCurrentUser();
        await loadMessages(); // Carrega o histórico
        connectWebSocket(); // Conecta para tempo real
    }

    initChat();
});