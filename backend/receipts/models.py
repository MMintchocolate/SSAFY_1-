from django.db import models
from django.conf import settings


class ReceiptText(models.Model):
    user              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1, related_name='receipts')
    original_filename = models.CharField(max_length=255, blank=True)
    image             = models.ImageField(upload_to='receipts/', blank=True, null=True)
    text              = models.TextField()
    fields            = models.JSONField(default=list, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.original_filename or "receipt"} ({self.created_at:%Y-%m-%d %H:%M})'
