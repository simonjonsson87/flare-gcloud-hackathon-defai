import { appendToChat } from './main.js';

const BACKEND_ROUTE = 'api/routes/chat/';

class ApiClient {
    constructor() {
        this.token = localStorage.getItem('google_token') || null;
        this.userInfo = null;
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('google_token', token);
    }

    clearSession() {
        this.token = null;
        this.userInfo = null;
        localStorage.removeItem('google_token');
    }

    async verifyGoogleToken(idToken) {
        try {
            const response = await fetch(BACKEND_ROUTE + 'verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: idToken })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Verification failed: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            this.setToken(idToken);
            this.userInfo = {
                user_id: data.user_id,
                email: data.email
            };
            return data;
        } catch (error) {
            console.error('Token verification failed:', error);
            throw error;
        }
    }

    async logout() {
        if (!this.token) return;

        try {
            const response = await fetch(BACKEND_ROUTE + 'logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.warn(`Logout failed: ${response.status} - ${errorText}`);
            }

            this.clearSession();
            return await response.json();
        } catch (error) {
            console.error('Logout failed:', error);
            throw error;
        }
    }
}

const apiClient = new ApiClient();
export { apiClient };
  
async function handleGoogleSignIn(response) {
    console.log('Google Sign-In response:', response);
    const idToken = response.credential;

    if (!idToken) {
        console.error('No credential in GIS response:', response);
        return;
    }

    try {
        const result = await apiClient.verifyGoogleToken(idToken);
        console.log('User verified:', result);
        updateUI(true);
    } catch (error) {
        console.error('Sign-in failed:', error);
        updateUI(false);
    }
}

function updateUI(isAuthenticated) {
    const loginBtn = document.getElementById('google-sign-in');
    const logoutBtn = document.getElementById('logout-btn');
    const chatInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');


    // TODO this makes updateUI innane.
    isAuthenticated = true

    if (isAuthenticated) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        chatInput.disabled = false;
        sendBtn.disabled = false;
    } else {
        loginBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        chatInput.disabled = true;
        sendBtn.disabled = true;
    }
}

window.addEventListener('load', function() {
    if (!window.google || !window.google.accounts || !window.google.accounts.id) {
        console.error('Google Identity Services script not loaded');
        return;
    }

    window.google.accounts.id.initialize({
        client_id: '289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com',
        callback: handleGoogleSignIn
    });

    const loginBtn = document.getElementById('google-sign-in');
    if (!loginBtn) {
        console.error('Login button not found');
        return;
    }

    loginBtn.onclick = function() {
        console.log('Button clicked, triggering prompt');
        window.google.accounts.id.prompt((notification) => {
            console.log('Prompt notification:', notification);
            if (notification.isNotDisplayed()) {
                console.log('Prompt not displayed:', notification.getNotDisplayedReason());
            } else if (notification.isSkippedMoment()) {
                console.log('Prompt skipped:', notification.getSkippedReason());
            } else if (notification.isDismissedMoment()) {
                console.log('Prompt dismissed:', notification.getDismissedReason());
            }
        });
    };

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.onclick = async function() {
            try {
                await apiClient.logout();
                console.log('Logged out successfully');
                updateUI(false);
            } catch (error) {
                console.error('Logout error:', error);
            }
        };
    }

    // Check existing session
    if (apiClient.token) {
        apiClient.verifyGoogleToken(apiClient.token)
            .then(() => updateUI(true))
            .catch(() => {
                apiClient.clearSession();
                updateUI(false);
            });
    } else {
        updateUI(false);
    }
    if (apiClient.token) {
        message = "Hi there! I’m your personal assistant, here to help you manage your crypto transactions with ease. Here’s what I can do for you: \n 💸 Transfer Funds – Send money securely to other accounts.\n 🔄 Swap Tokens – Exchange ERC-20 tokens instantly.\n📈 Stake Crypto – Grow your assets by staking your tokens.\n\n Just type what you need, and I’ll guide you through it! If you ever need help, just ask. 😊\nIf you don't already have a wallet, you could start by asking for one"
        appendToChat(message, false);
    }    

});