const BACKEND_ROUTE = 'api/routes/chat/';

const chat = document.getElementById('chat');
const input = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const loginBtn = document.getElementById('google-sign-in');

window.onload = function() {
  const messageInput = document.getElementById('message-input');
  messageInput.focus();
};

function appendToChat(text, isUser) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
  messageDiv.textContent = text;
  chat.appendChild(messageDiv);
  chat.scrollTop = chat.scrollHeight;
}

async function sendUserInputToBackend(text) {
  try {
    const response = await fetch(BACKEND_ROUTE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: text }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error('Error:', error);
    return 'Sorry, there was an error processing your request. Please try again.';
  }
}

async function handleSend() {
  const text = input.value.trim();
  if (text) {
    appendToChat(text, true);
    input.value = '';
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

function handleLogin() {
  // Empty for now, as it’s tied to GIS in google.js
}

console.log('Before the three event listeners');
sendBtn.addEventListener('click', handleSend);
loginBtn.addEventListener('click', handleLogin);

input.addEventListener('keypress', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});