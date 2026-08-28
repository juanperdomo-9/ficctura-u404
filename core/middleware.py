from django.conf import settings


class BrandMiddleware:
    """
    Resuelve qué marca (u404 / ficctura) corresponde a la request actual
    según el host, y la deja disponible como request.brand (str) y
    request.brand_config (dict, ver settings.BRANDS).

    Ver la nota de arquitectura en config/settings.py (sección
    "FICCTURA + UNIVERSO 404") para por qué se resuelve por host/puerto.

    Caso especial (28/8): mientras el host actual NO sea uno de los
    dominios reales de BRAND_HOSTS (ej. el *.onrender.com de Render
    antes de conectar los dominios propios, o cualquier preview), no
    hay forma de distinguir marca por host — un solo hostname no puede
    "ser" las dos marcas a la vez. Para poder probar/navegar igual en
    ese momento, se admite elegir la marca con ?marca=u404 / ?marca=
    ficctura en la URL (así arma los links el gateway en ese caso, ver
    core/context_processors.py::brand) y esa elección se guarda en la
    sesión para el resto de la visita — los links internos del sitio
    son relativos y no llevan esa query string, así que sin esto se
    perdía la marca elegida en cuanto navegabas a la página siguiente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        brand = settings.BRAND_HOSTS.get(host)

        if brand is None:
            query_brand = request.GET.get('marca')
            if query_brand in settings.BRANDS:
                request.session['brand_override'] = query_brand
            brand = request.session.get('brand_override', settings.DEFAULT_BRAND)

        request.brand = brand
        request.brand_config = settings.BRANDS[brand]

        return self.get_response(request)
