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
            userInfo.innerHTML = `<p><strong>Email:</strong> ${user.email}</p><p><strong>Game:</strong> ${user.game || 'N/A'}</p>`;
            return user;
        } catch (error) {
            console.error(error);
            localStorage.removeItem('accessToken');
            window.location.href = '/';
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

    function displayRecommendations(recommendations) {
        if (recommendations.length === 0) {
            recommendationsContainer.innerHTML = '<p>Nenhuma recomendação encontrada.</p>';
            return;
        }

        recommendationsContainer.innerHTML = recommendations.map(rec => `
            <div class="recommendation-card">
                <p><strong>Email:</strong> ${rec.email}</p>
                <p><strong>Game:</strong> ${rec.game}</p>
            </div>
        `).join('');
    }

    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.href = '/';
    });

    await fetchUserData();
    await fetchRecommendations();
});