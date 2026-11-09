from django.urls import path
from . import views

app_name = 'reportes'
urlpatterns = [path('excel/', views.exportar, name='exportar'), path('plantilla/', views.plantilla, name='plantilla')]
