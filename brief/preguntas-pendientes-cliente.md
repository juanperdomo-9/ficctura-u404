# Preguntas pendientes para el cliente — FICCTURA / UNIVERSO 404

Recopiladas del brief y el informe de onboarding. Todo lo que sigue está marcado explícitamente como PENDIENTE, PROPUESTO (sin cierre) o "no definir por cuenta propia" en los documentos del cliente — no se puede avanzar en desarrollo real sin estas respuestas.

## 1. Identidad visual
- [ ] Paleta de colores de FICCTURA (confirmado por audio: va a ser *distinta* a la de U404, pero los colores en sí siguen sin elegir).
- [ ] Paleta de colores de UNIVERSO 404 (ídem).
- [ ] Tipografía a usar (confirmado por audio: es **una sola, compartida** entre las dos marcas — ya no hace falta elegir dos. Falta elegir cuál).
- [x] ~~Logo de FICCTURA~~ — apareció en el informe de onboarding (planilla de marca completa): wordmark + ícono "FF" limpios, ya extraídos y en uso en el sitio (`static/img/ficctura-logo.png`, `ficctura-icon.png`).
- [ ] Archivo final del **wordmark** de UNIVERSO 404 con el nombre correcto: el informe solo trae la planilla vieja "UNIFORME 404" (nombre desactualizado). **El ícono/símbolo sí se pudo extraer y ya está en el sitio** (`static/img/u404-icon.png` — el propio informe confirma que el símbolo se mantiene al pasar de "Uniforme" a "Universo"), pero el logo con el texto "UNIVERSO 404" bien armado no vino en la exportación. ¿Nos pueden pasar ese archivo?
- [ ] Aplicaciones de marca ("A DESARROLLAR" en ambos manuales) — ¿hay lineamientos más allá del logo (uso en productos, redes, packaging)?

## 2. Arquitectura de las dos webs
- [ ] ¿FICCTURA va a tener checkout propio, o toda venta se redirige/unifica en el checkout de U404? (Explícitamente pendiente en el brief — "debe resolverse antes de implementar pagos en FICCTURA".)
- [ ] Confirmar: ¿las básicas FICCTURA se muestran dentro del catálogo de U404 identificadas como "Básicas FICCTURA", tal como quedó escrito el 7/8?

## 3. Producto y talles
- [ ] Tabla final de talles y medidas completas (incluyendo circunferencia/medida a la altura del ombligo). ¿La tiene el taller? ¿Cuándo la tienen lista?
- [ ] Fecha estimada de fotos reales del producto (la muestra impresa se había atrasado por rehacer la matriz; al 8/8 se esperaba para el martes siguiente — ¿ya está lista?)
- [ ] ¿Cuál de las remeras estampadas queda sin estampa en la espalda? (mencionado como "idea discutida el 7/8", sin cerrar)

## 4. Precios y promociones
- [ ] Precio final de lista por básica y por estampada (se habló de un piso de $35.000 / $38.000 el 5/8, pero no está confirmado como definitivo).
- [ ] Porcentaje final de descuento por pago con transferencia.
- [ ] Condiciones y costo real de las 3 cuotas con tarjeta.
- [ ] Números finales de los packs (Junior, Senior, Team Leader, CEO) — el naming/copy ya está aprobado, pero los montos deben revalidarse con precio final.
- [ ] Política de preventa: ¿se confirma o se descarta? (quedó "propuesta pero no confirmada")

## 5. Pagos y facturación
- [ ] CUIT / datos de facturación para activar Payway (paso bloqueante para habilitar tarjeta). **La integración con Payway (motor Decidir) ya está construida y lista en el código** (`catalog/payments.py`) — funciona con transferencia/efectivo ya mismo, y "tarjeta" se activa solo apenas carguemos las claves reales que Payway manda junto con la aprobación del CUIT. Cuando las tengan: pasarlas para cargarlas en el `.env` y hacer la primera prueba de cobro en sandbox.
- [ ] ¿Quién es la persona/entidad que factura lo que ingrese por tarjeta?

## 6. Envío
- [ ] Tarifas definitivas de envío por zona (correo / mensajería / retiro).
- [ ] Umbral de compra para envío gratis (se habló de "desde 3 remeras" como propuesta, sin cerrar).
- [ ] ¿Ya eligieron integrador de logística, o lo definimos junto con el desarrollo?

## 7. Catálogo y licencias
- [ ] ¿Qué diseños de la tanda "sin licencia" del 7/8 entran primero a producción/catálogo, y cuáles quedan como "disponible" vs. "agotado" vs. "próximamente"?
- [ ] Estado de la gestión de licencias para los diseños con bandas reales (GNR, AC/DC) — ¿se van a conseguir, o esos modelos quedan descartados/reemplazados por las versiones ficticias?
- [ ] Línea oversize 15–25 años (6 diseños exploratorios): ¿entra como cápsula dentro de U404, como marca aparte, o queda descartada por ahora?
- [ ] Confirmar el diseño "CBGB" queda fuera del catálogo por tema de licencia (el propio chat lo marca así) — ¿reemplazado 100% por la versión de bar ficticio?
- [ ] Nuevo por audio: se menciona como idea (no diseño encargado) un concepto "isla de Lost / iniciativa Dharma" para U404 — ¿pasa a producción? Igual que con las bandas, es una franquicia real con licencia propia a evaluar.
- [ ] Nuevo por audio: roadmap de categorías futuras de FICCTURA (buzos, camperas, pantalones, calzado) — ¿hay timeline u orden de prioridad, o es solo visión a largo plazo sin fecha?

## 8. Contacto y canales
- [ ] Número de WhatsApp Business a usar por marca (se habló de comprar un número separado para no usar personales — ¿ya lo tienen?)
- [ ] Confirmar handles finales de Instagram/Facebook por marca (U404 quedó en `@eluniverso404`; falta confirmar el de FICCTURA y el estado de la fanpage de Facebook, que al 27/7 seguía pendiente).

## 9. Contenido y assets
- [ ] Acceso de edición/lectura a la carpeta de Drive y a los dos manuales de marca (Google Docs) para trabajar sobre la fuente viva, no solo sobre el brief exportado.
- [ ] Planillas de métricas (XLSX) mencionadas en Drive — ¿las necesitamos para algo del desarrollo (ej. definir qué se trackea) o son solo para el equipo de marketing?

## 10. Analítica e integraciones (para saber qué priorizar)
- [ ] ¿Ya tienen creadas las cuentas de Meta Business Manager / Google Analytics / Tag Manager, o hay que crearlas desde cero como parte del proyecto?
- [ ] Prioridad real de día 1 vs. fase 2: ¿Instagram Shopping/Facebook Shop, recuperación de carritos abandonados y automatización de WhatsApp son para el lanzamiento o para después?

---

*Nota: no se incluyen acá preguntas sobre cosas que el brief ya cierra como VIGENTE (ej. Payway como pasarela, arquitectura de dos webs con catálogo unificado en U404, política de agotados con captura de interés vía WhatsApp) — esas ya están decididas y no hace falta re-confirmarlas.*
