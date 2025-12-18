import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

const isDevLoggingEnabled = (() => {
  const flag = import.meta.env.VITE_LIT_UP_APP_DEV;
  return flag === 'true' || flag === '1';
})();

// Register service worker for PWA functionality
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(`${import.meta.env.BASE_URL || '/'}sw.js`)
      .then((registration) => {
        if (isDevLoggingEnabled) {
          console.log('SW registered: ', registration);
        }

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (
                newWorker.state === 'installed' &&
                navigator.serviceWorker.controller
              ) {
                // New content is available, prompt user to refresh
                if (confirm('New version available! Refresh to update?')) {
                  window.location.reload();
                }
              }
            });
          }
        });
      })
      .catch((registrationError) => {
        console.error('SW registration failed: ', registrationError);
      });
  });
}

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element with id "root" not found');
}

const root = createRoot(container);
root.render(<App />);
