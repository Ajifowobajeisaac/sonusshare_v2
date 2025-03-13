import json
import logging
import time
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.conf import settings
from converter.utilities.utils_spotify import SpotifyAPI
from converter.utilities.utils_apple_music import AppleMusicAPI, get_developer_token
import sys
import os

# Add converter directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from io import StringIO

# Get logger for this app
logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def test_home(request):
    """Main test directory view."""
    return render(request, 'aoede_tests/test_home.html')

@ensure_csrf_cookie
def test_search(request):
    """Search test interface."""
    context = {
        'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
    }
    return render(request, 'aoede_tests/test_search.html', context)

@ensure_csrf_cookie
def test_playlist_creation(request):
    """Playlist creation test interface."""
    context = {
        'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
    }
    return render(request, 'aoede_tests/test_playlist.html', context)

@ensure_csrf_cookie
def test_track_matching(request):
    """Track matching test interface."""
    return render(request, 'aoede_tests/test_track_matching.html')

@ensure_csrf_cookie
def test_auth(request):
    """
    View for testing authentication flows with Spotify and Apple Music.
    """
    try:
        developer_token = settings.APPLE_MUSIC_DEVELOPER_TOKEN
        if not developer_token:
            logger.error("Apple Music developer token is None")
            raise ValueError("Failed to generate Apple Music developer token")

        # Log token details (first 10 chars only for security)
        logger.info(f"Developer token generated successfully: {developer_token[:10]}...")
        
        context = {
            'spotify_client_id': settings.SPOTIFY_CLIENT_ID,
            'developer_token': developer_token,
            'environment': 'development' if settings.DEBUG else 'production',
        }
        return render(request, 'aoede_tests/test_auth.html', context)
        
    except Exception as e:
        logger.error(f"Error in test_auth view: {str(e)}", exc_info=True)
        context = {
            'error_message': f"Apple Music setup error: {str(e)}",
            'spotify_client_id': settings.SPOTIFY_CLIENT_ID,
            'environment': 'development' if settings.DEBUG else 'production',
        }
        return render(request, 'aoede_tests/test_auth.html', context)

@ensure_csrf_cookie
def test_token(request):
    """Token management test interface."""
    context = {
        'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
    }
    return render(request, 'aoede_tests/test_token.html', context)

@ensure_csrf_cookie
def test_playback(request):
    """Playback test interface."""
    context = {
        'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
    }
    return render(request, 'aoede_tests/test_playback.html', context)

def test_spotify_callback(request):
    """Handle Spotify OAuth callback for test page."""
    try:
        error = request.GET.get('error')
        if error:
            return render(request, 'aoede_tests/test_auth.html', {
                'error_message': f'Spotify auth error: {error}',
                'spotify_client_id': settings.SPOTIFY_CLIENT_ID,
                'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
            })

        code = request.GET.get('code')
        state = request.GET.get('state')

        if not code:
            return render(request, 'aoede_tests/test_auth.html', {
                'error_message': 'No authorization code received',
                'spotify_client_id': settings.SPOTIFY_CLIENT_ID,
                'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
            })

        return render(request, 'aoede_tests/test_auth.html', {
            'auth_code': code,
            'state': state,
            'spotify_client_id': settings.SPOTIFY_CLIENT_ID,
            'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
        })

    except Exception as e:
        logger.error(f"Spotify test callback error: {str(e)}", exc_info=True)
        return render(request, 'aoede_tests/test_auth.html', {
            'error_message': str(e),
            'spotify_client_id': settings.SPOTIFY_CLIENT_ID,
            'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
        })

def run_test_class(test_class, test_name=None):
    """Run a specific test class or test method and capture output."""
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    
    if test_name:
        suite = unittest.TestLoader().loadTestsFromName(test_name, test_class)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    
    result = runner.run(suite)
    output = stream.getvalue()
    stream.close()
    
    return {
        'success': result.wasSuccessful(),
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'output': output,
        'details': [
            {'type': 'failure', 'message': f[1]} for f in result.failures
        ] + [
            {'type': 'error', 'message': e[1]} for e in result.errors
        ]
    }

@ensure_csrf_cookie
@require_http_methods(["POST"])
def run_test_suite(request, test_suite):
    """Execute a test suite and return results."""
    try:
        start_time = time.time()
        logger.info(f"Starting test suite: {test_suite}")
        
        # Parse parameters from request body
        try:
            parameters = json.loads(request.body)
            logger.info(f"Test parameters: {parameters}")
        except json.JSONDecodeError:
            parameters = {}
            logger.warning("No parameters provided or invalid JSON")
        
        # Initialize test result
        result = {
            'success': False,
            'test_output': None,
            'duration': 0,
            'details': []
        }
        
        # Run appropriate test based on test_suite
        if test_suite == 'apple_charts':
            try:
                api = AppleMusicAPI()
                response = api._make_request(
                    'GET',
                    'catalog/us/charts',
                    params={
                        'types': 'songs',
                        'limit': 25
                    }
                )
                result.update({
                    'success': True,
                    'test_output': response
                })
            except Exception as e:
                logger.error(f"Apple Music charts error: {str(e)}")
                result.update({
                    'success': False,
                    'error': str(e)
                })
                
        elif test_suite == 'spotify_auth':
            test_results = run_test_class(TestSpotifyAPI, 'test_get_auth_url')
            result.update(test_results)
            
        elif test_suite == 'spotify_search':
            test_results = run_test_class(TestSpotifyAPI, 'test_search_track_success')
            result.update(test_results)
            
        elif test_suite == 'apple_auth':
            test_results = run_test_class(TestAppleMusicAPI, 'test_developer_token_generation')
            result.update(test_results)
            
        elif test_suite == 'apple_search':
            test_results = run_test_class(TestAppleMusicAPI, 'test_search_track_success')
            result.update(test_results)
            
        elif test_suite == 'track_matching':
            # Run both Spotify and Apple Music search tests
            spotify_results = run_test_class(TestSpotifyAPI, 'test_search_track_success')
            apple_results = run_test_class(TestAppleMusicAPI, 'test_search_track_success')
            
            result.update({
                'success': spotify_results['success'] and apple_results['success'],
                'test_output': {
                    'spotify': spotify_results,
                    'apple_music': apple_results
                }
            })
            
        elif test_suite == 'playlist_creation':
            spotify_results = run_test_class(TestSpotifyAPI, 'test_create_playlist_success')
            apple_results = run_test_class(TestAppleMusicAPI, 'test_create_playlist_success')
            
            result.update({
                'success': spotify_results['success'] and apple_results['success'],
                'test_output': {
                    'spotify': spotify_results,
                    'apple_music': apple_results
                }
            })
            
        elif test_suite == 'playlist_sync':
            # Run playlist sync tests
            spotify_results = run_test_class(TestSpotifyAPI, 'test_get_playlist')
            apple_results = run_test_class(TestAppleMusicAPI, 'test_get_playlist')
            
            result.update({
                'success': spotify_results['success'] and apple_results['success'],
                'test_output': {
                    'spotify': spotify_results,
                    'apple_music': apple_results
                }
            })
            
        elif test_suite == 'token_generation':
            # Run token generation tests
            spotify_results = run_test_class(TestSpotifyAPI, 'test_get_token_from_code')
            apple_results = run_test_class(TestAppleMusicAPI, 'test_developer_token_generation')
            
            result.update({
                'success': spotify_results['success'] and apple_results['success'],
                'test_output': {
                    'spotify': spotify_results,
                    'apple_music': apple_results
                }
            })
            
        else:
            logger.error(f"Unknown test suite: {test_suite}")
            raise ValueError(f"Unknown test suite: {test_suite}")
        
        # Calculate duration
        duration = int((time.time() - start_time) * 1000)
        result['duration'] = duration
        
        logger.info(f"Test completed in {duration}ms")
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error running test: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'duration': int((time.time() - start_time) * 1000)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def apple_charts(request):
    """Fetch Apple Music charts."""
    try:
        logger.info("Starting Apple Music charts request")
        
        # Initialize API
        api = AppleMusicAPI()
        logger.info("AppleMusicAPI instance created")
        
        # Log the request parameters
        params = {
            'types': 'songs',
            'chart': 'most-played',
            'genre': 'all',
            'limit': 25,
            'offset': 0,
            'with': 'artists,albums'
        }
        logger.info(f"Request parameters: {params}")
        
        # Make request to Apple Music API
        logger.info("Making request to Apple Music API...")
        response = api._make_request(
            'GET',
            'catalog/us/charts',
            params=params
        )
        
        # Log the full response for debugging
        logger.info("Received response from Apple Music API")
        logger.debug(f"Full API Response: {json.dumps(response, indent=2)}")
        
        # Return successful response with chart data
        logger.info("Successfully processed charts data")
        return JsonResponse({
            'success': True,
            'test_output': response
        })
        
    except Exception as e:
        logger.error(f"Error fetching Apple Music charts: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def test_spotify(request):
    """Test Spotify API functionality."""
    try:
        spotify = SpotifyAPI()
        # Add test functionality here
        return JsonResponse({
            'success': True,
            'message': 'Spotify API test endpoint'
        })
    except Exception as e:
        logger.error(f"Spotify test error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def test_apple(request):
    """Test Apple Music API functionality."""
    try:
        api = AppleMusicAPI()
        # Add test functionality here
        return JsonResponse({
            'success': True,
            'message': 'Apple Music API test endpoint'
        })
    except Exception as e:
        logger.error(f"Apple Music test error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def test_artwork(request):
    """Test playlist artwork functionality"""
    context = {
        'developer_token': settings.APPLE_MUSIC_DEVELOPER_TOKEN
    }
    return render(request, 'aoede_tests/test_artwork.html', context)
