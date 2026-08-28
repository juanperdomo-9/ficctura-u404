from django.shortcuts import redirect, render
from django.templatetags.static import static

from catalog.models import Product, Size

# Títulos de las secciones todavía no construidas (catálogo, carrito,
# checkout dependen de datos que el cliente no cerró — ver
# brief/preguntas-pendientes-cliente.md). Los links del navbar apuntan acá
# en vez de a "#" muertos, para que nada rompa mientras se prueba el sitio.
COMING_SOON_SECTIONS = {
    'catalogo': 'Catálogo',
    'basicas-ficctura': 'Básicas Ficctura',
    'proximamente': 'Próximamente',
    # 'carrito' ya no está acá — ahora es real, ver catalog:cart.
    'checkout': 'Checkout',
    # 'nosotros', 'talles', 'contacto' y 'cambios-y-devoluciones' ya no
    # están acá — cada una tiene su propia página (ver abajo), aunque
    # todavía les falten datos puntuales del cliente.
}


def gateway(request):
    """
    Landing compartida ("/"), igual en las dos marcas: pantalla partida
    en dos con acceso a ÉPICAS (U404) y BÁSICAS (FICCTURA) — copy que ya
    aparece aprobado en el brief como cierre del reel madre. Desde acá
    el visitante elige a qué tienda entrar; a partir de esa elección
    todo el recorrido queda separado por marca.
    """
    return render(request, 'gateway.html')


def shop(request):
    """
    Home real de la tienda de la marca activa (a donde te lleva el
    gateway). Renderiza un template distinto por marca porque el brief
    pide identidades visuales separadas, aunque compartan backend.
    """
    # Antes usaba Product.objects.for_brand (mezclaba básicas Ficctura en
    # U404) — se sacó junto con el resto de la mezcla del catálogo (ver
    # catalog/views.py::catalog_list), mismo criterio: cada vidriera
    # muestra solo lo suyo.
    featured_products = (
        Product.objects
        .filter(brand=request.brand)
        .available()
        .select_related('category')
        .prefetch_related('images')[:4]
    )

    return render(request, f'{request.brand}/home.html', {'featured_products': featured_products})


def coming_soon(request, section):
    """
    Placeholder de una sección del navbar que todavía no se construyó
    (catálogo, próximamente, checkout — dependen de datos que el
    cliente no cerró, ver brief/preguntas-pendientes-cliente.md) — reusa
    el mismo template para todas, con el mismo look & feel de la marca
    activa.

    "nosotros", "talles", "contacto" y "cambios-y-devoluciones" son la
    excepción: tienen su propia página con diseño real en vez del
    placeholder genérico, aunque a algunas todavía les falte un dato
    puntual del cliente (tabla de medidas, WhatsApp, política de
    cambios) — ver cada vista abajo.
    """
    dedicated_views = {
        'nosotros': nosotros,
        'talles': talles,
        'contacto': contacto,
        'cambios-y-devoluciones': cambios_y_devoluciones,
    }
    if section in dedicated_views:
        return dedicated_views[section](request)

    title = COMING_SOON_SECTIONS.get(section, section.replace('-', ' ').title())

    return render(request, 'coming_soon.html', {'section_title': title})


def nosotros(request):
    """
    Página "Nosotros" — copy tal cual del brief (sección 2 "Relación
    entre las dos marcas" y sección 3 "Banco de frases"), sin inventar
    nada nuevo. Un solo template, ramificado por marca igual que
    catalog/list.html.
    """
    return render(request, 'nosotros.html')


def talles(request):
    """
    Guía de talles/calce. La tabla de medidas final todavía no la
    manda el taller (PENDIENTE en el brief) — la página no la inventa,
    solo muestra la filosofía de calce que SÍ es VIGENTE en el brief
    (sección 2) y los talles que ya existen cargados en el sistema
    (Size), sin medidas todavía.
    """
    return render(request, 'talles.html', {'sizes': Size.objects.all()})


def contacto(request):
    """
    Contacto — WhatsApp/Instagram reales si ya están cargados en
    settings.BRANDS (ver informe de onboarding), sin inventar ninguno
    que falte (el número de WhatsApp de las dos marcas sigue PENDIENTE).
    """
    return render(request, 'contacto.html')


def cambios_y_devoluciones(request):
    """
    Política de cambios y devoluciones — no aparece en el brief, el
    cliente nunca la definió. Pedido del usuario (13/8): armar un
    borrador estándar de e-commerce argentino en vez de dejarlo vacío
    ("hagamos bien bien el cambio y devoluciones... redactame un
    borrador estándar"). Incluye el derecho de arrepentimiento de 10
    días que exige la Ley 24.240 para compras a distancia (eso NO es
    negociable/inventado, es piso legal real) — el resto (30 días para
    cambio de talle/color, quién paga el envío en cada caso, plazo de
    reintegro) son términos razonables típicos del rubro, PENDIENTES DE
    QUE EL CLIENTE LOS CONFIRME O AJUSTE antes de darlos por definitivos.
    """
    return render(request, 'cambios_y_devoluciones.html')


def favicon(request):
    """Redirige /favicon.ico al .ico real de la marca activa (ver static/img/favicon-*.ico)."""
    name = 'favicon-u404.ico' if request.brand == 'u404' else 'favicon-ficctura.ico'
    return redirect(static(f'img/{name}'))
