# utils.py
import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs


# Utility functions
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.plain_text = []

    def handle_data(self, data):
        self.plain_text.append(data)

    def get_plain_text(self):
        return ''.join(self.plain_text)

class PlaylistError(Exception):
    """Custom exception for playlist-related errors"""
    pass

def sanitize_description(description):
    """Clean and format playlist descriptions"""
    if not description:
        return ""
    
    # Remove HTML tags
    clean_desc = re.sub(r'<[^>]+>', '', description)
    
    # Remove excessive whitespace
    clean_desc = ' '.join(clean_desc.split())
    
    # Limit length
    MAX_LENGTH = 300
    if len(clean_desc) > MAX_LENGTH:
        clean_desc = clean_desc[:MAX_LENGTH-3] + '...'
    
    return clean_desc

def extract_playlist_id(url, service):
    """Extract playlist ID from various streaming service URLs"""
    try:
        parsed_url = urlparse(url)
        
        if service == 'spotify':
            # Handle Spotify URLs
            path_parts = parsed_url.path.split('/')
            if 'playlist' in path_parts:
                return path_parts[path_parts.index('playlist') + 1]
        
        elif service == 'apple_music':
            # Handle Apple Music URLs
            path_parts = parsed_url.path.split('/')
            if 'playlist' in path_parts:
                return path_parts[-1]
        
        elif service == 'youtube':
            # Handle YouTube URLs
            if 'list' in parse_qs(parsed_url.query):
                return parse_qs(parsed_url.query)['list'][0]
        
        raise PlaylistError(f"Could not extract playlist ID from {url}")
    
    except Exception as e:
        raise PlaylistError(f"Error extracting playlist ID: {str(e)}")

def extract_track_info(tracks_data, platform):
    """Extract track name and artist from playlist data"""
    track_info = []
    
    try:
        if platform == 'spotify':
            for item in tracks_data:
                track = item['track']
                track_info.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name']
                })
        elif platform == 'apple_music':
            for track in tracks_data:
                track_info.append({
                    'name': track['attributes']['name'],
                    'artist': track['attributes']['artistName']
                })
        return track_info
        
    except Exception as e:
        logger.error(f"Error extracting track info: {str(e)}")
        raise ValueError(f"Error extracting track info: {str(e)}")
