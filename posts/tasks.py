from celery import shared_task
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from .models import Post
from social_accounts.models import SocialAccount
import requests
import json
import jwt

@shared_task
def post_to_linkedin(post_id, social_account_id):
    """
    Post content to LinkedIn using UGC Posts API
    """
    try:
        # Get the post and social account objects
        post = Post.objects.get(id=post_id)
        social_account = SocialAccount.objects.get(id=social_account_id)
        
        print(f"Starting LinkedIn post for post_id: {post_id}, account_id: {social_account_id}")
        print(f"Using access token: {social_account.access_token[:20]}...")
        
        headers = {
            'Authorization': f'Bearer {social_account.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
        }
        
        # Get user's LinkedIn URN from the ID token
        # The sub claim in the ID token is the LinkedIn member ID
        try:
            decoded = jwt.decode(social_account.access_token, options={"verify_signature": False})
            author = f"urn:li:person:{decoded['sub']}"
        except Exception as e:
            print(f"Error decoding ID token: {str(e)}")
            author = f"urn:li:person:{social_account.account_id}"  # Fallback to stored account_id
        
        print(f"Author URN: {author}")
        
        # Prepare post content
        post_data = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post.content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # If post has media attachments
        if post.media_attachments.exists():
            media = post.media_attachments.first()
            if media.media_type == 'image':
                print(f"Processing image attachment: {media.file.path}")
                # Register upload first
                register_upload_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
                register_data = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "owner": author,
                        "serviceRelationships": [{
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }]
                    }
                }
                print("Registering upload with LinkedIn...")
                upload_response = requests.post(register_upload_url, headers=headers, json=register_data)
                print(f"Upload registration response status: {upload_response.status_code}")
                print(f"Upload registration response: {upload_response.text}")
                
                if upload_response.status_code != 200:
                    raise Exception(f"Failed to register upload: {upload_response.text}")
                
                upload_data = upload_response.json()
                
                # Upload the image
                asset_url = upload_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                print(f"Uploading image to: {asset_url}")
                with open(media.file.path, 'rb') as image_file:
                    upload_image_response = requests.put(asset_url, data=image_file, headers={'Authorization': headers['Authorization']})
                    print(f"Image upload response status: {upload_image_response.status_code}")
                    if upload_image_response.status_code != 201:
                        print(f"Image upload response: {upload_image_response.text}")
                        raise Exception(f"Failed to upload image: {upload_image_response.text}")
                
                # Update post data with image
                post_data['specificContent']['com.linkedin.ugc.ShareContent'].update({
                    'shareMediaCategory': 'IMAGE',
                    'media': [{
                        'status': 'READY',
                        'media': upload_data['value']['asset'],
                        'title': {
                            'text': 'Image'
                        }
                    }]
                })
        
        # Post to LinkedIn
        post_url = 'https://api.linkedin.com/v2/ugcPosts'
        print(f"Posting to LinkedIn: {post_url}")
        print(f"Post data: {json.dumps(post_data, indent=2)}")
        response = requests.post(post_url, headers=headers, json=post_data)
        print(f"Post response status: {response.status_code}")
        print(f"Post response content: {response.text}")
        
        if response.status_code != 201:
            raise Exception(f"LinkedIn API error: {response.text}")
        
        # Update post status on success
        current_time = timezone.now().astimezone(get_current_timezone())
        post.status = 'published'
        post.published_at = current_time
        post.save()
        print("Post successfully published to LinkedIn")
        
        return True
        
    except Exception as e:
        # Update post status on failure
        post.status = 'failed'
        post.save()
        print(f"Error in post_to_linkedin: {str(e)}")
        raise Exception(f"LinkedIn posting failed: {str(e)}")

@shared_task
def publish_scheduled_posts():
    """
    Task to check and publish scheduled posts
    """
    current_time = timezone.now().astimezone(get_current_timezone())
    scheduled_posts = Post.objects.filter(
        status='scheduled',
        scheduled_time__lte=current_time
    )
    
    for post in scheduled_posts:
        try:
            # Here we'll implement the actual posting logic for each platform
            for social_account in post.social_accounts.all():
                if social_account.platform == 'linkedin':
                    post_to_linkedin.delay(post.id, social_account.id)
                elif social_account.platform == 'twitter':
                    # Implement Twitter posting
                    pass
                elif social_account.platform == 'instagram':
                    # Implement Instagram posting
                    pass
            
        except Exception as e:
            post.status = 'failed'
            post.save()
            # Log the error
            print(f"Error publishing post {post.id}: {str(e)}")

@shared_task
def update_post_analytics():
    """
    Task to update analytics for published posts
    """
    try:
        # Get all published posts with LinkedIn accounts
        published_posts = Post.objects.filter(
            status='published',
            social_accounts__platform='linkedin'
        ).distinct()
        
        for post in published_posts:
            try:
                # Get LinkedIn social accounts for this post
                linkedin_accounts = post.social_accounts.filter(platform='linkedin')
                
                for social_account in linkedin_accounts:
                    print(f"Fetching analytics for post {post.id} on LinkedIn account {social_account.id}")
                    
                    headers = {
                        'Authorization': f'Bearer {social_account.access_token}',
                        'Content-Type': 'application/json',
                        'X-Restli-Protocol-Version': '2.0.0',
                    }
                    
                    # Get social actions (likes, comments, shares)
                    social_metrics_url = f'https://api.linkedin.com/v2/socialActions/{post.id}'
                    print(f"Fetching social metrics from: {social_metrics_url}")
                    
                    metrics_response = requests.get(social_metrics_url, headers=headers)
                    print(f"Metrics response status: {metrics_response.status_code}")
                    print(f"Metrics response content: {metrics_response.text}")
                    
                    if metrics_response.status_code == 200:
                        metrics_data = metrics_response.json()
                        
                        # Extract metrics
                        likes = metrics_data.get('likesSummary', {}).get('totalLikes', 0)
                        comments = metrics_data.get('commentsSummary', {}).get('totalComments', 0)
                        shares = metrics_data.get('sharesSummary', {}).get('totalShares', 0)
                        
                        # Calculate engagement rate (likes + comments + shares / total impressions * 100)
                        total_engagement = likes + comments + shares
                        impressions = metrics_data.get('impressionsSummary', {}).get('totalImpressions', 0)
                        engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0
                        
                        # Update or create analytics record
                        from analytics.models import PostAnalytics
                        analytics, created = PostAnalytics.objects.update_or_create(
                            post=post,
                            social_account=social_account,
                            defaults={
                                'likes': likes,
                                'comments': comments,
                                'shares': shares,
                                'impressions': impressions,
                                'engagement_rate': engagement_rate,
                            }
                        )
                        
                        print(f"Analytics {'created' if created else 'updated'} for post {post.id}")
                    else:
                        print(f"Failed to fetch metrics for post {post.id}: {metrics_response.text}")
                        
            except Exception as e:
                print(f"Error updating analytics for post {post.id}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error in update_post_analytics task: {str(e)}")
        raise e

# Schedule analytics updates
from celery.schedules import crontab
from celery import current_app

# Update analytics every hour
current_app.conf.beat_schedule = {
    'update-post-analytics': {
        'task': 'posts.tasks.update_post_analytics',
        'schedule': crontab(minute=0),  # Run at the start of every hour
    },
} 