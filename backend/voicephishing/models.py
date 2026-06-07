from django.db import models


class PhishingAnalysis(models.Model):
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # 'audio' | 'text'
    transcript = models.TextField(blank=True, default='')
    probability = models.FloatField()  # 0.0 ~ 1.0
    label = models.CharField(max_length=50)   # '안전' | '의심' | '위험'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '보이스피싱 분석 내역'

    def __str__(self):
        return f'[{self.label}] {self.original_filename} ({self.probability:.1%})'
