from django.contrib import admin
from .models import ReglaClasificacion


@admin.register(ReglaClasificacion)
class ReglaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'enfermedad', 'categoria', 'tipo', 'prioridad', 'activa')
    list_filter = ('categoria', 'tipo', 'activa')
    search_fields = ('nombre', 'enfermedad', 'patron')

# Register your models here.
