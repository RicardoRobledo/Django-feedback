from django.urls import path
from . import views


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('', views.get_users, name='get_users'),
    path('user/', views.create_system_user, name='create_user'),
    path('user/<int:user_id>/', views.get_user, name='get_user'),
    path('user-delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user-update/<int:user_id>/', views.update_user, name='update_user'),
    path('user-update/<int:user_id>/password/',
         views.update_user_password, name='update_user_password'),
    path('user-update/<int:user_id>/account/',
         views.update_user_account, name='update_user_account'),
    path('user/user-permissions/', views.UserLevelPermissionView.as_view(),
         name="get_permissions"),
]
