from django.db import transaction

from comun.eventos import publicar

from .cifrado import checksum, cifrar
from .models import Documento, DocumentAccessLog


def registrar_acceso(documento, accion, id_usuario=None):
    DocumentAccessLog.objects.create(documento=documento, action=accion, id_usuario=id_usuario)


@transaction.atomic
def guardar_documento(document_type, id_siniestro=None, id_poliza=None, uploaded_by=None,
                      contenido=None, nombre_archivo="", content_type="", file_url=""):
    """
    Guarda un documento. Si trae `contenido` (bytes) se cifra y se almacena en el servicio;
    si trae `file_url` se guarda solo la referencia al almacenamiento externo.
    """
    documento = Documento(
        document_type=document_type,
        id_siniestro=id_siniestro,
        id_poliza=id_poliza,
        uploaded_by=uploaded_by,
        nombre_archivo=nombre_archivo,
        content_type=content_type,
        file_url=file_url,
    )
    if contenido is not None:
        documento.checksum = checksum(contenido)
        documento.contenido = cifrar(contenido)
        documento.encrypted = True
        documento.file_url = f"/api/v1/documentos/{documento.id_documento}/archivo"
    documento.save()

    registrar_acceso(documento, DocumentAccessLog.CARGA, uploaded_by)

    publicar("document.uploaded", {
        "id_documento": documento.id_documento,
        "id_siniestro": documento.id_siniestro,
        "id_poliza": documento.id_poliza,
        "document_type": documento.document_type,
    })
    return documento
