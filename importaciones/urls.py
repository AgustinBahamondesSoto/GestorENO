from django.urls import path
from . import views

app_name = 'importaciones'
urlpatterns = [
    path('', views.importar, name='importar'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/eliminar/', views.eliminar, name='eliminar'),
]
