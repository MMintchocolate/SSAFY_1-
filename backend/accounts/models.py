from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname            = models.CharField(max_length=30, unique=True, blank=True)
    cluster_eps         = models.FloatField(default=0.45)
    cluster_min_samples = models.IntegerField(default=6)

    def save(self, *args, **kwargs):
        if not self.nickname:
            self.nickname = self.username
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nickname or self.username
