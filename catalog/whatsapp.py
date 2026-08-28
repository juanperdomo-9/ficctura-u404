"""
WhatsApp de confirmación al cliente después de una compra — pedido del
usuario (13/8): "que se le envíe un WhatsApp con los datos de su
compra". Esto es un mensaje que la EMPRESA le manda al cliente sola,
sin que el cliente haga nada — muy distinto a los links wa.me que ya
usa el resto del sitio (esos abren WhatsApp de quien los clickea, acá
en cambio hace falta la API real de WhatsApp Business).

Implementado contra la API de WhatsApp de Twilio (https://www.twilio.
com/docs/whatsapp/api) — la opción más simple para arrancar sin pasar
directo por la verificación de negocio de Meta desde cero (Twilio hace
de intermediario). Sin credenciales todavía (hace falta una cuenta de
Twilio + un número de WhatsApp Business aprobado — ninguno de los dos
existe hoy, ni siquiera hay un número de WhatsApp cargado en
settings.BRANDS — ver brief/preguntas-pendientes-cliente.md), así que
is_configured() da False y el checkout NO llama a esto todavía (ver
catalog/views.py::checkout — queda comentado, listo para descomentar).

OJO — esto no se pudo verificar contra credenciales reales, dos cosas
para confirmar en la primera prueba:
1. Fuera del sandbox de pruebas de Twilio, WhatsApp exige que el
   PRIMER mensaje que una empresa le manda a un cliente (o cualquier
   mensaje fuera de una ventana de 24hs de conversación activa) use una
   "plantilla" (template) pre-aprobada por Meta — no se puede mandar
   texto libre de una, como arma _build_message() acá. Hay que crear y
   aprobar esa plantilla en la consola de Twilio/Meta ANTES de que esto
   funcione en producción real (el sandbox de pruebas sí deja texto
   libre, para probar el flujo).
2. TWILIO_WHATSAPP_FROM tiene que ser el número de WhatsApp Business
   real ya aprobado — uno por marca si quieren remitentes separados
   (habría que agregar un segundo par de variables tipo
   TWILIO_WHATSAPP_FROM_FICCTURA).
3. El checkout ahora pide WhatsApp específicamente (ya no "o email",
   pedido del usuario 13/8 — ver is_valid_whatsapp en catalog/views.py),
   pero igual puede llegar un número mal formado (código de país
   faltante, etc.) y Twilio lo rechace. Por eso send_order_confirmation
   nunca debe romper el checkout si falla (ver nota en el view).
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppError(Exception):
    """Cualquier fallo al intentar mandar el WhatsApp — de red, de configuración, o rechazo de la API."""


def is_configured():
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM)


def send_order_confirmation(order):
    """
    Manda el WhatsApp de confirmación al número que el cliente dejó en
    el checkout. Pensado para llamarse DESPUÉS de guardar el Order y
    sus OrderItem (usa order.items.all()), envuelto en try/except desde
    el view — la compra ya está hecha, no tiene que fallar por esto.
    """
    if not is_configured():
        raise WhatsAppError('WhatsApp no está configurado (faltan las claves en .env).')

    url = f'https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json'

    try:
        response = requests.post(
            url,
            data={
                'From': f'whatsapp:{settings.TWILIO_WHATSAPP_FROM}',
                'To': f'whatsapp:{order.contact}',
                'Body': _build_message(order),
            },
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise WhatsAppError(f'No se pudo conectar con Twilio: {exc}') from exc

    if response.status_code not in (200, 201):
        raise WhatsAppError(f'Twilio rechazó el mensaje (status {response.status_code}): {response.text[:200]}')

    return response.json()


def _build_message(order):
    """Texto plano con los datos del pedido — ver nota del módulo sobre la plantilla que va a hacer falta en producción."""
    lines = [
        f"¡Gracias por tu compra en {order.get_brand_display()}, {order.name}!",
        f"Pedido #{order.id}",
        '',
    ]

    for item in order.items.all():
        lines.append(f"• {item.product_name} — {item.size} / {item.color} x{item.quantity}")

    lines += [
        '',
        f"Total: $ {order.total:,.0f}".replace(',', '.'),
        f"Entrega: {order.get_delivery_method_display()}",
        f"Pago: {order.get_payment_preference_display()}",
    ]

    if order.status == order.Status.PENDING:
        lines.append('')
        lines.append('Todavía falta coordinar el pago — te contactamos para eso.')

    return '\n'.join(lines)
