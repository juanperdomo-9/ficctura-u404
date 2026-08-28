"""
Integración con Payway (tarjeta) para el checkout.

Payway Argentina corre sobre el motor Decidir. Sin credenciales reales
todavía (Payway las entrega junto con el manual completo recién cuando
el cliente activa CUIT/facturación — ver
brief/preguntas-pendientes-cliente.md), así que esto se armó contra lo
verificable públicamente, no a ciegas:

- SDK JS de tokenización (cliente, nunca ve la private key):
  https://github.com/decidir/sdk-javascript-v2
- SDK Node de referencia para el payload del lado servidor
  (site_transaction_id, payment_method_id, amount en centavos, etc.):
  https://github.com/decidir/sdk-nodejs-v2
- URLs base confirmadas: sandbox https://developers.decidir.com/api/v2,
  producción https://live.decidir.com/api/v2

OJO — lo que NO se pudo confirmar al 100% sin credenciales reales (re-
investigado 12/8, no cambió: ni el SDK ni la documentación pública
exponen esto sin llamar a un endpoint autenticado de Decidir):
1. El nombre exacto del header de autenticación con la private key.
   Se usa "apikey" acá por ser la convención más citada de Decidir,
   pero hay que confirmarlo contra el manual real que mande Payway.
2. `payment_method_id` está hardcodeado a 1 — en los ejemplos públicos
   del SDK, 1 aparece como "tarjeta de crédito/débito" genérico (no
   necesariamente solo Visa), pero no hay forma pública de confirmar
   si Decidir espera un id distinto por marca (Visa/Master/Amex/Cabal/
   Naranja) sin llamar a su endpoint autenticado de "payment methods".
   Con credenciales reales: pegar ahí, hacer un pago de prueba con una
   tarjeta que NO sea Visa, y si lo rechaza por medio de pago inválido,
   resolver el id real contra ese endpoint (o lo que devuelva el SDK
   JS al tokenizar — revisar `response` en static/js/checkout.js).

Primera prueba con credenciales de sandbox: revisar estos dos puntos
antes de asumir que un pago aprobado/rechazado es 100% confiable. Todo
lo demás (URLs, payload, flujo de tokenización, activación automática
de "tarjeta" en el checkout) ya está armado — no hace falta tocar más
código, solo pegar PAYWAY_PUBLIC_KEY / PAYWAY_PRIVATE_KEY en el .env.
"""
import requests
from django.conf import settings


class PaywayError(Exception):
    """Cualquier fallo al intentar cobrar — de red, de configuración, o rechazo del pago."""


def is_configured():
    return bool(settings.PAYWAY_PUBLIC_KEY and settings.PAYWAY_PRIVATE_KEY)


def create_payway_payment(token, amount_cents, site_transaction_id, installments=1, description=''):
    """
    Ejecuta el cobro contra la API de Payway/Decidir usando un token ya
    generado del lado del cliente (ver static/js/checkout.js — nunca
    pasa el número de tarjeta por acá). Devuelve el JSON de respuesta si
    Payway aprobó; levanta PaywayError si no.
    """
    if not is_configured():
        raise PaywayError('Payway no está configurado (faltan las claves en .env).')

    url = f"{settings.PAYWAY_API_BASE_URL}/payments"

    payload = {
        'site_transaction_id': site_transaction_id,
        'token': token,
        'payment_method_id': 1,  # placeholder — ver nota del módulo sobre resolver esto de verdad
        'amount': amount_cents,
        'currency': 'ARS',
        'installments': installments,
        'payment_type': 'single' if installments <= 1 else 'distributed',
        'description': description,
    }

    headers = {
        'apikey': settings.PAYWAY_PRIVATE_KEY,  # ver nota del módulo — confirmar contra el manual real
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
    except requests.RequestException as exc:
        raise PaywayError(f'No se pudo conectar con Payway: {exc}') from exc

    if response.status_code not in (200, 201):
        raise PaywayError(f'Payway rechazó el pago (status {response.status_code}): {response.text[:200]}')

    return response.json()
