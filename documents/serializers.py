from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True
    )
    

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "site_code",
            "category",
            "current_status",
            "file_url",
            "created_by_name",
            "created_datetime",
            "updated_datetime",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
