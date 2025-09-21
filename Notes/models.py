import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import bleach


def validate_file_size(value):
    """Validate file size is under 5MB"""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("Maximum file size is 5MB")


def user_directory_path(instance, filename):
    """Upload files to MEDIA_ROOT/user_<id>/<filename>"""
    return f'user_{instance.note.user.id}/{filename}'


class Category(models.Model):
    """Categories for organizing notes, user-specific"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('name', 'user')  # User can't have duplicate category names

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Template(models.Model):
    """Note templates for reusable content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()  # HTML content
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'user')  # User can't have duplicate template names

    def save(self, *args, **kwargs):
        # Sanitize HTML content before saving
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'div', 'span'
        ]
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'div': ['class'],
            'span': ['class']
        }
        self.content = bleach.clean(
            self.content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Note(models.Model):
    """Main Note model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()  # HTML content
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        # Sanitize HTML content before saving
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'div', 'span'
        ]
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'div': ['class'],
            'span': ['class']
        }
        self.content = bleach.clean(
            self.content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        # Create version history if this is an update
        is_update = self.pk is not None
        if is_update:
            # Get the old content before saving
            try:
                old_note = Note.objects.get(pk=self.pk)
                if old_note.content != self.content:
                    # Create version before updating
                    NoteVersion.objects.create(
                        note=self,
                        content=old_note.content
                    )
            except Note.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Note {str(self.id)[:8]}"


class NoteVersion(models.Model):
    """Version history for notes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()  # HTML content
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Version of {self.note} at {self.created_at}"


class NoteShare(models.Model):
    """Sharing permissions for notes"""
    PERMISSION_CHOICES = [
        ('READ', 'Read Only'),
        ('EDIT', 'Read and Edit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_notes')
    permission = models.CharField(max_length=4, choices=PERMISSION_CHOICES, default='READ')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('note', 'shared_with')  # Can't share same note with same user twice

    def __str__(self):
        return f"{self.note} shared with {self.shared_with.username} ({self.permission})"


class NoteFile(models.Model):
    """File attachments for notes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(
        upload_to=user_directory_path,
        validators=[
            validate_file_size,
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'svg', 'pdf'])
        ]
    )
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename} - {self.note}"