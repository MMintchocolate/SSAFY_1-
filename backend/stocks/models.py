from django.db import models
from django.conf import settings


class UserPredictionCache(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='predictions')
    symbol       = models.CharField(max_length=30)
    signal       = models.IntegerField()
    signal_label = models.CharField(max_length=20)
    prob_hold    = models.FloatField(default=0)
    prob_buy     = models.FloatField(default=0)
    prob_sell    = models.FloatField(default=0)
    latest_date  = models.CharField(max_length=20, blank=True)
    predicted_at = models.DateTimeField(auto_now=True)
    explanation  = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'symbol')
        ordering = ['-predicted_at']

    def __str__(self):
        return f'{self.user} - {self.symbol} → {self.signal_label}'


class WatchlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist',
    )
    symbol = models.CharField(max_length=30)
    name = models.CharField(max_length=200, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'symbol')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user} - {self.symbol}'
