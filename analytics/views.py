from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from posts.models import Post
from .models import PostAnalytics
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta

# Create your views here.

@login_required
def analytics_dashboard(request):
    # Get user's posts with analytics
    posts_with_analytics = Post.objects.filter(
        user=request.user,
        status='published'
    ).prefetch_related('postanalytics_set', 'social_accounts')
    
    # Calculate total engagement
    total_likes = 0
    total_comments = 0
    total_shares = 0
    total_impressions = 0
    avg_engagement_rate = 0
    
    # Get analytics for different time periods
    now = timezone.now()
    last_24h = now - timedelta(days=1)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    analytics_24h = PostAnalytics.objects.filter(
        post__user=request.user,
        post__published_at__gte=last_24h
    ).aggregate(
        likes=Sum('likes'),
        comments=Sum('comments'),
        shares=Sum('shares'),
        impressions=Sum('impressions'),
        engagement_rate=Avg('engagement_rate')
    )
    
    analytics_7d = PostAnalytics.objects.filter(
        post__user=request.user,
        post__published_at__gte=last_7d
    ).aggregate(
        likes=Sum('likes'),
        comments=Sum('comments'),
        shares=Sum('shares'),
        impressions=Sum('impressions'),
        engagement_rate=Avg('engagement_rate')
    )
    
    analytics_30d = PostAnalytics.objects.filter(
        post__user=request.user,
        post__published_at__gte=last_30d
    ).aggregate(
        likes=Sum('likes'),
        comments=Sum('comments'),
        shares=Sum('shares'),
        impressions=Sum('impressions'),
        engagement_rate=Avg('engagement_rate')
    )
    
    # Calculate platform-specific analytics
    linkedin_analytics = PostAnalytics.objects.filter(
        post__user=request.user,
        social_account__platform='linkedin'
    ).aggregate(
        likes=Sum('likes'),
        comments=Sum('comments'),
        shares=Sum('shares'),
        impressions=Sum('impressions'),
        engagement_rate=Avg('engagement_rate')
    )
    
    for post in posts_with_analytics:
        for analytics in post.postanalytics_set.all():
            total_likes += analytics.likes
            total_comments += analytics.comments
            total_shares += analytics.shares
            total_impressions += analytics.impressions
    
    if posts_with_analytics:
        avg_engagement_rate = (total_likes + total_comments + total_shares) / total_impressions * 100 if total_impressions > 0 else 0
    
    context = {
        'posts': posts_with_analytics,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_impressions': total_impressions,
        'avg_engagement_rate': avg_engagement_rate,
        'analytics_24h': analytics_24h,
        'analytics_7d': analytics_7d,
        'analytics_30d': analytics_30d,
        'linkedin_analytics': linkedin_analytics,
        'total_posts': posts_with_analytics.count(),
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
def post_analytics(request, post_id):
    # Get analytics for a specific post
    post = Post.objects.get(id=post_id, user=request.user)
    analytics = post.postanalytics_set.all().select_related('social_account')
    
    # Calculate total engagement for this post
    total_likes = sum(a.likes for a in analytics)
    total_comments = sum(a.comments for a in analytics)
    total_shares = sum(a.shares for a in analytics)
    total_impressions = sum(a.impressions for a in analytics)
    avg_engagement_rate = sum(a.engagement_rate for a in analytics) / len(analytics) if analytics else 0
    
    context = {
        'post': post,
        'analytics': analytics,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_impressions': total_impressions,
        'avg_engagement_rate': avg_engagement_rate,
    }
    
    return render(request, 'analytics/post_analytics.html', context)
