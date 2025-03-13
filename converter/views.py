# views.py

from django.http import JsonResponse
from django.shortcuts import render, redirect
import logging
import json
from .utilities.utils_spotify import SpotifyAPI, SpotifyAPIError
from .utilities.utils_apple_music import AppleMusicAPI, AppleMusicAPIError
from .utilities.utils import sanitize_description, extract_playlist_id, extract_track_info
import time
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
import secrets
from urllib.parse import urlencode
import base64

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with custom formatter
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Basic page views
def index(request):
    """Render index page with featured playlists"""
    try:
        # Featured playlist IDs
        featured_playlists = [
            {
                'id': 'pl.dc349df19c6f410d874c197db63ecfed',
                'url': 'https://music.apple.com/gb/playlist/afrobeats-hits/pl.dc349df19c6f410d874c197db63ecfed',
                'title': 'Afrobeats Hits',
                'curator': 'Apple Music Afrobeats'
            },
            {
                'id': 'pl.d25f5d1181894928af76c85c967f8f31',
                'url': 'https://music.apple.com/gb/playlist/top-100-global/pl.d25f5d1181894928af76c85c967f8f31',
                'title': 'Top 100: Global',
                'curator': 'Apple Music'
            },
            {
                'id': 'pl.d50f89dc1bbe47eba03caec1fe6280db',
                'url': 'https://music.apple.com/gb/playlist/top-25-london/pl.d50f89dc1bbe47eba03caec1fe6280db',
                'title': 'Top 25: London',
                'curator': 'Apple Music'
            }
        ]

        # Initialize Apple Music API
        apple_music = AppleMusicAPI()
        
        # Fetch playlist details including artwork
        for playlist in featured_playlists:
            try:
                playlist_data = apple_music.get_playlist(playlist['id'])
                if playlist_data and 'data' in playlist_data and playlist_data['data']:
                    attributes = playlist_data['data'][0]['attributes']
                    if 'artwork' in attributes:
                        playlist['artwork'] = attributes['artwork']
            except Exception as e:
                logger.error(f"Failed to fetch playlist {playlist['id']}: {str(e)}")
                playlist['artwork'] = None

        context = {
            'featured_playlists': featured_playlists,
            'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
        }
        return render(request, 'converter/index.html', context)
    except Exception as e:
        logger.error(f"Error in index view: {str(e)}")
        return render(request, 'converter/index.html', {
            'error_message': 'Failed to load featured playlists'
        })

def about(request):
    return render(request, 'converter/about.html')

def contact(request):
    return render(request, 'converter/contact.html')

def review_playlist(request):
    data = json.loads(request.GET.get('data', '{}'))
    data['developer_token'] = settings.APPLE_MUSIC_DEVELOPER_TOKEN
    return render(request, 'converter/review_playlist.html', data)

def convert_playlist(request):
    """Main playlist conversion logic"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    playlist_url = request.POST.get('playlist_url')
    destination_platform = request.POST.get('destination')
    
    if not playlist_url or not destination_platform:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    try:
        logger.info(f"Converting playlist to {destination_platform}: {playlist_url}")
        
        # Validate URL format and get source platform
        if 'music.apple.com' in playlist_url:
            if '/playlist/' not in playlist_url:
                raise ValueError("Invalid Apple Music URL")
            source_platform = 'apple_music'
        elif 'spotify.com' in playlist_url:
            if '/playlist/' not in playlist_url:
                raise ValueError("Invalid Spotify URL")
            source_platform = 'spotify'
        else:
            raise ValueError("Unsupported platform")

        # Extract playlist data
        playlist_id = extract_playlist_id(playlist_url, source_platform)
        
        if source_platform == 'apple_music':
            apple_music = AppleMusicAPI()
            playlist_data = apple_music.get_playlist(playlist_id)
            tracks = extract_track_info(
                playlist_data['data'][0]['relationships']['tracks']['data'], 
                'apple_music'
            )
            playlist_name = playlist_data['data'][0]['attributes']['name']
            playlist_description = playlist_data['data'][0]['attributes'].get('description', {}).get('standard', '')
        else:
            spotify = SpotifyAPI()
            playlist_data = spotify.get_playlist(playlist_id)
            tracks = extract_track_info(playlist_data['tracks']['items'], 'spotify')
            playlist_name = playlist_data['name']
            playlist_description = playlist_data.get('description', '')

        # Convert tracks and mark matched status
        converted_tracks = []
        failed_tracks = []
        matched_tracks = []
        
        api = SpotifyAPI() if destination_platform == 'spotify' else AppleMusicAPI()
        
        for track in tracks:
            result = api.search_track(track['name'], track['artist'])
            track_info = {
                'name': track['name'],
                'artist': track['artist'],
                'matched': bool(result)
            }
            matched_tracks.append(track_info)
            if result:
                converted_tracks.append({
                    'id': result,
                    'name': track['name'],
                    'artist': track['artist']
                })
            else:
                failed_tracks.append({
                    'name': track['name'],
                    'artist': track['artist']
                })

        success_rate = (len(converted_tracks) / len(tracks)) * 100
        
        if success_rate < 50:
            raise ValueError(f"Too many tracks failed to match: {len(failed_tracks)} out of {len(tracks)}")

        # Create context data
        context = {
            'platform': destination_platform,
            'playlist_name': f"{playlist_name}-converted",
            'playlist_description': sanitize_description(playlist_description),
            'tracks': converted_tracks,
            'failed_tracks': failed_tracks,
            'success_rate': f"{success_rate:.1f}%",
            'matched_tracks': matched_tracks,
            'track_ids': [track['id'] for track in converted_tracks],
            'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
        }
        
        # Store in session
        request.session['playlist_data'] = context
        request.session['pending_playlist_data'] = context  # Store in both places
        request.session.modified = True
        
        logger.info("Stored playlist data in session")
        logger.info(f"Session keys: {request.session.keys()}")
        
        return render(request, 'converter/review_playlist.html', context)
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=400)

def generate_spotify_auth_url():
    state = secrets.token_urlsafe(16)
    scope = "playlist-modify-public playlist-modify-private"
    params = {
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'state': state,
        'scope': scope
    }
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return auth_url, state

@ensure_csrf_cookie
@require_http_methods(["POST"])
def create_playlist(request):
    try:
        playlist_data = request.session.get('playlist_data')
        if not playlist_data:
            return JsonResponse({'error': 'No playlist data found'}, status=400)

        platform = playlist_data.get('platform')
        if platform == 'spotify':
            token = request.session.get('spotify_token')
            logger.info(f"Token present: {bool(token)}")
            
            if not token:
                # Store playlist data before auth
                request.session['pending_playlist_data'] = playlist_data
                request.session.modified = True
                
                # Generate auth URL
                auth_url, state = generate_spotify_auth_url()
                request.session['spotify_auth_state'] = state
                request.session.modified = True
                
                return JsonResponse({
                    'error': 'Not authenticated with Spotify',
                    'auth_url': auth_url
                }, status=401)
                
            try:
                spotify = SpotifyAPI.from_token(token)
                logger.info(f"Creating playlist: {playlist_data['playlist_name']}")
                
                playlist_url = spotify.create_playlist(
                    name=playlist_data['playlist_name'],
                    description=playlist_data.get('playlist_description', ''),
                    track_ids=playlist_data['track_ids']
                )
                
                # Clear session data after success
                request.session.pop('playlist_data', None)
                request.session.pop('pending_playlist_data', None)
                request.session.modified = True
                
                return JsonResponse({'playlist_url': playlist_url})
            
            except Exception as e:
                logger.error(f"Failed to create playlist: {str(e)}", exc_info=True)
                return JsonResponse({'error': str(e)}, status=400)
        else:
            return JsonResponse({'error': 'Unsupported platform'}, status=400)

    except Exception as e:
        logger.error(f"Failed to create playlist: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=400)

def spotify_callback(request):
    try:
        error = request.GET.get('error')
        if error:
            logger.error(f"Spotify auth error: {error}")
            return JsonResponse({'error': f'Spotify auth error: {error}'}, status=400)

        code = request.GET.get('code')
        state = request.GET.get('state')
        stored_state = request.session.get('spotify_auth_state')

        if not state or state != stored_state:
            logger.error("State mismatch in Spotify callback")
            return JsonResponse({'error': 'State verification failed'}, status=400)

        # Exchange code for token
        spotify = SpotifyAPI()
        token_data = spotify.get_token_from_code(code)
        
        # Store token in session
        request.session['spotify_token'] = token_data['access_token']
        request.session.modified = True
        
        logger.info("Successfully authenticated with Spotify")

        # Get the pending playlist data
        playlist_data = request.session.get('pending_playlist_data')
        if playlist_data:
            try:
                # Create the playlist immediately
                spotify = SpotifyAPI.from_token(token_data['access_token'])
                playlist_url = spotify.create_playlist(
                    name=playlist_data['playlist_name'],
                    description=playlist_data.get('playlist_description', ''),
                    track_ids=playlist_data['track_ids']
                )
                
                # Clear session data
                request.session.pop('pending_playlist_data', None)
                request.session.modified = True
                
                # Redirect directly to the created playlist
                return redirect(playlist_url)
            except Exception as e:
                logger.error(f"Failed to create playlist after auth: {str(e)}")
                # If creation fails, go back to review page with error message
                return render(request, 'converter/review_playlist.html', {
                    **playlist_data,
                    'auth_success': True,
                    'error_message': str(e)
                })
        
        # If we don't have playlist data, just go back to review page with success message
        return render(request, 'converter/review_playlist.html', {
            'auth_success': True
        })

    except Exception as e:
        logger.error(f"Spotify callback error: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=400)

def clear_session_data(request):
    """Clear temporary session data after successful creation"""
    keys = ['playlist_data', 'pending_playlist_data', 'spotify_auth_state']
    for key in keys:
        if key in request.session:
            del request.session[key]
    request.session.modified = True
