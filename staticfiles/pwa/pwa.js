// PWA Installation Handler
let deferredPrompt = null;
let isAppInstalled = false;

// Check if already installed
function checkIfInstalled() {
  // Check various installation indicators
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return true;
  }
  
  if (window.navigator.standalone === true) {
    return true;
  }
  
  // Check if launched from home screen
  if (window.matchMedia('(display-mode: fullscreen)').matches ||
      window.matchMedia('(display-mode: minimal-ui)').matches) {
    return true;
  }
  
  return false;
}

// Show install button
function showInstallButton() {
  const installBtn = document.getElementById('installButton');
  const installBtnMobile = document.getElementById('installButtonMobile');
  
  if (!isAppInstalled) {
    if (installBtn) {
      installBtn.style.display = 'flex';
      installBtn.addEventListener('click', installApp);
    }
    
    if (installBtnMobile) {
      installBtnMobile.style.display = 'flex';
      installBtnMobile.addEventListener('click', installApp);
    }
  }
}

// Hide install button
function hideInstallButton() {
  const installBtn = document.getElementById('installButton');
  const installBtnMobile = document.getElementById('installButtonMobile');
  
  if (installBtn) installBtn.style.display = 'none';
  if (installBtnMobile) installBtnMobile.style.display = 'none';
}

// Handle beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('🎯 beforeinstallprompt event fired');
  
  // Prevent Chrome 67 and earlier from automatically showing the prompt
  e.preventDefault();
  
  // Store the event
  deferredPrompt = e;
  
  // Check if already installed
  isAppInstalled = checkIfInstalled();
  
  // Show install buttons if not already installed
  if (!isAppInstalled) {
    showInstallButton();
  } else {
    hideInstallButton();
  }
  
  console.log('✅ Install prompt available');
});

// Install app function
async function installApp() {
  if (!deferredPrompt) {
    console.log('⚠️ Install prompt not available');
    return;
  }
  
  console.log('📱 Showing install prompt');
  
  // Show the install prompt
  deferredPrompt.prompt();
  
  // Wait for the user's response
  const choiceResult = await deferredPrompt.userChoice;
  console.log(`User choice: ${choiceResult.outcome}`);
  
  if (choiceResult.outcome === 'accepted') {
    console.log('✅ User accepted the install');
    isAppInstalled = true;
    hideInstallButton();
    showInstallSuccess();
  } else {
    console.log('❌ User dismissed the install');
  }
  
  // Clear the deferredPrompt
  deferredPrompt = null;
}

// Handle appinstalled event
window.addEventListener('appinstalled', (evt) => {
  console.log('✅ App installed successfully');
  isAppInstalled = true;
  hideInstallButton();
  deferredPrompt = null;
  showInstallSuccess();
});

// Show success message
function showInstallSuccess() {
  const existingMessage = document.querySelector('.install-success-message');
  if (existingMessage) {
    existingMessage.remove();
  }
  
  const message = document.createElement('div');
  message.className = 'install-success-message';
  message.innerHTML = `
    <div class="fixed top-20 right-4 z-50 bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg animate-fade-in">
      <div class="flex items-center space-x-3">
        <i class="fas fa-check-circle text-xl"></i>
        <div>
          <div class="font-semibold">App Installed!</div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(message);
  
  setTimeout(() => {
    if (message.parentNode) {
      message.remove();
    }
  }, 5000);
}

// Register service worker
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      // Register service worker at root scope
      navigator.serviceWorker.register('/serviceworker.js')
        .then(registration => {
          console.log('ServiceWorker registered with scope:', registration.scope);
          
          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            console.log('ServiceWorker update found!');
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                console.log('New content is available; please refresh.');
                // You could show a "New content available" notification here
              }
            });
          });
        })
        .catch(error => {
          console.error('ServiceWorker registration failed:', error);
        });
    });
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Check if already installed
  isAppInstalled = checkIfInstalled();
  
  if (isAppInstalled) {
    hideInstallButton();
    console.log('📱 App is already installed');
  }
  
  // Register service worker
  registerServiceWorker();
  
  // Check if we're online
  if (!navigator.onLine) {
    console.log('📴 Currently offline');
    // You could show an offline indicator here
  }
});

// Sync install buttons
document.addEventListener('DOMContentLoaded', () => {
  const installBtn = document.getElementById('installButton');
  const installBtnMobile = document.getElementById('installButtonMobile');
  
  if (installBtn && installBtnMobile) {
    // Ensure both buttons show/hide together
    const updateMobileButton = () => {
      const isDesktopVisible = window.getComputedStyle(installBtn).display !== 'none';
      installBtnMobile.style.display = isDesktopVisible ? 'flex' : 'none';
    };
    
    // Initial update
    updateMobileButton();
    
    // Set up observer for changes
    const observer = new MutationObserver(updateMobileButton);
    observer.observe(installBtn, { attributes: true, attributeFilter: ['style'] });
  }
});

console.log('🚀 Abuja Rentals PWA initialized');