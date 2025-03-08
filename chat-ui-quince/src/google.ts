const BACKEND_ROUTE = 'api/routes/chat/'

interface TokenRequest {
  token: string;
}

interface VerifyResponse {
  user_id: string;
  email: string;
  message: string;
  error?: string;
}

declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (options: { client_id: string, callback: (response: { credentials: string }) => void }) => void;
          triggerLogin: () => void;
        }
      }
    };
  }
}

async function handleGoogleSignIn(response: { credentials: string }): Promise<void> {
  const idToken = response.credentials;
  const request: TokenRequest = { token: idToken };

  try {
    const response = await fetch(BACKEND_ROUTE + 'verify/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data: VerifyResponse = await response.json();
    console.log('User verified:', data);
  } catch (error) {
    console.error('Sign-in failed:', error);
  }
}

window.addEventListener('load', () => {
  const loginBtn = document.getElementById('google-sign-in') as HTMLButtonElement;

  if (!window.google || !window.google.accounts || !window.google.accounts.id) {
    console.error('Google Identity Services script not loaded');
    return;
  }

  window.google.accounts.id.initialize({
    client_id: '289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com',
    callback: handleGoogleSignIn
  });

  loginBtn.onclick = function() {
    window.google.accounts.id.signIn();
  };
});