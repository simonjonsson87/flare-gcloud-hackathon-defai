// src/main.ts
//interface Message {
//  text: string;
//  isUser: boolean;
//}

const BACKEND_ROUTE = 'api/routes/chat/' 

const chat = document.getElementById('chat') as HTMLDivElement;
const input = document.getElementById('message-input') as HTMLTextAreaElement;
const sendBtn = document.getElementById('send-btn') as HTMLButtonElement;
const loginBtn = document.getElementById('login-btn') as HTMLButtonElement;

window.onload = function () {
  const messageInput = document.getElementById('message-input') as HTMLInputElement;
  messageInput.focus();
};

const appendToChat = (text: string, isUser: boolean): void => {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
  messageDiv.textContent = text;
  chat.appendChild(messageDiv);
  chat.scrollTop = chat.scrollHeight;
};

const sendUserInputToBackend = async (text: string): Promise<string> => {
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
    
    // Check if response contains a transaction preview
    //if (data.response.includes('Transaction Preview:')) {
    //  setAwaitingConfirmation(true);
    //  setPendingTransaction(text);
    //}
    
    return data.response;
  } catch (error) {
    console.error('Error:', error);
    return 'Sorry, there was an error processing your request. Please try again.';
  }
};

const handleSend = async (): Promise<void> => {
  const text = input.value.trim();
  if (text) {
    appendToChat(text, true);
    input.value = '';

    try {
      const response = await sendUserInputToBackend(text);
      console.log("Backend response:", response);
      appendToChat(response, false); // ✅ Move this inside try block
    } catch (error) {
      console.error("Error sending input:", error);
      appendToChat("An error occurred. Please try again.", false);
    }
  }

};

const handleLogin = (): void => {

};

sendBtn.addEventListener('click', handleSend);
loginBtn.addEventListener('click', handleLogin);

input.addEventListener('keypress', (e: KeyboardEvent) => {

  if (e.key === 'Enter' && !e.shiftKey) { // Enter without Shift sends
    e.preventDefault();
    handleSend();
  }
});

