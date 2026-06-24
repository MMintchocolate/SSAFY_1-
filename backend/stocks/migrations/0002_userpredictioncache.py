import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPredictionCache',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol',       models.CharField(max_length=30)),
                ('signal',       models.IntegerField()),
                ('signal_label', models.CharField(max_length=20)),
                ('prob_hold',    models.FloatField(default=0)),
                ('prob_buy',     models.FloatField(default=0)),
                ('prob_sell',    models.FloatField(default=0)),
                ('latest_date',  models.CharField(blank=True, max_length=20)),
                ('predicted_at', models.DateTimeField(auto_now=True)),
                ('explanation',  models.TextField(blank=True)),
                ('user',         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-predicted_at'],
                'unique_together': {('user', 'symbol')},
            },
        ),
    ]
