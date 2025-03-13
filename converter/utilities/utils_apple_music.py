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
    """Generate an Apple Music developer token"""
    try:
        # Try generating token using Node.js first
        try:
            token = generate_token_using_node()
            logger.info("Successfully got token from Node.js script")
            
            # Test the token
            test_url = "https://api.music.apple.com/v1/catalog/us/songs/203709340"
            test_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            logger.debug(f"Testing token with URL: {test_url}")
            response = requests.get(test_url, headers=test_headers)
            
            if response.status_code == 200:
                logger.info("Token validated successfully with Apple Music API")
                return token
            else:
                logger.warning(f"Node.js token validation failed with status {response.status_code}")
                # Continue with Python implementation
        except Exception as node_error:
            logger.warning(f"Node.js token generation failed, falling back to Python: {str(node_error)}")

        # Continue with Python implementation
        logger.info("Using Python token generation")
        
        # Get credentials from settings
        team_id = settings.APPLE_TEAM_ID
        key_id = settings.APPLE_KEY_ID

        if not team_id or not key_id:
            raise ValueError(f"Missing required credentials: team_id={bool(team_id)}, key_id={bool(key_id)}")

        # Load private key
        key_path = Path(__file__).parent / 'apple_auth_key.p8'
        logger.info(f"Looking for private key at: {key_path}")
        
        if not key_path.exists():
            raise FileNotFoundError(f"Apple Music private key not found at {key_path}")
            
        with open(key_path, 'r') as key_file:
            private_key = key_file.read()

        # Validate and clean private key
        if not private_key.strip():
            raise ValueError("Private key file is empty")
            
        private_key = clean_private_key(private_key)
        
        # Generate token with same parameters as Node.js script
        now = int(time.time())
        payload = {
            'iss': team_id,
            'iat': now,
            'exp': now + (60 * 60 * 24 * 180),  # 180 days
        }
        
        headers = {
            'alg': 'ES256',
            'kid': key_id
        }
        
        token = jwt.encode(
            payload,
            private_key,
            algorithm='ES256',
            headers=headers
        )

        # Test the token
        test_url = "https://api.music.apple.com/v1/catalog/us/songs/203709340"
        test_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(test_url, headers=test_headers)
        if response.status_code != 200:
            raise AppleMusicAPIError(f"Token validation failed (HTTP {response.status_code}): {response.text}")

        return token

    except Exception as e:
        logger.error(f"Developer token generation failed: {str(e)}", exc_info=True)
        raise AppleMusicAPIError(f"Token generation failed: {str(e)}")

class AppleMusicAPI:
    """Class to handle Apple Music API requests"""
    
    BASE_URL = "https://api.music.apple.com/v1"
    
    def __init__(self, user_token=None):
        self.developer_token = get_developer_token()
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
