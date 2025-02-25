from django.contrib import admin
from .models import PostAnalytics

@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('post', 'social_account', 'likes', 'comments', 'shares', 'engagement_rate', 'updated_at')
    list_filter = ('social_account__platform', 'created_at')
    search_fields = ('post__content', 'social_account__account_name')
