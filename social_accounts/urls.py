from django.urls import path
from . import views

urlpatterns = [
    path('', views.social_account_list, name='social_accounts'),
    path('connect/<str:platform>/', views.social_account_connect, name='social_account_connect'),
    path('disconnect/<int:account_id>/', views.social_account_disconnect, name='social_account_disconnect'),
    path('linkedin/callback/', views.linkedin_callback, name='linkedin_callback'),
] 