from django.db import models
from django.conf import settings


class Importacion(models.Model):
    archivo = models.CharField(max_length=255)
    creada = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    total = models.PositiveIntegerField(default=0)
    validas = models.PositiveIntegerField(default=0)
    invalidas = models.PositiveIntegerField(default=0)
    omitidas = models.PositiveIntegerField(default=0)
    pacientes_nuevos = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-creada', '-pk']
        verbose_name_plural = 'importaciones'

    def __str__(self):
        return f'Importación {self.pk} · {self.archivo}'


class Inconsistencia(models.Model):
    importacion = models.ForeignKey(Importacion, related_name='inconsistencias', on_delete=models.CASCADE)
    fila = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, choices=[('ERROR', 'Error'), ('CONFLICTO', 'Conflicto de datos')])
    motivo = models.TextField()

    class Meta:
        ordering = ['fila', 'pk']

# Create your models here.
