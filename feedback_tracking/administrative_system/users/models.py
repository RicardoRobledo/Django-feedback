from django.db import models

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager

from feedback_tracking.base.models import BaseModel
from feedback_tracking.administrative_system.organizations.models import OrganizationModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton


class UserManager(BaseUserManager):

    def create_user(self, first_name, middle_name, last_name, username, password, email, is_staff, is_active, is_superuser=False):
        user = self.model(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            username=username,
            email=email,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=is_superuser,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, middle_name, last_name, username, password, email):
        return self.create_user(first_name, middle_name, last_name, username, password, email, True, True, True)


class UserModel(AbstractBaseUser, PermissionsMixin, BaseModel):
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
    stripe_customer_id = models.CharField(
        max_length=100, unique=True, blank=True, null=True, help_text="Unique identifier for the Stripe customer")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):

        # first delete the Stripe customer if it exists
        if self.stripe_customer_id:
            try:
                # Attempt to delete the customer from Stripe
                StripeSingleton().customer().delete(self.stripe_customer_id)
            except Exception as e:
                print(f"Error deleting Stripe customer: {e}")

        super().delete(*args, **kwargs)

    def __str__(self):
        return self.username

    def __repr__(self):
        return (f'UserModel('
                f'id={self.id}, '
                f'stripe_customer_id={self.stripe_customer_id}, '
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
