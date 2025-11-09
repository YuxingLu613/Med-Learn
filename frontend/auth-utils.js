// Authentication utilities for API calls

// Get authentication headers
function getAuthHeaders() {
    const token = localStorage.getItem('accessToken');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

// Make authenticated API call
async function apiCall(url, options = {}) {
    const headers = getAuthHeaders();

    const response = await fetch(url, {
        ...options,
        headers: {
            ...headers,
            ...(options.headers || {})
        }
    });

    // Check if unauthorized
    if (response.status === 401) {
        // Clear auth data and redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        window.location.href = '/login.html';
        throw new Error('Unauthorized');
    }

    return response;
}

// Check if user is logged in
function isLoggedIn() {
    return !!localStorage.getItem('accessToken');
}

// Get current user
function getCurrentUser() {
    const userJson = localStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
}

// Logout
function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    window.location.href = '/landing.html';
}

// Require authentication (redirect if not logged in)
function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}
