import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_game_cover"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="discount_percent",
            field=models.PositiveIntegerField(
                default=0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(90),
                ],
            ),
        ),
    ]
