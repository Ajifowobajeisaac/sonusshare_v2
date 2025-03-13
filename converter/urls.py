from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('convert_playlist/', views.convert_playlist, name='convert_playlist'),
    path('review_playlist/', views.review_playlist, name='review_playlist'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('create_playlist/', views.create_playlist, name='create_playlist'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
]
