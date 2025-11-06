from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from feedback_tracking.administrative_system.organizations.models import SubscriptionModel, InvoiceModel, PriceModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton
from feedback_tracking.api.permissions import IsOrganizationPortalOwner, BelongsToOrganizationPermission
from .serializers import GETInvoicesSerializer, GETInvoiceItemSerializer, GETPriceSerializer


class CancelSubscriptionView(APIView):

    permission_classes = (IsAuthenticated, IsOrganizationPortalOwner,)

    def delete(self, request, *args, **kwargs):
        """
        This endpoint is used to cancel a subscription.
        Allows cancellation only if the subscription is at least 2 weeks old (UTC-based).
        """

        organization = request.user.organization
        queryset = SubscriptionModel.objects.filter(
            organization=organization,
            status=SubscriptionModel.SubscriptionStatus.ACTIVE
        )

        if not queryset.exists():
            return Response({'msg': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)

        subscription = queryset.first()

        # 🔹 Verify that it has at least 2 weeks since its creation (UTC-based)
        now = timezone.now()  # Both are in UTC automatically
        age = now - subscription.created_at

        if age < timedelta(weeks=2):
            return Response({'msg': f'Subscription cannot be cancelled yet, please wait 2 weeks until cancellation is allowed.', 'days_remaining': 14-age.days}, status=status.HTTP_403_FORBIDDEN)

        # 🔹 Cancel in Stripe
        try:
            StripeSingleton().Subscription.cancel(
                subscription.stripe_subscription_id,
                prorate=True,
                invoice_now=False
            )
        except Exception as e:
            return Response({'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'msg': 'Subscription cancelled successfully'}, status=status.HTTP_200_OK)


class UpdateSubscriptionView(APIView):

    permission_classes = (IsAuthenticated, IsOrganizationPortalOwner,)

    # minos value = "better" plan (enterprise is best = 1)
    PLAN_RANK = {
        "BASIC": 3,
        "PROFESSIONAL": 2,
        "ENTERPRISE": 1,
    }

    def _get_plan_name_and_frequency(self, price_obj):
        """
        Extracts plan name and frequency from a PriceModel.
        Adjust attributes if your model uses different names.
        """

        plan_name = getattr(price_obj, "plan_name", None) or getattr(
            price_obj, "planName", None) or getattr(price_obj, "planType", None)
        frequency = getattr(price_obj, "frequency", None) or getattr(
            price_obj, "interval", None)

        if plan_name:
            plan_name = str(plan_name).upper()
        if frequency:
            frequency = str(frequency).upper()

        return plan_name, frequency

    def put(self, request, *args, **kwargs):

        organization = request.user.organization
        subscription_qs = SubscriptionModel.objects.filter(
            organization=organization, status=SubscriptionModel.SubscriptionStatus.ACTIVE
        )

        if not subscription_qs.exists():
            return Response({"msg": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

        price_id = request.data.get("price_id", None)

        if not price_id:
            return Response({"msg": "price_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_price = PriceModel.objects.get(stripe_price_id=price_id)
        except PriceModel.DoesNotExist:
            return Response({"msg": "Price was not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get current subscription
        subscription = subscription_qs.first()
        current_price = subscription.price

        # Normalize current and new plan names and frequencies
        current_name, current_freq = current_price.plan_type, current_price.interval
        new_name, new_freq = new_price.plan_type, new_price.interval

        current_rank = self.PLAN_RANK.get(current_name)
        new_rank = self.PLAN_RANK.get(new_name)

        # Business rule:
        # - Allow if new_rank < current_rank (upgrade to a higher plan)
        # - Allow if same tier and MONTHLY -> ANNUAL
        allowed = False
        if new_rank < current_rank:
            allowed = True
        elif new_rank == current_rank and current_freq == 'MONTHLY' and new_freq == 'ANNUAL':
            allowed = True

        if not allowed:
            return Response({
                'msg': 'Change not allowed. Only "upgrade" to a higher plan, or change the same plan from MONTHLY → ANNUAL is permitted.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Execute modification in Stripe and persist the change locally
        try:
            with transaction.atomic():

                subscription = StripeSingleton().Subscription.retrieve(
                    subscription.stripe_subscription_id)
                item_id = subscription['items']['data'][0]['id']
                StripeSingleton().Subscription.modify(
                    subscription.id,
                    items=[{'id': item_id, 'price': price_id}],
                    proration_behavior='create_prorations',
                    payment_behavior='allow_incomplete',
                )

        except Exception as e:
            return Response({'msg': 'Error updating subscription in Stripe or DB'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'msg': 'Subscription updated successfully'}, status=status.HTTP_200_OK)


class ListInvoicesView(APIView):

    permission_classes = (
        IsAuthenticated, BelongsToOrganizationPermission, IsOrganizationPortalOwner,)

    def get(self, request, *args, **kwargs):

        organization = request.user.organization
        queryset = InvoiceModel.objects.filter(
            subscription__organization=organization
        ).order_by('-created_at')

        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 25))
        page = paginator.paginate_queryset(queryset, request)
        serializer = GETInvoicesSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
