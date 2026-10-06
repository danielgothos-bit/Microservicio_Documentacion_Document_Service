import uuid
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from comun.eventos import INTERNAL_TOKEN

from .models import AccesoInmutable, Documento, DocumentAccessLog


@mock.patch("documentos.servicios.publicar")
class DocumentosTests(APITestCase):
    def evento(self, nombre, data):
        return self.client.post("/api/v1/eventos", {"event": nombre, "data": data},
                                format="json", HTTP_X_INTERNAL_TOKEN=INTERNAL_TOKEN)

    def test_subir_archivo_cifrado_y_descargar(self, publicar):
        siniestro = str(uuid.uuid4())
        archivo = SimpleUploadedFile("foto.jpg", b"contenido-de-la-foto", content_type="image/jpeg")
        resp = self.client.post("/api/v1/documentos", {
            "document_type": "evidencia_fotografica", "id_siniestro": siniestro, "archivo": archivo,
        }, format="multipart")

        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data["encrypted"])
        self.assertEqual(len(resp.data["checksum"]), 64)
        self.assertEqual(publicar.call_args[0][0], "document.uploaded")

        documento = Documento.objects.get(pk=resp.data["id_documento"])
        self.assertNotIn(b"contenido-de-la-foto", bytes(documento.contenido))  # guardado cifrado

        resp = self.client.get(f"/api/v1/documentos/{documento.pk}/archivo")
        self.assertEqual(resp.content, b"contenido-de-la-foto")

        resp = self.client.get(f"/api/v1/documentos/siniestro/{siniestro}")
        self.assertEqual(len(resp.data), 1)

        acciones = [a["action"] for a in self.client.get(f"/api/v1/documentos/{documento.pk}/accesos").data]
        self.assertEqual(acciones, ["carga", "descarga", "lectura"])

    def test_documento_por_enlace(self, publicar):
        resp = self.client.post("/api/v1/documentos", {
            "document_type": "poliza_pdf", "id_poliza": str(uuid.uuid4()), "file_url": "https://storage/poliza.pdf",
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data["encrypted"])

    def test_validaciones(self, publicar):
        resp = self.client.post("/api/v1/documentos", {"document_type": "x", "file_url": "https://a"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_log_es_solo_insercion(self, publicar):
        doc = Documento.objects.create(document_type="x", file_url="https://a")
        log = DocumentAccessLog.objects.create(documento=doc, action="lectura")
        with self.assertRaises(AccesoInmutable):
            log.save()
        with self.assertRaises(AccesoInmutable):
            log.delete()
        with self.assertRaises(AccesoInmutable):
            DocumentAccessLog.objects.all().update(action="carga")

    def test_eventos_generan_informe_y_comprobante(self, publicar):
        siniestro = str(uuid.uuid4())
        self.evento("inspection.completed", {"id_siniestro": siniestro, "findings": "Daño leve"})
        pago = {"payment_id": str(uuid.uuid4()), "tipo": "indemnizacion", "id_siniestro": siniestro,
                "referencia_id": siniestro, "amount": "1000.00", "method": "transferencia"}
        self.evento("payment.completed", pago)
        self.evento("payment.completed", pago)  # repetido: no duplica

        tipos = sorted(d["document_type"] for d in self.client.get(f"/api/v1/documentos/siniestro/{siniestro}").data)
        self.assertEqual(tipos, ["comprobante_pago", "informe_pericial"])
