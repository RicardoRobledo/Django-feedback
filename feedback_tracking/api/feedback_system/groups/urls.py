from django.urls import path
from . import views


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('', views.get_groups, name="get_groups"),
    path('group/', views.GroupView.as_view(), name="base_group"),
    path('group/retrieve/<int:group_id>/',
         views.get_group, name="retrieve_group"),
    path('group/update/<int:group_id>/',
         views.update_group, name="group"),
    path('group/delete/<int:group_id>/',
         views.delete_group, name="delete_group"),
    path('group/<int:group_id>/locations/',
         views.get_group_locations, name="get_group_locations"),
]
