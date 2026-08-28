from django.conf import settings
from django.db import models
from django.utils.text import slugify

# Mismas claves que settings.BRAND_HOSTS/BRANDS ('u404' / 'ficctura') —
# una sola fuente de verdad para qué marcas existen.
BRAND_CHOICES = [(key, cfg['name']) for key, cfg in settings.BRANDS.items()]


class ProductQuerySet(models.QuerySet):

    def available(self):
        return self.filter(status=self.model.Status.AVAILABLE)


class Category(models.Model):
    """
    Categoría de producto, siempre de una sola marca (remeras básicas,
    y a futuro buzos/camperas/pantalones/calzado para Ficctura; prendas
    gráficas, gorras/buzos/pantalones para U404 — ver brief sección 4).
    """

    brand = models.CharField('marca', max_length=10, choices=BRAND_CHOICES)
    name = models.CharField('nombre', max_length=60)
    slug = models.SlugField(max_length=70, blank=True)
    order = models.PositiveIntegerField('orden', default=0)

    # El brief pide secciones "Próximamente" (gorras, buzos, pantalones)
    # para categorías sin mercadería real todavía, con captura de interés
    # en vez de productos de verdad. Marcar acá en lugar de inventar
    # productos placeholder.
    is_coming_soon = models.BooleanField(
        'próximamente', default=False,
        help_text="Se muestra como 'Próximamente' sin productos reales, con botón de interés.",
    )

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['brand', 'order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_brand_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def whatsapp_interest_url(self):
        """
        Link a WhatsApp con mensaje precargado para "me interesa" en una
        categoría todavía sin stock — mecanismo que pide el brief en vez
        de un form propio: la conversación de WhatsApp del cliente ES la
        lista de interesados, no hace falta guardar un lead en la base.

        Sin argumentos a propósito: los templates de Django no pueden
        pasarle parámetros a un método, así que resuelve el número de
        WhatsApp solo, a partir de su propio `brand`.
        """
        whatsapp_number = settings.BRANDS.get(self.brand, {}).get('whatsapp_number')
        message = f"Hola! Me interesa la categoría {self.name}, ¿cuándo va a estar disponible?"

        return build_whatsapp_url(whatsapp_number, message)


class Size(models.Model):
    """
    Talle genérico (S/M/L/XL, etc.). Global por ahora — cuando se sume
    calzado (roadmap de Ficctura mencionado por audio) probablemente
    necesite su propia escala numérica; revisar en ese momento.
    """

    name = models.CharField(max_length=10, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'talle'
        verbose_name_plural = 'talles'

    def __str__(self):
        return self.name


class Product(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Disponible'
        # "Agotado" tal como lo define el brief: un producto real que
        # existió y se quedó sin stock, se conserva visible con captura
        # de interés — no se oculta ni se borra.
        SOLD_OUT = 'sold_out', 'Agotado'

    class LicenseStatus(models.TextChoices):
        NOT_NEEDED = 'not_needed', 'No requiere licencia'
        PENDING = 'pending', 'Licencia pendiente de resolver'
        CLEARED = 'cleared', 'Licencia resuelta'

    class UrgencyType(models.TextChoices):
        NONE = 'none', 'Ninguno'
        STOCK = 'stock', 'Contador de stock (ej: "6 / 100 unidades")'
        COUNTDOWN = 'countdown', 'Cuenta regresiva a una fecha límite'
        BOTH = 'both', 'Los dos'

    brand = models.CharField('marca', max_length=10, choices=BRAND_CHOICES)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products', verbose_name='categoría',
    )

    name = models.CharField('nombre', max_length=80, help_text='Ej: "Sobrio", "Primera Chamba"')
    slug = models.SlugField(max_length=100, blank=True)

    # Copy de producto — el brief trae varios de estos ya escritos
    # textualmente (sección 7) y pide reproducirlos tal cual, sin
    # reescritura publicitaria. No completar con texto inventado.
    description = models.TextField(
        blank=True,
        help_text='Copy/historia del producto. Si el brief ya trae el texto para este modelo, pegarlo tal cual — no reescribir.',
    )

    material = models.CharField(max_length=120, blank=True, help_text='Ej: "Algodón peinado 20/1"')
    fit_notes = models.TextField(
        blank=True,
        help_text='Notas de calce (ej: "deja espacio en el abdomen, no aprieta la panza").',
    )

    # Precio pendiente de confirmación del cliente (brief: "no definir
    # por cuenta propia") — el campo existe para poder cargarlo cuando
    # lo manden, no arranca con un valor inventado.
    price = models.DecimalField('precio', max_digits=10, decimal_places=2, null=True, blank=True)

    # El % de descuento por transferencia es una política general, no
    # por producto (ver Brand/settings) — placeholder hasta que el
    # cliente lo confirme; no se modela acá.

    status = models.CharField('estado', max_length=10, choices=Status.choices, default=Status.AVAILABLE)

    is_limited_edition = models.BooleanField(
        'edición limitada', default=False,
        help_text='Diseños con licencia real (bandas, franquicias) van como "edición limitada" — ver brief 7/8.',
    )

    # Bandera de seguridad para no publicar por error un diseño que
    # necesita licencia y todavía no se resolvió (ej: GNR/AC-DC, el
    # concepto "CBGB" antes de reemplazarlo por venue ficticio).
    license_status = models.CharField(
        'estado de la licencia', max_length=12, choices=LicenseStatus.choices, default=LicenseStatus.NOT_NEEDED,
    )

    # ==========================================================
    # Widget de urgencia (opcional) — pedido del usuario el 10/8,
    # inspirado en preventas tipo Elemental Outfit. Elegible por
    # producto desde el admin, no es un truco automático: el contador
    # de stock y la fecha límite los carga el cliente/vos a mano, así
    # que "reiniciar" es simplemente cambiar el número o la fecha
    # cuando arranca una tanda nueva — no es un timer falso por visita.
    # ==========================================================
    urgency_type = models.CharField(
        max_length=10, choices=UrgencyType.choices, default=UrgencyType.NONE,
        verbose_name='Widget de urgencia',
    )
    urgency_stock_limit = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Total del lote (ej: 100)',
    )
    urgency_stock_remaining = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Unidades restantes del lote (ej: 6)',
        help_text='Se actualiza a mano — no está atado al stock real de las variantes.',
    )
    urgency_countdown_ends_at = models.DateTimeField(
        null=True, blank=True, verbose_name='La promo termina el',
        help_text='Para "reiniciar" la cuenta regresiva simplemente cambiá esta fecha.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'producto'
        verbose_name_plural = 'productos'

    def __str__(self):
        return f"{self.name} ({self.get_brand_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def total_stock(self):
        return sum(v.stock for v in self.variants.all())

    @property
    def urgency_stock_percent(self):
        if not self.urgency_stock_limit:
            return 0
        remaining = self.urgency_stock_remaining or 0
        return max(0, min(100, round(remaining / self.urgency_stock_limit * 100)))

    @property
    def urgency_countdown_active(self):
        from django.utils import timezone
        return bool(self.urgency_countdown_ends_at and self.urgency_countdown_ends_at > timezone.now())

    def whatsapp_interest_url(self):
        """
        Botón de WhatsApp para modelos agotados — "me gustó tal remera y
        no la vi en stock" (idea textual del brief). Igual que en
        Category, no se guarda un lead en la base: la charla de WhatsApp
        ya funciona como lista de interesados para el cliente. Sin
        argumentos por la misma razón que Category.whatsapp_interest_url.
        """
        whatsapp_number = settings.BRANDS.get(self.brand, {}).get('whatsapp_number')
        message = f"Hola! Me interesa el modelo \"{self.name}\" y lo vi agotado, ¿cuándo vuelve a haber stock?"

        return build_whatsapp_url(whatsapp_number, message)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='productos/')
    alt_text = models.CharField(max_length=140, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    # Pedido del cliente (13/8): fotos por color, no solo por producto.
    # Opcional a propósito — vacío = foto general del producto (se
    # sigue mostrando siempre, como hasta ahora); con un color cargado,
    # la ficha puede mostrar esa foto puntual cuando eligen ese color.
    color = models.CharField(
        'color', max_length=30, blank=True,
        help_text='Opcional — si esta foto es de un color puntual (tiene que coincidir con el texto del color de la variante, ej. "Negro"). Vacío = foto general.',
    )

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Imagen de {self.product.name}"


class SizeMeasurement(models.Model):
    """
    Medidas de un talle PARA UN MODELO PUNTUAL, no una tabla genérica —
    el brief pide medir cada modelo (incluyendo circunferencia a la
    altura del ombligo) porque el calce varía según el corte. Tabla
    final todavía no la mandó el cliente; esto es la estructura para
    cargarla cuando llegue.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='measurements')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)

    chest_cm = models.DecimalField('pecho (cm)', max_digits=5, decimal_places=1, null=True, blank=True)
    length_cm = models.DecimalField('largo (cm)', max_digits=5, decimal_places=1, null=True, blank=True)
    waist_cm = models.DecimalField(
        'ombligo/abdomen (cm)', max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Medida a la altura del ombligo — pedida explícitamente en el brief.',
    )
    sleeve_cm = models.DecimalField('manga (cm)', max_digits=5, decimal_places=1, null=True, blank=True)

    class Meta:
        unique_together = ['product', 'size']
        ordering = ['size__order']

    def __str__(self):
        return f"{self.product.name} — {self.size.name}"


class ProductVariant(models.Model):
    """
    Lo que realmente se agrega al carrito: producto + talle + color, con
    su propio stock. El color queda como texto libre (no un catálogo de
    colores) porque la paleta de producto todavía no está cerrada más
    allá de blanco/negro de la primera tanda.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.PROTECT)
    color = models.CharField(max_length=30, default='Blanco')
    # Pedido del cliente (13/8): elegir el color con un selector visual
    # (hex), no solo como texto — se usa para pintar un círculo de color
    # real en el admin y en la tienda al lado del nombre. Opcional: si
    # queda vacío, se sigue mostrando solo el texto como antes.
    hex_color = models.CharField(
        'color (hex)', max_length=7, blank=True,
        help_text='Opcional — para mostrar un círculo con el color real. Ej: #1a1a1a',
    )
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=40, blank=True)

    class Meta:
        unique_together = ['product', 'size', 'color']
        ordering = ['size__order', 'color']

    def __str__(self):
        return f"{self.product.name} — {self.color} / {self.size.name}"


class ProductReservation(models.Model):
    """
    Reserva para la próxima tanda de producción. Pedido explícito del
    usuario (10/8): las remeras agotadas de U404 se muestran difuminadas
    en el catálogo con un botón "reservar para la próxima entrega" que
    lleva a una ficha aparte (ahí sí, la remera se ve bien, sin
    difuminar). A diferencia del botón de WhatsApp para categorías
    "Próximamente" (ver Category.whatsapp_interest_url, que no guarda
    nada porque el chat de WhatsApp ya funciona como lista), ACÁ sí
    interesa guardar el dato: la idea del usuario es poder contar
    reservas por producto para decidir qué remeras priorizar en la
    próxima producción — eso requiere datos agregables, no un chat.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reservations', verbose_name='producto',
    )
    name = models.CharField('nombre', max_length=100)
    contact = models.CharField('contacto', max_length=100, help_text='WhatsApp (con código de país)')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='talle deseado')
    created_at = models.DateTimeField('creada', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'

    def __str__(self):
        return f"{self.name} — {self.product.name}"


class BrandPromotion(models.Model):
    """
    Contador/promo GENERAL de la marca — no atado a un producto puntual.
    Pedido del usuario (10/8) después de probar el widget de urgencia por
    producto (ver Product.urgency_*) y decidir que no lo querían en una
    ficha específica, sino como un banner de la marca entera. Aparece
    fijo arriba de TODAS las páginas de esa marca (ver
    templates/{u404,ficctura}/_navbar.html) cuando `is_active=True`.

    Un renglón por marca (uno para U404, uno para Ficctura, independientes
    entre sí — confirmado por el usuario).
    """

    class UrgencyType(models.TextChoices):
        NONE = 'none', 'Ninguno'
        STOCK = 'stock', 'Contador de stock (ej: "6 / 100 unidades")'
        COUNTDOWN = 'countdown', 'Cuenta regresiva a una fecha límite'
        BOTH = 'both', 'Los dos'

    brand = models.CharField('marca', max_length=10, choices=BRAND_CHOICES, unique=True)
    is_active = models.BooleanField('activa', default=False)

    # Vínculo opcional a una Promotion real (el 3x2, etc.). Bug real que
    # encontró el usuario (10/8): sin esto, el banner podía seguir
    # anunciando "3X2" con un mensaje de texto libre aunque la promo ya
    # estuviera desactivada — nada los mantenía sincronizados. Si se
    # vincula, el banner se apaga solo cuando `linked_promotion` deja de
    # estar activa (ver core/context_processors.py::brand). Para
    # anuncios generales sin relación a una promo puntual (ej. "envío
    # gratis esta semana"), dejar sin vincular y usar `message` como
    # siempre.
    linked_promotion = models.ForeignKey(
        'Promotion', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='banners', verbose_name='promoción vinculada',
        help_text=(
            'Si el banner anuncia una promo puntual (3x2, etc.), vinculala acá — '
            'el banner se apaga solo cuando esta promoción se desactiva. '
            'Si la vinculás, dejá "mensaje" vacío: se arma solo a partir de la promo.'
        ),
    )

    message = models.CharField(
        'mensaje', max_length=140, blank=True,
        help_text='Ej: "¡Preventa exclusiva!" — texto del banner. Se ignora si hay una promoción vinculada arriba.',
    )
    link_url = models.CharField(
        'link del banner', max_length=200, blank=True,
        help_text='A dónde lleva el banner al clickear (opcional). Ej: /catalogo/',
    )

    urgency_type = models.CharField(
        'widget de urgencia', max_length=10, choices=UrgencyType.choices, default=UrgencyType.NONE,
    )
    urgency_stock_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name='Total del lote (ej: 100)')
    urgency_stock_remaining = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Unidades restantes (ej: 6)',
        help_text='Se actualiza a mano. Para "reiniciar", cambiá este número.',
    )
    urgency_countdown_ends_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Termina el',
        help_text='Para "reiniciar" la cuenta regresiva, cambiá esta fecha.',
    )

    class Meta:
        verbose_name = 'promoción de marca'
        verbose_name_plural = 'promociones de marca'

    def __str__(self):
        estado = 'activa' if self.is_active else 'inactiva'
        return f"Promo {self.get_brand_display()} ({estado})"

    @property
    def is_effectively_active(self):
        """
        `is_active` solo no alcanza si el banner está vinculado a una
        Promotion puntual: en ese caso, también tiene que seguir activa
        ESA promoción. Así se evita el bug de un banner anunciando un 3x2
        que ya se desactivó.
        """
        if not self.is_active:
            return False
        if self.linked_promotion_id and not self.linked_promotion.is_active:
            return False
        return True

    @property
    def display_message(self):
        """El texto que se muestra en el banner: si hay una promo vinculada, se arma desde ahí; si no, el mensaje libre."""
        if self.linked_promotion_id and self.linked_promotion.is_active:
            promo = self.linked_promotion
            return f"{promo.badge_text or promo.name} — {promo.name}" if promo.badge_text else promo.name
        return self.message

    @property
    def urgency_stock_percent(self):
        if not self.urgency_stock_limit:
            return 0
        remaining = self.urgency_stock_remaining or 0
        return max(0, min(100, round(remaining / self.urgency_stock_limit * 100)))

    @property
    def urgency_countdown_active(self):
        from django.utils import timezone
        return bool(self.urgency_countdown_ends_at and self.urgency_countdown_ends_at > timezone.now())


class Promotion(models.Model):
    """
    Regla de "llevá X, llevate Y" — pedido del usuario (10/8): "otro tipo
    de ofertas... 3x2, si te llevás dos buzos una remera gratis". No es
    un descuento simple, son dos categorías (o la misma) relacionadas:
    - 3x2 clásico: comprás 3 de "Remeras" → 1 de esas 3 sale gratis.
      (buy_category=Remeras, buy_quantity=3, get_category=None [mismo],
      get_quantity=1, get_discount_percent=100)
    - "2 buzos, 1 remera gratis": comprás 2 de "Buzos" → 1 de "Remeras"
      gratis. (buy_category=Buzos, buy_quantity=2, get_category=Remeras,
      get_quantity=1, get_discount_percent=100)

    IMPORTANTE: esto es solo el DATO de la promo — todavía no hay
    carrito/checkout construido, así que el cálculo automático del
    descuento al comprar no existe todavía. Por ahora esto sirve para
    mostrar el badge de la oferta en el catálogo (ver
    catalog/templates/catalog/list.html) y tenerlo listo para cuando se
    construya el carrito.
    """

    brand = models.CharField('marca', max_length=10, choices=BRAND_CHOICES)
    name = models.CharField(
        'nombre', max_length=100, help_text='Ej: "3x2 en remeras", "Buzo + remera de regalo"',
    )
    badge_text = models.CharField(
        'texto del badge', max_length=20, blank=True,
        help_text='Texto corto para el catálogo, ej: "3X2" o "2X1 REGALO". Si queda vacío, no se muestra badge.',
    )
    banner_text = models.CharField(
        'texto del banner', max_length=100, blank=True,
        help_text=(
            'Lo que se lee en el banner de arriba de la tienda mientras esté activa. '
            'Ej: "3X2 EN REMERAS BÁSICAS". Si lo dejás vacío, se arma solo con el texto '
            'del badge (o el nombre, si no hay badge).'
        ),
    )
    is_active = models.BooleanField('activa', default=False)

    buy_category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='promotions_as_buy',
        verbose_name='comprando de la categoría',
    )
    buy_quantity = models.PositiveIntegerField(default=3, verbose_name='cuántas unidades')

    get_category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='promotions_as_get',
        null=True, blank=True, verbose_name='te regala/descuenta de la categoría',
        help_text='Vacío = la misma categoría que "comprando de" (para un 3x2 clásico).',
    )
    get_quantity = models.PositiveIntegerField(default=1, verbose_name='cuántas unidades de regalo/descuento')
    get_discount_percent = models.PositiveIntegerField(
        default=100, verbose_name='% de descuento en esas unidades',
        help_text='100 = gratis. Ej: 50 = mitad de precio.',
    )

    starts_at = models.DateTimeField(null=True, blank=True, verbose_name='empieza el')
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name='termina el')

    class Meta:
        ordering = ['-id']
        verbose_name = 'promoción (llevá X, llevate Y)'
        verbose_name_plural = 'promociones (llevá X, llevate Y)'

    def __str__(self):
        return self.name

    @property
    def display_banner_text(self):
        """Lo que se muestra en el ticker del banner (ver core/context_processors.py::brand)."""
        return self.banner_text or self.badge_text or self.name

    def applies_to_category(self, category):
        """Si esta promo involucra `category`, ya sea como la que hay que comprar o la del regalo."""
        relevant_ids = {self.buy_category_id, self.get_category_id or self.buy_category_id}
        return category.id in relevant_ids


class PaymentDiscount(models.Model):
    """
    Descuento por elegir transferencia o efectivo en vez de tarjeta —
    pedido del brief ("destacar descuento por transferencia"), ver
    brief/preguntas-pendientes-cliente.md: el % final todavía no lo
    confirmó el cliente, así que arranca en 0 (sin descuento) y se carga
    acá cuando lo manden. Un renglón por marca, igual que BrandPromotion.
    Se aplica sobre el total YA con la promo "llevá X, llevate Y"
    descontada (ver Cart.get_payment_discount_amount).
    """

    brand = models.CharField('marca', max_length=10, choices=BRAND_CHOICES, unique=True)
    is_active = models.BooleanField('activo', default=False)
    transferencia_percent = models.PositiveIntegerField(
        'descuento por transferencia (%)', default=0,
        help_text='Ej: 10 = 10% off pagando por transferencia. 0 = sin descuento.',
    )
    efectivo_percent = models.PositiveIntegerField(
        'descuento por efectivo (%)', default=0,
        help_text='Ej: 10 = 10% off pagando en efectivo. 0 = sin descuento.',
    )
    banner_text = models.CharField(
        'texto del banner', max_length=100, blank=True,
        help_text=(
            'Lo que se lee en el banner de arriba de la tienda mientras esté activo. '
            'Ej: "10% OFF PAGANDO POR TRANSFERENCIA". Si lo dejás vacío, se arma solo '
            'a partir de los % cargados arriba.'
        ),
    )
    countdown_ends_at = models.DateTimeField(
        'cuenta regresiva — termina el', null=True, blank=True,
        help_text=(
            'Opcional: si lo cargás, en el banner aparece "Termina en HH:MM:SS" al lado '
            'del texto de este descuento. Dejalo vacío para que el descuento se vea sin '
            'contador. Para "reiniciar" la cuenta regresiva, simplemente cambiá esta fecha.'
        ),
    )

    class Meta:
        verbose_name = 'descuento por forma de pago'
        verbose_name_plural = 'descuentos por forma de pago'

    def __str__(self):
        estado = 'activo' if self.is_active else 'inactivo'
        return f"Descuento por pago {self.get_brand_display()} ({estado})"

    def percent_for(self, payment_preference):
        if not self.is_active:
            return 0
        return {
            'transferencia': self.transferencia_percent,
            'efectivo': self.efectivo_percent,
        }.get(payment_preference, 0)

    @property
    def display_banner_text(self):
        """Lo que se muestra en el ticker del banner (ver core/context_processors.py::brand)."""
        if self.banner_text:
            return self.banner_text

        parts = []
        if self.transferencia_percent:
            parts.append(f"{self.transferencia_percent}% OFF TRANSFERENCIA")
        if self.efectivo_percent:
            parts.append(f"{self.efectivo_percent}% OFF EFECTIVO")
        return " · ".join(parts)

    @property
    def countdown_active(self):
        from django.utils import timezone
        return bool(self.countdown_ends_at and self.countdown_ends_at > timezone.now())


def build_whatsapp_url(whatsapp_number, message):
    """
    Arma un link wa.me con mensaje precargado. Si todavía no hay número
    de WhatsApp cargado para la marca (ver settings.BRANDS), devuelve
    None en vez de un link roto — el template decide qué mostrar en ese
    caso (hoy: nada, mismo criterio que el navbar).
    """
    if not whatsapp_number:
        return None

    from urllib.parse import quote

    return f"https://wa.me/{whatsapp_number}?text={quote(message)}"


class Order(models.Model):
    """
    Pedido — se crea al "finalizar compra". NO hay cobro automático
    todavía: Payway sigue esperando el CUIT/facturación del cliente (ver
    brief/preguntas-pendientes-cliente.md), así que esto solo REGISTRA
    el pedido con los datos de contacto y entrega elegidos; después se
    coordina el pago manualmente (WhatsApp — ver whatsapp_url()). No es
    un carrito abandonado silencioso: el cliente que hizo el pedido ve
    una confirmación clara de que falta ese paso.
    """

    class DeliveryMethod(models.TextChoices):
        CORREO = 'correo', 'Correo'
        RETIRO = 'retiro', 'Retiro en persona'
        MENSAJERIA = 'mensajeria', 'Mensajería'

    class PaymentPreference(models.TextChoices):
        TARJETA = 'tarjeta', 'Tarjeta (3 cuotas)'
        TRANSFERENCIA = 'transferencia', 'Transferencia'
        EFECTIVO = 'efectivo', 'Efectivo'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente de contacto'
        CONFIRMED = 'confirmed', 'Confirmado'
        CANCELLED = 'cancelled', 'Cancelado'

    brand = models.CharField('marca', max_length=10, choices=BRAND_CHOICES)

    name = models.CharField('nombre', max_length=100)
    contact = models.CharField('contacto', max_length=100, help_text='WhatsApp (con código de país)')
    address = models.CharField(
        'dirección', max_length=255, blank=True,
        help_text='Solo hace falta si el método de entrega es correo o mensajería.',
    )
    delivery_method = models.CharField('método de entrega', max_length=12, choices=DeliveryMethod.choices)
    payment_preference = models.CharField('forma de pago', max_length=14, choices=PaymentPreference.choices)
    notes = models.TextField('notas', blank=True)

    # Snapshot de los totales al momento del pedido — no recalcular
    # después desde el carrito (ya no existe) ni desde precios actuales
    # de producto (podrían cambiar).
    subtotal = models.DecimalField('subtotal', max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        'descuento por promo', max_digits=10, decimal_places=2, default=0,
        help_text='Descuento por "llevá X, llevate Y". El de transferencia/efectivo está aparte, abajo.',
    )
    payment_discount = models.DecimalField(
        'descuento por forma de pago', max_digits=10, decimal_places=2, default=0,
    )
    total = models.DecimalField('total', max_digits=10, decimal_places=2)

    status = models.CharField('estado', max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField('creado', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'

    def __str__(self):
        return f"Pedido #{self.id} — {self.name}"

    def whatsapp_url(self):
        whatsapp_number = settings.BRANDS.get(self.brand, {}).get('whatsapp_number')
        message = (
            f"Hola! Soy {self.name}, hice el pedido #{self.id} por ${self.total} "
            f"— quiero coordinar el pago y la entrega."
        )
        return build_whatsapp_url(whatsapp_number, message)


class OrderItem(models.Model):
    """
    Línea de un pedido. Se guardan nombre/talle/color/precio como texto
    plano (snapshot), NO una FK a ProductVariant — si el producto cambia
    de precio o se borra después, el historial del pedido tiene que
    quedar intacto tal como se compró.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField('producto', max_length=100)
    size = models.CharField('talle', max_length=10)
    color = models.CharField('color', max_length=30)
    quantity = models.PositiveIntegerField('cantidad')
    unit_price = models.DecimalField('precio unitario', max_digits=10, decimal_places=2)
    subtotal = models.DecimalField('subtotal', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'producto del pedido'
        verbose_name_plural = 'productos del pedido'

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
