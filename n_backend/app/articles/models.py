from django.db import models
from n_backend.app.users.models import BaseModel

class Articles(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey('users.Users', on_delete=models.CASCADE)
    media = models.JSONField(default=list, null=True, blank=True)  # For storing array of media URLs
    category = models.CharField(max_length=255, null=True, blank=True)
    published = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('deleted', 'Deleted')
        ],
        default='draft'
    )

    class Meta:
        db_table = 'articles'

    def __str__(self):
        return self.title

    @property
    def likes_count(self):
        """Returns the number of likes for this article"""
        return self.interactions.filter(liked=True).count()

    @property
    def comments_count(self):
        """Returns the number of comments for this article"""
        return self.interactions.exclude(comment__isnull=True).exclude(comment='').count()

    def extract_cloudinary_public_ids(self):
        """Extract Cloudinary public IDs from media URLs for cleanup"""
        public_ids = []
        for media_url in self.media:
            if 'cloudinary.com' in media_url:
                # Extract public ID from Cloudinary URL
                parts = media_url.split('/')
                if 'image/upload' in parts:
                    upload_index = parts.index('image/upload')
                    if len(parts) > upload_index + 1:
                        public_id_with_format = parts[upload_index + 1]
                        public_id = public_id_with_format.split('.')[0]  # Remove file extension
                        public_ids.append(public_id)
        return public_ids


class ArticleInteraction(BaseModel):
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    user = models.ForeignKey(
        'users.Users',
        on_delete=models.CASCADE,
        related_name='article_interactions'
    )
    comment = models.TextField(null=True, blank=True)
    liked = models.BooleanField(default=False)
    saved = models.BooleanField(default=False)

    class Meta:
        db_table = 'article_interactions'
        unique_together = ['article', 'user']

    def __str__(self):
        return f"Interaction by {self.user} on {self.article}"