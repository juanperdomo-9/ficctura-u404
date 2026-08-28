from django import template

register = template.Library()


@register.filter
def pesos(value):
    """
    Formatea un precio como "$ 24.999" — sin decimales, separador de
    miles con punto (formato AR). Si no hay precio cargado todavía
    (campo nullable a propósito, ver catalog/models.py), muestra
    "Consultar" en vez de un $0 o un vacío confuso.
    """
    if value is None:
        return "Consultar"

    try:
        amount = int(round(float(value)))
    except (TypeError, ValueError):
        return value

    return f"$ {amount:,}".replace(",", ".")


@register.filter
def dict_get(mapping, key):
    """Django no deja hacer {{ mi_dict.key_variable }} con una clave que es otra variable — este filtro es el atajo."""
    return mapping.get(key)
