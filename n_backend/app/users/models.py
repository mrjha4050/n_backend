from djongo import models
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Users(BaseModel):
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=255, choices=[('reader', 'Reader'), ('journalist', 'Journalist'), ('user', 'User')])
    profileUrl = models.CharField(max_length=255, blank=True, default='', null=True)
    pdfUrl = models.CharField(max_length=255, blank=True, default='', null=True)

    class Meta:
        db_table = 'users'


    def __str__(self):
        return f"{self.username} ({self.email})"

    def clean(self):
        super().clean()
        if not self.email:
            raise ValidationError("Email is required")
        
        if not self.username:
            raise ValidationError("Username is required")
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        """
        Check if the provided raw password matches the hashed password
        """
        return check_password(raw_password, self.password)