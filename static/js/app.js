// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyBBYpRV3aRJCJ2Y2JALcoKNTUXVS4cl-iA",
    authDomain: "habitual-2d3d3.firebaseapp.com",
    projectId: "habitual-2d3d3",
    storageBucket: "habitual-2d3d3.firebasestorage.app",
    messagingSenderId: "1033611963287",
    appId: "1:1033611963287:web:3c697309d618920495b2d2",
    measurementId: "G-2M658H9Z3Y"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// Application State
let currentUser = null;
let userProfile = null;
let lastSyncTime = localStorage.getItem('lastSyncTime');

// Authentication Functions
function signInWithGoogle() {
    const provider = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(provider)
        .then((result) => {
            console.log('Google sign-in successful');
            closeModal();
        })
        .catch((error) => {
            console.error('Google sign-in error:', error);
            showSyncStatus('Sign-in failed: ' + error.message, 'error');
        });
}

function signInWithEmail() {
    // For now, redirect to Google sign-in
    // You could implement email/password auth here
    signInWithGoogle();
}

function signOut() {
    auth.signOut().then(() => {
        console.log('Sign-out successful');
        currentUser = null;
        userProfile = null;
        updateAuthUI();
        // Switch back to localStorage-only mode
        initializeApp();
    });
}

// Auth State Observer
auth.onAuthStateChanged((user) => {
    currentUser = user;
    updateAuthUI();
    
    if (user) {
        // User signed in
        getUserProfile().then(() => {
            syncWithFirestore();
        });
    } else {
        // User signed out - fall back to localStorage
        loadFromLocalStorage();
    }
});

// UI Updates
function updateAuthUI() {
    const authSection = document.getElementById('auth-section');
    
    if (currentUser) {
        authSection.innerHTML = `
            <div class="user-info">
                <span>${currentUser.email}</span>
                <span class="subscription-badge ${userProfile?.subscription_tier || 'free'}">${userProfile?.subscription_tier || 'Free'}</span>
            </div>
            <button class="btn btn-secondary" onclick="signOut()">Sign Out</button>
        `;
        
        // Show premium features for free users
        if (!userProfile || userProfile.subscription_tier === 'free') {
            document.getElementById('premium-features').style.display = 'block';
        }
    } else {
        authSection.innerHTML = `
            <button class="btn btn-primary" onclick="openModal()">Sign In</button>
        `;
        document.getElementById('premium-features').style.display = 'none';
    }
}

// Modal Functions
function openModal() {
    document.getElementById('auth-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

// Sync Status Display
function showSyncStatus(message, type) {
    const statusEl = document.getElementById('sync-status');
    statusEl.textContent = message;
    statusEl.className = `sync-status ${type}`;
    statusEl.style.display = 'block';
    
    if (type !== 'syncing') {
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    }
}

// Firebase Integration
async function getUserProfile() {
    if (!currentUser) return null;
    
    try {
        const response = await fetch('/api/profile', {
            headers: {
                'Authorization': `Bearer ${await currentUser.getIdToken()}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            userProfile = data.profile;
            return userProfile;
        }
    } catch (error) {
        console.error('Error getting user profile:', error);
    }
    return null;
}

async function syncWithFirestore() {
    if (!currentUser) return;
    
    try {
        showSyncStatus('Syncing...', 'syncing');
        
        const response = await fetch('/api/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${await currentUser.getIdToken()}`
            },
            body: JSON.stringify({
                habitData: habitData,
                lastSync: lastSyncTime
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            if (result.status === 'success') {
                if (result.action === 'server_to_local') {
                    // Server data is newer, update local
                    habitData = result.data;
                    updateUIFromData();
                    saveToLocalStorage();
                }
                
                lastSyncTime = new Date().toISOString();
                localStorage.setItem('lastSyncTime', lastSyncTime);
                showSyncStatus('Synced successfully', 'success');
            } else {
                showSyncStatus('Sync failed: ' + result.message, 'error');
            }
        } else {
            showSyncStatus('Sync failed', 'error');
        }
    } catch (error) {
        console.error('Sync error:', error);
        showSyncStatus('Sync failed: ' + error.message, 'error');
    }
}

// Auto-sync every 30 seconds if user is authenticated
setInterval(() => {
    if (currentUser) {
        syncWithFirestore();
    }
}, 30000);

// Premium Features
function upgradeToPremium() {
    if (!currentUser) {
        openModal();
        return;
    }
    
    // Redirect to Stripe checkout (will implement later)
    alert('Premium subscription coming soon! 🚀');
}

// Update UI from habit data
function updateUIFromData() {
    document.getElementById('started-date').value = habitData.startedDate;
    document.getElementById('frequency').value = habitData.frequency;
    document.getElementById('counter').value = habitData.counter;
    
    // Update checkboxes based on today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('done-checkbox').checked = habitData.completedDates.includes(today);
    document.getElementById('not-done-checkbox').checked = habitData.notDoneDates.includes(today);
    
    // Update why field
    const whyField = document.getElementById('why-field');
    const whyText = document.getElementById('why-text');
    if (habitData.notDoneDates.includes(today)) {
        whyField.style.display = 'block';
        whyText.value = habitData.whyEntries[today] || '';
    } else {
        whyField.style.display = 'none';
    }
    
    updatePercentage();
}

// Enhanced save function that syncs with server if authenticated
function saveHabitData() {
    saveToLocalStorage();
    
    if (currentUser) {
        // Debounced sync to server
        clearTimeout(window.syncTimeout);
        window.syncTimeout = setTimeout(() => {
            syncWithFirestore();
        }, 1000);
    }
}