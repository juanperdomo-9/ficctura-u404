from functools import wraps

from django.contrib.auth.views import redirect_to_login


def staff_required(view):
    """
    Panel propio (no /admin/) — pedido del usuario (13/8), estilo del
    panel de Las Manolas (ver memoria del proyecto). Login separado del
    admin de Django: si no hay sesión de staff, manda a dashboard:login.
    """
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect_to_login(request.get_full_path(), login_url='dashboard:login')
        return view(request, *args, **kwargs)
    return wrapped
