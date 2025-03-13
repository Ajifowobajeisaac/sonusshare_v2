# Known Issues

## Apple Music User Token Authentication Issue

### Issue Description
Unable to obtain valid user tokens for Apple Music library access, preventing the ability to create playlists in users' Apple Music libraries.

### Impact
- Cannot convert Spotify playlists to Apple Music
- Cannot create or modify playlists in user's Apple Music library
- Limited to catalog access only

### Current Status
- 🔴 Active Issue
- 🔄 Under Investigation
- ⚠️ Workaround: One-way conversion (Apple Music to Spotify) available

### Technical Details

#### Environment
- MusicKit JS API v1/v3
- Django Backend
- Modern web browsers

#### Symptoms
1. User authentication flow completes successfully
2. Catalog access works (can search and play previews)
3. User token is not properly obtained/validated
4. Library access operations fail with authorization errors

#### Investigation Steps Taken
1. Implemented standard MusicKit JS authorization flow
2. Verified developer token generation
3. Confirmed app is properly configured in Apple Developer portal
4. Tested different MusicKit JS versions (v1 and v3)

#### Error Messages
```javascript
// Typical error when attempting library access
"Music catalog is not available" or "Unauthorized access"
```

#### Related Documentation
- [MusicKit JS Documentation](https://developer.apple.com/documentation/musickitjs)
- [Apple Music API](https://developer.apple.com/documentation/applemusicapi)

#### Forum Discussions
- https://developer.apple.com/forums/thread/744299
- https://developer.apple.com/forums/thread/121318
- https://developer.apple.com/forums/thread/670272
- https://developer.apple.com/forums/thread/711390
- https://developer.apple.com/forums/thread/709966?answerId=726133022#726133022

### Potential Solutions Under Investigation
1. Implementing native iOS authentication flow
2. Exploring alternative authorization methods
3. Reviewing token generation and validation process
4. Investigating session management improvements

### Workaround
Currently, the application supports:
- Converting Apple Music playlists to Spotify
- Searching Apple Music catalog
- Playing preview tracks

### Next Steps
1. Continue monitoring Apple Developer forums for similar issues
2. Gather more detailed error logs from user sessions
3. Consider implementing alternative authentication flows
4. Test on different browsers and platforms

### Updates
- [YYYY-MM-DD] Initial investigation
- [YYYY-MM-DD] Tested MusicKit JS v3
- [YYYY-MM-DD] Implemented catalog-only access as temporary solution

### Related Issues
- #[Issue Number] - Initial bug report
- #[Issue Number] - Investigation findings
- #[Issue Number] - Workaround implementation

### Additional Notes
This issue is being actively tracked and investigated. Users are currently notified of this limitation through the UI, and the application continues to provide value through its Apple Music to Spotify conversion functionality. 
