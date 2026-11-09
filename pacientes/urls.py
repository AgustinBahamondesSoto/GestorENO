from django.urls import path
from . import views

app_name = 'pacientes'
urlpatterns = [path('', views.listado, name='listado'), path('<int:pk>/', views.detalle, name='detalle')]
