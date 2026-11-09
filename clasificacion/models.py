from django.db import models
from django.core.exceptions import ValidationError
import re


class ReglaClasificacion(models.Model):
    nombre = models.CharField(max_length=150)
    enfermedad = models.CharField(max_length=150)
    categoria = models.CharField(max_length=10, choices=[('ENO', 'ENO'), ('GES_AUGE', 'GES/AUGE')])
    tipo = models.CharField(max_length=10, choices=[('PALABRA', 'Palabra clave'), ('REGEX', 'Expresión regular')])
    patron = models.CharField('patrón', max_length=300)
    prioridad = models.PositiveIntegerField(default=100, help_text='Menor número se aplica primero si hay varias categorías.')
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['prioridad', 'pk']
        verbose_name = 'regla de clasificación'
        verbose_name_plural = 'reglas de clasificación'

    def clean(self):
        super().clean()
        if self.tipo == 'REGEX':
            try:
                re.compile(self.patron)
            except re.error as exc:
                raise ValidationError({'patron': f'Expresión regular inválida: {exc}'})
        if not self.patron.strip():
            raise ValidationError({'patron': 'El patrón no puede estar vacío.'})

    def __str__(self):
        return self.nombre

# Create your models here.
