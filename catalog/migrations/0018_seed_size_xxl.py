from django.db import migrations


# Los talles (S/M/L/XL...) nunca se sembraron por migración — se
# cargaron a mano en el dev local (shell/admin), así que en una base
# nueva (Render, Postgres vacía) no existe NINGUNO todavía. Esta
# migración solo agrega XXL (pedido del cliente, 28/8) sin tocar los
# que ya existan en cada entorno — get_or_create no pisa nada si el
# talle ya está.
def add_xxl(apps, schema_editor):
    Size = apps.get_model('catalog', 'Size')
    Size.objects.get_or_create(name='XXL', defaults={'order': 4})


def remove_xxl(apps, schema_editor):
    Size = apps.get_model('catalog', 'Size')
    Size.objects.filter(name='XXL').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0017_productimage_color_productvariant_hex_color'),
    ]

    operations = [
        migrations.RunPython(add_xxl, remove_xxl),
    ]
