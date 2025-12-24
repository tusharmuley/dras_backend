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
