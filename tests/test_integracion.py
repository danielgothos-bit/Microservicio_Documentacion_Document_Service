"""Prueba de integración: endpoint + lógica de negocio + base de datos funcionando juntos."""
import uuid
from unittest import mock

from rest_framework.test import APITestCase

from comun.eventos import INTERNAL_TOKEN
from documentos.models import Documento


@mock.patch("documentos.servicios.publicar")
class DocumentosIntegracionTests(APITestCase):
    def test_evento_de_pago_genera_comprobante_descargable(self, publicar):
        id_sin = str(uuid.uuid4())
        datos = {"payment_id": str(uuid.uuid4()), "tipo": "indemnizacion", "id_siniestro": id_sin, "referencia_id": id_sin,
                 "amount": "3500000", "method": "transferencia", "paid_at": "2026-11-17T10:00:00Z"}
        resp = self.client.post("/api/v1/eventos", {"event": "payment.completed", "data": datos, "event_id": str(uuid.uuid4())},
                                format="json", HTTP_X_INTERNAL_TOKEN=INTERNAL_TOKEN)
        self.assertIn(resp.status_code, (200, 202))
        doc = Documento.objects.get(id_siniestro=id_sin, document_type="comprobante_pago")
        archivo = self.client.get(f"/api/v1/documentos/{doc.pk}/archivo")
        self.assertEqual(archivo.status_code, 200)
        self.assertIn(b"COMPROBANTE DE PAGO", archivo.content)
