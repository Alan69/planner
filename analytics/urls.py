from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics'),
    path('post/<int:post_id>/', views.post_analytics, name='post_analytics'),
] 