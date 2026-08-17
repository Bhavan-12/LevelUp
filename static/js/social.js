/**
 * LevelUp Social Controller - Friends, Friend Requests & User Search
 */

async function loadSocial() {
    try {
        const [friends, pending] = await Promise.all([
            API.get('/api/social/friends'),
            API.get('/api/social/pending')
        ]);

        renderFriendsList(friends);
        renderPendingRequests(pending);
    } catch (err) {
        console.error('Failed to load social data:', err);
    }
}

function renderFriendsList(friends) {
    const container = document.getElementById('friends-list');
    if (!container) return;

    if (!friends || friends.length === 0) {
        container.innerHTML = `<div class="text-muted small p-3">No friends added yet. Use the search bar on the left to connect!</div>`;
        return;
    }

    container.innerHTML = friends.map(f => `
        <div class="list-group-item d-flex justify-content-between align-items-center p-3">
            <div class="d-flex align-items-center">
                <div class="avatar-circle me-3">${escapeHtml((f.username || 'U').charAt(0).toUpperCase())}</div>
                <div>
                    <h6 class="mb-0 fw-semibold">${escapeHtml(f.username)}</h6>
                    <small class="text-muted">Level ${f.level} • ${f.current_streak} day streak</small>
                </div>
            </div>
            <button class="btn btn-sm btn-outline-primary" onclick="viewFriendProfile(${f.id})">
                View Profile
            </button>
        </div>
    `).join('');
}

function renderPendingRequests(requests) {
    const container = document.getElementById('pending-requests-list');
    if (!container) return;

    if (!requests || requests.length === 0) {
        container.innerHTML = `<div class="text-muted small p-3">No pending friend requests.</div>`;
        return;
    }

    container.innerHTML = requests.map(r => `
        <div class="list-group-item d-flex justify-content-between align-items-center p-3">
            <div>
                <h6 class="mb-0 fw-semibold">${escapeHtml(r.sender_username)}</h6>
                <small class="text-muted">Level ${r.sender_level}</small>
            </div>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-success" onclick="respondFriendRequest(${r.id}, 'accept')">Accept</button>
                <button class="btn btn-outline-danger" onclick="respondFriendRequest(${r.id}, 'reject')">Decline</button>
            </div>
        </div>
    `).join('');
}

async function handleUserSearch() {
    const input = document.getElementById('social-search-input');
    const resultsContainer = document.getElementById('social-search-results');
    const query = input ? input.value.trim() : '';

    if (!query) return;

    try {
        const users = await API.get('/api/social/search', { query });

        if (!users || users.length === 0) {
            resultsContainer.innerHTML = `<div class="text-muted small p-2">No users found matching "${escapeHtml(query)}"</div>`;
            return;
        }

        resultsContainer.innerHTML = users.map(u => {
            let actionBtn = '';
            if (u.friendship_status === 'friends') {
                actionBtn = `<span class="badge bg-success-subtle text-success">Friends</span>`;
            } else if (u.friendship_status === 'pending_sent') {
                actionBtn = `<span class="badge bg-secondary-subtle text-light">Request Sent</span>`;
            } else if (u.friendship_status === 'pending_received') {
                actionBtn = `<span class="badge bg-warning-subtle text-warning">Pending Your Response</span>`;
            } else {
                actionBtn = `<button class="btn btn-sm btn-primary" onclick="sendFriendRequest(${u.id})">Add Friend</button>`;
            }

            return `
                <div class="list-group-item d-flex justify-content-between align-items-center p-2">
                    <div>
                        <span class="fw-semibold">${escapeHtml(u.username)}</span>
                        <span class="small text-muted ms-2">(Lvl ${u.level})</span>
                    </div>
                    <div>${actionBtn}</div>
                </div>
            `;
        }).join('');

    } catch (err) {
        alert(err.message || 'Failed to search users');
    }
}

async function sendFriendRequest(receiverId) {
    try {
        await API.post('/api/social/request', { receiver_id: receiverId });
        handleUserSearch();
    } catch (err) {
        alert(err.message || 'Failed to send friend request');
    }
}

async function respondFriendRequest(requestId, action) {
    try {
        await API.post(`/api/social/respond?action=${action}`, { request_id: requestId });
        loadSocial();
    } catch (err) {
        alert(err.message || 'Failed to respond to friend request');
    }
}

async function viewFriendProfile(friendId) {
    try {
        const friend = await API.get(`/api/social/profile/${friendId}`);

        const usernameElem = document.getElementById('friendModalUsername');
        const avatarElem = document.getElementById('friendModalAvatar');
        const bioElem = document.getElementById('friendModalBio');
        const levelElem = document.getElementById('friendModalLevel');
        const streakElem = document.getElementById('friendModalStreak');
        const completionsElem = document.getElementById('friendModalCompletions');

        if (usernameElem) usernameElem.textContent = friend.username;
        if (avatarElem) avatarElem.innerHTML = `<div class="avatar-circle mx-auto fs-3" style="width:64px;height:64px;">${escapeHtml(friend.username.charAt(0).toUpperCase())}</div>`;
        if (bioElem) bioElem.textContent = friend.bio || 'No bio provided.';
        if (levelElem) levelElem.textContent = friend.level;
        if (streakElem) streakElem.textContent = `${friend.current_streak} days`;
        if (completionsElem) completionsElem.textContent = friend.total_completions;

        const modalElem = document.getElementById('friendProfileModal');
        if (modalElem) {
            const modal = new bootstrap.Modal(modalElem);
            modal.show();
        }
    } catch (err) {
        alert('Failed to load friend profile');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('social-search-btn');
    const searchInput = document.getElementById('social-search-input');

    if (searchBtn) searchBtn.addEventListener('click', handleUserSearch);
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handleUserSearch();
        });
    }
});