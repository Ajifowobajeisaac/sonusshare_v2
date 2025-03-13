# utils_spotify.py
from django.shortcuts import render, redirect
import urllib.parse
from django.conf import settings
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import base64

logger = logging.getLogger(__name__)

class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors"""
    pass

class SpotifyAPI:
    """Class to handle Spotify API requests and authentication"""
    
    BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    SCOPE = 'playlist-read-private playlist-modify-private playlist-modify-public'
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        self.token = None
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise SpotifyAPIError("Missing Spotify credentials in settings")
        
        # Use client credentials flow for non-user-specific operations
        self.client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=self.client_credentials_manager)
    
    @classmethod
    def from_user_token(cls, access_token):
        """Create instance with user token instead of client credentials"""
        instance = cls()
        instance.sp = spotipy.Spotify(auth=access_token)
        return instance
    
    @property
    def access_token(self):
        """Get the current access token from the client credentials manager"""
        return self.client_credentials_manager.get_access_token()['access_token']
    
    def search_track(self, track_name, artist_name):
        try:
            query = f"track:{track_name} artist:{artist_name}"
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                return results['tracks']['items'][0]['id']
            logger.warning(f"No track found for: {track_name} by {artist_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching track: {str(e)}")
            return None
            
    def get_token_from_code(self, code):
        """Exchange authorization code for access token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        try:
            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                data=data
            )
            response.raise_for_status()
            token_data = response.json()
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get token from code: {str(e)}")
            raise Exception(f"Failed to get Spotify access token: {str(e)}")

    def create_playlist(self, name, description, track_ids):
        """Create a playlist and add tracks to it"""
        if not self.token:
            raise Exception("No access token available")

        try:
            # Get user ID using spotipy client
            user_response = self.sp.me()
            user_id = user_response['id']

            # Create playlist using spotipy client
            playlist = self.sp.user_playlist_create(
                user_id,
                name,
                public=True,
                description=description
            )

            # Add tracks to playlist using spotipy client
            self.sp.playlist_add_items(playlist['id'], track_ids)
            return playlist['external_urls']['spotify']

        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Failed to create playlist: {str(e)}")
            raise Exception(f"Failed to create Spotify playlist: {str(e)}")

    def get_auth_url(self):
        """Generate the Spotify authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': self.SCOPE,
            'show_dialog': True
        }
        return f'{self.AUTH_URL}?{urllib.parse.urlencode(params)}'

    def process_callback(self, auth_code):
        """Process the callback from Spotify and return token info"""
        if not auth_code:
            raise SpotifyAPIError("No authorization code received")
            
        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.SCOPE
        )
        
        return auth_manager.get_access_token(auth_code)

    @classmethod
    def from_token(cls, token):
        """Create instance with user token and verify connection"""
        instance = cls()
        instance.token = token
        # Initialize propper auth manager
        instance.sp = spotipy.Spotify(auth=token)
        return instance

    def get_playlist(self, playlist_id):
        """Get a playlist by ID"""
        try:
            # Use spotipy client to get playlist
            playlist = self.sp.playlist(playlist_id)
            return playlist
        except Exception as e:
            logger.error(f"Failed to get playlist: {str(e)}")
            raise SpotifyAPIError(f"Failed to get playlist: {str(e)}")


def spotify_auth(request):
    spotify = SpotifyAPI()
    auth_url = spotify.get_auth_url()
    return redirect(auth_url)

def spotify_callback(request):
    try:
        auth_code = request.GET.get('code')
        spotify = SpotifyAPI()
        token_info = spotify.process_callback(auth_code)
        request.session['spotify_token'] = token_info['access_token']
        return redirect('convert_playlist')
            
    except Exception as e:
        logger.error(f"Error in spotify callback: {str(e)}")
        return redirect('error')

def create_spotify_playlist(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('spotify_auth')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        track_ids = request.POST.get('track_ids').split(',')

        try:
            # Use SpotifyAPI class instead of direct spotipy usage
            spotify = SpotifyAPI.from_user_token(access_token)
            playlist_url = spotify.create_playlist(name, description, track_ids)
            
            return render(request, 'sonoshareapp/playlist_created.html', {
                'playlist_url': playlist_url,
            })
            
        except Exception as e:
            error_message = "Failed to create playlist"
            error_details = {
                'error_message': str(e)
            }
            return render(request, 'sonoshareapp/error.html', {
                'error_message': error_message,
                'error_details': error_details,
            })
    
    return render(request, 'sonoshareapp/index.html')

def search_tracks_on_spotify(track_info):
    """
    Search for multiple tracks on Spotify and return their IDs.
    
    Args:
        track_info: List of dicts, each containing 'name' and 'artist' keys
        
    Returns:
        tuple: (list of found track IDs, list of failed track names)
    """
    spotify = SpotifyAPI()
    spotify_track_ids = []
    failed_tracks = []
    
    for track in track_info:
        track_id = spotify.search_track(track['name'], track['artist'])
        if track_id:
            spotify_track_ids.append(track_id)
        else:
            failed_tracks.append(f"{track['name']} by {track['artist']}")
            
    if failed_tracks:
        logger.warning(f"Failed to find tracks: {', '.join(failed_tracks)}")
        
    return spotify_track_ids, failed_tracks
