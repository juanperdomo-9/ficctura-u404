from django import forms
from django.contrib import admin

from core.admin import admin_site

from .models import (
    BrandPromotion, Category, Order, OrderItem, Pack, PaymentDiscount, Product, ProductImage,
    ProductReservation, ProductVariant, Promotion, Size, SizeMeasurement,
)


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'is_coming_soon', 'order']
    list_filter = ['brand', 'is_coming_soon']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Pack, site=admin_site)
class PackAdmin(admin.ModelAdmin):
    # Se administra acá (no en /panel/) a propósito, para no duplicar
    # una pantalla nueva por una tabla que el cliente pidió con 4 filas
    # fijas — cuidar el uso (pedido explícito del usuario).
    list_display = ['name', 'tagline', 'ficctura_negro_qty', 'ficctura_blanco_qty', 'u404_qty', 'bonus_basica_qty', 'discount_percent', 'free_shipping', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order']


@admin.register(Size, site=admin_site)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    ordering = ['order']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'color', 'alt_text', 'is_primary', 'order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['size', 'color', 'hex_color', 'stock', 'sku']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Pedido del cliente (13/8): elegir el color con un selector
        # visual, no escribir el hex a mano — input[type=color] nativo
        # del navegador, sin librerías extra.
        if db_field.name == 'hex_color':
            kwargs['widget'] = forms.TextInput(attrs={'type': 'color', 'style': 'height: 2.2rem; padding: 2px;'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class SizeMeasurementInline(admin.TabularInline):
    model = SizeMeasurement
    extra = 1


@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'category', 'status', 'price',
        'is_limited_edition', 'license_status', 'reservation_count',
    ]
    list_filter = ['brand', 'status', 'category', 'is_limited_edition', 'license_status', 'urgency_type']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline, SizeMeasurementInline]

    fieldsets = (
        (None, {
            'fields': ('brand', 'category', 'name', 'slug', 'status', 'price'),
        }),
        ('Copy y detalle', {
            'fields': ('description', 'material', 'fit_notes'),
        }),
        ('Licencia', {
            'fields': ('is_limited_edition', 'license_status'),
        }),
        ('Widget de urgencia — caso especial para ESTE producto puntual', {
            'classes': ('collapse',),
            'fields': (
                'urgency_type',
                'urgency_stock_limit', 'urgency_stock_remaining',
                'urgency_countdown_ends_at',
            ),
            'description': (
                'Para la promo GENERAL de la marca (la que se ve como banner arriba de '
                'todas las páginas) usá "Promociones de marca" en el menú, no esto. '
                'Esta sección es solo para un contador excepcional en la ficha de UN '
                'producto puntual.'
            ),
        }),
    )

    @admin.display(description='Reservas')
    def reservation_count(self, obj):
        return obj.reservations.count()


@admin.register(ProductReservation, site=admin_site)
class ProductReservationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'contact', 'size', 'created_at']
    list_filter = ['product__brand', 'product']
    search_fields = ['name', 'contact', 'product__name']
    readonly_fields = ['created_at']


@admin.register(BrandPromotion, site=admin_site)
class BrandPromotionAdmin(admin.ModelAdmin):
    """
    OJO: esto ya NO es "el" banner — el banner del navbar se arma solo
    con TODO lo que esté activo (ver core/context_processors.py::brand):
    cada "Promoción (llevá X, llevate Y)" activa y el "Descuento por
    forma de pago" activo aparecen ahí automáticamente, sin tocar nada
    acá. Este modelo es solo para dos cosas EXTRA y opcionales:
    un anuncio de texto libre sin promo propia (ej. "envío gratis esta
    semana"), y el contador de stock/cuenta regresiva.
    """
    list_display = ['brand', 'is_active', 'banner_preview', 'urgency_type']
    list_editable = ['is_active']
    fieldsets = (
        (None, {
            'fields': ('brand', 'is_active', 'message', 'link_url'),
            'description': (
                'Las promociones y el descuento por forma de pago YA se ven solos en el '
                'banner cuando están activos — no hace falta cargar nada acá para eso. '
                'Usá esto solo si querés sumar un anuncio de texto suelto (sin promo propia).'
            ),
        }),
        ('Contador (opcional)', {
            'fields': ('urgency_type', 'urgency_stock_limit', 'urgency_stock_remaining', 'urgency_countdown_ends_at'),
            'description': 'Si lo activás, se agrega al final del banner (ej. "6 / 100 unidades" o una cuenta regresiva).',
        }),
        ('Legacy (no usar)', {
            'fields': ('linked_promotion',),
            'classes': ('collapse',),
            'description': 'Ya no hace falta — las promos se muestran solas. Se deja el campo para no perder datos viejos.',
        }),
    )

    @admin.display(description='Anuncio de texto libre')
    def banner_preview(self, obj):
        return obj.message or '(sin mensaje — solo aporta el contador, si está activado)'


@admin.register(Promotion, site=admin_site)
class PromotionAdmin(admin.ModelAdmin):
    """
    Lista pensada para que el cliente vea de un vistazo qué promo está
    corriendo sin tener que abrir cada una — "regla" arma una frase
    ("Comprás 3 de Remera → llevás 1 gratis") a partir de los mismos
    campos que se cargan en el formulario de abajo.
    """
    list_display = ['name', 'brand', 'regla', 'banner_text', 'badge_text', 'is_active']
    list_editable = ['is_active']
    list_filter = ['brand', 'is_active']
    fieldsets = (
        (None, {'fields': ('brand', 'name', 'badge_text', 'banner_text', 'is_active')}),
        ('Regla: llevá X, llevate Y', {
            'fields': ('buy_category', 'buy_quantity', 'get_category', 'get_quantity', 'get_discount_percent'),
            'description': (
                '3x2 clásico: dejá "te regala/descuenta" vacío (usa la misma categoría), '
                'cantidad a comprar 3, cantidad de regalo 1, descuento 100%. '
                'Ejemplo "2 buzos, 1 remera gratis": comprando de = Buzos (2), '
                'te regala/descuenta = Remeras (1), 100%.'
            ),
        }),
        ('Vigencia (opcional)', {
            'fields': ('starts_at', 'ends_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Regla en criollo')
    def regla(self, obj):
        get_category = obj.get_category or obj.buy_category
        premio = 'gratis' if obj.get_discount_percent == 100 else f'con {obj.get_discount_percent}% off'
        return (
            f"Comprás {obj.buy_quantity} de \"{obj.buy_category}\" → "
            f"llevás {obj.get_quantity} de \"{get_category}\" {premio}"
        )


@admin.register(PaymentDiscount, site=admin_site)
class PaymentDiscountAdmin(admin.ModelAdmin):
    """
    Un renglón por marca. Todo editable directo desde la lista (sin
    entrar a cada uno) — poné el % y tildá "activo".
    """
    list_display = ['brand', 'is_active', 'transferencia_percent', 'efectivo_percent', 'banner_text', 'countdown_ends_at']
    list_editable = ['is_active', 'transferencia_percent', 'efectivo_percent']
    fields = ['brand', 'is_active', 'transferencia_percent', 'efectivo_percent', 'banner_text', 'countdown_ends_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'size', 'color', 'quantity', 'unit_price', 'subtotal']
    can_delete = False


@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'brand', 'name', 'status', 'payment_preference', 'delivery_method', 'total', 'created_at']
    list_filter = ['brand', 'status', 'payment_preference', 'delivery_method']
    search_fields = ['name', 'contact']
    readonly_fields = ['subtotal', 'discount', 'payment_discount', 'total', 'created_at']
    inlines = [OrderItemInline]
