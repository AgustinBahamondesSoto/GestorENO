from django.contrib import admin
from .models import Paciente, Consulta

# Register your models here.
@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido', 'edad', 'sexo', 'prevision')
    search_fields = ('rut', 'nombre', 'apellido')
    readonly_fields = ('rut', 'nombre', 'apellido', 'domicilio_comuna', 'edad', 'sexo', 'prevision', 'actualizado')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha', 'clasificacion', 'eno_notificado', 'ges_vigente')
    list_filter = ('clasificacion', 'eno_notificado', 'ges_vigente')
    search_fields = ('paciente__rut', 'paciente__nombre')
    readonly_fields = tuple(f.name for f in Consulta._meta.fields if f.name not in ('eno_notificado', 'ges_vigente'))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
