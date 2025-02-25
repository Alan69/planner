from django.contrib import admin
from .models import Post, MediaAttachment

class MediaAttachmentInline(admin.TabularInline):
    model = MediaAttachment
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'scheduled_time', 'created_at', 'published_at')
    list_filter = ('status', 'created_at', 'scheduled_time')
    search_fields = ('user__username', 'content')
    inlines = [MediaAttachmentInline]
    filter_horizontal = ('social_accounts',)

@admin.register(MediaAttachment)
class MediaAttachmentAdmin(admin.ModelAdmin):
    list_display = ('post', 'media_type', 'created_at')
    list_filter = ('media_type', 'created_at')
