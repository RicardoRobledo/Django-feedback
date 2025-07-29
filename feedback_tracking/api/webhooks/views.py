import hashlib
import hmac
import urllib.parse

from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from feedback_tracking.administrative_system.organizations.models import PaymentModel, OrganizationModel, SubscriptionModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton


__author__ = 'Ricardo'
__version__ = '0.1'


def manage_payment(data):
    """
    This function is used to manage a payment.

    :param data: The data of the payment received from the webhook.
    """

    payment = StripeSingleton().payment().search(
        {'id': data['data']['id']})

    if data['action'] == 'payment.updated' or data['action'] == 'payment.created':

        payment = payment['response']['results'][0]
        payment_status = PaymentModel.PaymentStatus(payment['status'].upper())
        organization = OrganizationModel.objects.filter(
            mercadopago_user_id=payment['payer']['id']).first()

        match data['action']:

            case 'payment.created':

                PaymentModel.objects.create(
                    organization=organization,
                    mercadopago_payment_id=data['data']['id'],
                    status=payment_status,
                    amount=payment['transaction_amount'],
                    date_approved=payment['date_approved'],
                    payment_type=payment['payment_type_id'],
                    payment_method=payment['payment_method_id'],)

            case 'payment.updated':

                payment_status = PaymentModel.PaymentStatus(
                    payment['status'].upper())
                PaymentModel.objects.filter(
                    mercadopago_payment_id=data['data']['id']).update(status=payment_status)


def manage_subscription(data):
    """
    This function is used to manage a subscription.

    :param data: The data of the subscription received from the webhook.
    """

    subscription = StripeSingleton().preapproval().search({
        'id': data['data']['id']})

    subscription = subscription['response']['results'][0]
    subscription_status = SubscriptionModel.SubscriptionStatus(
        subscription['status'].upper())

    if data['action'] == 'updated':
        SubscriptionModel.objects.filter(
            mercadopago_subscription_id=data['data']['id']).update(status=subscription_status)


class MercadopagoWebhookView(APIView):
    """
    This endpoint is used to test the webhook from mercadopago.
    """

    permission_classes = ()

    def post(self, request, *args, **kwargs):

        x_signature = request.headers.get("x-signature")
        x_request_id = request.headers.get("x-request-id")

        if not x_signature or not x_request_id:
            return Response({'error': 'Missing required headers'}, status=400)

        # Obtener query params de la URL
        query_params = urllib.parse.parse_qs(request.META['QUERY_STRING'])

        # Extraer "data.id" (si no está, valor vacío)
        data_id = query_params.get("data.id", [""])[0]

        # Separar la firma en partes
        parts = x_signature.split(",")
        ts = None
        hash_received = None

        for part in parts:
            key_value = part.split("=", 1)
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                if key == "ts":
                    ts = value
                elif key == "v1":
                    hash_received = value

        if not all([ts, hash_received]):
            return Response({'error': 'Invalid signature header'}, status=400)

        # Generar el string "manifest" según doc oficial
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"

        # Calcular el hash
        calculated_hash = hmac.new(
            settings.MERCADOPAGO_SECRET_KEY.encode(),
            msg=manifest.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Validar
        if not hmac.compare_digest(calculated_hash, hash_received):
            return Response({'error': 'Signature mismatch'}, status=403)

        data = request.data

        if data['type'] == 'payment':
            manage_payment(data)
        elif data['type'] == 'subscription_preapproval':
            manage_subscription(data)

        return Response(data={'message': 'Webhook received'}, status=status.HTTP_200_OK)
