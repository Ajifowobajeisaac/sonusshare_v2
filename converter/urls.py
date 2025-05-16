from django.urls import path
from . import views

app_name = 'converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('convert/', views.convert_playlist, name='convert_playlist'),
    path('review/', views.review_playlist, name='review_playlist'),
    path('create-spotify-playlist/', views.create_spotify_playlist, name='create_spotify_playlist'),
    path('create-apple-playlist/', views.create_apple_playlist, name='create_apple_playlist'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('clear-session/', views.clear_session_data, name='clear_session'),
]
