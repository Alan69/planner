from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from posts.models import Post

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        # Handle profile update
        subscription_plan = request.POST.get('subscription_plan')
        if subscription_plan in dict(UserProfile.SUBSCRIPTION_CHOICES):
            request.user.userprofile.subscription_plan = subscription_plan
            request.user.userprofile.save()
            messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    # Get published posts count
    published_posts = Post.objects.filter(user=request.user, status='published').count()
    
    context = {
        'published_posts': published_posts,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def dashboard(request):
    # Get post counts
    scheduled_posts = Post.objects.filter(user=request.user, status='scheduled').count()
    published_posts = Post.objects.filter(user=request.user, status='published').count()
    recent_posts = Post.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'scheduled_posts': scheduled_posts,
        'published_posts': published_posts,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'accounts/dashboard.html', context)

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
    return redirect('dashboard')
