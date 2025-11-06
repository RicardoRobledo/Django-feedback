from django.contrib.auth.base_user import BaseUserManager
from django.db import models

from tenant_users.tenants.models import UserProfile, UserProfileManager

from feedback_tracking.base.models import BaseModel
from feedback_tracking.administrative_system.organizations.models import OrganizationModel


class UserManager(UserProfileManager):

    def create_user(self, first_name, middle_name, last_name, username, password, email, is_staff=False, is_active=True):
        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            username=username,
            email=email,
            is_staff=is_staff,
            is_active=is_active,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, middle_name, last_name, username, password, email):
        return self.create_user(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            username=username,
            password=password,
            email=email,
            is_staff=True,
            is_active=True,
        )


class UserModel(UserProfile, BaseModel):
    """
    This model define an user

    Attributes:
        email (str): email of the user
        username (str): username of the user
        created_at (datetime): creation date
    """

    class Meta:
        app_label = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(name='user_id_idx', fields=['id']),
        ]

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'middle_name', 'last_name', 'email']

    objects = UserManager()
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_model_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_model_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    organization = models.ForeignKey(
        OrganizationModel,
        on_delete=models.DO_NOTHING,
        related_name='user_organization',
        verbose_name='Organization',
        help_text='Organization of the user',
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=50, null=False, blank=False)
    middle_name = models.CharField(max_length=50, null=False, blank=False,)
    last_name = models.CharField(max_length=50, null=False, blank=False,)
    username = models.CharField(
        unique=True, max_length=20, null=False, blank=False,)
    email = models.EmailField(unique=True, null=False, blank=False,)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    def __repr__(self):
        return (f'UserModel('
                f'id={self.id}, '
                f'first_name={self.first_name}, '
                f'middle_name={self.middle_name}, '
                f'last_name={self.last_name}, '
                f'username={self.username}, '
                f'email={self.email}, '
                f'organization={self.organization}, '
                f'is_staff={self.is_staff}, '
                f'is_active={self.is_active}, '
                f'created_at={self.created_at}, '
                f'updated_at={self.updated_at})')
