from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.text import slugify


class StoreAdminSite(admin.AdminSite):
    """
    Admin site propio en vez del default de Django: el cliente entra acá
    a cargar promos/productos/pedidos y necesita un menú simple, no la
    lista alfabética de Django (que mezclaba todo: "Buzones de X" al
    lado de "Órdenes" al lado de "Tamaños", con Usuarios y Grupos de
    yapa). Se reagrupan los mismos modelos en secciones fijas, con
    Promociones primero porque es lo que el cliente más va a tocar.

    Los modelos se registran en catalog/admin.py contra esta instancia
    (`admin_site`), no contra el `admin.site` default.
    """

    site_header = 'FICCTURA · UNIVERSO 404'
    site_title = 'Panel de administración'
    index_title = 'Gestión de la tienda'

    # (nombre de la sección, [nombres de clase de modelo en ese orden])
    GROUPS = [
        ('Promociones', ['BrandPromotion', 'Promotion', 'PaymentDiscount']),
        ('Catálogo', ['Product', 'Category', 'Size', 'ProductReservation']),
        ('Pedidos', ['Order']),
        ('Cuentas', ['User']),
    ]

    # Template propio (templates/admin/index.html) que agrega una guía
    # corta arriba del menú explicando las 3 formas de hacer una promo —
    # pedido del cliente (le costaba entender qué hacía cada modelo).
    index_template = 'admin/index.html'

    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request, app_label)

        models_by_name = {}
        for app in app_dict.values():
            for model in app['models']:
                models_by_name[model['object_name']] = model

        grouped = []
        seen = set()
        for group_name, model_names in self.GROUPS:
            models = [models_by_name[name] for name in model_names if name in models_by_name]
            seen.update(model_names)
            if models:
                grouped.append({
                    'name': group_name,
                    'app_label': slugify(group_name),
                    'app_url': '#',
                    'has_module_perms': True,
                    'models': models,
                })

        # Si aparece un modelo nuevo que todavía no se agregó a GROUPS
        # arriba, que caiga en "Otros" en vez de desaparecer del menú.
        leftover = [m for name, m in models_by_name.items() if name not in seen]
        if leftover:
            grouped.append({
                'name': 'Otros',
                'app_label': 'otros',
                'app_url': '#',
                'has_module_perms': True,
                'models': leftover,
            })

        return grouped


admin_site = StoreAdminSite(name='admin')

# Se muestra en "Cuentas" para poder cambiar la contraseña propia desde
# acá. Group (permisos por rol) no se registra: con una sola cuenta de
# cliente no aporta nada, solo ruido.
admin.register(User, site=admin_site)(UserAdmin)
