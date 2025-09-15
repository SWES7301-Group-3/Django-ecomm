from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
import datetime

class CustomUser(AbstractUser):
    """
    Custom user model using email as the primary login field instead of username.
    Overriding groups and user_permissions to avoid reverse accessor name clashes.
    """
    # Make email required and unique
    email = models.EmailField(
        verbose_name="email address",
        unique=True,
        help_text="Required. Enter a valid email address."
    )
    
    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="customuser_set",
        related_query_name="customuser",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="customuser_permissions_set",
        related_query_name="customuser_permission",
    )

    # Set email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Required when creating superuser via createsuperuser

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserOTP(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at