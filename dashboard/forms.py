from django import forms
from django.forms import inlineformset_factory

from catalog.models import Category, Product, ProductImage, ProductVariant


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
