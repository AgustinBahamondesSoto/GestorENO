from django.urls import path
from . import views

app_name = 'clasificacion'
urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('enfermedades/nueva/', views.enfermedad_nueva, name='enfermedad_nueva'),
    path('reglas/nueva/', views.regla_editar, name='regla_nueva'),
    path('reglas/<int:pk>/editar/', views.regla_editar, name='regla_editar'),
    path('reclasificar/', views.reclasificar, name='reclasificar'),
]
