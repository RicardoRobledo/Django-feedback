from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from rest_framework.response import Response

from feedback_tracking.administrative_system.organizations.models import OrganizationModel, SubscriptionModel


def send_email_organization_created(organization: OrganizationModel, subscription: SubscriptionModel) -> Response:
    """
    Send an email to the customer subscription.

    :param subscription: The subscription data
    :param organization: The organization data
    :return: Response indicating success or failure
    """

    subject = "🎟️ Suscripción completada"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [organization.company_email]

    # Texto alternativo por si el cliente no admite HTML
    text_content = f"""
    Tu suscripción ha sido registrada.
    Plan: {subscription.price.name}
    Monto: ${subscription.unit_amount}

    Organización: {organization.name}
    Portal: {organization.portal}
    """

    # HTML del ticket
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
            <h2 style="text-align: center; color: #2d8659;">✅ ¡Suscripción completada!</h2>
            <p style="text-align: center; color: #555;">
                Gracias por confiar en nosotros. Aquí están los datos de tu suscripción:
            </p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">📌 Datos de la Organización</h3>
            <p><strong>Nombre:</strong> {organization.name}</p>
            <p><strong>Estado:</strong> {organization.state}</p>
            <p><strong>Teléfono:</strong> {organization.phone_number}</p>
            <p><strong>Portal:</strong> <code>{organization.portal}</code></p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px;">📄 Datos de la Suscripción</h3>
            <p><strong>Monto:</strong> ${subscription.unit_amount}</p>
            <p><strong>Plan:</strong> {subscription.price.name}</p>

            <p style="font-size: 12px; color: #888; margin-top: 8px;">
                ⏳ Nota: La activación de tu organización puede tardar unos minutos.  
                Si no puedes acceder de inmediato, inténtalo de nuevo más tarde.
            </p>
        </div>
    </body>
    </html>"""

    # Crear el mensaje
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_email_subscription_updated(organization: OrganizationModel, subscription: SubscriptionModel) -> Response:
    """
    Send an email to the customer subscription updated.

    :param subscription: The subscription data
    :param organization: The organization data
    :return: Response indicating success or failure
    """

    subject = "🎟️ Suscripción actualizada"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [organization.company_email]

    # Texto alternativo por si el cliente no admite HTML
    text_content = f"""
    Tu suscripción ha sido actualizada.
    Plan: {subscription.price.name}
    Monto: ${subscription.unit_amount}

    Organización: {organization.name}
    Portal: {organization.portal}
    """

    # HTML del ticket
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
            <h2 style="text-align: center; color: #2d8659;">✅ ¡Suscripción actualizada!</h2>
            <p style="text-align: center; color: #555;">
                Gracias por confiar en nosotros. Aquí están los datos de tu suscripción actualizada:
            </p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">📌 Datos de la Organización</h3>
            <p><strong>Nombre:</strong> {organization.name}</p>
            <p><strong>Estado:</strong> {organization.state}</p>
            <p><strong>Teléfono:</strong> {organization.phone_number}</p>
            <p><strong>Portal:</strong> <code>{organization.portal}</code></p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px;">📄 Datos de la Suscripción</h3>
            <p><strong>Monto:</strong> ${subscription.unit_amount}</p>
            <p><strong>Plan:</strong> {subscription.price.name}</p>

            <p style="font-size: 12px; color: #888; margin-top: 8px;">
                ⏳ Nota: La activación de tu organización puede tardar unos minutos.  
                Si no puedes acceder de inmediato, inténtalo de nuevo más tarde.
            </p>
        </div>
    </body>
    </html>"""

    # Crear el mensaje
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_email_subscription_canceled(organization: OrganizationModel, subscription: SubscriptionModel) -> Response:
    """
    Send an email to the organization when a subscription is canceled.

    :param subscription: The subscription data
    :param organization: The organization data
    :return: Response indicating success or failure
    """

    subject = "❌ Suscripción cancelada"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [organization.company_email]

    # Texto alternativo por si el cliente no admite HTML
    text_content = f"""
    Tu suscripción ha sido cancelada.

    Organización: {organization.name}
    Portal: {organization.portal}
    Plan: {subscription.price.name}
    Monto mensual: ${subscription.unit_amount}
    Estado actual: {subscription.status}
    """

    # HTML del correo
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
            <h2 style="text-align: center; color: #c0392b;">❌ Suscripción cancelada</h2>
            <p style="text-align: center; color: #555;">
                Te informamos que tu suscripción ha sido cancelada. Aquí están los detalles:
            </p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">📌 Datos de la Organización</h3>
            <p><strong>Nombre:</strong> {organization.name}</p>
            <p><strong>Estado:</strong> {organization.state}</p>
            <p><strong>Teléfono:</strong> {organization.phone_number}</p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px;">📄 Datos de la Suscripción</h3>
            <p><strong>Plan:</strong> {subscription.price.name}</p>
            <p><strong>Estado:</strong> {subscription.status}</p>

            <p style="font-size: 12px; color: #888; margin-top: 8px;">
                Si crees que esta cancelación fue un error o deseas reactivar tu suscripción, 
                por favor contáctanos o ingresa nuevamente a tu portal.
            </p>
        </div>
    </body>
    </html>"""

    # Crear el mensaje
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
