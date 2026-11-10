from django.urls import path
from . import views

app_name = 'pacientes'
urlpatterns = [
    path('', views.listado, name='listado'),
    path('nuevo/', views.editar, name='nuevo'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/atenciones/nueva/', views.agregar_consulta, name='agregar_consulta'),
    path('<int:pk>/atenciones/<int:consulta_pk>/editar/', views.agregar_consulta, name='editar_consulta'),
]
