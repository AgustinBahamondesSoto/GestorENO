from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from .cifrado import cifrar_texto, descifrar_texto


@override_settings(CLAVE_CIFRADO=Fernet.generate_key())
class CifradoTests(SimpleTestCase):
    def test_recupera_texto_con_tildes(self):
        original = 'Paciente ficticio: diagnóstico y presión arterial.'
        cifrado = cifrar_texto(original)

        self.assertNotIn(original, cifrado)
        self.assertEqual(descifrar_texto(cifrado), original)

    def test_recupera_texto_vacio(self):
        cifrado = cifrar_texto('')

        self.assertNotEqual(cifrado, '')
        self.assertEqual(descifrar_texto(cifrado), '')

    def test_rechaza_clave_diferente(self):
        cifrado = cifrar_texto('Antecedente ficticio')

        with override_settings(CLAVE_CIFRADO=Fernet.generate_key()):
            with self.assertRaises(InvalidToken):
                descifrar_texto(cifrado)

    def test_rechaza_contenido_alterado(self):
        cifrado = cifrar_texto('Antecedente ficticio')
        posicion = len(cifrado) // 2
        reemplazo = 'A' if cifrado[posicion] != 'A' else 'B'
        alterado = (
            cifrado[:posicion]
            + reemplazo
            + cifrado[posicion + 1:]
        )

        with self.assertRaises(InvalidToken):
            descifrar_texto(alterado)

    @override_settings(CLAVE_CIFRADO=b'clave-invalida')
    def test_rechaza_clave_mal_formada(self):
        with self.assertRaises(ImproperlyConfigured):
            cifrar_texto('Antecedente ficticio')