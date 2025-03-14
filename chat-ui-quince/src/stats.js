// src/stats.js

const API_BASE_URL = '/api/routes/chat'; // Adjust if your API prefix differs

// Stats fields mapping
export const statsFields = {
  'flr': document.getElementById('value-flr'),
  'wflr': document.getElementById('value-wflr'),
  'usdc': document.getElementById('value-usdc'),
  'usdt': document.getElementById('value-usdt'),
  'joule': document.getElementById('value-joule'),
  'weth': document.getElementById('value-weth'),
  'sflr': document.getElementById('value-sflr'),
  'skflr': document.getElementById('value-skflr'),
};

// Fetch stats from backend
export async function fetchStats(token) {
  if (!token) {
    console.error('No token available, please sign in');
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/stats`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    updateStats(data);
  } catch (error) {
    console.error('Error fetching stats:', error);
    updateStatsWithError();
  }
}

// Update stats in sidebar
export function updateStats(balances) {
  Object.keys(statsFields).forEach(token => {
    const value = balances[token] !== undefined ? balances[token].toFixed(4) : '0.0000';
    statsFields[token].textContent = value;
  });
}

// Clear or set stats to N/A
export function clearStats() {
  Object.values(statsFields).forEach(field => {
    field.textContent = 'N/A';
  });
}

function updateStatsWithError() {
  Object.values(statsFields).forEach(field => {
    field.textContent = 'N/A';
  });
}