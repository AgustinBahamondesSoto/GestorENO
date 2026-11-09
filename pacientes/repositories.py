from abc import ABC, abstractmethod

from .models import Paciente
from .validators import normalizar_rut


class RepositorioPacientes(ABC):
    @abstractmethod
    def obtener_o_crear(self, rut, datos):
        raise NotImplementedError

    @abstractmethod
    def consultar(self):
        raise NotImplementedError


class RepositorioDjango(RepositorioPacientes):
    def obtener_o_crear(self, rut, datos):
        return Paciente.objects.get_or_create(rut=normalizar_rut(rut), defaults=datos)

    def consultar(self):
        return Paciente.objects.all()
