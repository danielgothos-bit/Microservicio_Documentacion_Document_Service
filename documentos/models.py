import uuid

from django.db import models
from django.db.models import Q


class Documento(models.Model):
    id_documento = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_siniestro = models.UUIDField(blank=True, null=True)  # FK-ext -> Claims Service
    id_poliza = models.UUIDField(blank=True, null=True)  # FK-ext -> Policy Service
    document_type = models.CharField(max_length=50)
    file_url = models.TextField()
    checksum = models.CharField(max_length=64, blank=True)  # SHA-256 del archivo original
    uploaded_by = models.UUIDField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    encrypted = models.BooleanField(default=False)
    # Contenido cifrado del archivo (cuando se sube al servicio en lugar de un enlace externo).
    nombre_archivo = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    contenido = models.BinaryField(blank=True, null=True)

    class Meta:
        db_table = "documento"
        indexes = [
            models.Index(fields=["id_siniestro"], name="idx_documento_siniestro"),
            models.Index(fields=["id_poliza"], name="idx_documento_poliza"),
        ]

    def __str__(self):
        return f"{self.document_type} - {self.id_documento}"


class AccesoInmutable(Exception):
    pass


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise AccesoInmutable("document_access_log es de solo inserción.")

    def delete(self):
        raise AccesoInmutable("document_access_log es de solo inserción.")


class DocumentAccessLog(models.Model):
    """Auditoría de accesos: solo inserción, sin UPDATE ni DELETE (sección 5.6)."""

    LECTURA, DESCARGA, MODIFICACION, CARGA = "lectura", "descarga", "modificacion", "carga"
    ACTION_CHOICES = [(LECTURA, "Lectura"), (DESCARGA, "Descarga"), (MODIFICACION, "Modificación"), (CARGA, "Carga")]

    id_log = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT, related_name="accesos", db_column="id_documento")
    id_usuario = models.UUIDField(blank=True, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = "document_access_log"
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["documento"], name="idx_document_access_log_doc"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(action__in=["lectura", "descarga", "modificacion", "carga"]),
                name="chk_access_log_action",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AccesoInmutable("document_access_log es de solo inserción.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AccesoInmutable("document_access_log es de solo inserción.")
