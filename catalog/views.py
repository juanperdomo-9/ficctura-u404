import json
import logging
import time

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .cart import Cart
from .models import (
    Category, Order, OrderItem, Product, ProductReservation, ProductVariant, Promotion, Size,
)
from .payments import PaywayError, create_payway_payment, is_configured as payway_is_configured
from .whatsapp import WhatsAppError, is_configured as whatsapp_is_configured, send_order_confirmation

logger = logging.getLogger(__name__)


def is_valid_whatsapp(value):
    """
    Pedido del usuario (13/8): "el contacto de los clientes solo quiero
    WhatsApp, no mail" — validación ligera, no un validador de teléfonos
    completo: rechaza lo obvio (un email) y pide que haya bastantes
    dígitos como para ser un número real. No exige un formato exacto
    (con/sin +54 9, con/sin espacios) para no trabar a alguien que
    escribe distinto.
    """
    if '@' in value:
        return False
    digit_count = sum(ch.isdigit() for ch in value)
    return digit_count >= 8


def catalog_list(request):
    """
    Catálogo de la marca activa, agrupado por categoría.

    Antes U404 mostraba también las básicas de Ficctura (regla original
    del brief). El cliente pidió separar las vidrieras del todo (12/8):
    cada marca muestra SOLO lo suyo — catálogo, ficha de producto,
    carrito y destacados de la home — y en el catálogo de U404 hay en
    cambio un cartel de cross-sell invitando a Ficctura (ver sección más
    abajo en el template).
    """
    products = (
        Product.objects
        .filter(brand=request.brand)
        .select_related('category')
        .prefetch_related('images')
    )

    # Buscador — pedido del usuario (13/8). Busca en nombre, descripción
    # y material (ej. "algodón") para que también encuentre por tela. Si
    # hay término de búsqueda, no se muestran las categorías "Próximamente"
    # (no tiene sentido ofrecer "avisame" en medio de resultados de
    # búsqueda) ni el cross-sell de abajo — son ruido cuando alguien ya
    # sabe lo que busca.
    search_query = request.GET.get('q', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(material__icontains=search_query)
        )

    sections_by_category = {}
    for product in products:
        sections_by_category.setdefault(product.category, []).append(product)

    sections = sorted(sections_by_category.items(), key=lambda item: (item[0].order, item[0].name))

    # Promos "llevá X, llevate Y" activas y visibles en esta tienda —
    # ahora estrictamente de la marca activa, mismo criterio que el
    # catálogo (ver comentario arriba).
    promotions_qs = Promotion.objects.filter(is_active=True, brand=request.brand).select_related(
        'buy_category', 'get_category',
    )

    active_promotions = list(promotions_qs)
    for category, _products in sections:
        category.promotions = [p for p in active_promotions if p.applies_to_category(category)]

    coming_soon_categories = (
        Category.objects.none() if search_query
        else Category.objects.filter(brand=request.brand, is_coming_soon=True)
    )

    return render(request, 'catalog/list.html', {
        'sections': sections,
        'coming_soon_categories': coming_soon_categories,
        'search_query': search_query,
    })


def product_detail(request, slug):
    """
    Ficha de producto. Se busca solo entre los productos de ESTA marca
    — si alguien intenta ver un producto de la otra marca (por link
    directo o adivinando la URL), da 404 en vez de mostrarlo fuera de
    su tienda. Ver catalog_list para el mismo criterio.
    """
    product = get_object_or_404(
        Product.objects.filter(brand=request.brand).prefetch_related(
            'images', 'variants__size', 'measurements__size',
        ),
        slug=slug,
    )

    in_stock = product.status == Product.Status.AVAILABLE and product.total_stock > 0

    variants = list(product.variants.all())

    # Talle y color se eligen POR SEPARADO (pedido del usuario 10/8) — no
    # un combo único en un <select>. Se listan todos los talles/colores
    # que existen para este producto, tengan stock o no; el JS decide si
    # la combinación elegida está disponible. Nunca se manda el número
    # de stock al front, solo si hay (True/False) — el cliente no tiene
    # por qué ver "quedan 3".
    sizes, seen_sizes = [], set()
    colors, seen_colors = [], set()
    color_hex = {}  # nombre de color -> hex cargado en la variante (13/8, para el circulito de color en la ficha)
    for variant in sorted(variants, key=lambda v: v.size.order):
        if variant.size_id not in seen_sizes:
            sizes.append(variant.size)
            seen_sizes.add(variant.size_id)
        if variant.color not in seen_colors:
            colors.append(variant.color)
            seen_colors.add(variant.color)
        if variant.hex_color and variant.color not in color_hex:
            color_hex[variant.color] = variant.hex_color

    variants_json = json.dumps([
        {'id': v.id, 'size_id': v.size_id, 'color': v.color, 'available': v.stock > 0}
        for v in variants
    ])

    product_url = request.build_absolute_uri()
    share_text = f"Mirá esto en {request.brand_config.get('name', request.brand)}: {product.name} — {product_url}"

    return render(request, 'catalog/detail.html', {
        'product': product,
        'in_stock': in_stock,
        'sizes': sizes,
        'colors': colors,
        'color_hex': color_hex,
        'variants_json': variants_json,
        'share_text': share_text,
    })


def reserve_product(request, slug):
    """
    Reservar un producto agotado para la próxima tanda de producción —
    pedido del usuario (10/8): en vez del link directo a
    WhatsApp, esto guarda la reserva en la base (ver ProductReservation)
    para que el cliente pueda contar cuántas reservas tiene cada modelo y
    priorizar qué producir después. Acá la remera se muestra bien, sin el
    difuminado que tiene en el listado.
    """
    product = get_object_or_404(Product.objects.filter(brand=request.brand), slug=slug)

    # Talles: los que tuvo el producto originalmente si existen, si no
    # el listado global — igual sirve solo como preferencia, no reserva
    # stock real (el producto está agotado, no hay variante con stock).
    size_ids = product.variants.values_list('size_id', flat=True)
    sizes = Size.objects.filter(id__in=size_ids) or Size.objects.all()

    error = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact = request.POST.get('contact', '').strip()
        size_id = request.POST.get('size') or None

        if name and contact and is_valid_whatsapp(contact):
            ProductReservation.objects.create(
                product=product, name=name, contact=contact, size_id=size_id,
            )
            # POST-redirect-GET: evita reenviar el form si refrescan la página.
            return redirect(f"{request.path}?ok=1")

        error = 'Completá tu nombre y tu WhatsApp (no un email).'

    return render(request, 'catalog/reserve.html', {
        'product': product,
        'sizes': sizes,
        'reserved': request.GET.get('ok') == '1',
        'error': error,
    })


# ==========================================================
# CARRITO
# ==========================================================

def _cart_payload(cart, error=None):
    """
    Estado del carrito en un dict listo para JSON — lo consume tanto el
    panel lateral (fetch en cada cambio) como cualquier otra pantalla
    que necesite el resumen sin recargar la página.
    """
    items = []
    for item in cart.items():
        variant = item['variant']
        image = variant.product.primary_image
        items.append({
            'variant_id': variant.id,
            'product_slug': variant.product.slug,
            'product_name': variant.product.name,
            'size': variant.size.name,
            'color': variant.color,
            'quantity': item['quantity'],
            'unit_price': str(variant.product.price or 0),
            'subtotal': str(item['subtotal']),
            'image_url': image.image.url if image else '',
            'stock': variant.stock,
        })

    promotions = [
        {
            'name': d['promotion'].name,
            'badge_text': d['promotion'].badge_text,
            'free_units': d['free_units'],
            'discount_amount': str(d['discount_amount']),
        }
        for d in cart.get_applicable_discounts()
    ]

    payload = {
        'success': error is None,
        'count': len(cart),
        'subtotal': str(cart.get_subtotal()),
        'discount': str(cart.get_discount_total()),
        'total': str(cart.get_total()),
        'items': items,
        'promotions': promotions,
    }

    if error:
        payload['error'] = error

    return payload


def cart_view(request):
    """Página completa del carrito — funciona sin JS (el panel lateral es progressive enhancement encima de esto)."""
    cart = Cart(request)

    return render(request, 'catalog/cart.html', {
        'items': cart.items(),
        'promotions': cart.get_applicable_discounts(),
        'subtotal': cart.get_subtotal(),
        'discount': cart.get_discount_total(),
        'total': cart.get_total(),
    })


def cart_state(request):
    """JSON del carrito — lo usa el panel lateral para pintarse al cargar cualquier página."""
    return JsonResponse(_cart_payload(Cart(request)))


def cart_add(request, variant_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    variant = get_object_or_404(
        ProductVariant.objects.select_related('product'),
        pk=variant_id,
        product__brand=request.brand,
    )

    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))

    current_qty = cart.cart.get(str(variant.id), {}).get('quantity', 0)

    if current_qty + quantity > variant.stock:
        available = max(0, variant.stock - current_qty)
        if available <= 0:
            return JsonResponse(_cart_payload(cart, error=f'No queda más stock de {variant.product.name} ({variant.size.name} / {variant.color}).'), status=400)
        quantity = available

    cart.add(variant, quantity=quantity)

    return JsonResponse(_cart_payload(cart))


def cart_subtract(request, variant_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    variant = get_object_or_404(ProductVariant, pk=variant_id)
    cart = Cart(request)

    current_qty = cart.cart.get(str(variant.id), {}).get('quantity', 0)
    cart.update(variant, current_qty - 1)

    return JsonResponse(_cart_payload(cart))


def cart_remove(request, variant_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    variant = get_object_or_404(ProductVariant, pk=variant_id)
    cart = Cart(request)
    cart.remove(variant)

    return JsonResponse(_cart_payload(cart))


def cart_clear(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    cart = Cart(request)
    cart.clear()

    return JsonResponse(_cart_payload(cart))


# ==========================================================
# CHECKOUT
# ==========================================================

def checkout(request):
    """
    A diferencia de regalbox (pedido del usuario 10/8: "tiene que tener
    cobro automático, no es como regalbox"): si eligen "tarjeta" y
    Payway está configurado, esto cobra de verdad contra la API antes
    de crear el pedido — no es un formulario que solo registra la
    intención. Transferencia y efectivo siguen siendo manuales (no
    necesitan gateway, son formas de pago que se coordinan directo).
    """
    cart = Cart(request)
    items = cart.items()

    if not items:
        return redirect('catalog:list')

    error = None
    payway_configured = payway_is_configured()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('address', '').strip()
        delivery_method = request.POST.get('delivery_method')
        payment_preference = request.POST.get('payment_preference')
        notes = request.POST.get('notes', '').strip()
        installments = int(request.POST.get('installments') or 1)
        payway_token = request.POST.get('payway_token', '').strip()

        valid_delivery = delivery_method in Order.DeliveryMethod.values
        valid_payment = payment_preference in Order.PaymentPreference.values

        if not (name and contact and valid_delivery and valid_payment):
            error = 'Completá tu nombre, tu WhatsApp, y elegí método de entrega y de pago.'
        elif not is_valid_whatsapp(contact):
            error = 'Ingresá un número de WhatsApp válido (no un email).'

        order_status = Order.Status.PENDING

        if not error and payment_preference == Order.PaymentPreference.TARJETA:
            if not payway_configured:
                error = 'El pago con tarjeta todavía no está habilitado — probá con transferencia o efectivo.'
            elif not payway_token:
                error = 'No pudimos leer los datos de la tarjeta. Revisá los datos e intentá de nuevo.'
            else:
                try:
                    create_payway_payment(
                        token=payway_token,
                        amount_cents=int(cart.get_total() * 100),
                        site_transaction_id=f"{request.brand}-{int(time.time())}",
                        installments=installments,
                        description=f"Pedido {request.brand_config.get('name', request.brand)}",
                    )
                    order_status = Order.Status.CONFIRMED
                except PaywayError as exc:
                    error = f'El pago no se pudo procesar: {exc}'

        if not error:
            order = Order.objects.create(
                brand=request.brand, name=name, contact=contact, address=address,
                delivery_method=delivery_method, payment_preference=payment_preference, notes=notes,
                subtotal=cart.get_subtotal(), discount=cart.get_discount_total(),
                payment_discount=cart.get_payment_discount_amount(payment_preference),
                total=cart.get_total(payment_preference),
                status=order_status,
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product_name=item['variant'].product.name,
                    size=item['variant'].size.name,
                    color=item['variant'].color,
                    quantity=item['quantity'],
                    unit_price=item['variant'].product.price or 0,
                    subtotal=item['subtotal'],
                )

            # WhatsApp de confirmación al cliente (ver catalog/whatsapp.py)
            # — pedido del usuario (13/8), dejado armado y listo para
            # cuando haya cuenta de Twilio/WhatsApp Business real (hoy
            # is_configured() da False, así que esto no hace nada). Nunca
            # tiene que romper el checkout: la compra ya se guardó.
            if whatsapp_is_configured():
                try:
                    send_order_confirmation(order)
                except WhatsAppError as exc:
                    logger.warning('No se pudo mandar el WhatsApp de confirmación del pedido #%s: %s', order.id, exc)

            cart.clear()
            return redirect('catalog:order_confirmation', order_id=order.id)

    # % por método, para que el checkout.html muestre "Transferencia
    # (10% off)" al lado de cada opción y JS recalcule el total sin
    # recargar la página al elegirla (ver static/js/checkout.js).
    payment_discount_percents = {
        value: cart.get_payment_discount_percent(value) for value, _ in Order.PaymentPreference.choices
    }

    return render(request, 'catalog/checkout.html', {
        'items': items,
        'promotions': cart.get_applicable_discounts(),
        'subtotal': cart.get_subtotal(),
        'discount': cart.get_discount_total(),
        'total': cart.get_total(),
        'total_after_promo': cart.get_subtotal() - cart.get_discount_total(),
        'payment_discount_percents': payment_discount_percents,
        'error': error,
        'delivery_choices': Order.DeliveryMethod.choices,
        'payment_choices': Order.PaymentPreference.choices,
        'payway_configured': payway_configured,
        'payway_public_key': settings.PAYWAY_PUBLIC_KEY,
        'payway_api_base_url': settings.PAYWAY_API_BASE_URL,
        'payway_js_sdk_url': settings.PAYWAY_JS_SDK_URL,
    })


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, pk=order_id, brand=request.brand)

    return render(request, 'catalog/order_confirmation.html', {'order': order})
