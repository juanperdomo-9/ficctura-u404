from django.db import migrations
from django.utils.text import slugify


# Pedido del cliente (18/9): "Principiante" queda muy cortado en las
# tarjetas de mobile — vuelve a "Junior" (nombre más corto). Mismo
# criterio que 0021_rename_pack_junior.py: busca por nombre, no rompe
# nada si ya se editó a mano desde el dashboard.
def rename_back_to_junior(apps, schema_editor):
    Pack = apps.get_model('catalog', 'Pack')
    Pack.objects.filter(name='Principiante').update(name='Junior', slug=slugify('Junior'))


def rename_to_principiante(apps, schema_editor):
    Pack = apps.get_model('catalog', 'Pack')
    Pack.objects.filter(name='Junior').update(name='Principiante', slug=slugify('Principiante'))


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0022_alter_product_status'),
    ]

    operations = [
        migrations.RunPython(rename_back_to_junior, rename_to_principiante),
    ]
