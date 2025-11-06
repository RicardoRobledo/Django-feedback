import stripe
import logging

from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from feedback_tracking.administrative_system.organizations.models import PaymentMethodModel, PriceModel, OrganizationModel, SubscriptionModel, InvoiceModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton
from .email_senders import send_email_organization_created, send_email_subscription_canceled


__author__ = 'Ricardo'
__version__ = '0.1'


logger = logging.getLogger(__name__)


class StripeWebhookView(APIView):

    permission_classes = [AllowAny]  # Public webhook

    def post(self, request, *args, **kwargs):

        payload = request.body
        sig_header = request.headers.get('stripe-signature')

        try:
            # Verify and construct the event
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.STRIPE_SIGNING_SECRET
            )
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event_type = event['type']
        data_object = event['data']['object']

        stripe_connection = StripeSingleton()

        if event_type == 'customer.updated':
            pass

        elif event_type == 'invoice.payment_succeeded':
            manage_invoice_succeeded(stripe_connection, data_object)

        elif event_type == 'invoice.payment_failed':
            register_payment_failed(stripe_connection, data_object)

        elif event_type == 'payment_method.attached':
            register_payment_method(stripe_connection, data_object)

        elif event_type == 'invoice.finalized':
            pass

        elif event_type == 'customer.subscription.updated':

            if data_object.get('status') == 'unpaid':
                deactivate_unpaid_subscription(stripe_connection, data_object)
            elif data_object.get('status') == 'past_due':
                deactivate_pastdue_subscription(stripe_connection, data_object)
            elif data_object.get('status') == 'active':
                change_price_subscription(data_object)

        elif event_type == 'customer.subscription.deleted':

            if data_object.get('status') == 'canceled':
                cancel_subscription(data_object)

        return Response(status=200)


def register_payment_method(stripe_connection, data_object: dict):
    """
    Register a new payment method for an organization.

    :param stripe_connection: The Stripe connection object.
    :param data_object: The Stripe data object containing payment method details.
    """

    type = data_object.get('type')

    stripe_customer = stripe_connection.Customer.retrieve(
        data_object.get('customer'))

    organization = OrganizationModel.objects.get(
        id=int(stripe_customer.get('metadata').get('organization_id')),
    )

    with transaction.atomic():

        if organization.payment_methods_organization.exists():
            organization.payment_methods_organization.all().delete()

        if type == 'card':

            card = data_object.get('card')
            PaymentMethodModel.objects.create(
                organization=organization,
                type=PaymentMethodModel.PaymentMethodEnum.CARD,
                stripe_payment_method_id=data_object.get('id'),
                brand=card.get('brand'),
                last_four_digits=card.get('last4'),
                exp_month=card.get('exp_month'),
                exp_year=card.get('exp_year'),
            )

        elif type == 'us_bank_account':

            bank = data_object.get('us_bank_account')
            PaymentMethodModel.objects.create(
                organization=organization,
                type=PaymentMethodModel.PaymentMethodEnum.US_BANK_ACCOUNT,
                stripe_payment_method_id=data_object.get('id'),
                account_type=bank.get('account_type'),
                bank_name=bank.get('bank_name'),
                last_four_digits=bank.get('last4'),
            )

        elif type == 'sepa_debit':

            sepa = data_object.get('sepa_debit')
            PaymentMethodModel.objects.create(
                organization=organization,
                type=PaymentMethodModel.PaymentMethodEnum.SEPA_DEBIT,
                brand=data_object.get('brand'),
                stripe_payment_method_id=data_object.get('id'),
                bank_code=sepa.get('bank_code'),
                last_four_digits=sepa.get('last4'),
            )


def manage_invoice_succeeded(stripe_connection, data_object: dict):
    """
    This function handles the successful payment of an invoice.

    :param stripe_connection: The Stripe connection object.
    :param data_object: The subscription object containing relevant data.
    """

    stripe_customer = stripe_connection.Customer.retrieve(
        data_object.get('customer'))
    billing_reason = data_object.get('billing_reason')

    if billing_reason == 'subscription_create':

        sessions = stripe_connection.checkout.Session.list(
            subscription=data_object.get('subscription')).data

        if sessions:
            stripe_subscription = sessions[0]
        else:
            stripe_subscription = stripe_connection.Subscription.retrieve(
                data_object.get('subscription')
            )

        customer_id = int(stripe_customer.get(
            'metadata').get('organization_id'))
        subscription_id = int(stripe_subscription.get(
            'metadata').get('subscription_id'))

        subscription = SubscriptionModel.objects.get(id=subscription_id,)

        organization = OrganizationModel.objects.get(id=customer_id,)
        stripe_subscription = StripeSingleton().Subscription.retrieve(
            data_object.get('subscription'))

        payment_methods = organization.payment_methods_organization

        if payment_methods.exists():

            StripeSingleton().Customer.modify(
                stripe_customer.get('id'),
                invoice_settings={
                    'default_payment_method': payment_methods.first().stripe_payment_method_id},
            )

            with transaction.atomic():

                organization.stripe_customer_id = stripe_customer.get('id')
                organization.is_active = True
                organization.save()

                subscription.status = SubscriptionModel.SubscriptionStatus(
                    stripe_subscription.get('status').upper())
                subscription.stripe_subscription_id = data_object.get(
                    'subscription') or data_object.get('id')
                subscription.save()

                # Search for the line that is NOT proration (the new plan)
                new_plan_line = None
                for line in data_object['lines']['data']:
                    if not line.get('proration', False):
                        new_plan_line = line
                        break

                subscription.price = PriceModel.objects.get(
                    stripe_price_id=new_plan_line['price']['id'])
                subscription.unit_amount = int(
                    new_plan_line['price']['unit_amount']) / 100
                subscription.save()

                InvoiceModel.objects.get_or_create(
                    stripe_invoice_id=data_object.get('id'),
                    defaults={
                        'subscription': subscription,
                        'total': int(data_object.get('total'))/100,
                        'subtotal': int(data_object.get('subtotal'))/100,
                        'amount': int(data_object.get('amount_paid'))/100,
                        'paid_at': data_object.get('status_transitions').get('paid_at'),
                        'currency': data_object.get('currency'),
                        'hosted_invoice_url': data_object.get('hosted_invoice_url'),
                        'invoice_pdf': data_object.get('invoice_pdf'),
                        'created': data_object.get('created'),
                        'billing_reason': data_object.get('billing_reason'),
                        'collection_method': data_object.get('collection_method'),
                        'status': InvoiceModel.InvoiceStatus(data_object.get('status').upper()),
                    }
                )

            try:
                send_email_organization_created(organization, subscription)
            except Exception as e:
                logger.error(f"Email error: {str(e)}")

    elif billing_reason == 'subscription_update':

        customer_id = int(stripe_customer.get(
            'metadata').get('organization_id'))

        subscription = SubscriptionModel.objects.get(
            stripe_subscription_id=data_object.get('subscription'))

        organization = OrganizationModel.objects.get(id=customer_id,)
        stripe_subscription = StripeSingleton().Subscription.retrieve(
            data_object.get('subscription'))

        is_active = True if stripe_subscription.get(
            'status') == 'active' else False

        with transaction.atomic():

            organization.is_active = is_active
            organization.save()

            subscription.status = SubscriptionModel.SubscriptionStatus(
                stripe_subscription.get('status').upper())
            subscription.stripe_subscription_id = data_object.get(
                'subscription')

            # Search for the line that is NOT proration (the new plan)
            new_plan_line = None
            for line in data_object['lines']['data']:
                if not line.get('proration', False):
                    new_plan_line = line
                    break

            subscription.price = PriceModel.objects.get(
                stripe_price_id=new_plan_line['price']['id'])
            subscription.unit_amount = int(
                new_plan_line['price']['unit_amount']) / 100

            subscription.save()

            InvoiceModel.objects.get_or_create(
                stripe_invoice_id=data_object.get('id'),
                defaults={
                    'subscription': subscription,
                    'total': int(data_object.get('total'))/100,
                    'subtotal': int(data_object.get('subtotal'))/100,
                    'amount': int(data_object.get('amount_paid'))/100,
                    'paid_at': data_object.get('status_transitions').get('paid_at'),
                    'currency': data_object.get('currency'),
                    'hosted_invoice_url': data_object.get('hosted_invoice_url'),
                    'invoice_pdf': data_object.get('invoice_pdf'),
                    'created': data_object.get('created'),
                    'billing_reason': data_object.get('billing_reason'),
                    'collection_method': data_object.get('collection_method'),
                    'status': InvoiceModel.InvoiceStatus(data_object.get('status').upper()),
                }
            )

    elif billing_reason == 'subscription_cycle':

        customer_id = int(stripe_customer.get(
            'metadata').get('organization_id'))

        subscription = SubscriptionModel.objects.get(
            stripe_subscription_id=data_object.get('subscription'))

        organization = OrganizationModel.objects.get(id=customer_id,)
        stripe_subscription = StripeSingleton().Subscription.retrieve(
            subscription.stripe_subscription_id)

        is_active = True if stripe_subscription.get(
            'status') == 'active' else False

        with transaction.atomic():

            InvoiceModel.objects.get_or_create(
                stripe_invoice_id=data_object.get('id'),
                defaults={
                    'subscription': subscription,
                    'amount': int(data_object.get('amount_paid'))/100,
                    'subtotal': int(data_object.get('subtotal'))/100,
                    'total': int(data_object.get('total'))/100,
                    'paid_at': data_object.get('status_transitions').get('paid_at'),
                    'currency': data_object.get('currency'),
                    'hosted_invoice_url': data_object.get('hosted_invoice_url'),
                    'invoice_pdf': data_object.get('invoice_pdf'),
                    'created': data_object.get('created'),
                    'billing_reason': data_object.get('billing_reason'),
                    'collection_method': data_object.get('collection_method'),
                    'status': InvoiceModel.InvoiceStatus(data_object.get('status').upper()),
                }
            )


def deactivate_pastdue_subscription(stripe_connection, data_object: dict):
    """
    This function deactivates a past-due subscription based on the subscription object.
    """
    customer_id = stripe_connection.Customer.retrieve(
        data_object.get('customer')).get('metadata').get('organization_id')
    subscription_id = stripe_connection.Subscription.retrieve(
        data_object.get('subscription')).get('metadata').get('subscription_id')

    with transaction.atomic():
        organization = OrganizationModel.objects.get(id=customer_id)
        subscription = SubscriptionModel.objects.get(id=subscription_id)

        organization.is_active = False
        organization.save()

        subscription.status = SubscriptionModel.SubscriptionStatus.PAST_DUE
        subscription.save()


def deactivate_unpaid_subscription(stripe_connection, data_object: dict):
    """
    This function deactivates an unpaid subscription based on the subscription object.

    :param stripe_connection: The Stripe connection object.
    :param data_object: The subscription object containing relevant data.
    """

    customer_id = stripe_connection.Customer.retrieve(
        data_object.get('customer')).get('metadata').get('organization_id')
    subscription_id = stripe_connection.Subscription.retrieve(
        data_object.get('subscription')).get('metadata').get('subscription_id')

    with transaction.atomic():
        organization = OrganizationModel.objects.get(id=customer_id)
        subscription = SubscriptionModel.objects.get(id=subscription_id)

        organization.is_active = False
        organization.save()

        subscription.status = SubscriptionModel.SubscriptionStatus.UNPAID
        subscription.save()


def register_payment_failed(stripe_connection, data_object: dict):
    """
    This function registers a failed payment for a subscription based on the subscription object.
    """
    subscription_id = stripe_connection.Subscription.retrieve(
        data_object.get('subscription')).get('metadata').get('subscription_id')

    with transaction.atomic():
        subscription = SubscriptionModel.objects.get(id=subscription_id)
        subscription.status = SubscriptionModel.SubscriptionStatus.PAST_DUE
        subscription.save()


def change_price_subscription(data_object: dict):
    """
    Change the price of a subscription in the database upon receiving an event from Stripe.

    :param stripe_object: The subscription object sent by Stripe (e.g., in webhook)
    """

    subscription = SubscriptionModel.objects.get(
        stripe_subscription_id=data_object.get('id'))
    price = PriceModel.objects.get(
        stripe_price_id=data_object['items']['data'][0]['price']['id']
    )

    with transaction.atomic():
        subscription.price = price
        subscription.unit_amount = int(
            data_object['items']['data'][0]['price']['unit_amount'])/100
        subscription.save()


def cancel_subscription(data_object: dict):
    """
    This function cancels a subscription in your database upon receiving an event from Stripe.

    :param stripe_object: The subscription object sent by Stripe (e.g., in webhook)
    """

    organization = OrganizationModel.objects.get(
        stripe_customer_id=data_object.get('customer'))
    subscription = SubscriptionModel.objects.get(
        stripe_subscription_id=data_object.get('id'))

    with transaction.atomic():

        organization.is_active = False
        organization.save()

        subscription.status = SubscriptionModel.SubscriptionStatus.CANCELED
        subscription.save()

    try:
        send_email_subscription_canceled(organization, subscription)
    except Exception as e:
        logger.error(f"Email error: {str(e)}")

# customer.created
# payment_method.attached
# customer.updated
# invoiceitem.created
# invoice.created
# customer.updated
# charge.succeeded
# payment_intent.created
# payment_intent.succeeded
# invoice.updated
# invoice.finalized
# invoice.paid
# invoice.payment_succeeded - x
# El usuario cancela manualmente una suscripción:
#    Stripe envía:
#    🔔 customer.subscription.deleted
#    La suscripción expira automáticamente (sin renovación):
#    Stripe envía:
#    🔔 customer.subscription.updated con status = 'canceled'
#    y luego, si se elimina por completo:
#    🔔 customer.subscription.deleted
#    Pagos fallan repetidamente y Stripe cancela la suscripción:
#    Stripe envía:
#    🔔 invoice.payment_failed
#    🔔 customer.subscription.updated → con status = 'past_due', 'unpaid' o 'canceled'#    🔔 customer.subscription.deleted (si no se recupera)
