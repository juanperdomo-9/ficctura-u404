from django.conf import settings


class BrandMiddleware:
    """
    Resuelve qué marca (u404 / ficctura) corresponde a la request actual
    según el host, y la deja disponible como request.brand (str) y
    request.brand_config (dict, ver settings.BRANDS).

    Ver la nota de arquitectura en config/settings.py (sección
    "FICCTURA + UNIVERSO 404") para por qué se resuelve por host/puerto.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        brand = settings.BRAND_HOSTS.get(host, settings.DEFAULT_BRAND)

        request.brand = brand
        request.brand_config = settings.BRANDS[brand]

        return self.get_response(request)
