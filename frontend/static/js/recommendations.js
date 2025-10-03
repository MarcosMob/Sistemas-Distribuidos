document.addEventListener('DOMContentLoaded', async () => {
    const userInfo = document.getElementById('user-info');
    const recommendationsContainer = document.getElementById('recommendations-container');
    const logoutButton = document.getElementById('logout-button');

    const API_URL = 'http://127.0.0.1:8000';
    const token = localStorage.getItem('accessToken');

    if (!token) {
        window.location.href = '/';
        return;
    }

    let currentUser = null;
    let userMatches = new Map(); // Map<userId, matchId> para armazenar matches
    let userLikesSent = new Set(); // Para armazenar IDs dos usuários que já curtimos
    let userLikesReceived = new Set(); // Para armazenar IDs dos usuários que nos curtiram

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
            userInfo.innerHTML = `<p><strong>Email:</strong> ${user.email}</p><p><strong>Game:</strong> ${user.game || 'N/A'}</p>`;
            return user;
        } catch (error) {
            console.error(error);
            localStorage.removeItem('accessToken');
            window.location.href = '/';
        }
    }

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
            // Armazenar matches com seus IDs
            matches.forEach(match => {
                if (match.status === 'matched') {
                    // Armazenar o match_id para cada usuário
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

    async function fetchRecommendations() {
        try {
            const response = await fetch(`${API_URL}/auth/users/match`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch recommendations');
            }

            const recommendations = await response.json();
            displayRecommendations(recommendations);
        } catch (error) {
            console.error(error);
        }
    }

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
                // Recarregar recomendações para atualizar botões
                await fetchRecommendations();
            } else if (result.status === 'LIKED') {
                alert('Curtida enviada! Aguarde o outro usuário responder.');
                userLikesSent.add(targetUserId);
                // Recarregar recomendações para atualizar botões
                await fetchRecommendations();
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

    function startChat(userId) {
        // Buscar o match_id correto para este usuário
        const matchId = userMatches.get(userId);
        
        if (matchId) {
            window.location.href = `/chat/${matchId}`;
        } else {
            alert('Match não encontrado');
        }
    }

    function displayRecommendations(recommendations) {
        if (recommendations.length === 0) {
            recommendationsContainer.innerHTML = '<p>Nenhuma recomendação encontrada.</p>';
            return;
        }

        recommendationsContainer.innerHTML = recommendations.map(rec => {
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
    await fetchRecommendations();
});