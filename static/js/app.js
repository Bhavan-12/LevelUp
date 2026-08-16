/**
 * LevelUp SPA Router & Theme Controller
 */

let currentUser = null;

function navigateTo(viewName) {
    // Hide all view panels
    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // Remove active class from sidebar navigation items
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Show target view panel
    const targetPanel = document.getElementById(`view-${viewName}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
    }

    // Highlight target sidebar navigation item
    const targetNavItem = document.querySelector(`.sidebar-nav .nav-item[data-view="${viewName}"]`);
    if (targetNavItem) {
        targetNavItem.classList.add('active');
    }

    // Update Header Title
    const titleElem = document.getElementById('page-title');
    if (titleElem) {
        titleElem.textContent = viewName.charAt(0).toUpperCase() + viewName.slice(1);
    }

    // Trigger specific view data loaders
    switch (viewName) {
        case 'dashboard':
            if (typeof loadDashboard === 'function') loadDashboard();
            break;
        case 'habits':
            if (typeof loadHabits === 'function') loadHabits();
            break;
        case 'leaderboard':
            if (typeof loadLeaderboard === 'function') loadLeaderboard();
            break;
        case 'gamification':
            if (typeof loadGamification === 'function') loadGamification();
            break;
        case 'social':
            if (typeof loadSocial === 'function') loadSocial();
            break;
        case 'analytics':
            if (typeof loadAnalytics === 'function') loadAnalytics();
            break;
        case 'settings':
            if (typeof loadProfileSettings === 'function') loadProfileSettings();
            break;
    }
}

function updateHeaderStats(user) {
    if (!user) return;
    currentUser = user;

    const levelElem = document.getElementById('header-level');
    const xpText = document.getElementById('header-xp-text');
    const xpBar = document.getElementById('header-xp-bar');
    const streakElem = document.getElementById('header-streak');
    const avatarElem = document.getElementById('header-avatar');

    if (levelElem) levelElem.textContent = `Lvl ${user.level}`;
    if (xpText) xpText.textContent = `${user.xp} XP`;
    if (streakElem) streakElem.textContent = user.current_streak;

    // Calculate percentage to next level
    // Level formula: level = floor(sqrt(xp / 25)) + 1
    const currentLvlBaseXp = Math.pow(user.level - 1, 2) * 25;
    const nextLvlXp = Math.pow(user.level, 2) * 25;
    const diff = nextLvlXp - currentLvlBaseXp;
    const progress = diff > 0 ? Math.min(100, Math.max(0, ((user.xp - currentLvlBaseXp) / diff) * 100)) : 0;
    if (xpBar) xpBar.style.width = `${progress}%`;

    if (avatarElem) {
        avatarElem.innerHTML = `<span class="avatar-circle">${(user.username || 'U').charAt(0).toUpperCase()}</span>`;
    }
}

async function initApp() {
    try {
        const user = await API.get('/api/users/profile');
        updateHeaderStats(user);

        // Apply saved theme preference
        if (user.theme_preference) {
            document.documentElement.setAttribute('data-theme', user.theme_preference);
            const themeIcon = document.getElementById('theme-icon');
            if (themeIcon) {
                themeIcon.className = user.theme_preference === 'light' ? 'bi bi-sun' : 'bi bi-moon-stars';
            }
        }

        // Navigate to view based on hash or default to dashboard
        const initialView = window.location.hash.replace('#', '') || 'dashboard';
        navigateTo(initialView);
    } catch (err) {
        console.error('Initialization error:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar link routing
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = link.getAttribute('data-view');
            window.location.hash = view;
            navigateTo(view);
        });
    });

    // Theme toggle button
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', async () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);

            const themeIcon = document.getElementById('theme-icon');
            if (themeIcon) {
                themeIcon.className = newTheme === 'light' ? 'bi bi-sun' : 'bi bi-moon-stars';
            }

            try {
                await API.put('/api/users/profile', { theme_preference: newTheme });
            } catch (e) {
                console.error('Failed to save theme preference');
            }
        });
    }

    // Sidebar mobile toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }
});