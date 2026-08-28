from django import forms
from django.forms import inlineformset_factory

from catalog.models import BrandPromotion, Category, PaymentDiscount, Product, ProductImage, ProductVariant, Promotion


class DashStyledFormMixin:
    """Pinta todos los inputs de texto/número/textarea/select con .dash-input — los checkbox quedan sin tocar (se ven bien con el estilo default)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' dash-input').strip()


class CategoryForm(DashStyledFormMixin, forms.ModelForm):
    # Pedido del usuario (13/8): poder elegir la marca a mano en vez de
    # que quede fija por el dominio desde el que entrás al panel.
    class Meta:
        model = Category
        fields = ['name', 'brand', 'order', 'is_coming_soon']


class ProductForm(DashStyledFormMixin, forms.ModelForm):
    # brand no está en el form, mismo criterio que CategoryForm.
    def __init__(self, *args, brand=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brand:
            self.fields['category'].queryset = Category.objects.filter(brand=brand)

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'material', 'fit_notes',
            'price', 'status', 'is_limited_edition', 'license_status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'fit_notes': forms.Textarea(attrs={'rows': 2}),
        }


# Editor "Colores, talles y fotos" — versión simplificada respecto a
# la referencia de Las Manolas (memoria del proyecto): en vez de armar
# tarjetas por color con JS clonando el empty_form (patrón con un bug
# real ya documentado ahí, TOTAL_FORMS), se usan filas nativas de
# Django con `extra` fijo — cada fila de variante YA tiene su propio
# selector de color (hex) al lado del talle y el stock, cada fila de
# foto tiene su propio campo de color para asociarla. Menos vistoso
# que tarjetas agrupadas, misma funcionalidad completa, cero JS
# custom de formsets (pedido explícito: cuidar el uso).
_dash_input = {'class': 'dash-input'}

ProductVariantFormSet = inlineformset_factory(
    Product, ProductVariant,
    fields=['size', 'color', 'hex_color', 'stock', 'sku'],
    extra=12, can_delete=True,
    widgets={
        'size': forms.Select(attrs=_dash_input),
        'color': forms.TextInput(attrs=_dash_input),
        'hex_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-14 bg-transparent border border-white/15 rounded-lg'}),
        'stock': forms.NumberInput(attrs=_dash_input),
        'sku': forms.TextInput(attrs=_dash_input),
    },
)

# "Ofertas" — pedido del usuario (28/8): antes esta sección redirigía a
# /admin/ (Promociones ya estaba bien armada ahí, se linkeaba para no
# duplicar trabajo) — ahora pide que NO vaya al admin de Django, así
# que se arma acá con el mismo criterio que el resto del panel.
def _dt_local():
    # Función en vez de una única instancia compartida: Django usa el
    # widget que se le pase en Meta.widgets TAL CUAL (no lo clona al
    # armar los base_fields de la clase) — si el mismo objeto se
    # reutilizara para más de un campo, terminarían compartiendo el
    # mismo dict `.attrs` por izq. Cada campo pide su propia instancia.
    return forms.DateTimeInput(attrs={'type': 'datetime-local', **_dash_input})


class BrandPromotionForm(DashStyledFormMixin, forms.ModelForm):
    """Banner/urgencia GENERAL de la marca — un solo renglón por marca (ver modelo), por eso no tiene lista, se edita directo."""

    def __init__(self, *args, brand=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brand:
            self.fields['linked_promotion'].queryset = Promotion.objects.filter(brand=brand)
        self.fields['linked_promotion'].required = False

    class Meta:
        model = BrandPromotion
        fields = [
            'is_active', 'linked_promotion', 'message', 'link_url',
            'urgency_type', 'urgency_stock_limit', 'urgency_stock_remaining',
            'urgency_countdown_ends_at',
        ]
        widgets = {'urgency_countdown_ends_at': _dt_local()}


class PaymentDiscountForm(DashStyledFormMixin, forms.ModelForm):
    """Descuento por transferencia/efectivo — también un solo renglón por marca."""

    class Meta:
        model = PaymentDiscount
        fields = ['is_active', 'transferencia_percent', 'efectivo_percent', 'banner_text', 'countdown_ends_at']
        widgets = {'countdown_ends_at': _dt_local()}


class PromotionForm(DashStyledFormMixin, forms.ModelForm):
    """Regla "llevá X, llevate Y" (3x2 y variantes) — esta sí es una lista, puede haber varias por marca."""

    def __init__(self, *args, brand=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brand:
            self.fields['buy_category'].queryset = Category.objects.filter(brand=brand)
            self.fields['get_category'].queryset = Category.objects.filter(brand=brand)
        self.fields['get_category'].required = False

    class Meta:
        model = Promotion
        fields = [
            'name', 'badge_text', 'banner_text', 'is_active',
            'buy_category', 'buy_quantity', 'get_category', 'get_quantity', 'get_discount_percent',
            'starts_at', 'ends_at',
        ]
        widgets = {'starts_at': _dt_local(), 'ends_at': _dt_local()}


ProductImageFormSet = inlineformset_factory(
    Product, ProductImage,
    fields=['image', 'color', 'alt_text', 'is_primary', 'order'],
    extra=8, can_delete=True,
    widgets={
        'color': forms.TextInput(attrs={**_dash_input, 'placeholder': 'Ej: Negro (vacío = foto general)'}),
        'alt_text': forms.TextInput(attrs=_dash_input),
        'order': forms.NumberInput(attrs=_dash_input),
    },
)
