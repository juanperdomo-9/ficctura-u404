from django.db import migrations
from django.utils.text import slugify


# Pedido del cliente (11/9): el pack "Junior" pasa a llamarse
# "Principiante" — mismo pack, mismo slug nuevo generado a partir del
# nombre nuevo (no se toca ninguna otra columna). Se busca por el
# nombre VIEJO (no por slug, más robusto si alguien ya lo tocó a mano
# desde el dashboard) y no rompe nada si ya no existe (idempotente).
def rename_junior(apps, schema_editor):
    Pack = apps.get_model('catalog', 'Pack')
    Pack.objects.filter(name='Junior').update(name='Principiante', slug=slugify('Principiante'))


def rename_back(apps, schema_editor):
    Pack = apps.get_model('catalog', 'Pack')
    Pack.objects.filter(name='Principiante').update(name='Junior', slug=slugify('Junior'))


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0020_seed_packs'),
    ]

    operations = [
        migrations.RunPython(rename_junior, rename_back),
    ]
