const BACKEND_ROUTE = 'api/routes/chat/';

// No interfaces needed in JS, but we'll keep structure in mind
// TokenRequest: { token: string }
// VerifyResponse: { user_id: string, email: string, message: string, error?: string }

async function handleGoogleSignIn(response) {
  console.log('Callback triggered! Response:', response);
  const idToken = response.credential;
  if (!idToken) {
    console.error('No credential in GIS response:', response);
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
      const errorText = await fetchResponse.text();
      console.error('Fetch failed:', fetchResponse.status, errorText);
      throw new Error(`HTTP error! status: ${fetchResponse.status}`);
    }
    const data = await fetchResponse.json();
    console.log('User verified:', data);
  } catch (error) {
    console.error('Sign-in failed:', error);
  }
}

window.addEventListener('load', function() {
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

  const loginBtn = document.getElementById('google-sign-in');
  if (!loginBtn) {
    console.error('Login button not found');
    return;
  }
  loginBtn.onclick = function() {
    console.log('Button clicked, triggering prompt');
    console.log('Calling prompt:', window.google.accounts.id.prompt);
    window.google.accounts.id.prompt(function(notification) {
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
});