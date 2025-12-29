from rest_framework import serializers
from .models import User


class EmployeeSerializer(serializers.ModelSerializer):
    # 👇 combined name
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "username",
            "role",
            "mobile",
            "employee_id",
            "created_by",
        ]

    def get_full_name(self, obj):
        # safely combine first + last name
        first = obj.first_name or ""
        last = obj.last_name or ""
        return f"{first} {last}".strip()


class AuthDataSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    created_datetime = serializers.SerializerMethodField()
    updated_datetime = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "is_active",
            "employee_id",
            "mobile",
            "created_by",
            "created_datetime",
            "updated_datetime",
        ]

    def get_created_by(self, obj):
        return obj.created_by.id if obj.created_by else None

    def get_created_datetime(self, obj):
        return obj.created_datetime.isoformat() if obj.created_datetime else None

    def get_updated_datetime(self, obj):
        return obj.updated_datetime.isoformat() if obj.updated_datetime else None