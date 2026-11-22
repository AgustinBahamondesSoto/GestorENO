from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from two_factor.utils import default_device


class MFAObligatoriaMiddleware(MiddlewareMixin):
    """Exige una sesión verificada antes de acceder a funciones del sistema."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            # Las vistas del proyecto mantienen su requisito de inicio de sesión.
            return None

        nombre = request.resolver_match.view_name
        if nombre in {'login', 'logout', 'two_factor:login'}:
            return None

        if request.user.is_verified():
            return None

        tiene_dispositivo = default_device(request.user) is not None
        if not tiene_dispositivo:
            if nombre in {'two_factor:setup', 'two_factor:qr'}:
                return None
            return redirect('two_factor:setup')

        # Un usuario que ya tiene MFA debe verificarlo antes de reconfigurarlo.
        return redirect_to_login(
            request.get_full_path(),
            login_url=reverse('two_factor:login'),
        )
