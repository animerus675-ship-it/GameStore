from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="cover",
            field=models.ImageField(blank=True, null=True, upload_to="games/covers/"),
        ),
    ]
