import { fetchStats, updateStats, clearStats } from './stats.js';

///////////////////////////////////////////////////
// Classes
///////////////////////////////////////////////////
class ApiClient {
    constructor(updateUICallback) {
        this.token = localStorage.getItem('google_token') || null;
        this.userInfo = null;
        this.updateUI = updateUICallback
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('google_token', token);
    }

    clearSession() {
        this.token = null;
        this.userInfo = null;
        localStorage.removeItem('google_token');
        if (this.updateUI) this.updateUI(false);
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
                this.clearSession()
                throw new Error(`Verification failed: ${response.status} - ${errorText}`);
                refreshStatsButton.style.display = 'none';
            }

            const data = await response.json();
            this.setToken(idToken);
            this.userInfo = {
                user_id: data.user_id,
                email: data.email
            };

            refreshStatsButton.style.display = 'inline-block';

            return data;
        } catch (error) {
            console.error('Token verification failed:', error);
            this.clearSession()
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
            } else {
                console.log(`Logout succesful.`);
            }

            return await response.json();
        } catch (error) {
            console.error('Logout failed:', error);
            throw error;
        } finally {
            this.clearSession();
            refreshStatsButton.style.display = 'none';
        }
    }
}

///////////////////////////////////////////////////
// Functions
///////////////////////////////////////////////////

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
        appendToChat("Hi there! I’m your personal assistant, here to help you manage your crypto transactions with ease. Here’s what I can do for you: <br> 💸 Transfer Funds – Send money securely to other accounts.<br> 🔄 Swap Tokens – Exchange ERC-20 tokens instantly.<br> 📈 Stake Crypto – Grow your assets by staking your tokens.<br><br>Just type what you need, and I’ll guide you through it! If you ever need help, just ask. 😊\n If you don't already have a wallet, you could start by asking for one.", false);
        fetchStats(apiClient.token);

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

    if (isAuthenticated) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        //chatInput.disabled = false;
        //sendBtn.disabled = false;
    } else {
        loginBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        //chatInput.disabled = true;
        //sendBtn.disabled = true;
    }
}

function appendToChat(text, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    //messageDiv.textContent = text;

    //messageDiv.innerHTML = marked.parse(text);
    const safeHTML = DOMPurify.sanitize(marked.parse(text));
    messageDiv.innerHTML = safeHTML;

    chat.appendChild(messageDiv);
    chat.scrollTop = chat.scrollHeight;

    // Read the message out loud if from backend
    if (!isUser) {
        speakMessage(text);
    }
}

function speakMessage(text) {
    // Check if SpeechSynthesis is supported
    const speechSynthesis = window.speechSynthesis;
    if (!speechSynthesis) {
        console.warn("Speech Synthesis not supported.");
        return;
    }

    //

    // Create a speech synthesis utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";  // Set language
    if (isReadOutLoudEnabled) {
        speechSynthesis.speak(utterance);
    }
}

async function sendUserInputToBackend(text) {
    if (!apiClient.token) {
        throw new Error('Not authenticated. Please login');
    }

    try {
        const response = await fetch(BACKEND_ROUTE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiClient.token}`
            },
            body: JSON.stringify({ message: text })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Chat request failed: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Error sending message:', error);
        
        if (error.message.includes("Failed to fetch")) {
            return "Network error. Please check your internet connection.";
        }
        
        return 'Sorry, there was an error processing your request. Please try again.';
    }
}

async function handleSend() {
    const text = input.value.trim();
    if (text) {

        appendToChat(text, true);
        input.value = '';

        if (!apiClient.token) {
            appendToChat("Sorry, we can't start working before you login.", false); // Bot response if not logged in
            return;
        }

        try {
            const response = await sendUserInputToBackend(text);
            console.log('Backend response:', response);
            appendToChat(response, false);
        } catch (error) {
            console.error('Error sending input:', error);
            appendToChat('An error occurred. Please try again.', false);
        }
    }
}

function toggleReadOutLoud() {
    console.log("In toggleReadOutLoud and isReadOutLoudEnabled=", isReadOutLoudEnabled);
    isReadOutLoudEnabled = !isReadOutLoudEnabled;

    const readOutLoudBtn = document.getElementById('read-out-loud-btn');
    const readOutLoudBtnEnabled = document.getElementById('read-out-loud-btn-enabled')
    const readOutLoudBtnDisabled = document.getElementById('read-out-loud-btn-disabled')
    // Update the button icon based on the read out loud status
    if (isReadOutLoudEnabled) {
        // speakerIcon.src = "speaker-enabled.png"; // Speaker image
        readOutLoudBtnEnabled.style.display = "flex";
        readOutLoudBtnDisabled.style.display = "none";
    } else {
        //speakerIcon.src = "speaker-disabled.png"; // Crossed-out speaker image
        readOutLoudBtnEnabled.style.display = "none";
        readOutLoudBtnDisabled.style.display = "flex";
    }

    // Optionally, stop any current speech when toggling
    if (!isReadOutLoudEnabled && speechSynthesis.speaking) {
        speechSynthesis.cancel();
    }
}

///////////////////////////////////////////////////
// Actions and definitions
///////////////////////////////////////////////////
const apiClient = new ApiClient(updateUI);

const BACKEND_ROUTE = 'api/routes/chat/';

const chat = document.getElementById('chat');
const input = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
//const readOutLoudBtn = document.getElementById('read-out-loud-btn');
const readOutLoudBtn = document.querySelector('.read-out-loud-btn');
const refreshStatsButton = document.getElementById('refresh-stats-btn');




let isReadOutLoudEnabled = false; 
///////////////////////////////////////////////////
// Window load
///////////////////////////////////////////////////
window.addEventListener('load', function() {
    if (!window.google || !window.google.accounts || !window.google.accounts.id) {
        console.error('Google Identity Services script not loaded');
        return;
    }

    window.google.accounts.id.initialize({
        client_id: '289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com',
        callback: handleGoogleSignIn,
        cancel_on_tap_outside: true
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
    //if (apiClient.token) {
    //    message = "Hi there! I’m your personal assistant, here to help you manage your crypto transactions with ease. Here’s what I can do for you: \n 💸 Transfer Funds – Send money securely to other accounts.\n 🔄 Swap Tokens – Exchange ERC-20 tokens instantly.\n📈 Stake Crypto – Grow your assets by staking your tokens.\n\n Just type what you need, and I’ll guide you through it! If you ever need help, just ask. 😊\nIf you don't already have a wallet, you could start by asking for one"
    //    appendToChat(message, false);
    //}    

});

window.onload = function() {
    const messageInput = document.getElementById('message-input');
    messageInput.focus();

    // Initial UI setup is handled in google.js
};

///////////////////////////////////////////////////
// Event listeners
///////////////////////////////////////////////////
refreshStatsButton.addEventListener('click', () => {
    fetchStats(apiClient.token);
});
  
sendBtn.addEventListener("click", handleSend);

input.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

readOutLoudBtn.addEventListener('click', function () { 
    toggleReadOutLoud();
});

///////////////////////////////////////////////////
// Voice input
///////////////////////////////////////////////////


document.addEventListener("DOMContentLoaded", () => {
    const messageInput = document.getElementById("message-input");
    const voiceBtn = document.getElementById('voice-btn');
    const voiceEar = document.getElementById("voice-ear");
    const voiceMic = document.getElementById("voice-mic");

    // Check if SpeechRecognition is available
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.warn("Speech Recognition is not supported in this browser.");
        voiceBtn.style.display = "none"; // Hide button if not supported
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US"; // Set language
    recognition.interimResults = false; // Only send final results
    recognition.maxAlternatives = 1; // Only take the most confident result

    voiceBtn.addEventListener("click", () => {
        console.log("Clicked the voice button.");
        recognition.start();
        /*voiceBtn.innerText = "Listening...";*/
        voiceMic.style.display = "none";
        voiceEar.style.display = "flex";
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        messageInput.value = transcript; // Insert the transcribed text
        handleSend()
        voiceMic.style.display = "flex";
        voiceEar.style.display = "none";
    };

    recognition.onerror = (event) => {
        console.error("Speech Recognition Error:", event.error);
        voiceMic.style.display = "flex";
        voiceEar.style.display = "none";
    };

    recognition.onend = () => {
        voiceMic.style.display = "flex";
        voiceEar.style.display = "none";
    };
});