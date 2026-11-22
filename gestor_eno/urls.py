from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from two_factor.admin import AdminSiteOTPRequired
from two_factor.urls import urlpatterns as rutas_mfa


# Conserva las inscripciones existentes del administrador y exige OTP.
admin.site.__class__ = AdminSiteOTPRequired

urlpatterns = [
    path('', include(rutas_mfa)),
    path('admin/', admin.site.urls),
    # La dirección antigua solo redirige. Ya no autentica con contraseña sola.
    path(
        'cuentas/entrar/',
        RedirectView.as_view(
            pattern_name='two_factor:login',
            query_string=True,
        ),
        name='login',
    ),
    path('cuentas/salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('indicadores.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('importaciones/', include('importaciones.urls')),
    path('reportes/', include('reportes.urls')),
    path('clasificacion/', include('clasificacion.urls')),
]
