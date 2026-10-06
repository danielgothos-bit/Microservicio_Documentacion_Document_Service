# Microservicio de Documentación — Document Service

Microservicio de InsureFlow definido en la sección 4.6 del documento de arquitectura.

## Responsabilidad

Almacenar de forma segura (cifrada) pólizas, informes periciales, comprobantes y evidencia de siniestros, con auditoría de cada acceso.

## Tecnología

Python · Django REST Framework · PostgreSQL (`document_db`) · Celery + Redis · Docker

## Modelo de datos (3FN, IDs UUID)

`documento` (checksum SHA-256, contenido cifrado con Fernet) y `document_access_log` (solo inserción).

## Endpoints

```
POST /api/v1/documentos — cargar documento (multipart `archivo`) o enlace (`file_url`)
GET  /api/v1/documentos/{id} — metadatos del documento
GET  /api/v1/documentos/{id}/archivo — descargar archivo
GET  /api/v1/documentos/{id}/accesos — auditoría de accesos
GET  /api/v1/documentos/siniestro/{id} — documentos de un siniestro
GET  /api/v1/documentos/poliza/{id} — documentos de una póliza
GET  /health — estado del servicio y de su base de datos
POST /api/v1/eventos — endpoint interno donde otros microservicios entregan eventos
```

## Eventos

Publica:
- document.uploaded

Consume:
- inspection.completed (informe pericial)
- payment.completed (comprobante)

Los eventos se encolan con Celery/Redis y se entregan por HTTP al endpoint `/api/v1/eventos` de cada
suscriptor, con reintentos y backoff exponencial (módulo `comun/eventos.py`). Cada evento se procesa una
sola vez (idempotencia por `event_id`).

## Variables de entorno

- `DATABASE_URL`, `REDIS_URL`: base de datos y Redis propios
- `INTERNAL_TOKEN`: token compartido por todos los microservicios para los eventos
- `RUN_WORKER_IN_WEB=1`: corre el worker de Celery dentro del mismo contenedor (Render gratis)
- `SYNC_TIMEOUT`: timeout de las llamadas REST síncronas (3 s por defecto)
- `CLAIMS_SERVICE_URL`: microservicio de Siniestros

Si una URL no está configurada, el servicio funciona en modo aislado (omite esa validación o ese evento).

## Ejecución local

```bash
docker compose up --build
```

El servicio queda en http://localhost:8005 y las migraciones se aplican solas al arrancar.

Pruebas:

```bash
docker compose exec document_service python manage.py test documentos
```

## Despliegue en Render

En Render: **New → Blueprint** → conectar este repositorio → **Deploy Blueprint**.
El `render.yaml` crea el servicio web, su PostgreSQL y su Redis (plan gratis).
