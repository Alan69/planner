from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from posts.models import Post

# Create your views here.

@login_required
def calendar_view(request):
    # Get the current year and month
    today = timezone.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Get the number of days in the month
    _, num_days = monthrange(year, month)
    
    # Create calendar data structure
    first_day = timezone.datetime(year, month, 1)
    last_day = timezone.datetime(year, month, num_days)
    
    # Get all scheduled posts for this month
    posts = Post.objects.filter(
        user=request.user,
        scheduled_time__year=year,
        scheduled_time__month=month
    ).order_by('scheduled_time')
    
    # Create calendar weeks
    calendar_data = []
    week = []
    
    # Add empty slots for days before the first day of the month
    first_weekday = first_day.weekday()  # Monday is 0
    for _ in range(first_weekday):
        week.append({'day': None, 'posts': []})
    
    # Fill in the days of the month
    for day in range(1, num_days + 1):
        current_date = timezone.datetime(year, month, day)
        day_posts = [post for post in posts if post.scheduled_time.date() == current_date.date()]
        
        week.append({
            'day': day,
            'today': current_date.date() == today.date(),
            'posts': day_posts
        })
        
        if len(week) == 7:
            calendar_data.append(week)
            week = []
    
    # Add empty slots for remaining days
    if week:
        while len(week) < 7:
            week.append({'day': None, 'posts': []})
        calendar_data.append(week)
    
    # Get previous and next month links
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
        
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    context = {
        'calendar': calendar_data,
        'current_month': first_day.strftime('%B %Y'),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'year': year,
        'month': month,
    }
    
    return render(request, 'content_plan/calendar.html', context)
