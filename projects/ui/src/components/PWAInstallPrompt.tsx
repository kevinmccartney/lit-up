import React, { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

const PWAInstallPrompt: React.FC = () => {
  const isDevLoggingEnabled = (() => {
    const flag = import.meta.env.VITE_LIT_UP_APP_DEV;
    return flag === 'true' || flag === '1';
  })();
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(
    null,
  );
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      // Stash the event so it can be triggered later
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setShowInstallPrompt(true);
    };

    const handleAppInstalled = () => {
      if (isDevLoggingEnabled) {
        console.log('PWA was installed');
      }
      setShowInstallPrompt(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [isDevLoggingEnabled]);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      if (isDevLoggingEnabled) {
        console.log('User accepted the install prompt');
      }
    } else {
      if (isDevLoggingEnabled) {
        console.log('User dismissed the install prompt');
      }
    }

    // Clear the deferredPrompt
    setDeferredPrompt(null);
    setShowInstallPrompt(false);
  };

  const handleDismiss = () => {
    setShowInstallPrompt(false);
    // Don't show again for this session
    sessionStorage.setItem('pwa-install-dismissed', 'true');
  };

  // Don't show if user dismissed it in this session
  if (sessionStorage.getItem('pwa-install-dismissed')) {
    return null;
  }

  if (!showInstallPrompt || !deferredPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-80 bg-[var(--theme-tertiary)] border-2 border-[var(--theme-secondary)] rounded-xl p-4 shadow-lg z-50">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <Download className="w-6 h-6 text-[var(--theme-secondary)]" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-[var(--theme-primary)] mb-1">
            Install Lit Up
          </h3>
          <p className="text-xs text-[var(--theme-primary)] opacity-80 mb-3">
            Install this app for better audio playback and offline access.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleInstallClick}
              type="button"
              className="px-3 py-1.5 bg-[var(--theme-secondary)] text-[var(--theme-tertiary)] rounded-lg text-xs font-medium hover:opacity-90 transition-opacity"
            >
              Install
            </button>
            <button
              onClick={handleDismiss}
              type="button"
              aria-label="Dismiss install prompt"
              className="px-3 py-1.5 text-[var(--theme-primary)] opacity-60 hover:opacity-100 transition-opacity"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;
