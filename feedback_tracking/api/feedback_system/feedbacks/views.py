import datetime
from datetime import timedelta
from collections import defaultdict

from django.utils import timezone
from django.db.models import Count, Q, F, Prefetch, FloatField, ExpressionWrapper
from django.db.models.functions import TruncHour, TruncDay, TruncMonth
from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from feedback_tracking.feedback_system.feedbacks.models import FeedbackModel, PositiveFeedbackModel, NegativeFeedbackModel, PositiveFeedbackTypeModel, NegativeFeedbackTypeModel
from feedback_tracking.feedback_system.locations.models import LocationModel, GroupModel, AvailabilityModel
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel
from feedback_tracking.api.permissions import BelongsToOrganizationPermission
from .serializers import GETFeedbackSerializer, GETFeedbacksSerializer, GETNegativeFeedbackSerializer, GETPositiveFeedbackSerializer
from .statistics import get_feedback_distribution


__author__ = 'Ricardo'
__version__ = '0.1'


paginator = PageNumberPagination()


# --------------------------------------------
#               Create feedback
# --------------------------------------------

def manage_positive_feedbacks(feedback_classification, feedback_types, feedback_comment, location):
    """
    Function to manage positive feedbacks

    :param feedback_classification(str): feedback classification
    :param feedback_types(str): list of feedback types
    :param feedback_comment(str): feedback comment
    :param location: location gotten
    """

    positive_feedbacks_gotten = PositiveFeedbackModel.objects.filter(
        id__in=feedback_types, in_use=True)
    positive_feedbacks = positive_feedbacks_gotten.values_list(
        'id', flat=True)

    if set(positive_feedbacks) != set(feedback_types):
        return JsonResponse({"msg": "Not all positive feedbacks exist"}, status=status.HTTP_400_BAD_REQUEST)

    new_feedback = FeedbackModel.objects.create(
        classification=feedback_classification,
        comment=feedback_comment,
        location=location
    )

    PositiveFeedbackTypeModel.objects.bulk_create([PositiveFeedbackTypeModel(
        feedback=new_feedback, positive_feedback=positive_feedback) for positive_feedback in positive_feedbacks_gotten])

    return JsonResponse({"msg": "Positive feedback received"}, status=status.HTTP_201_CREATED)


def manage_negative_feedbacks(feedback_classification, feedback_types, feedback_comment, location):
    """
    Function to manage negative feedbacks

    :param feedback_classification(str): feedback classification
    :param feedback_types(str): list of feedback types
    :param feedback_comment(str): feedback comment
    :param location: location gotten
    """

    negative_feedbacks_gotten = NegativeFeedbackModel.objects.filter(
        id__in=feedback_types, in_use=True)
    negative_feedbacks = negative_feedbacks_gotten.values_list(
        'id', flat=True)

    if set(negative_feedbacks) != set(feedback_types):
        return JsonResponse({"msg": "No negative feedbacks exist"}, status=status.HTTP_400_BAD_REQUEST)

    new_feedback = FeedbackModel.objects.create(
        classification=feedback_classification,
        comment=feedback_comment,
        location=location
    )

    NegativeFeedbackTypeModel.objects.bulk_create([NegativeFeedbackTypeModel(
        feedback=new_feedback, negative_feedback=negative_feedback) for negative_feedback in negative_feedbacks_gotten])

    return JsonResponse({"msg": "Negative feedback received"}, status=status.HTTP_201_CREATED)


class FeedbackView(APIView):

    permission_classes = ()

    def post(self, request, *args, **kwargs):
        """
        Function to create feedbacks

        :header machine_number: machine number
        :header signature: signature

        :param feedback(str): enum feedback classification (EX, GO, AV, BA)
        :param feedback_types(list): list of feedback types being ids
        :param feedback_comment(str): feedback comment
        """

        # headers
        machine_number = request.headers.get('X-Machine-Number', None)
        signature = request.headers.get('X-Signature', None)

        # body
        feedback = request.POST.get('feedback', None)
        feedback_types = request.POST.getlist('feedback_types[]', None)
        feedback_comment = request.POST.get('feedback_comment', None)
        location_id = request.POST.get('location_id', None)

        # verify headers and body
        if not all([machine_number, signature]):
            return JsonResponse({"msg": "Missing required headers"}, status=status.HTTP_400_BAD_REQUEST)

        if not location_id:
            return JsonResponse({"msg": "Missing field: location_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            feedback_types = [int(ft) for ft in feedback_types]
        except (ValueError, TypeError):
            return JsonResponse({"msg": "Invalid feedback_types. All must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        if not all([feedback, feedback_types]):
            return JsonResponse({"msg": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        if not LocationModel.verify_signature(machine_number, signature):
            return JsonResponse({"msg": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

        # validating existence
        location = LocationModel.objects.filter(
            id=location_id, machine_number=machine_number, is_active=True)

        if not location.exists():
            return JsonResponse({"msg": "Location does not exist or is not in use"}, status=status.HTTP_404_NOT_FOUND)

        date = datetime.datetime.now()
        today = date.strftime('%A').lower()
        now = date.time()

        location = location.first()
        availability = AvailabilityModel.objects.filter(
            location=location,).first()

        if not getattr(availability, today):
            return JsonResponse({"msg": "Location is not available today"}, status=status.HTTP_403_FORBIDDEN)

        if not (availability.start_time <= now <= availability.end_time):
            return JsonResponse({"msg": "Location is not available at this hour"}, status=status.HTTP_403_FORBIDDEN)

        if feedback not in FeedbackModel.FeedbackClassification.values:
            return JsonResponse({"msg": "Invalid feedback classification"}, status=400)

        # verify feedback types
        feedback_classification = FeedbackModel.FeedbackClassification(
            feedback)

        if feedback_classification in [FeedbackModel.FeedbackClassification.EXCELLENT, FeedbackModel.FeedbackClassification.GOOD]:
            response = manage_positive_feedbacks(
                feedback_classification, feedback_types, feedback_comment, location)
        else:
            response = manage_negative_feedbacks(
                feedback_classification, feedback_types, feedback_comment, location)

        return response


@api_view(['POST'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def create_feedback_type(request, portal, feedback_category):
    """
    Function to create a feedback based on the category

    :param request: request
    :param portal: portal
    :param feedback_category: category of the feedback, can be 'positive' or 'negative'
    """

    feedback = request.POST.get('feedback', None)

    if not feedback:
        return JsonResponse({"msg": "Missing feedback field"}, status=status.HTTP_400_BAD_REQUEST)

    if feedback_category == 'positive':

        if PositiveFeedbackModel.objects.filter(feedback=feedback).exists():
            return JsonResponse({"msg": "Feedback already exists"}, status=status.HTTP_400_BAD_REQUEST)

        positive_feedback = PositiveFeedbackModel.objects.create(
            feedback=feedback,
        )

        return Response(GETPositiveFeedbackSerializer(positive_feedback).data, status=status.HTTP_201_CREATED)

    elif feedback_category == 'negative':

        if NegativeFeedbackModel.objects.filter(feedback=feedback).exists():
            return JsonResponse({"msg": "Feedback already exists"}, status=status.HTTP_400_BAD_REQUEST)

        negative_type = NegativeFeedbackModel.objects.create(
            feedback=feedback,
        )

        return Response(GETNegativeFeedbackSerializer(negative_type).data, status=status.HTTP_201_CREATED)

    else:
        return JsonResponse({"msg": "Invalid feedback category"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([])
def get_negative_feedback_types(request, portal):
    """
    Function to get negative feedbacks

    :param request: request
    """

    negative_feedbacks = NegativeFeedbackModel.objects.all().values('id',
                                                                    'feedback', 'in_use')

    return JsonResponse({"negative_feedbacks": list(negative_feedbacks)}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([])
def get_positive_feedback_types(request, portal):
    """
    Function to get positive feedbacks

    :param request: request
    """

    positive_feedbacks = PositiveFeedbackModel.objects.all().values('id',
                                                                    'feedback', 'in_use')

    return JsonResponse({"positive_feedbacks": list(positive_feedbacks)}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_feedbacks(request, portal):
    """
    Function to get feedbacks

    :param request: request
    """

    group_id = request.query_params.get("group_id", None)
    location_id = request.query_params.get("location_id", None)
    classification = request.query_params.get("classification", None)

    if classification is not None and classification not in FeedbackModel.FeedbackClassification:
        return JsonResponse({"msg": "Invalid classification"}, status=status.HTTP_400_BAD_REQUEST)

    if group_id:

        group = GroupModel.objects.filter(id=group_id)

        if not group.exists():
            return JsonResponse({"msg": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        group = group.first()

    if location_id:

        location = LocationModel.objects.filter(id=location_id)

        if not location.exists():
            return JsonResponse({"msg": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

        location = location.first()

        if group_id and location.group.id != group.id:
            return JsonResponse({"msg": "Location does not belong to the specified group"}, status=status.HTTP_400_BAD_REQUEST)

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        feedbacks = FeedbackModel.objects.select_related("location").prefetch_related(
            Prefetch("positive_types", queryset=PositiveFeedbackTypeModel.objects.select_related(
                "positive_feedback")),
            Prefetch("negative_types", queryset=NegativeFeedbackTypeModel.objects.select_related(
                "negative_feedback"))
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(
            has_permission=True).values_list('group_id', flat=True)

        if not permission_ids:
            return JsonResponse({"msg": "Manager does not have permission to access to that location"}, status=status.HTTP_403_FORBIDDEN)

        # Obtener feedbacks solo de esas locaciones
        feedbacks = FeedbackModel.objects.filter(
            location__group_id__in=permission_ids
        ).select_related("location").prefetch_related(
            Prefetch(
                "positive_types",
                queryset=PositiveFeedbackTypeModel.objects.select_related(
                    "positive_feedback")
            ),
            Prefetch(
                "negative_types",
                queryset=NegativeFeedbackTypeModel.objects.select_related(
                    "negative_feedback")
            )
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        # Obtener las IDs de locaciones permitidas para el usuario
        permission_ids = request.user.user_location_permissions.all().values_list(
            'location_id', flat=True
        )

        if not permission_ids:
            return JsonResponse({"msg": "User does not have permission to access to this location"}, status=status.HTTP_403_FORBIDDEN)

        # Obtener feedbacks solo de esas locaciones
        feedbacks = FeedbackModel.objects.filter(location_id__in=permission_ids).select_related("location").prefetch_related(
            Prefetch(
                "positive_types",
                queryset=PositiveFeedbackTypeModel.objects.select_related(
                    "positive_feedback")
            ),
            Prefetch(
                "negative_types",
                queryset=NegativeFeedbackTypeModel.objects.select_related(
                    "negative_feedback")
            )
        )

    if group_id:
        feedbacks = feedbacks.filter(location__group=group)

    if classification:
        feedbacks = feedbacks.filter(
            classification=FeedbackModel.FeedbackClassification(classification))

    if location_id:
        feedbacks = feedbacks.filter(location=location)

    paginator.page_size = int(request.query_params.get('page_size', 30))
    result_page = paginator.paginate_queryset(feedbacks, request)
    serializer = GETFeedbacksSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_feedback(request, portal, pk):
    """
    Function to get a feedback

    :param request: request
    :param pk: pk
    """

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        feedback = FeedbackModel.objects.filter(id=pk)

        if not feedback.exists():
            return JsonResponse({"msg": "Feedback does not exist"}, status=status.HTTP_404_NOT_FOUND)

        feedback = feedback.first()

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(
            has_permission=True).values_list('group_id', flat=True)

        if not permission_ids:
            return JsonResponse({"msg": "Manager does not have permission to access any location"}, status=status.HTTP_403_FORBIDDEN)

        # Obtener feedbacks solo de esas locaciones
        feedback = FeedbackModel.objects.filter(
            id=pk,
            location__group_id__in=permission_ids
        )

        if not feedback.exists():
            return JsonResponse({"msg": "Feedback does not exist"}, status=status.HTTP_404_NOT_FOUND)

        feedback = feedback.first()

        if feedback.location.group.id not in permission_ids:
            return JsonResponse({"msg": "Manager does not have permission to access this feedback"}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        # Get locations for manager and user roles based on their permissions
        permission_ids = request.user.user_location_permissions.all().values_list('location_id',
                                                                                  flat=True)

        feedback = FeedbackModel.objects.filter(
            id=pk, location_id__in=permission_ids)

        if not feedback.exists():
            return JsonResponse({"msg": "Feedback does not exist"}, status=status.HTTP_404_NOT_FOUND)

        feedback = feedback.first()

        if feedback.location.id not in permission_ids:
            return JsonResponse({"msg": "User does not have permission to access this feedback"}, status=status.HTTP_403_FORBIDDEN)

    return Response(GETFeedbackSerializer(feedback).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_feedback_logistics(request, portal):
    """
    Function to get feedback logistics

    :param request: request
    :param portal: portal
    """

    interval = request.GET.get('interval', None)

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        feedbacks = FeedbackModel.objects.select_related("location").prefetch_related(
            Prefetch("positive_types", queryset=PositiveFeedbackTypeModel.objects.select_related(
                "positive_feedback")),
            Prefetch("negative_types", queryset=NegativeFeedbackTypeModel.objects.select_related(
                "negative_feedback"))
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(
            has_permission=True).values_list('group_id', flat=True)

        if not permission_ids:
            return JsonResponse({"msg": "Manager does not have permission to access to that location"}, status=status.HTTP_403_FORBIDDEN)

        # Obtener feedbacks solo de esas locaciones
        feedbacks = FeedbackModel.objects.filter(
            location__group_id__in=permission_ids
        ).select_related("location").prefetch_related(
            Prefetch(
                "positive_types",
                queryset=PositiveFeedbackTypeModel.objects.select_related(
                    "positive_feedback")
            ),
            Prefetch(
                "negative_types",
                queryset=NegativeFeedbackTypeModel.objects.select_related(
                    "negative_feedback")
            )
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        # Obtener las IDs de locaciones permitidas para el usuario
        permission_ids = request.user.user_location_permissions.all().values_list(
            'location_id', flat=True
        )

        if not permission_ids:
            return JsonResponse({"msg": "User does not have permission to access to this location"}, status=status.HTTP_403_FORBIDDEN)

        # Obtener feedbacks solo de esas locaciones
        feedbacks = FeedbackModel.objects.filter(location_id__in=permission_ids).select_related("location").prefetch_related(
            Prefetch(
                "positive_types",
                queryset=PositiveFeedbackTypeModel.objects.select_related(
                    "positive_feedback")
            ),
            Prefetch(
                "negative_types",
                queryset=NegativeFeedbackTypeModel.objects.select_related(
                    "negative_feedback")
            )
        )

    now = timezone.now()

    if interval:

        interval = interval.upper()

        if interval in ['DAY', 'WEEK', 'MONTH', 'YEAR']:
            if interval == 'DAY':
                start_date = now.replace(
                    hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                trunc_fn = TruncHour("created_at")
                date_format = "%H:%M"

            elif interval == 'WEEK':
                start_date = (now - timedelta(days=now.weekday())
                              ).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                trunc_fn = TruncDay("created_at")
                date_format = "%d/%m"

            elif interval == 'MONTH':
                start_date = now.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                trunc_fn = TruncDay("created_at")
                date_format = "%Y-%m-%d"

            elif interval == 'YEAR':
                start_date = now.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                trunc_fn = TruncMonth("created_at")
                date_format = "%b"

            feedbacks = feedbacks.filter(
                created_at__gte=start_date, created_at__lte=end_date)

        else:
            return Response({"msg": "Invalid interval"}, status=status.HTTP_400_BAD_REQUEST)

    trend_data = feedbacks.annotate(
        period=trunc_fn
    ).values('period', 'classification').annotate(
        count=Count('id')
    ).order_by('period')

    trend = defaultdict(lambda: {"positive": 0, "negative": 0})

    for item in trend_data:
        if interval == 'MONTH':
            # Group by week for monthly trend
            monday = item['period'] - timedelta(days=item['period'].weekday())
            key = monday.strftime("%d/%m")
        else:
            key = item['period'].strftime(date_format)

        if item['classification'] in ['EX', 'GO']:
            trend[key]['positive'] += item['count']
        else:
            trend[key]['negative'] += item['count']

    total_feedbacks = feedbacks.count()
    total_positive_feedbacks = feedbacks.filter(classification__in=[
                                                FeedbackModel.FeedbackClassification.EXCELLENT, FeedbackModel.FeedbackClassification.GOOD]).count()
    total_negative_feedbacks = feedbacks.filter(classification__in=[
                                                FeedbackModel.FeedbackClassification.AVERAGE, FeedbackModel.FeedbackClassification.BAD]).count()
    total_excellent_feedbacks = feedbacks.filter(
        classification=FeedbackModel.FeedbackClassification.EXCELLENT).count()
    total_good_feedbacks = feedbacks.filter(
        classification=FeedbackModel.FeedbackClassification.GOOD).count()
    total_average_feedbacks = feedbacks.filter(
        classification=FeedbackModel.FeedbackClassification.AVERAGE).count()
    total_bad_feedbacks = feedbacks.filter(
        classification=FeedbackModel.FeedbackClassification.BAD).count()

    top_locations = feedbacks.annotate(
        loc_id=F('location__id'),
        loc_name=F('location__name')
    ).values(
        'loc_id', 'loc_name'
    ).annotate(
        total=Count('id'),
        positive=Count('id', filter=Q(classification__in=[
            FeedbackModel.FeedbackClassification.EXCELLENT,
            FeedbackModel.FeedbackClassification.GOOD
        ])),
        satisfaction=ExpressionWrapper(
            F('positive') * 100.0 / F('total'),
            output_field=FloatField()
        )
    ).order_by('-satisfaction')[:5]

    data = {
        'overall': {
            'quantity': total_feedbacks,
            'overall_satisfaction_percentage': get_feedback_distribution(total_positive_feedbacks, total_feedbacks),
            'positive_feedbacks': total_positive_feedbacks,
            'negative_feedbacks': total_negative_feedbacks,
        },
        'trend': [
            {"time": time, "positive": values["positive"], "negative": values["negative"]} for time, values in sorted(trend.items())
        ],
        'distribution': {
            'excellent_feedbacks': get_feedback_distribution(total_excellent_feedbacks, total_feedbacks),
            'good_feedbacks': get_feedback_distribution(total_good_feedbacks, total_feedbacks),
            'average_feedbacks': get_feedback_distribution(total_average_feedbacks, total_feedbacks),
            'bad_feedbacks': get_feedback_distribution(total_bad_feedbacks, total_feedbacks)
        },
        'location_perfomance': [
            {"id": loc["loc_id"], "name": loc["loc_name"],
                "satisfaction_percentage": round(loc["satisfaction"])}
            for loc in top_locations
        ],
        'feedback_type_summary': {
            'excelent_feedbacks_quantity': total_excellent_feedbacks,
            'good_feedbacks_quantity': total_good_feedbacks,
            'average_feedbacks_quantity': total_average_feedbacks,
            'bad_feedbacks_quantity': total_bad_feedbacks,
        }
    }

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def delete_feedback_type(request, portal, feedback_category, feedback_id):
    """
    Function to delete a feedback type

    :param request: request
    :param portal: portal
    :param feedback_category: category of the feedback, can be 'positive' or 'negative'
    :param feedback_id: primary key of the feedback type
    """

    if feedback_category == 'positive':
        feedback_type = PositiveFeedbackModel.objects.filter(id=feedback_id)
    elif feedback_category == 'negative':
        feedback_type = NegativeFeedbackModel.objects.filter(id=feedback_id)
    else:
        return Response({"msg": "Invalid feedback category"}, status=status.HTTP_400_BAD_REQUEST)

    if not feedback_type.exists():
        return Response({"msg": "Feedback type not found"}, status=status.HTTP_404_NOT_FOUND)

    feedback_type.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def update_feedback_types(request, portal):
    """
    Function to update the feedback types

    :param request: request
    :param portal: portal
    """

    positive_feedback_ids = request.data.get('positive_feedback_ids', [])
    negative_feedback_ids = request.data.get('negative_feedback_ids', [])

    if not positive_feedback_ids and not negative_feedback_ids:
        return Response({"msg": "positive_feedback_ids and negative_feedback_ids are required"}, status=status.HTTP_400_BAD_REQUEST)

    if not (len(positive_feedback_ids) == 6 and len(negative_feedback_ids) == 6):
        return Response(
            {"msg": "positive_feedback_ids and negative_feedback_ids must contain exactly 6 IDs each"},
            status=status.HTTP_400_BAD_REQUEST
        )

    positive_feedbacks = PositiveFeedbackModel.objects.filter(
        id__in=positive_feedback_ids)
    negative_feedbacks = NegativeFeedbackModel.objects.filter(
        id__in=negative_feedback_ids)

    # Verify that all positive feedbacks exist
    if positive_feedbacks.count() != len(positive_feedback_ids):
        return Response(
            {"msg": "One or more positive feedback IDs do not exist"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify that all negative feedbacks exist
    if negative_feedbacks.count() != len(negative_feedback_ids):
        return Response(
            {"msg": "One or more negative feedback IDs do not exist"},
            status=status.HTTP_400_BAD_REQUEST
        )

    PositiveFeedbackModel.objects.all().update(in_use=False)
    NegativeFeedbackModel.objects.all().update(in_use=False)

    positive_feedbacks.update(in_use=True)
    negative_feedbacks.update(in_use=True)

    return Response(status=status.HTTP_201_CREATED)
