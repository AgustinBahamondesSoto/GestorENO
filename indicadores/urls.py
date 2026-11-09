from django.urls import path
from .views import panel

app_name = 'indicadores'
urlpatterns = [path('', panel, name='panel')]
