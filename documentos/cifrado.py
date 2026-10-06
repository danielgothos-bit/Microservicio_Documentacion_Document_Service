"""
Cifrado en reposo de los archivos (sección 4.6).

Usa Fernet (AES-128 + HMAC). La clave sale de DOCUMENT_ENCRYPTION_KEY; si no está
definida, se deriva de JWT_SECRET (solo recomendable en desarrollo).
"""
import base64
import hashlib
import os

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    clave = os.getenv("DOCUMENT_ENCRYPTION_KEY")
    if not clave:
        clave = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(clave)


def cifrar(datos: bytes) -> bytes:
    return _fernet().encrypt(datos)


def descifrar(datos: bytes) -> bytes:
    return _fernet().decrypt(bytes(datos))


def checksum(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()
