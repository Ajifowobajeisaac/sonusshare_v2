# utils_apple_music.py
import requests
import jwt
import time
import os
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache
from pathlib import Path
import logging
import subprocess

logger = logging.getLogger(__name__)

class AppleMusicAPIError(Exception):
    """Custom exception for Apple Music API errors"""
    pass

def generate_token_using_node():
    """Use Node.js script to generate the token"""
    try:
        script_path = Path(__file__).parent / 'generate_token.js'
        logger.info(f"Attempting to run Node.js script at: {script_path}")
        
        # Run the Node.js script
        process = subprocess.Popen(['node', str(script_path)], 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Node.js script failed with error: {stderr}")
            raise AppleMusicAPIError(f"Node.js token generation failed: {stderr}")
            
        # Parse the output to get the token
        for line in stdout.split('\n'):
            if line and not line.startswith(('=', 'Generated', 'Token', 'Header:', 'Payload:', 'Expiration:')):
                token = line.strip()
                logger.info("Successfully generated token using Node.js script")
                return token
                
        raise AppleMusicAPIError("Could not find token in Node.js script output")
        
    except Exception as e:
        logger.error(f"Failed to generate token using Node.js: {str(e)}")
        raise AppleMusicAPIError(f"Node.js token generation failed: {str(e)}")

@lru_cache(maxsize=1)
def get_developer_token():
    """
    Get the Apple Music developer token from environment variables.
    If not found, generate a new one using the private key.
    """
    try:
        # First try to get the token from environment variables
        token = os.getenv('APPLE_MUSIC_DEVELOPER_TOKEN')
        if token:
            return token

        # If no token in env, generate a new one
        key_id = os.getenv('APPLE_MUSIC_KEY_ID')
        team_id = os.getenv('APPLE_MUSIC_TEAM_ID')
        
        # Look for private key in secure location first, then fall back to project directory
        private_key_paths = [
            os.path.expanduser('~/.sonusshare/keys/apple_auth_key.p8'),
            os.path.join(os.path.dirname(__file__), 'apple_auth_key.p8')
        ]
        
        private_key_path = None
        for path in private_key_paths:
            if os.path.exists(path):
                private_key_path = path
                break
                
        if not private_key_path:
            raise AppleMusicAPIError("Private key file not found in any of the expected locations")

        if not all([key_id, team_id]):
            raise AppleMusicAPIError("Missing required credentials: team_id={}, key_id={}".format(
                bool(team_id), bool(key_id)
            ))

        # Read the private key
        with open(private_key_path, 'r') as key_file:
            private_key = key_file.read()

        # Generate the token
        headers = {
            'alg': 'ES256',
            'kid': key_id
        }

        payload = {
            'iss': team_id,
            'iat': int(time.time()),
            'exp': int(time.time() + 15777000)  # 6 months from now
        }

        # Generate the token
        token = jwt.encode(
            payload,
            private_key,
            algorithm='ES256',
            headers=headers
        )

        # Set the token in environment variables for future use
        os.environ['APPLE_MUSIC_DEVELOPER_TOKEN'] = token
        return token

    except Exception as e:
        raise AppleMusicAPIError(f"Token generation failed: {str(e)}")

class AppleMusicAPI:
    """Class to handle Apple Music API requests"""
    
    BASE_URL = "https://api.music.apple.com/v1"
    
    def __init__(self, user_token=None, developer_token=None):
        self.developer_token = developer_token or get_developer_token()
        self.user_token = user_token
        self.headers = {
            'Authorization': f'Bearer {self.developer_token}',
            'Content-Type': 'application/json'
        }
        if user_token:
            self.headers['Music-User-Token'] = user_token

    def create_playlist(self, name, description, track_ids):
        """Create a playlist in user's library"""
        if not self.user_token:
            raise AppleMusicAPIError("User authentication required")

        try:
            # First create an empty playlist
            playlist_data = {
                'attributes': {
                    'name': name,
                    'description': description or ''
                }
            }

            # Create playlist in user's library
            response = self._make_request('POST', 'me/library/playlists', json=playlist_data)
            
            if not response.get('data'):
                raise AppleMusicAPIError("No playlist data in response")
            
            playlist_id = response['data'][0]['id']
            
            # Add tracks to the playlist
            tracks_data = {
                'data': [{'id': tid, 'type': 'songs'} for tid in track_ids]
            }
            
            # Add tracks to the playlist
            self._make_request('POST', f'me/library/playlists/{playlist_id}/tracks', json=tracks_data)
            
            # Return the playlist URL
            return f'https://music.apple.com/library/playlist/{playlist_id}'

        except Exception as e:
            logger.error(f"Failed to create playlist: {str(e)}")
            raise AppleMusicAPIError(f"Failed to create Apple Music playlist: {str(e)}")

    def get_playlist(self, playlist_id, storefront='gb'):
        """Get a playlist by ID"""
        try:
            return self._make_request('GET', f"catalog/{storefront}/playlists/{playlist_id}")
        except Exception as e:
            raise AppleMusicAPIError(f"Failed to get playlist: {str(e)}")

    def search_track(self, track_name, artist_name, storefront='us', limit=1):
        """Search for a track"""
        params = {
            'types': 'songs',
            'term': f"{track_name} {artist_name}",
            'limit': limit
        }
        response = self._make_request('GET', f"catalog/{storefront}/search", params=params)
        
        try:
            tracks = response['results']['songs']['data']
            return tracks[0]['id'] if tracks else None
        except (KeyError, IndexError):
            return None

    def _make_request(self, method, endpoint, **kwargs):
        """Generic method to make API requests"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise AppleMusicAPIError(f"API request failed: {str(e)}")

# Simple wrapper for backward compatibility
def get_apple_music_playlist(playlist_id):
    """Wrapper function for backward compatibility"""
    api = AppleMusicAPI()
    return api.get_playlist(playlist_id)

def clean_private_key(key_content):
    """Clean and format the private key content."""
    if not key_content:
        return None
        
    # Remove any whitespace and ensure proper line breaks
    key_lines = [line.strip() for line in key_content.split('\n') if line.strip()]
    
    # Ensure proper PEM format
    if not key_lines[0].startswith('-----BEGIN PRIVATE KEY-----'):
        key_lines.insert(0, '-----BEGIN PRIVATE KEY-----')
    if not key_lines[-1].endswith('-----END PRIVATE KEY-----'):
        key_lines.append('-----END PRIVATE KEY-----')
    
    # Join with proper newlines and ensure proper PEM format
    formatted_key = '\n'.join([
        '-----BEGIN PRIVATE KEY-----',
        '\n'.join(line for line in key_lines if not line.startswith('-----')),
        '-----END PRIVATE KEY-----'
    ])
    return formatted_key
