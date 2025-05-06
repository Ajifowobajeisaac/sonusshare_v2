/* global MusicKit */
// MusicKit initialization handler
class MusicKitManager {
  constructor (developerToken) {
    this.developerToken = developerToken;
    this.initialized = false;
    this.initPromise = null;
    console.log('[MusicKit] Manager created with developer token');
  }

  async initialize () {
    console.log('[MusicKit] Initialization requested');
    
    if (this.initialized) {
      console.log('[MusicKit] Already initialized, returning existing instance');
      return MusicKit.getInstance();
    }

    if (this.initPromise) {
      console.log('[MusicKit] Initialization already in progress, returning existing promise');
      return this.initPromise;
    }

    this.initPromise = new Promise((resolve, reject) => {
      // Check if MusicKit script is already loaded
      if (document.querySelector('script[src*="musickit.js"]')) {
        console.log('[MusicKit] Script already loaded, proceeding with configuration');
        this._configureAndResolve(resolve, reject);
        return;
      }

      // Load MusicKit script
      console.log('[MusicKit] Loading MusicKit script...');
      const script = document.createElement('script');
      script.src = 'https://js-cdn.music.apple.com/musickit/v3/musickit.js';
      script.async = true;

      script.onload = () => {
        console.log('[MusicKit] Script loaded successfully');
        this._configureAndResolve(resolve, reject);
      };
      script.onerror = () => {
        console.error('[MusicKit] Failed to load MusicKit script');
        reject(new Error('Failed to load MusicKit script'));
      };

      document.head.appendChild(script);
    });

    return this.initPromise;
  }

  async _configureAndResolve (resolve, reject) {
    try {
      console.log('[MusicKit] Waiting for MusicKit to be defined...');
      // Wait for MusicKit to be defined
      await this._waitForMusicKit();
      console.log('[MusicKit] MusicKit defined, proceeding with configuration');

      // Configure MusicKit
      console.log('[MusicKit] Configuring MusicKit instance...');
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

      console.log('[MusicKit] Configuration successful');
      this.initialized = true;
      
      // Add authorization state change listener
      instance.addEventListener('authorizationStatusDidChange', (event) => {
        console.log(`[MusicKit] Authorization status changed: ${event.authorizationStatus}`);
      });

      // Add user token change listener
      instance.addEventListener('userTokenDidChange', (event) => {
        console.log('[MusicKit] User token changed');
      });

      resolve(instance);
    } catch (error) {
      console.error('[MusicKit] Initialization failed:', error);
      reject(error);
    }
  }

  async _waitForMusicKit (timeout = 10000) {
    const start = Date.now();
    console.log('[MusicKit] Starting wait for MusicKit definition');

    while (Date.now() - start < timeout) {
      if (typeof MusicKit !== 'undefined') {
        console.log('[MusicKit] MusicKit definition found');
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    console.error('[MusicKit] Timeout waiting for MusicKit definition');
    throw new Error('MusicKit failed to initialize within timeout');
  }
}

export default MusicKitManager;
