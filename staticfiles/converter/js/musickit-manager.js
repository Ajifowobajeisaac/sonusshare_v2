/* global MusicKit */
// MusicKit initialization handler
class MusicKitManager {
  constructor (developerToken) {
    this.developerToken = developerToken;
    this.initialized = false;
    this.initPromise = null;
  }

  async initialize () {
    if (this.initialized) {
      return MusicKit.getInstance();
    }

    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = new Promise((resolve, reject) => {
      // Check if MusicKit script is already loaded
      if (document.querySelector('script[src*="musickit.js"]')) {
        this._configureAndResolve(resolve, reject);
        return;
      }

      // Load MusicKit script
      const script = document.createElement('script');
      script.src = 'https://js-cdn.music.apple.com/musickit/v3/musickit.js';
      script.async = true;

      script.onload = () => this._configureAndResolve(resolve, reject);
      script.onerror = () => reject(new Error('Failed to load MusicKit script'));

      document.head.appendChild(script);
    });

    return this.initPromise;
  }

  async _configureAndResolve (resolve, reject) {
    try {
      // Wait for MusicKit to be defined
      await this._waitForMusicKit();

      // Configure MusicKit
      const instance = await MusicKit.configure({
        developerToken: this.developerToken,
        app: {
          name: 'SonusShare',
          build: '1.0.0',
          icon: '/static/converter/images/logo.png'
        },
        suppressErrorDialog: true,
        autoplayEnabled: false,
        bundleId: '732N38L7AM.media.sonusshare.app'
      });

      console.log('MusicKit configured successfully');
      this.initialized = true;
      resolve(instance);
    } catch (error) {
      console.error('MusicKit initialization failed:', error);
      reject(error);
    }
  }

  async _waitForMusicKit (timeout = 10000) {
    const start = Date.now();

    while (Date.now() - start < timeout) {
      if (typeof MusicKit !== 'undefined') {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('MusicKit failed to initialize within timeout');
  }
}

export default MusicKitManager;
