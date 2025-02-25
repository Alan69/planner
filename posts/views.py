from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import get_current_timezone

from posts.tasks import post_to_linkedin
from .models import Post, MediaAttachment
from social_accounts.models import SocialAccount

@login_required
def post_list(request):
    posts = Post.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'posts/post_list.html', {'posts': posts})

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    return render(request, 'posts/post_detail.html', {'post': post})

@login_required
def post_create(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        scheduled_time = request.POST.get('scheduled_time')
        social_account_ids = request.POST.getlist('social_accounts')
        action = request.POST.get('action', 'schedule')
        
        if content and social_account_ids:
            try:
                current_tz = get_current_timezone()
                current_time = timezone.now().astimezone(current_tz)
                
                # Set the status and scheduled time based on the action
                if action == 'post_now':
                    status = 'published'
                    scheduled_time = current_time
                else:
                    if not scheduled_time:
                        messages.error(request, 'Please specify a schedule time')
                        social_accounts = SocialAccount.objects.filter(user=request.user, is_active=True)
                        return render(request, 'posts/post_create.html', {'social_accounts': social_accounts})
                    status = 'scheduled'
                
                post = Post.objects.create(
                    user=request.user,
                    content=content,
                    scheduled_time=scheduled_time,
                    status=status,
                    published_at=current_time if status == 'published' else None
                )
                
                # Add selected social accounts
                social_accounts = SocialAccount.objects.filter(
                    id__in=social_account_ids,
                    user=request.user
                )
                post.social_accounts.set(social_accounts)
                
                # Handle media attachments
                for file in request.FILES.getlist('media'):
                    media_type = 'video' if file.content_type.startswith('video') else 'image'
                    MediaAttachment.objects.create(
                        post=post,
                        file=file,
                        media_type=media_type
                    )
                
                # If posting now, trigger the publishing process immediately
                if action == 'post_now':
                    try:
                        for social_account in social_accounts:
                            if social_account.platform == 'linkedin':
                                # Call the task synchronously for immediate posting
                                try:
                                    print(f"Attempting to post to LinkedIn for post {post.id}")
                                    result = post_to_linkedin.apply(args=[post.id, social_account.id])
                                    if not result.successful():
                                        print(f"Task failed: {result.result}")
                                        raise Exception(f"LinkedIn posting task failed: {result.result}")
                                    print("LinkedIn posting task completed successfully")
                                except Exception as e:
                                    print(f"Error in LinkedIn posting: {str(e)}")
                                    raise Exception(f"LinkedIn posting failed: {str(e)}")
                            elif social_account.platform == 'twitter':
                                # Implement Twitter posting
                                pass
                            elif social_account.platform == 'instagram':
                                # Implement Instagram posting
                                pass
                        messages.success(request, 'Post published successfully!')
                    except Exception as e:
                        post.status = 'failed'
                        post.save()
                        messages.error(request, f'Error publishing post: {str(e)}')
                else:
                    messages.success(request, 'Post scheduled successfully!')
                
                return redirect('post_detail', post_id=post.id)
            except Exception as e:
                messages.error(request, f'Error creating post: {str(e)}')
        else:
            messages.error(request, 'Please fill all required fields')
    
    social_accounts = SocialAccount.objects.filter(user=request.user, is_active=True)
    return render(request, 'posts/post_create.html', {'social_accounts': social_accounts})

@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    
    if post.status == 'published':
        messages.error(request, 'Cannot edit published posts')
        return redirect('post_detail', post_id=post.id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        scheduled_time = request.POST.get('scheduled_time')
        social_account_ids = request.POST.getlist('social_accounts')
        
        if content and scheduled_time and social_account_ids:
            try:
                post.content = content
                post.scheduled_time = scheduled_time
                post.save()
                
                # Update selected social accounts
                social_accounts = SocialAccount.objects.filter(
                    id__in=social_account_ids,
                    user=request.user
                )
                post.social_accounts.set(social_accounts)
                
                # Handle new media attachments
                for file in request.FILES.getlist('media'):
                    media_type = 'video' if file.content_type.startswith('video') else 'image'
                    MediaAttachment.objects.create(
                        post=post,
                        file=file,
                        media_type=media_type
                    )
                
                messages.success(request, 'Post updated successfully!')
                return redirect('post_detail', post_id=post.id)
            except Exception as e:
                messages.error(request, f'Error updating post: {str(e)}')
        else:
            messages.error(request, 'Please fill all required fields')
    
    social_accounts = SocialAccount.objects.filter(user=request.user, is_active=True)
    return render(request, 'posts/post_edit.html', {
        'post': post,
        'social_accounts': social_accounts
    })

@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('post_list')
    
    return render(request, 'posts/post_delete.html', {'post': post})
