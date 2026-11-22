"""Prepara secretos locales sin mostrar ni reemplazar claves existentes."""
from pathlib import Path
import secrets
import sqlite3

from cryptography.fernet import Fernet


def main():
    raiz = Path(__file__).resolve().parent.parent
    clave_cifrado = raiz / '.env.clave_cifrado'
    base = raiz / 'db.sqlite3'
    if base.exists() and not clave_cifrado.exists():
        with sqlite3.connect(f'file:{base.as_posix()}?mode=ro', uri=True) as conexion:
            tiene_migraciones = conexion.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='django_migrations'"
            ).fetchone()
            cifrado_aplicado = tiene_migraciones and conexion.execute(
                "SELECT 1 FROM django_migrations WHERE app=? AND name=?",
                ('pacientes', '0005_cifrado_clinico'),
            ).fetchone()
        if cifrado_aplicado:
            raise SystemExit('La base ya fue cifrada. Recupera su clave original antes de continuar.')
    for ruta, generar in (
        (clave_cifrado, Fernet.generate_key),
        (raiz / '.env.secret_django', lambda: secrets.token_urlsafe(64).encode('ascii')),
    ):
        try:
            with ruta.open('xb') as archivo:
                archivo.write(generar())
        except FileExistsError:
            print(f'{ruta.name}: conservada.')
        else:
            print(f'{ruta.name}: creada.')


if __name__ == '__main__':
    main()
