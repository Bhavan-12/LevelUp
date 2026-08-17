/**
 * LevelUp Habits Management Controller
 */

async function loadHabits() {
    const categorySelect = document.getElementById('habit-category-filter');
    const showArchivedToggle = document.getElementById('show-archived-toggle');
    const container = document.getElementById('habits-grid');

    const category = categorySelect ? categorySelect.value : 'All';
    const includeArchived = showArchivedToggle ? showArchivedToggle.checked : false;

    try {
        const habits = await API.get('/api/habits', {
            category: category === 'All' ? '' : category,
            include_archived: includeArchived
        });

        if (!container) return;

        if (!habits || habits.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5 text-muted">
                    <i class="bi bi-card-checklist fs-1 d-block mb-2"></i>
                    <p>No habits found matching your filter criteria.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = habits.map(h => `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100 ${h.is_archived ? 'opacity-75' : ''}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="d-flex align-items-center">
                                <span class="badge me-2 p-2" style="background-color: ${h.color || '#4f46e5'}">
                                    <i class="bi ${h.icon || 'bi-check-circle'}"></i>
                                </span>
                                <h6 class="card-title mb-0 fw-bold">${escapeHtml(h.title)}</h6>
                            </div>
                            <span class="badge bg-secondary-subtle text-light small">${escapeHtml(h.frequency)}</span>
                        </div>

                        <p class="card-text small text-muted mb-3">${escapeHtml(h.description || 'No description provided.')}</p>

                        <div class="row g-2 mb-3 text-center small">
                            <div class="col-6">
                                <div class="p-2 border rounded">
                                    <div class="text-muted">Streak</div>
                                    <div class="fw-bold text-warning">${h.current_streak} days</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="p-2 border rounded">
                                    <div class="text-muted">Success Rate</div>
                                    <div class="fw-bold text-success">${h.completion_rate}%</div>
                                </div>
                            </div>
                        </div>

                        <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                            <span class="badge bg-info-subtle text-info">${escapeHtml(h.category)}</span>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-secondary" onclick="openEditHabitModal(${h.id})" title="Edit">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-outline-secondary" onclick="toggleArchiveHabit(${h.id}, ${h.is_archived})" title="${h.is_archived ? 'Unarchive' : 'Archive'}">
                                    <i class="bi ${h.is_archived ? 'bi-archive-fill text-warning' : 'bi-archive'}"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteHabit(${h.id})" title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Failed to load habits:', err);
    }
}

async function openEditHabitModal(habitId) {
    try {
        const habit = await API.get(`/api/habits/${habitId}`);
        document.getElementById('habit-edit-id').value = habit.id;
        document.getElementById('habit-title').value = habit.title;
        document.getElementById('habit-desc').value = habit.description || '';
        document.getElementById('habit-frequency').value = habit.frequency;
        document.getElementById('habit-category').value = habit.category;
        document.getElementById('habit-priority').value = habit.priority;
        document.getElementById('habit-color').value = habit.color || '#4f46e5';

        document.getElementById('habitModalLabel').textContent = 'Edit Habit';

        const modalElem = document.getElementById('habitModal');
        const modal = new bootstrap.Modal(modalElem);
        modal.show();
    } catch (err) {
        alert('Failed to load habit details for editing');
    }
}

async function toggleArchiveHabit(habitId, currentStatus) {
    try {
        await API.put(`/api/habits/${habitId}`, { is_archived: !currentStatus });
        loadHabits();
    } catch (err) {
        alert(err.message || 'Failed to update archive status');
    }
}

async function deleteHabit(habitId) {
    if (!confirm('Are you sure you want to delete this habit and all its check-in records?')) {
        return;
    }

    try {
        await API.delete(`/api/habits/${habitId}`);
        loadHabits();
    } catch (err) {
        alert(err.message || 'Failed to delete habit');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Habit filter changes
    const categorySelect = document.getElementById('habit-category-filter');
    const showArchivedToggle = document.getElementById('show-archived-toggle');

    if (categorySelect) categorySelect.addEventListener('change', loadHabits);
    if (showArchivedToggle) showArchivedToggle.addEventListener('change', loadHabits);

    // Habit Form Submit (Create / Edit)
    const habitForm = document.getElementById('habit-form');
    if (habitForm) {
        habitForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const editId = document.getElementById('habit-edit-id').value;
            const habitPayload = {
                title: document.getElementById('habit-title').value.trim(),
                description: document.getElementById('habit-desc').value.trim(),
                frequency: document.getElementById('habit-frequency').value,
                category: document.getElementById('habit-category').value,
                priority: document.getElementById('habit-priority').value,
                color: document.getElementById('habit-color').value
            };

            try {
                if (editId) {
                    await API.put(`/api/habits/${editId}`, habitPayload);
                } else {
                    await API.post('/api/habits', habitPayload);
                }

                habitForm.reset();
                document.getElementById('habit-edit-id').value = '';
                document.getElementById('habitModalLabel').textContent = 'Create New Habit';

                const modalElem = document.getElementById('habitModal');
                const modal = bootstrap.Modal.getInstance(modalElem);
                if (modal) modal.hide();

                loadHabits();
            } catch (err) {
                alert(err.message || 'Failed to save habit');
            }
        });
    }
});