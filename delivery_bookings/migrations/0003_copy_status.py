from django.db import migrations


def copy_status(apps, schema_editor):
    Booking = apps.get_model("delivery_bookings", "Booking")
    Booking.objects.using(schema_editor.connection.alias).filter(
        is_cancelled=True
    ).update(status="cancelled")


class Migration(migrations.Migration):
    dependencies = [("delivery_bookings", "0002_add_status")]

    operations = [migrations.RunPython(copy_status, migrations.RunPython.noop)]
