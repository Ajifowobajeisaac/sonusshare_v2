from django.urls import path
from . import views

app_name = 'aoede_tests'

urlpatterns = [
    # Test Directory Home
    path('', views.test_home, name='home'),
    
    # Test Categories
    path('search/', views.test_search, name='search'),
    path('playlist/', views.test_playlist_creation, name='playlist'),
    path('track-matching/', views.test_track_matching, name='track_matching'),
    path('playback/', views.test_playback, name='playback'),
    path('artwork/', views.test_artwork, name='artwork'),
    
    # Authentication Tests
    path('auth/', views.test_auth, name='auth'),
    path('callback/spotify/', views.test_spotify_callback, name='spotify_callback'),
    
    # Token Management
    path('token/', views.test_token, name='token'),
    
    # Test Execution
    path('run-test/<str:test_suite>/', views.run_test_suite, name='run_test_suite'),
    path('run-test/spotify/', views.test_spotify, name='test_spotify'),
    path('run-test/apple/', views.test_apple, name='test_apple'),
    path('run-test/apple_charts/', views.apple_charts, name='apple_charts'),
]
