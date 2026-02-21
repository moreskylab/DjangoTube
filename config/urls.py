from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.home, name='home'),
    path('upload/', views.upload_video, name='upload'),
    path('watch/<int:video_id>/', views.video_detail, name='video_detail'),
    path('like/<int:video_id>/', views.like_video, name='like_video'),
    path('subscribe/<int:channel_id>/', views.subscribe_channel, name='subscribe_channel'),

    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]