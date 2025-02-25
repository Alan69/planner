from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from .models import SocialAccount
import requests
import json
import urllib.parse
import base64

# Create your views here.

@login_required
def linkedin_connect(request):
    """
    Initiate LinkedIn OAuth2 flow
    """
    params = {
        'response_type': 'code',
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
        'scope': settings.LINKEDIN_SCOPE,
        'state': request.session.session_key,
    }
    
    authorize_url = 'https://www.linkedin.com/oauth/v2/authorization?' + urllib.parse.urlencode(params)
    return redirect(authorize_url)

@login_required
def linkedin_callback(request):
    """
    Handle LinkedIn OAuth2 callback
    """
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code or state != request.session.session_key:
        messages.error(request, 'LinkedIn authentication failed.')
        return redirect('social_accounts')
    
    # Exchange code for access token
    token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
    token_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'client_secret': settings.LINKEDIN_CLIENT_SECRET,
        'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
    }
    
    try:
        print("Requesting access token with params:", token_params)  # Debug log
        token_response = requests.post(token_url, data=token_params)
        print("Token response status:", token_response.status_code)  # Debug log
        print("Token response content:", token_response.text)  # Debug log
        
        token_data = token_response.json()
        
        if 'access_token' not in token_data or 'id_token' not in token_data:
            messages.error(request, f'Failed to obtain LinkedIn tokens. Error: {token_data.get("error_description", "Unknown error")}')
            return redirect('social_accounts')
        
        # Parse the ID token to get user information
        id_token = token_data['id_token']
        # The ID token is a JWT with three parts: header.payload.signature
        # We only need the payload part which is the second part
        payload = id_token.split('.')[1]
        # Add padding if needed
        payload += '=' * (-len(payload) % 4)
        # Decode the base64 payload
        profile_data = json.loads(base64.b64decode(payload).decode('utf-8'))
        
        print("Profile data from ID token:", profile_data)  # Debug log
        
        # Create or update social account
        account, created = SocialAccount.objects.update_or_create(
            user=request.user,
            platform='linkedin',
            account_id=profile_data['sub'],  # Use 'sub' claim as the unique identifier
            defaults={
                'account_name': f"{profile_data.get('given_name', '')} {profile_data.get('family_name', '')}",
                'access_token': token_data['access_token'],
                'token_expires_at': None,  # LinkedIn tokens don't expire by default
                'is_active': True,
            }
        )
        
        if created:
            messages.success(request, 'LinkedIn account connected successfully!')
        else:
            messages.success(request, 'LinkedIn account updated successfully!')
            
    except Exception as e:
        print("Error in LinkedIn callback:", str(e))  # Debug log
        messages.error(request, f'Error connecting LinkedIn account: {str(e)}')
    
    return redirect('social_accounts')

@login_required
def social_account_list(request):
    accounts = SocialAccount.objects.filter(user=request.user)
    platform_choices = dict(SocialAccount.PLATFORM_CHOICES)
    
    context = {
        'accounts': accounts,
        'platform_choices': platform_choices,
    }
    return render(request, 'social_accounts/account_list.html', {'accounts': accounts})

@login_required
def social_account_connect(request, platform):
    if platform not in dict(SocialAccount.PLATFORM_CHOICES):
        messages.error(request, 'Invalid platform')
        return redirect('social_accounts')
    
    if platform == 'linkedin':
        return linkedin_connect(request)
    elif platform == 'twitter':
        # Implement Twitter OAuth
        pass
    elif platform == 'instagram':
        # Implement Instagram OAuth
        pass
    
    return redirect('social_accounts')

@login_required
def social_account_disconnect(request, account_id):
    account = get_object_or_404(SocialAccount, id=account_id, user=request.user)
    account.delete()
    messages.success(request, f'Successfully disconnected {account.platform} account')
    return redirect('social_accounts')
