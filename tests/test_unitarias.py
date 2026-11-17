"""Pruebas unitarias: una unidad de lógica de negocio aislada; las dependencias externas se simulan con mocks."""
from django.test import SimpleTestCase, TestCase

from documentos.cifrado import checksum, cifrar, descifrar
from documentos.models import AccesoInmutable, DocumentAccessLog, Documento


class CifradoUnitTests(SimpleTestCase):
    def test_cifrar_y_descifrar_conserva_el_contenido(self):
        original = "Informe pericial confidencial".encode()
        cifrado = cifrar(original)
        self.assertNotEqual(cifrado, original)
        self.assertEqual(descifrar(cifrado), original)
        self.assertEqual(len(checksum(original)), 64)


class AuditoriaUnitTests(TestCase):
    def test_bitacora_de_accesos_no_permite_modificar(self):
        doc = Documento.objects.create(document_type="comprobante_pago", file_url="interno://x")
        log = DocumentAccessLog.objects.create(documento=doc, action="lectura")
        with self.assertRaises(AccesoInmutable):
            DocumentAccessLog.objects.filter(pk=log.pk).update(action="descarga")
