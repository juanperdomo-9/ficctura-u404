from decimal import Decimal

from .models import Pack, PaymentDiscount, Product, ProductVariant, Promotion


class Cart:
    """
    Carrito basado en sesión (sin login, mismo patrón que regalbox) —
    pero acá se guarda por VARIANTE (talle+color), no por producto,
    porque en esta tienda hay que elegir talle antes de comprar.

    Es un carrito POR DOMINIO (sesión de Django = por dominio/puerto):
    cada marca tiene su propio carrito, con solo sus propios productos
    — U404 y Ficctura quedaron con vidrieras separadas (pedido del
    usuario, 12/8), ya no se mezclan ni en catálogo ni en carrito.
    """

    SESSION_KEY = 'cart'

    def __init__(self, request):
        self.session = request.session
        self.brand = getattr(request, 'brand', None)

        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def add(self, variant, quantity=1):
        variant_id = str(variant.id)
        quantity = int(quantity)

        if variant_id not in self.cart:
            self.cart[variant_id] = {'quantity': quantity}
        else:
            self.cart[variant_id]['quantity'] += quantity

        self.save()

    def remove(self, variant):
        variant_id = str(variant.id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def update(self, variant, quantity):
        variant_id = str(variant.id)
        quantity = int(quantity)

        if variant_id in self.cart:
            if quantity <= 0:
                del self.cart[variant_id]
            else:
                self.cart[variant_id]['quantity'] = quantity
            self.save()

    def clear(self):
        # Vacía el dict EN EL LUGAR (self.cart.clear(), no una reasignación)
        # — self.cart y self.session[SESSION_KEY] son el mismo objeto desde
        # __init__, así que reemplazar la clave de la sesión por un dict
        # nuevo dejaría a self.cart apuntando al viejo, con los items
        # todavía adentro. Bug real, encontrado probando el vaciado.
        self.cart.clear()
        self.save()

    def save(self):
        self.session.modified = True

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def items(self):
        """
        Reconstruye la lista de items desde la base (no confía en datos
        viejos de la sesión: si una variante se borró, se saca sola del
        carrito acá, igual que regalbox hace con GiftBox).
        """
        variant_ids = [int(vid) for vid in self.cart.keys()]

        variants = (
            ProductVariant.objects
            .filter(id__in=variant_ids)
            .select_related('product', 'product__category', 'size')
            .prefetch_related('product__images')
        )
        variants_by_id = {v.id: v for v in variants}

        items = []
        for variant_id_str in list(self.cart.keys()):
            variant = variants_by_id.get(int(variant_id_str))

            if not variant:
                del self.cart[variant_id_str]
                self.save()
                continue

            quantity = self.cart[variant_id_str]['quantity']
            price = variant.product.price or Decimal('0')

            items.append({
                'variant': variant,
                'quantity': quantity,
                'subtotal': price * quantity,
            })

        return items

    def get_subtotal(self):
        return sum((item['subtotal'] for item in self.items()), Decimal('0'))

    def get_promotions(self):
        """Promos "llevá X, llevate Y" activas de ESTA marca — cada carrito solo ve las suyas (ver catalog_list, mismo criterio)."""
        if not self.brand:
            return Promotion.objects.none()

        return (
            Promotion.objects
            .filter(is_active=True, brand=self.brand)
            .select_related('buy_category', 'get_category')
        )

    def get_applicable_discounts(self):
        """
        Para cada promo activa, mira si lo que hay en el carrito alcanza
        la condición ("llevá X de esta categoría") y calcula cuánto se
        descuenta. Las unidades más baratas de la categoría "regalo" son
        las que se descuentan primero (criterio estándar de este tipo de
        ofertas).
        """
        items = self.items()
        discounts = []

        for promo in self.get_promotions():
            buy_category_id = promo.buy_category_id
            get_category_id = promo.get_category_id or promo.buy_category_id

            buy_qty_in_cart = sum(
                item['quantity'] for item in items
                if item['variant'].product.category_id == buy_category_id
            )

            if buy_qty_in_cart < promo.buy_quantity:
                continue

            sets = buy_qty_in_cart // promo.buy_quantity
            free_units = sets * promo.get_quantity

            candidate_prices = []
            for item in items:
                if item['variant'].product.category_id == get_category_id:
                    price = item['variant'].product.price or Decimal('0')
                    candidate_prices.extend([price] * item['quantity'])

            candidate_prices.sort()
            discounted_prices = candidate_prices[:free_units]

            if not discounted_prices:
                continue

            discount_amount = sum(
                (price * Decimal(promo.get_discount_percent) / Decimal('100'))
                for price in discounted_prices
            )

            if discount_amount > 0:
                discounts.append({
                    'promotion': promo,
                    'free_units': len(discounted_prices),
                    'discount_amount': discount_amount,
                })

        return discounts

    def get_discount_total(self):
        return sum((d['discount_amount'] for d in self.get_applicable_discounts()), Decimal('0'))

    # ---- Pack (29/8) ----
    # El pack no es una promo de catálogo (Promotion) ni un producto de
    # precio fijo — es una marca en la SESIÓN (la puso pack_build en
    # catalog/views.py) que dice "el % de descuento y el envío gratis de
    # tal pack se aplican sobre lo que hay en el carrito ahora".

    def _pack_item_counts(self):
        """
        Cuenta cuántas unidades de cada "ingrediente" de pack hay AHORA
        en el carrito (Ficctura Negro / Ficctura Blanco / U404). Única
        fuente de esta cuenta — la usan tanto get_active_pack() acá
        abajo como catalog/views.py::_pack_recommendation.
        """
        items = self.items()
        negro = sum(
            i['quantity'] for i in items
            if i['variant'].product.brand == 'ficctura' and i['variant'].color == 'Negro'
        )
        blanco = sum(
            i['quantity'] for i in items
            if i['variant'].product.brand == 'ficctura' and i['variant'].color == 'Blanco'
        )
        u404 = sum(i['quantity'] for i in items if i['variant'].product.brand == 'u404')
        return negro, blanco, u404

    def get_active_pack(self):
        """
        Bug real (18/9, reportado por el usuario): "si agrego un pack y
        lo borro me sigue apareciendo pack junior aplicado y envío
        gratis". Antes esto devolvía ciegamente lo que hubiera en la
        sesión — cart_remove/cart_subtract NUNCA llamaban a
        clear_active_pack() (pese a lo que decía el comentario viejo
        acá), solo se limpiaba si el carrito quedaba TOTALMENTE vacío
        (ver _cart_payload). Si sacabas UNA sola remera del pack y
        dejabas las demás (o cualquier otra cosa) en el carrito, el
        pack seguía "aplicado" para siempre con datos que ya no
        reflejan lo que hay adentro.

        Ahora cada vez que se pide el pack activo, se revalida contra
        el carrito actual — si ya no alcanza para justificarlo, se
        limpia solo. Esto también es lo que hace que
        _pack_recommendation vuelva a funcionar: esa función no
        recomienda nada mientras haya un active_pack (aunque esté
        stale), así que este fix arregla los dos síntomas reportados
        con el mismo cambio.
        """
        pack_data = self.session.get('active_pack')
        if not pack_data:
            return None

        pack = Pack.objects.filter(pk=pack_data.get('pack_id')).first()
        if not pack:
            self.clear_active_pack()
            return None

        negro, blanco, u404 = self._pack_item_counts()
        if negro < pack.ficctura_negro_qty or blanco < pack.ficctura_blanco_qty or u404 < pack.u404_qty:
            self.clear_active_pack()
            return None

        return pack_data

    def get_pack_discount_amount(self):
        pack = self.get_active_pack()
        if not pack or not pack.get('discount_percent'):
            return Decimal('0')
        base = self.get_subtotal() - self.get_discount_total()
        return base * Decimal(pack['discount_percent']) / Decimal('100')

    def has_free_shipping(self):
        pack = self.get_active_pack()
        return bool(pack and pack.get('free_shipping'))

    def clear_active_pack(self):
        self.session.pop('active_pack', None)
        self.save()

    def get_payment_discount_percent(self, payment_preference):
        """% de descuento (transferencia/efectivo) configurado para esta marca — 0 si no hay fila cargada, no está activo, o la forma de pago no aplica (tarjeta nunca tiene)."""
        if not payment_preference or not self.brand:
            return 0
        config = PaymentDiscount.objects.filter(brand=self.brand).first()
        return config.percent_for(payment_preference) if config else 0

    def get_payment_discount_amount(self, payment_preference):
        """
        Se calcula sobre lo que queda DESPUÉS del descuento por promo
        ("llevá X, llevate Y") — se apilan, no compiten entre sí.
        """
        percent = self.get_payment_discount_percent(payment_preference)
        if not percent:
            return Decimal('0')
        base = self.get_subtotal() - self.get_discount_total() - self.get_pack_discount_amount()
        return base * Decimal(percent) / Decimal('100')

    def get_total(self, payment_preference=None):
        total = self.get_subtotal() - self.get_discount_total() - self.get_pack_discount_amount()
        if payment_preference:
            total -= self.get_payment_discount_amount(payment_preference)
        return total
