from django.conf import settings


def brand(request):
    """
    Expone la marca activa (resuelta por core.middleware.BrandMiddleware)
    a todos los templates como {{ brand }} y {{ brand_config }}, más las
    URLs de ambas tiendas ({{ brand_urls.u404 }} / {{ brand_urls.ficctura }})
    para el gateway split-screen que enlaza de una marca a la otra.

    También arma {{ banner_items }} para el ticker fijo del navbar
    (catalog/_promo_banner.html) — pedido del usuario (12/8): "cada
    promoción que se active se vea en el banner", automático, SIN tener
    que ir a "Promociones de marca" a vincularla a mano (eso es lo que
    generaba el bug viejo de banners desincronizados: quedaba anunciando
    algo que ya se había desactivado). Ahora el ticker se arma solo, cada
    vez que se pide una página, a partir de TODO lo que esté activo en
    ese momento:
      - Cada Promotion activa de la marca ("llevá X, llevate Y").
      - El PaymentDiscount activo de la marca, si tiene algún % cargado
        — con su propia cuenta regresiva opcional (countdown_ends_at).
      - El anuncio de texto libre de BrandPromotion, si está activo
        (para cosas sueltas sin modelo propio, ej. "envío gratis esta
        semana") — su contador de stock/cuenta regresiva también se
        expone acá como {{ banner_urgency }}.

    Cada item de banner_items es un dict {'text': str, 'countdown_to':
    datetime o None} en vez de un string plano, para que cada promo
    pueda tener su propia cuenta regresiva independiente en el ticker.
    """
    active_brand = getattr(request, 'brand', None)

    # brand_urls: normalmente son los dominios reales fijos de
    # settings.BRAND_URLS (cruzan de marca a marca por dominio). Pero
    # si el host actual todavía no es ninguno de esos dominios (ver
    # BrandMiddleware) — típicamente el *.onrender.com antes de
    # conectar los dominios propios — no hay otro dominio al que
    # cruzar todavía, así que ambos links del gateway apuntan al MISMO
    # host actual con ?marca=..., que el middleware sabe interpretar.
    host = request.get_host().lower()
    if host in settings.BRAND_HOSTS:
        brand_urls = settings.BRAND_URLS
    else:
        base = request.build_absolute_uri('/tienda/')
        brand_urls = {b: f'{base}?marca={b}' for b in settings.BRANDS}

    banner_items = []
    banner_urgency = None
    banner_link = None

    if active_brand:
        # Imports acá adentro (no al tope del archivo) para evitar un
        # import circular: catalog todavía no depende de core, pero
        # conviene no asumirlo a nivel de módulo.
        from catalog.models import BrandPromotion, PaymentDiscount, Promotion

        for promo in Promotion.objects.filter(brand=active_brand, is_active=True):
            banner_items.append({'text': f"🎁 {promo.display_banner_text}", 'countdown_to': None})

        payment_discount = PaymentDiscount.objects.filter(brand=active_brand, is_active=True).first()
        if payment_discount and payment_discount.display_banner_text:
            banner_items.append({
                'text': f"💳 {payment_discount.display_banner_text}",
                'countdown_to': payment_discount.countdown_ends_at if payment_discount.countdown_active else None,
            })

        brand_promo = BrandPromotion.objects.filter(brand=active_brand, is_active=True).first()
        if brand_promo:
            if brand_promo.message:
                banner_items.append({'text': f"⚡ {brand_promo.message}", 'countdown_to': None})
            if brand_promo.urgency_type != BrandPromotion.UrgencyType.NONE:
                banner_urgency = brand_promo
            if brand_promo.link_url:
                banner_link = brand_promo.link_url

    return {
        'brand': active_brand,
        'brand_config': getattr(request, 'brand_config', None),
        'brand_urls': brand_urls,
        'banner_items': banner_items,
        'banner_urgency': banner_urgency,
        'banner_link': banner_link,
    }


def cart(request):
    """
    Expone el carrito de la sesión actual como {{ cart }} en todos los
    templates — el panel lateral lo usa para el conteo inicial (antes de
    que el JS haga su primer fetch) y catalog/cart.html lo usa directo.
    """
    from catalog.cart import Cart

    return {'cart': Cart(request)}
