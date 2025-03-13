# SonusShare API Integration Details

## Apple Music Integration

### Authentication Flow
1. **Developer Token Generation**
   ```python
   def get_developer_token():
       """Generate Apple Music API developer token using JWT"""
       private_key = clean_private_key(settings.APPLE_PRIVATE_KEY)
       team_id = settings.APPLE_TEAM_ID
       key_id = settings.APPLE_KEY_ID
       
       # Token generation logic
       token = jwt.encode(
           payload={
               'iss': team_id,
               'iat': time.time(),
               'exp': time.time() + 15777000
           },
           key=private_key,
           algorithm='ES256',
           headers={
               'kid': key_id
           }
       )
       return token
   ```

2. **MusicKit JS Integration**
   ```javascript
   // MusicKit configuration
   const music = await MusicKit.configure({
       developerToken: token,
       app: {
           name: 'SonusShare',
           build: '1.0.0'
       }
   });
   ```

### Playlist Operations

1. **Fetching Playlist Details**
   ```python
   def get_playlist(self, playlist_id, storefront='gb'):
       """Fetch playlist details from Apple Music"""
       endpoint = f"/catalog/{storefront}/playlists/{playlist_id}"
       params = {
           'include': 'tracks,curator',
           'fields[playlists]': 'artwork,name,curator,description,trackCount'
       }
       return self._make_request('GET', endpoint, params=params)
   ```

2. **Track Information Extraction**
   ```python
   def extract_track_info(playlist_data):
       """Extract essential track information from playlist data"""
       tracks = []
       for item in playlist_data['relationships']['tracks']['data']:
           track = {
               'id': item['id'],
               'name': item['attributes']['name'],
               'artist': item['attributes']['artistName'],
               'album': item['attributes']['albumName'],
               'duration': item['attributes']['durationInMillis'],
               'isrc': item['attributes'].get('isrc')
           }
           tracks.append(track)
       return tracks
   ```

## Spotify Integration

### Authentication Flow
1. **OAuth Setup**
   ```python
   def generate_spotify_auth_url():
       """Generate Spotify OAuth URL"""
       params = {
           'client_id': settings.SPOTIFY_CLIENT_ID,
           'response_type': 'code',
           'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
           'scope': 'playlist-modify-public playlist-modify-private',
           'state': generate_state_token()
       }
       return f"https://accounts.spotify.com/authorize?{urlencode(params)}"
   ```

2. **Token Management**
   ```python
   def refresh_access_token(self):
       """Refresh Spotify access token"""
       auth_header = base64.b64encode(
           f"{self.client_id}:{self.client_secret}".encode()
       ).decode()
       
       response = requests.post(
           'https://accounts.spotify.com/api/token',
           data={
               'grant_type': 'refresh_token',
               'refresh_token': self.refresh_token
           },
           headers={
               'Authorization': f'Basic {auth_header}'
           }
       )
       return response.json()
   ```

### Playlist Operations

1. **Creating Playlists**
   ```python
   def create_playlist(self, user_id, name, description, tracks):
       """Create a new Spotify playlist"""
       # Create playlist
       playlist = self._make_request(
           'POST',
           f'/users/{user_id}/playlists',
           json={
               'name': name,
               'description': description,
               'public': False
           }
       )
       
       # Add tracks in batches
       track_uris = [track['uri'] for track in tracks]
       for i in range(0, len(track_uris), 100):
           batch = track_uris[i:i + 100]
           self.add_tracks_to_playlist(playlist['id'], batch)
       
       return playlist
   ```

2. **Track Search**
   ```python
   def search_track(self, track_name, artist_name):
       """Search for a track on Spotify"""
       query = f"track:{track_name} artist:{artist_name}"
       params = {
           'q': query,
           'type': 'track',
           'limit': 5
       }
       results = self._make_request('GET', '/search', params=params)
       return results['tracks']['items']
   ```

## Error Handling

### API Error Classes
```python
class AppleMusicAPIError(Exception):
    """Custom exception for Apple Music API errors"""
    pass

class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors"""
    pass
```

### Error Handling Implementation
```python
def _make_request(self, method, endpoint, **kwargs):
    """Make an API request with error handling"""
    try:
        response = requests.request(
            method,
            f"{self.BASE_URL}{endpoint}",
            **kwargs
        )
        
        if not response.ok:
            error_data = response.json()
            raise APIError(
                f"API request failed: {error_data.get('error', {}).get('message')}"
            )
            
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")
```

## Rate Limiting

### Implementation
```python
class RateLimiter:
    def __init__(self, calls_per_second=5):
        self.calls_per_second = calls_per_second
        self.last_call = 0
        self.lock = threading.Lock()

    def wait(self):
        """Wait if necessary to respect rate limits"""
        with self.lock:
            elapsed = time.time() - self.last_call
            if elapsed < 1.0 / self.calls_per_second:
                time.sleep(1.0 / self.calls_per_second - elapsed)
            self.last_call = time.time()
```

## Caching Strategy

### Implementation
```python
@lru_cache(maxsize=100)
def get_track_details(track_id):
    """Cache track details to reduce API calls"""
    return api.get_track(track_id)

def clear_track_cache():
    """Clear the track details cache"""
    get_track_details.cache_clear()
```

## API Response Processing

### Data Normalization
```python
def normalize_track_data(track, platform):
    """Normalize track data from different platforms"""
    if platform == 'apple_music':
        return {
            'name': track['attributes']['name'],
            'artist': track['attributes']['artistName'],
            'album': track['attributes']['albumName'],
            'duration': track['attributes']['durationInMillis'],
            'isrc': track['attributes'].get('isrc')
        }
    elif platform == 'spotify':
        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'duration': track['duration_ms'],
            'isrc': track.get('external_ids', {}).get('isrc')
        }
```

## Testing

### API Mock Setup
```python
class MockAPI:
    """Mock API for testing"""
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def mock_response(self, endpoint, response):
        self.responses[endpoint] = response

    def _make_request(self, method, endpoint, **kwargs):
        self.calls.append((method, endpoint, kwargs))
        if endpoint in self.responses:
            return self.responses[endpoint]
        raise APIError(f"No mock response for {endpoint}")
```

### Integration Tests
```python
class APIIntegrationTests(TestCase):
    def setUp(self):
        self.apple_music = AppleMusicAPI()
        self.spotify = SpotifyAPI()

    def test_playlist_conversion(self):
        # Test complete conversion flow
        source_playlist = self.apple_music.get_playlist(TEST_PLAYLIST_ID)
        tracks = extract_track_info(source_playlist)
        
        spotify_tracks = []
        for track in tracks:
            spotify_track = self.spotify.search_track(
                track['name'],
                track['artist']
            )
            if spotify_track:
                spotify_tracks.append(spotify_track[0])
                
        self.assertGreater(len(spotify_tracks), 0) 
