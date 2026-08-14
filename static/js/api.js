/**
 * LevelUp API Client - Fetch API Wrapper with JWT Token Management
 */

const TOKEN_KEY = 'levelup_token';

const API = {
    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    },

    setToken(token) {
        localStorage.setItem(TOKEN_KEY, token);
    },

    removeToken() {
        localStorage.removeItem(TOKEN_KEY);
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            // Handle session expiration
            if (response.status === 401) {
                this.removeToken();
                if (typeof showAuthOverlay === 'function') {
                    showAuthOverlay();
                }
                throw new Error('Session expired. Please log in again.');
            }

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const errorMessage = (data && data.detail) || `Request failed with status ${response.status}`;
                throw new Error(errorMessage);
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error.message);
            throw error;
        }
    },

    get(endpoint, params = {}) {
        const query = new URLSearchParams(params).toString();
        const fullPath = query ? `${endpoint}?${query}` : endpoint;
        return this.request(fullPath, { method: 'GET' });
    },

    post(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    put(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};