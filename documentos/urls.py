from django.urls import path

from . import views

urlpatterns = [
    path("api/v1/documentos", views.documentos),
    path("api/v1/documentos/<uuid:id>", views.documento_detalle),
    path("api/v1/documentos/<uuid:id>/archivo", views.documento_archivo),
    path("api/v1/documentos/<uuid:id>/accesos", views.documento_accesos),
    path("api/v1/documentos/siniestro/<uuid:id>", views.documentos_por_siniestro),
    path("api/v1/documentos/poliza/<uuid:id>", views.documentos_por_poliza),
]
