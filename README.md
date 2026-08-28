# FICCTURA + UNIVERSO 404 — ecommerce

Proyecto de dos marcas relacionadas (FICCTURA: básicos premium / UNIVERSO 404: remeras con estampas y narrativa) que comparten backend y catálogo/carrito, según el brief del cliente. Ver `brief/` para los documentos originales.

## Stack

Mismo stack que el proyecto regalbox: Django + SQLite + Tailwind CSS v4 (CLI) + JS vanilla.

## Arquitectura de dos marcas

Un solo proyecto Django sirve las dos webs. La marca activa se resuelve por **host** en `core/middleware.py::BrandMiddleware`, mapeado en `config/settings.py::BRAND_HOSTS`:

- `www.universo404.com.ar` → marca `u404`
- `ficctura.com.ar` → marca `ficctura`

En desarrollo local no se puede simular dos hosts reales sin tocar el archivo `hosts` del sistema, así que se distinguen **por puerto**:

- U404 → `http://localhost:8010`
- FICCTURA → `http://localhost:8011`

Los templates viven separados por marca (`templates/u404/`, `templates/ficctura/`) porque el brief pide identidades visuales distintas; el `core` app (modelos, vistas, carrito) es compartido.

## Correr el proyecto

```bash
venv/Scripts/python.exe manage.py runserver 8010   # U404
venv/Scripts/python.exe manage.py runserver 8011   # FICCTURA
```

CSS (Tailwind):

```bash
npm run watch:css
```

## Estado actual

Scaffold técnico inicial: Django + Tailwind + routing por marca + home placeholder de cada sitio. **No hay catálogo, carrito, checkout ni pagos implementados todavía** — varios datos necesarios (paleta, tipografías, tabla de talles, precio final, medio de pago activado) están pendientes de confirmación del cliente. Ver `brief/preguntas-pendientes-cliente.md`.
