from django_tenants.middleware.main import TenantMainMiddleware
from django.http import Http404
from django.db import connection

from feedback_tracking.administrative_system.organizations.models import OrganizationModel


class PathTenantMiddleware(TenantMainMiddleware):
    """
    Middleware to set the tenant based on the path of the request.
    This middleware assumes that the tenant is specified in the URL path like a portal.
    For example, if the URL is http://example.com/portal_name/, then "portal_name"
    """

    def process_request(self, request):

        path_parts = request.path.strip("/").split("/")
        portal = path_parts[0]

        if portal not in ["panel-control", "accounts", "webhooks", "integrations",]:

            try:

                organization = OrganizationModel.objects.get(
                    portal=portal, is_active=True)
                request.organization = organization
                connection.set_schema(organization.schema_name, True)

            except OrganizationModel.DoesNotExist:
                raise Http404('Organization does not exist or is inactive.')
