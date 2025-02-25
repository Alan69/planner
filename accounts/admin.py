from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'is_verified', 'created_at')
    list_filter = ('subscription_plan', 'is_verified')
    search_fields = ('user__username', 'user__email')
