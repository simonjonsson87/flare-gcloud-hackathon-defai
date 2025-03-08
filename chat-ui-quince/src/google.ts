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
          prompt: () => void;
        }
      }
    };
  }
}

 

async function handleGoogleSignIn(response: { credential: string }): Promise<void> {
    console.log('Callback triggered! Response:', response);
    const idToken = response.credential;
    if (!idToken) {
      console.error("No credential in GIS response:", response);
      return;
    }
    const request = { token: idToken };
    console.log('Sending to /verify:', JSON.stringify(request));
    try {
      const fetchResponse = await fetch(BACKEND_ROUTE + 'verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!fetchResponse.ok) {
        const errorText = await fetchResponse.text();  // Get response body
        console.error('Fetch failed:', fetchResponse.status, errorText);
        throw new Error(`HTTP error! # status: ${fetchResponse.status}`);
      }
      const data: VerifyResponse = await fetchResponse.json();
      console.log('User verified:', data);
    } catch (error) {
      console.error('Sign-in failed:', error);
    }
  }

window.addEventListener('load', () => {
    console.log('Window loaded, checking google.accounts.id:', window.google.accounts.id);
    if (!window.google || !window.google.accounts || !window.google.accounts.id) {
      console.error('Google Identity Services script not loaded');
      return;
    }
    console.log('Before initialize, google.accounts.id:', window.google.accounts.id);
    window.google.accounts.id.initialize({
      client_id: '289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com',
      callback: handleGoogleSignIn
    });
    console.log('After initialize, google.accounts.id:', window.google.accounts.id);

    const loginBtn = document.getElementById('google-sign-in') as HTMLButtonElement;
    loginBtn.onclick = function() {
      console.log('Before calling signIn, google.accounts.id:', window.google.accounts.id);
      //console.log('Calling signIn:', window.google.accounts.id.signIn);
      console.log('Calling prompt:', window.google.accounts.id.prompt);
      window.google.accounts.id.prompt();
    };
  });