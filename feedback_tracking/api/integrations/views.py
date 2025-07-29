from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from feedback_tracking.singletons.stripe_singleton import StripeSingleton


__author__ = 'Ricardo'
__version__ = '0.1'


class PricesView(APIView):
    """
    This view handles the integration with Stripe to get prices.
    """

    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        Returns the prices of the plans available in Stripe.
        """
        prices = StripeSingleton().Price.list(active=True)['data']
        prices = list(map(lambda price: {
            'id': price.id,
            'nickname': price.nickname,
            'unit_amount': price.unit_amount,
            'currency': price.currency,
            'interval': price.recurring.interval,
        }, prices))

        return Response(prices, status=status.HTTP_200_OK)
