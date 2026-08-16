/**
 * LevelUp Dashboard Controller - Habits Checklist, Check-ins & Analytics Cards
 */

async function loadDashboard() {
    try {
        // Fetch summary metrics, habits, challenges, and activity feed in parallel
        const [summary, habits, challenges, activity] = await Promise.all([
            API.get('/api/analytics/summary'),
            API.get('/api/habits'),
            API.get('/api/gamification/challenges'),
            API.get('/api/gamification/activity')
        ]);

        // 1. Render Summary Stat Cards
        const progText = document.getElementById('dash-progress-text');
        const streakText = document.getElementById('dash-streak-text');
        const xpText = document.getElementById('dash-xp-text');
        const lvlText = document.getElementById('dash-level-text');

        if (progText) progText.textContent = `${summary.completed_today}/${summary.total_habits}`;
        if (streakText) streakText.textContent = `${summary.current_streak} Days`;
        if (xpText) xpText.textContent = `${summary.total_xp} XP`;
        if (lvlText) lvlText.textContent = `Level ${summary.level}`;

        // 2. Render Today's Habits Checklist
        renderDashboardHabits(habits);

        // 3. Render Daily Challenges
        renderDashboardChallenges(challenges);

        // 4. Render Recent Activity Feed
        renderDashboardActivity(activity);

    } catch (err) {
        console.error('Failed to load dashboard data:', err);
    }
}

function renderDashboardHabits(habits) {
    const container = document.getElementById('dashboard-habits-list');
    if (!container) return;

    if (!habits || habits.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                <p>No habits created yet. Click "+ New Habit" to get started!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = habits.map(h => {
        const isDone = h.is_completed_today;
        const isMissed = h.today_status === 'missed';

        return `
            <div class="habit-item" data-id="${h.id}">
                <div class="d-flex align-items-center">
                    <span class="badge me-3 p-2" style="background-color: ${h.color || '#4f46e5'}">
                        <i class="bi ${h.icon || 'bi-check-circle'} fs-6"></i>
                    </span>
                    <div>
                        <h6 class="mb-0 fw-semibold ${isDone ? 'text-decoration-line-through text-muted' : ''}">${escapeHtml(h.title)}</h6>
                        <small class="text-muted">${escapeHtml(h.category)} • ${h.current_streak} day streak</small>
                    </div>
                </div>

                <div class="d-flex gap-2">
                    ${isDone ? `
                        <span class="badge bg-success-subtle text-success py-2 px-3">
                            <i class="bi bi-check2-all me-1"></i>Completed
                        </span>
                    ` : isMissed ? `
                        <span class="badge bg-danger-subtle text-danger py-2 px-3">
                            <i class="bi bi-x-circle me-1"></i>Missed
                        </span>
                    ` : `
                        <button class="btn btn-sm btn-outline-danger" onclick="openMissedReasonModal(${h.id})">
                            <i class="bi bi-x-lg"></i>
                        </button>
                        <button class="btn btn-sm btn-success" onclick="handleCheckIn(${h.id}, 'completed')">
                            <i class="bi bi-check-lg me-1"></i>Done
                        </button>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

function renderDashboardChallenges(challenges) {
    const container = document.getElementById('dashboard-challenges-list');
    if (!container) return;

    if (!challenges || challenges.length === 0) {
        container.innerHTML = `<div class="text-muted small">No active challenges today.</div>`;
        return;
    }

    container.innerHTML = challenges.map(c => {
        const pct = Math.min(100, Math.round((c.progress / c.target_count) * 100));
        return `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="small fw-semibold">${escapeHtml(c.title)}</span>
                    <span class="badge ${c.completed ? 'bg-success' : 'bg-secondary'} small">+${c.xp_reward} XP</span>
                </div>
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar ${c.completed ? 'bg-success' : 'bg-primary'}" style="width: ${pct}%;"></div>
                </div>
                <div class="d-flex justify-content-between small text-muted mt-1">
                    <span>${c.description}</span>
                    <span>${c.progress}/${c.target_count}</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderDashboardActivity(activity) {
    const container = document.getElementById('dashboard-activity-list');
    if (!container) return;

    if (!activity || activity.length === 0) {
        container.innerHTML = `<div class="text-muted small">No recent activity.</div>`;
        return;
    }

    container.innerHTML = activity.slice(0, 5).map(act => `
        <div class="d-flex align-items-start mb-3">
            <i class="bi bi-activity text-primary me-2 mt-1"></i>
            <div>
                <div class="small fw-semibold">${escapeHtml(act.title)}</div>
                <div class="small text-muted">${escapeHtml(act.description || '')}</div>
            </div>
        </div>
    `).join('');
}

async function handleCheckIn(habitId, status, reason = '') {
    try {
        const res = await API.post('/api/tracking/checkin', {
            habit_id: habitId,
            status: status,
            reason: reason
        });

        // Refresh user stats in top navbar
        const user = await API.get('/api/users/profile');
        updateHeaderStats(user);

        // Reload dashboard view data
        loadDashboard();

        if (res.level_up) {
            alert(`🎉 Congratulations! You reached Level ${res.new_level}!`);
        }
    } catch (err) {
        alert(err.message || 'Failed to record check-in');
    }
}

function openMissedReasonModal(habitId) {
    const idInput = document.getElementById('missed-habit-id');
    const reasonInput = document.getElementById('missed-reason-input');
    if (idInput) idInput.value = habitId;
    if (reasonInput) reasonInput.value = '';

    const modalElem = document.getElementById('missedReasonModal');
    if (modalElem) {
        const modal = new bootstrap.Modal(modalElem);
        modal.show();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const submitMissedBtn = document.getElementById('submit-missed-reason-btn');
    if (submitMissedBtn) {
        submitMissedBtn.addEventListener('click', async () => {
            const habitId = document.getElementById('missed-habit-id').value;
            const reason = document.getElementById('missed-reason-input').value.trim();

            if (!reason) {
                alert('Please provide a brief reason for accountability.');
                return;
            }

            const modalElem = document.getElementById('missedReasonModal');
            if (modalElem) {
                const modal = bootstrap.Modal.getInstance(modalElem);
                if (modal) modal.hide();
            }

            await handleCheckIn(parseInt(habitId), 'missed', reason);
        });
    }
});

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}