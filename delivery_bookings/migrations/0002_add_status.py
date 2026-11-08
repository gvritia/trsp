from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("delivery_bookings", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Действует"),
                    ("cancelled", "Отменено"),
                    ("completed", "Завершено"),
                ],
                default="active",
                max_length=10,
                verbose_name="статус",
            ),
        ),
    ]
