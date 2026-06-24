from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='FinancialProductCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('deposit', '정기예금'), ('savings', '적금')], max_length=10, unique=True)),
                ('data', models.JSONField(default=list)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '금융상품 캐시',
            },
        ),
    ]
