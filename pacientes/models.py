from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .validators import normalizar_rut


class Paciente(models.Model):
    rut = models.CharField('RUT', max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200, blank=True)
    domicilio_comuna = models.CharField('domicilio y comuna', max_length=300, blank=True)
    edad = models.PositiveSmallIntegerField(validators=[MaxValueValidator(130)])
    sexo = models.CharField(max_length=30)
    prevision = models.CharField('previsión', max_length=100)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre', 'rut']

    def clean(self):
        super().clean()
        self.rut = normalizar_rut(self.rut)

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.rut} · {self.nombre_completo}'

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'.strip()


class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, related_name='consultas', on_delete=models.PROTECT)
    importacion = models.ForeignKey('importaciones.Importacion', related_name='consultas', on_delete=models.PROTECT)
    fila = models.PositiveIntegerField()
    huella = models.CharField(max_length=64, unique=True, editable=False)
    fecha = models.DateField(null=True, blank=True)
    registrada = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200, blank=True)
    domicilio_comuna = models.CharField('domicilio y comuna', max_length=300, blank=True)
    enfermedades_declaradas = models.TextField('enfermedades crónicas o complicaciones de la planilla', blank=True)
    ultimas_consultas = models.TextField('últimas consultas de la planilla', blank=True)
    destino = models.CharField('destino del paciente', max_length=200, blank=True)
    condicion_declarada = models.CharField('condición indicada en la planilla', max_length=100, blank=True)
    edad = models.PositiveSmallIntegerField(validators=[MaxValueValidator(130)])
    peso = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    sexo = models.CharField(max_length=30)
    prevision = models.CharField(max_length=100)
    antecedentes = models.TextField(blank=True)
    signos_vitales = models.TextField(blank=True)
    clasificacion = models.CharField(max_length=20, choices=[('ENO', 'ENO'), ('GES_AUGE', 'GES/AUGE'), ('SIN_ANTECEDENTES', 'Sin antecedentes')], default='SIN_ANTECEDENTES')
    enfermedades = models.JSONField(default=list, blank=True)
    reglas_aplicadas = models.JSONField(default=list, blank=True)
    eno_notificado = models.BooleanField('notificación ENO registrada', default=False)
    ges_vigente = models.BooleanField('seguimiento GES vigente', default=False)

    class Meta:
        ordering = ['-fecha', '-registrada', '-pk']

    def __str__(self):
        return f'{self.paciente.rut} · consulta {self.pk}'

# Create your models here.
