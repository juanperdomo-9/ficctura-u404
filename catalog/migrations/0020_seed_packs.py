from django.db import migrations


# Los 4 packs que pidió el cliente (29/8) — nombre, composición y
# beneficios tal cual los mandó. get_or_create por nombre: no pisa nada
# si ya se cargaron/editaron a mano desde el admin.
PACKS = [
    dict(
        name='Junior', order=1,
        tagline='Vas bien pero recién estás arrancando',
        ficctura_negro_qty=1, ficctura_blanco_qty=1, u404_qty=1,
        discount_percent=0, free_shipping=True, bonus_basica_qty=0,
    ),
    dict(
        name='Senior', order=2,
        tagline='Ya estás algo experimentado pero falta',
        ficctura_negro_qty=2, ficctura_blanco_qty=2, u404_qty=2,
        discount_percent=10, free_shipping=True, bonus_basica_qty=0,
    ),
    dict(
        name='Team Leader', order=3,
        tagline='Escalando como un campeón',
        ficctura_negro_qty=2, ficctura_blanco_qty=2, u404_qty=4,
        discount_percent=15, free_shipping=True, bonus_basica_qty=0,
    ),
    dict(
        name='CEO', order=4,
        tagline='Sos el jefe',
        ficctura_negro_qty=4, ficctura_blanco_qty=4, u404_qty=4,
        discount_percent=15, free_shipping=True, bonus_basica_qty=1,
    ),
]


def add_packs(apps, schema_editor):
    Pack = apps.get_model('catalog', 'Pack')
    from django.utils.text import slugify
    for data in PACKS:
        Pack.objects.get_or_create(name=data['name'], defaults={**data, 'slug': slugify(data['name'])})


def remove_packs(apps, schema_editor):
    Pack = apps.get_model('catalog', 'Pack')
    Pack.objects.filter(name__in=[p['name'] for p in PACKS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0019_pack'),
    ]

    operations = [
        migrations.RunPython(add_packs, remove_packs),
    ]
