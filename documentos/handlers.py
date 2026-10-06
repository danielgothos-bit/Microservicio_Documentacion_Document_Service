"""
Eventos que consume el microservicio de Documentación (sección 4.6 y paso 14 del diagrama).

inspection.completed -> guarda el informe pericial como evidencia del siniestro
payment.completed    -> genera y guarda el comprobante de pago
"""
from .models import Documento
from .servicios import guardar_documento


def on_inspection_completed(data):
    id_siniestro = data.get("id_siniestro")
    if Documento.objects.filter(id_siniestro=id_siniestro, document_type="informe_pericial").exists():
        return

    if data.get("report_url"):
        guardar_documento("informe_pericial", id_siniestro=id_siniestro, file_url=data["report_url"])
    else:
        texto = (
            "INFORME PERICIAL\n"
            f"Siniestro: {id_siniestro}\n"
            f"Inspección: {data.get('id_inspeccion')}\n"
            f"Perito: {data.get('id_perito')}\n"
            f"Fecha: {data.get('completed_at')}\n\n"
            f"Hallazgos:\n{data.get('findings', '')}\n"
        )
        guardar_documento("informe_pericial", id_siniestro=id_siniestro, contenido=texto.encode("utf-8"),
                          nombre_archivo="informe_pericial.txt", content_type="text/plain; charset=utf-8")


def on_payment_completed(data):
    id_siniestro = data.get("id_siniestro") if data.get("tipo") == "indemnizacion" else None
    id_poliza = data.get("id_poliza") if data.get("tipo") == "prima" else None
    nombre = f"comprobante_{data.get('payment_id')}.txt"
    if Documento.objects.filter(document_type="comprobante_pago", nombre_archivo=nombre).exists():
        return

    texto = (
        "COMPROBANTE DE PAGO - INSUREFLOW\n"
        f"Pago: {data.get('payment_id')}\n"
        f"Tipo: {data.get('tipo')}\n"
        f"Referencia: {data.get('referencia_id')}\n"
        f"Monto: {data.get('amount')}\n"
        f"Método: {data.get('method')}\n"
        f"Fecha de pago: {data.get('paid_at')}\n"
    )
    guardar_documento("comprobante_pago", id_siniestro=id_siniestro, id_poliza=id_poliza,
                      contenido=texto.encode("utf-8"), nombre_archivo=nombre,
                      content_type="text/plain; charset=utf-8")


HANDLERS = {
    "inspection.completed": on_inspection_completed,
    "payment.completed": on_payment_completed,
}
