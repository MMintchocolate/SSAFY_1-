from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PortfolioItem(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    symbol    = models.CharField(max_length=20)   # e.g. 005930.KS
    name      = models.CharField(max_length=100)  # e.g. 삼성전자
    quantity  = models.DecimalField(max_digits=12, decimal_places=4)
    avg_price = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'symbol')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.name} ({self.symbol})'
