from django.db import models
from django.core.exceptions import ValidationError
import re
import unicodedata


def clave_enfermedad(nombre):
    texto = ' '.join(nombre.split()).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


class Enfermedad(models.Model):
    nombre = models.CharField(max_length=150)
    clave = models.CharField(max_length=150, unique=True, editable=False)

    class Meta:
        ordering = ['nombre', 'pk']
        verbose_name_plural = 'enfermedades'

    def save(self, *args, **kwargs):
        self.nombre = ' '.join(self.nombre.split())
        self.clave = clave_enfermedad(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


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
