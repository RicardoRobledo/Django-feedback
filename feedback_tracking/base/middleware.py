from django_tenants.middleware.main import TenantMainMiddleware
from feedback_tracking.administrative_system.organizations.models import OrganizationModel
from django.http import Http404


class PathTenantMiddleware(TenantMainMiddleware):
    """
    Middleware to set the tenant based on the path of the request.
    This middleware assumes that the tenant is specified in the URL path like a portal.
    For example, if the URL is http://example.com/portal_name/, then "portal_name"
    """

    def process_request(self, request):

        path_parts = request.path.strip("/").split("/")
        portal = path_parts[0]

        if portal not in ["panel-control", "accounts"]:

            try:

                OrganizationModel.objects.get(portal=portal)

            except OrganizationModel.DoesNotExist:
                raise Http404("Portal not found")
