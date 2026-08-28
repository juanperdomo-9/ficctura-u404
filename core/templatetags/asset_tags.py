import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    """
    Como {% static %}, pero le agrega ?v=<mtime del archivo> para que el
    navegador nunca sirva una versión vieja cacheada de CSS/JS después de
    un cambio — nos pasó varias veces durante el desarrollo del gateway.

    Solo mira STATICFILES_DIRS (desarrollo). Después de collectstatic en
    producción, el mtime en STATIC_ROOT puede no reflejar el último commit
    si el deploy no copia timestamps — no es un problema hoy, pero si se
    nota en producción hay que migrar a ManifestStaticFilesStorage.
    """
    url = static(path)

    for static_dir in settings.STATICFILES_DIRS:
        candidate = os.path.join(static_dir, path)
        if os.path.exists(candidate):
            return f"{url}?v={int(os.path.getmtime(candidate))}"

    return url
