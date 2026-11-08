from django.db import migrations


def populate_slugs(apps, schema_editor):
    Route = apps.get_model("delivery_routes", "Route")
    routes = Route.objects.using(schema_editor.connection.alias)
    for route in routes.filter(slug__isnull=True).iterator():
        routes.filter(pk=route.pk).update(slug=f"marshrut-{route.pk}")


class Migration(migrations.Migration):
    dependencies = [("delivery_routes", "0002_alter_route_options_alter_routeorder_options_and_more")]

    operations = [migrations.RunPython(populate_slugs, migrations.RunPython.noop)]
