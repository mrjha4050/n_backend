from django.db import models
from n_backend.app.users.models import BaseModel

class Articles(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey('users.Users', on_delete=models.CASCADE)
    media = models.JSONField(default=list)  # For storing array of media URLs
    category = models.CharField(max_length=255)
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