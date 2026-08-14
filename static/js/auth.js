/**
 * LevelUp Auth UI Handler - Registration, Login & Session Management
 */

function showAuthOverlay() {
    const overlay = document.getElementById('auth-overlay');
    if (overlay) {
        overlay.classList.remove('d-none');
    }
}

function hideAuthOverlay() {
    const overlay = document.getElementById('auth-overlay');
    if (overlay) {
        overlay.classList.add('d-none');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Handle Login Form Submit
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            loginError.classList.add('d-none');

            const identifier = document.getElementById('login-identifier').value.trim();
            const password = document.getElementById('login-password').value;

            try {
                const res = await API.post('/api/auth/login', {
                    username_or_email: identifier,
                    password: password
                });

                API.setToken(res.access_token);
                hideAuthOverlay();
                loginForm.reset();

                if (typeof initApp === 'function') {
                    initApp();
                }
            } catch (err) {
                loginError.textContent = err.message;
                loginError.classList.remove('d-none');
            }
        });
    }

    // 2. Handle Registration Form Submit
    const registerForm = document.getElementById('register-form');
    const regError = document.getElementById('reg-error');

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            regError.classList.add('d-none');

            const username = document.getElementById('reg-username').value.trim();
            const email = document.getElementById('reg-email').value.trim();
            const password = document.getElementById('reg-password').value;
            const bio = document.getElementById('reg-bio').value.trim();

            try {
                const res = await API.post('/api/auth/register', {
                    username: username,
                    email: email,
                    password: password,
                    bio: bio,
                    avatar_url: 'avatar-1'
                });

                API.setToken(res.access_token);
                hideAuthOverlay();
                registerForm.reset();

                if (typeof initApp === 'function') {
                    initApp();
                }
            } catch (err) {
                regError.textContent = err.message;
                regError.classList.remove('d-none');
            }
        });
    }

    // 3. Handle Logout Button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            API.removeToken();
            showAuthOverlay();
        });
    }

    // 4. Check Authentication on Load
    if (!API.isAuthenticated()) {
        showAuthOverlay();
    } else {
        hideAuthOverlay();
        if (typeof initApp === 'function') {
            initApp();
        }
    }
});