from django.db import migrations


def copy_status(apps, schema_editor):
    # Историческая модель отражает схему на этом шаге миграций: есть оба поля.
    Booking = apps.get_model("delivery_bookings", "Booking")
    # Старое True переводим в cancelled до удаления is_cancelled.
    Booking.objects.using(schema_editor.connection.alias).filter(
        is_cancelled=True
    ).update(status="cancelled")


class Migration(migrations.Migration):
    dependencies = [("delivery_bookings", "0002_add_status")]

    # Обратное преобразование не требуется: noop оставляет данные как есть.
    operations = [migrations.RunPython(copy_status, migrations.RunPython.noop)]
