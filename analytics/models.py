from django.db import models
from posts.models import Post
from social_accounts.models import SocialAccount

# Create your models here.

class PostAnalytics(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    reach = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['post', 'social_account']
        verbose_name_plural = 'Post analytics'
    
    def __str__(self):
        return f"{self.post.id} - {self.social_account.platform} Analytics"
