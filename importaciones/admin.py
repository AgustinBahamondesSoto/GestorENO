from django.contrib import admin
from .models import Importacion, Inconsistencia


class InconsistenciaInline(admin.TabularInline):
    model = Inconsistencia
    extra = 0
    readonly_fields = ('fila', 'tipo', 'motivo')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Importacion)
class ImportacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'archivo', 'creada', 'total', 'validas', 'invalidas', 'omitidas')
    readonly_fields = tuple(f.name for f in Importacion._meta.fields)
    inlines = [InconsistenciaInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Register your models here.
