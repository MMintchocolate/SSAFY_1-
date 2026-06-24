from django.db import models


class FinancialProductCache(models.Model):
    DEPOSIT = 'deposit'
    SAVINGS = 'savings'
    TYPE_CHOICES = [(DEPOSIT, '정기예금'), (SAVINGS, '적금')]

    product_type = models.CharField(max_length=10, choices=TYPE_CHOICES, unique=True)
    data         = models.JSONField(default=list)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '금융상품 캐시'

    def __str__(self):
        return f'{self.get_product_type_display()} ({self.updated_at:%Y-%m-%d %H:%M})'
