from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('detect_choice/', views.detect_choice_view, name='detect_choice'),
    path('detect/live/', views.live_detect_view, name='live_detect'),
    path('detect/image/', views.image_detect_view, name='image_detect'),
    path('detect/video/', views.video_detect_view, name='video_detect'),
    path('result/', views.result_view, name='result'),
    path('logout/', views.logout_view, name='logout'),
]
