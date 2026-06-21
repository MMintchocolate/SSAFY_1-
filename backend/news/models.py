from django.db import models


class News(models.Model):
    keyword = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    content = models.TextField(blank=True)
    summary = models.TextField(blank=True, default='')
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return f'[{self.keyword}] {self.title}'
