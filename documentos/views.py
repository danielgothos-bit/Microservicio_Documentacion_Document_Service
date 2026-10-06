import uuid

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .cifrado import descifrar
from .models import Documento, DocumentAccessLog
from .serializers import AccesoSerializer, CargaSerializer, DocumentoSerializer
from .servicios import guardar_documento, registrar_acceso


def usuario(request):
    """El API Gateway envía el usuario autenticado en X-User-Id."""
    try:
        return uuid.UUID(request.headers.get("X-User-Id", ""))
    except ValueError:
        return None


@api_view(["GET", "POST"])
def documentos(request):
    if request.method == "GET":
        qs = Documento.objects.order_by("-uploaded_at")
        return Response(DocumentoSerializer(qs, many=True).data)

    serializer = CargaSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    datos = serializer.validated_data
    archivo = datos.get("archivo")

    documento = guardar_documento(
        document_type=datos["document_type"],
        id_siniestro=datos.get("id_siniestro"),
        id_poliza=datos.get("id_poliza"),
        uploaded_by=datos.get("uploaded_by") or usuario(request),
        contenido=archivo.read() if archivo else None,
        nombre_archivo=archivo.name if archivo else "",
        content_type=getattr(archivo, "content_type", "") if archivo else "",
        file_url=datos.get("file_url", ""),
    )
    return Response(DocumentoSerializer(documento).data, status=status.HTTP_201_CREATED)


def _listar(request, **filtro):
    qs = list(Documento.objects.filter(**filtro).order_by("-uploaded_at"))
    for documento in qs:
        registrar_acceso(documento, DocumentAccessLog.LECTURA, usuario(request))
    return Response(DocumentoSerializer(qs, many=True).data)


@api_view(["GET"])
def documentos_por_siniestro(request, id):
    return _listar(request, id_siniestro=id)


@api_view(["GET"])
def documentos_por_poliza(request, id):
    return _listar(request, id_poliza=id)


@api_view(["GET"])
def documento_detalle(request, id):
    documento = get_object_or_404(Documento, id_documento=id)
    registrar_acceso(documento, DocumentAccessLog.LECTURA, usuario(request))
    return Response(DocumentoSerializer(documento).data)


@api_view(["GET"])
def documento_archivo(request, id):
    documento = get_object_or_404(Documento, id_documento=id)
    registrar_acceso(documento, DocumentAccessLog.DESCARGA, usuario(request))

    if documento.contenido is None:
        return HttpResponseRedirect(documento.file_url)

    respuesta = HttpResponse(descifrar(documento.contenido),
                             content_type=documento.content_type or "application/octet-stream")
    nombre = documento.nombre_archivo or f"{documento.id_documento}"
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return respuesta


@api_view(["GET"])
def documento_accesos(request, id):
    documento = get_object_or_404(Documento, id_documento=id)
    return Response(AccesoSerializer(documento.accesos.all(), many=True).data)
