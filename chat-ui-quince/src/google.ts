
// google.ts
const BACKEND_ROUTE = 'api/routes/chat/' 

// Define interfaces for type safety
interface TokenRequest {
    token: string;
  }
  
  interface VerifyResponse {
    user_id: string;
    email: string;
    message: string;
    error?: string;
  }
  
  // Declare Google API types (since gapi isn’t natively typed, we extend the global scope)
  declare global {
    interface Window {
      gapi: {
        load: (api: string, callback: () => void) => void;
        auth2: {
          init: (options: { client_id: string }) => Promise<any>;
        };
        signin2: {
          render: (
            id: string,
            options: {
              scope: string;
              width: number;
              height: number;
              longtitle: boolean;
              theme: string;
              onsuccess: (googleUser: GoogleUser) => void;
              onfailure: (error: any) => void;
            }
          ) => void;
        };
      };
    }
  }
  
  interface GoogleUser {
    getAuthResponse: () => { id_token: string };
  }
  
  // Handle successful sign-in
async function handleGoogleSignIn(googleUser: GoogleUser): Promise<void> {
    console.log("In handleGoogleSignIn");
    const idToken = googleUser.getAuthResponse().id_token;
    const request: TokenRequest = { token: idToken };
  
      try {
      const response = await fetch(BACKEND_ROUTE+'verify/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data: VerifyResponse = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
  
      console.log('User verified:', data);
      // Update UI, e.g., display welcome message
      const statusDiv = document.getElementById('status');
      if (statusDiv) {
        statusDiv.innerText = `Welcome, ${data.email}! (User ID: ${data.user_id})`;
      }
    } catch (error) {
      console.error('Sign-in failed:', error);
      const statusDiv = document.getElementById('status');
      if (statusDiv) {
        statusDiv.innerText = `Sign-in failed: ${error instanceof Error ? error.message : 'Unknown error'}`;
      }
    }
  }
  
  // Handle sign-in failure
  function handleGoogleSignInFailure(error: any): void {
    console.error('Google Sign-In failed:', error);
    const statusDiv = document.getElementById('status');
    if (statusDiv) {
      statusDiv.innerText = 'Failed to sign in with Google.';
    }
  }
  
  // Initialize Google Sign-In and render the button
  function initGoogleSignIn(): void {
    if (!window.gapi) {
      console.error('Google API script not loaded');
      return;
    }
  
    window.gapi.load('auth2', () => {
      window.gapi.auth2
        .init({
          client_id: '289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com',
        })
        .then(() => {
          window.gapi.signin2.render('google-sign-in', {
            scope: 'profile email',
            width: 240,
            height: 50,
            longtitle: true,
            theme: 'dark',
            onsuccess: handleGoogleSignIn,
            onfailure: handleGoogleSignInFailure,
          });
        })
        .catch((error: any) => {
          console.error('Failed to initialize Google Auth:', error);
        });
    });
  }
  
  console.log("Before DOMContentLoadeds");

  // Run initialization when the DOM is loaded
  document.addEventListener('DOMContentLoaded', () => {
    initGoogleSignIn();
  });