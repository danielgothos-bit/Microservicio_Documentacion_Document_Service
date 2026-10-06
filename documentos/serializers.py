from rest_framework import serializers

from .models import Documento, DocumentAccessLog

MAX_BYTES = 5 * 1024 * 1024  # 5 MB


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = [
            "id_documento",
            "id_siniestro",
            "id_poliza",
            "document_type",
            "file_url",
            "checksum",
            "uploaded_by",
            "uploaded_at",
            "encrypted",
            "nombre_archivo",
            "content_type",
        ]


class CargaSerializer(serializers.Serializer):
    """Carga por archivo (multipart, campo `archivo`) o por enlace externo (`file_url`)."""

    document_type = serializers.CharField(max_length=50)
    id_siniestro = serializers.UUIDField(required=False, allow_null=True)
    id_poliza = serializers.UUIDField(required=False, allow_null=True)
    uploaded_by = serializers.UUIDField(required=False, allow_null=True)
    archivo = serializers.FileField(required=False)
    file_url = serializers.CharField(required=False, allow_blank=False)

    def validate_archivo(self, archivo):
        if archivo.size > MAX_BYTES:
            raise serializers.ValidationError("El archivo supera los 5 MB.")
        return archivo

    def validate(self, data):
        if not data.get("archivo") and not data.get("file_url"):
            raise serializers.ValidationError("Envía un `archivo` o un `file_url`.")
        if not data.get("id_siniestro") and not data.get("id_poliza"):
            raise serializers.ValidationError("El documento debe pertenecer a un siniestro o a una póliza.")
        return data


class AccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAccessLog
        fields = ["id_log", "id_usuario", "action", "timestamp"]
