from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta
from django.utils import timezone

class User(AbstractUser):

    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),
        ("admin", "Admin"),
        ("employee", "Employee"),
    )

    role = models.CharField( max_length=20, choices=ROLE_CHOICES)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    created_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_datetime = models.DateTimeField(auto_now=True, null=True, blank=True)

    # Employee additional fields
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)

    # hierarchy mapping
    created_by = models.ForeignKey("self",null=True,  blank=True, on_delete=models.SET_NULL, related_name="created_users")

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
    
   
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)