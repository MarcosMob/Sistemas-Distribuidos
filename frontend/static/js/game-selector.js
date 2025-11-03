document.addEventListener('DOMContentLoaded', async () => {
    const gameSelector = document.getElementById('game-selector');
    const searchButton = document.getElementById('search-button');
    const recommendationsContainer = document.getElementById('recommendations-container');
    const usersList = document.getElementById('users-list');
    const errorMessage = document.getElementById('error-message');
    const logoutButton = document.getElementById('logout-button');

    const API_URL = '';
    const token = localStorage.getItem('accessToken');

    if (!token) {
        window.location.href = '/';
        return;
    }

    let currentUser = null;
    let userMatches = new Map();
    let userLikesSent = new Set();
    let userLikesReceived = new Set();

    // Buscar dados do usuário atual
    async function fetchUserData() {
        try {
            const response = await fetch(`${API_URL}/auth/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user data');
            }

            const user = await response.json();
            currentUser = user;
            
            // Se o usuário já tem um jogo, pré-selecionar
            if (user.game) {
                gameSelector.value = user.game;
            }
            
            return user;
        } catch (error) {
            console.error(error);
            localStorage.removeItem('accessToken');
            window.location.href = '/';
        }
    }

    // Buscar matches do usuário
    async function fetchUserMatches() {
        try {
            const response = await fetch(`${API_URL}/matches/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch matches');
            }

            const matches = await response.json();
            matches.forEach(match => {
                if (match.status === 'matched') {
                    userMatches.set(match.user_a.id, match.id);
                    userMatches.set(match.user_b.id, match.id);
                }
            });
            return matches;
        } catch (error) {
            console.error('Error fetching matches:', error);
            return [];
        }
    }

    // Buscar likes enviados
    async function fetchUserLikesSent() {
        try {
            const response = await fetch(`${API_URL}/matches/likes-sent`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch likes sent');
            }

            const likes = await response.json();
            likes.forEach(like => {
                userLikesSent.add(like.liked_user_id);
            });
            return likes;
        } catch (error) {
            console.error('Error fetching likes sent:', error);
            return [];
        }
    }

    // Buscar likes recebidos
    async function fetchUserLikesReceived() {
        try {
            const response = await fetch(`${API_URL}/matches/likes-received`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch likes received');
            }

            const likes = await response.json();
            likes.forEach(like => {
                userLikesReceived.add(like.liker_user_id);
            });
            return likes;
        } catch (error) {
            console.error('Error fetching likes received:', error);
            return [];
        }
    }

    // Atualizar jogo do usuário e buscar matches
    async function updateGameAndSearch() {
        const selectedGame = gameSelector.value;
        
        if (!selectedGame) {
            errorMessage.textContent = 'Por favor, selecione um jogo';
            return;
        }

        errorMessage.textContent = '';
        searchButton.disabled = true;
        searchButton.textContent = 'Buscando...';

        try {
            // 1. Atualizar o jogo do usuário
            const updateResponse = await fetch(`${API_URL}/auth/users/me`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game: selectedGame }),
            });

            if (!updateResponse.ok) {
                const errorData = await updateResponse.json();
                throw new Error(errorData.detail || 'Failed to update game');
            }

            const updatedUser = await updateResponse.json();
            currentUser = updatedUser;

            // 2. Buscar usuários com o mesmo jogo
            const matchesResponse = await fetch(`${API_URL}/auth/users/match`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!matchesResponse.ok) {
                throw new Error('Failed to fetch matches');
            }

            const recommendations = await matchesResponse.json();
            
            // 3. Recarregar dados de matches e likes
            await fetchUserMatches();
            await fetchUserLikesSent();
            await fetchUserLikesReceived();
            
            // 4. Exibir recomendações
            displayRecommendations(recommendations);
            recommendationsContainer.style.display = 'block';

        } catch (error) {
            console.error(error);
            errorMessage.textContent = error.message || 'Erro ao buscar jogadores';
        } finally {
            searchButton.disabled = false;
            searchButton.textContent = 'Buscar Jogadores';
        }
    }

    // Curtir usuário
    async function likeUser(targetUserId) {
        try {
            const response = await fetch(`${API_URL}/matches/like/${targetUserId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to like user');
            }

            const result = await response.json();
            
            if (result.status === 'MATCHED') {
                alert('Match! Vocês se curtiram!');
                userMatches.set(targetUserId, result.match_id);
                userLikesSent.add(targetUserId);
                // Recarregar recomendações
                await updateGameAndSearch();
            } else if (result.status === 'LIKED') {
                alert('Curtida enviada! Aguarde o outro usuário responder.');
                userLikesSent.add(targetUserId);
                await updateGameAndSearch();
            } else if (result.status === 'ALREADY_LIKED') {
                alert('Você já curtiu este usuário!');
            } else if (result.status === 'ERROR') {
                alert(result.message);
            }
        } catch (error) {
            console.error('Error liking user:', error);
            alert('Erro ao curtir usuário');
        }
    }

    // Iniciar chat
    function startChat(userId) {
        const matchId = userMatches.get(userId);
        
        if (matchId) {
            window.location.href = `/chat/${matchId}`;
        } else {
            alert('Match não encontrado');
        }
    }

    // Exibir recomendações
    function displayRecommendations(recommendations) {
        if (recommendations.length === 0) {
            usersList.innerHTML = '<p>Nenhum jogador encontrado para este jogo.</p>';
            return;
        }

        usersList.innerHTML = recommendations.map(rec => {
            const hasMatch = userMatches.has(rec.id);
            const hasLiked = userLikesSent.has(rec.id);
            const hasReceivedLike = userLikesReceived.has(rec.id);
            const isCurrentUser = currentUser && rec.id === currentUser.id;
            
            let buttonText = 'Curtir';
            let buttonClass = 'match-button';
            let buttonDisabled = false;
            
            if (hasMatch) {
                buttonText = 'Match!';
                buttonClass = 'match-button matched';
                buttonDisabled = true;
            } else if (hasLiked) {
                buttonText = 'Aguardando...';
                buttonClass = 'match-button pending';
                buttonDisabled = true;
            } else if (hasReceivedLike) {
                buttonText = 'Curtir de volta!';
                buttonClass = 'match-button received-like';
            }
            
            return `
                <div class="recommendation-card">
                    <p><strong>Email:</strong> ${rec.email}</p>
                    <p><strong>Game:</strong> ${rec.game}</p>
                    ${hasReceivedLike && !hasLiked && !hasMatch ? '<p class="like-indicator">Esta pessoa curtiu você!</p>' : ''}
                    <div class="card-actions">
                        ${!isCurrentUser ? `
                            <button class="${buttonClass}" onclick="likeUser(${rec.id})" 
                                    ${buttonDisabled ? 'disabled' : ''}>
                                ${buttonText}
                            </button>
                            ${hasMatch ? `
                                <button class="chat-button" onclick="startChat(${rec.id})">
                                     Chat
                                </button>
                            ` : ''}
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Event listeners
    searchButton.addEventListener('click', updateGameAndSearch);
    
    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.href = '/';
    });

    // Tornar funções globais para uso nos botões
    window.likeUser = likeUser;
    window.startChat = startChat;

    // Carregar dados iniciais
    await fetchUserData();
    await fetchUserMatches();
    await fetchUserLikesSent();
    await fetchUserLikesReceived();
});

