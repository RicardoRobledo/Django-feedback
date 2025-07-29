from django.urls import path

from . import views


urlpatterns = [
    path('', views.get_locations, name='locations'),
    path('location/', views.LocationView.as_view(), name='base_location'),
    path('location/credentials/<int:location_id>/',
         views.get_location_credentials, name='get_location_credentials'),
    path('location/verify-credentials/<int:location_id>/',
         views.verify_location_credentials, name='verify_location_credentials'),
    path('location/retrieve/<int:location_id>/',
         views.get_location, name='retrieve_location'),
    path('location/update/<int:location_id>/',
         views.update_location, name='update_location'),
    path('location/delete/<int:location_id>/',
         views.delete_location, name='delete_location'),
]
