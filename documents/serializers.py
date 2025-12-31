# from rest_framework import serializers
# from .models import Document


# class DocumentSerializer(serializers.ModelSerializer):
#     file_url = serializers.SerializerMethodField()
#     created_by_name = serializers.CharField(
#         source="created_by.username",
#         read_only=True
#     )
    

#     class Meta:
#         model = Document
#         fields = [
#             "id",
#             "title",
#             "site_code",
#             "category",
#             "current_status",
#             "file_url",
#             "created_by_name",
#             "created_datetime",
#             "updated_datetime",
#         ]

#     def get_file_url(self, obj):
#         request = self.context.get("request")
#         if obj.file and request:
#             return request.build_absolute_uri(obj.file.url)
#         return None

from rest_framework import serializers
from .models import UploadedDocument, DocumentAudit
from accounts.models import User
from .models import Category, ProjectCode

# -------------------------------
# Nested serializers for FK expansion (GET only)
# -------------------------------
class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

class CategoryNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category']

# -------------------------------
# GET serializer for UploadedDocument
# -------------------------------
class UploadedDocumentReadSerializer(serializers.ModelSerializer):
    uploaded_by = UserNestedSerializer(read_only=True)
    approved_by = UserNestedSerializer(read_only=True)
    category = CategoryNestedSerializer(read_only=True)
    is_signed = serializers.SerializerMethodField()

    class Meta:
        model = UploadedDocument
        fields = [
            "id",
            "title",
            "category",
            "project_code",
            "current_status",
            "uid",
            "file",
            "uploaded_by",
            "approved_by",
            "created_at",
            "approved_at",
            "is_signed",
        ]
    
    def get_is_signed(self, obj):
        """Check if document has a signed version uploaded"""
        return obj.versions.filter(version_type="SIGNED").exists()

# -------------------------------
# Default serializer for create/update (POST/PUT)
# -------------------------------
class UploadedDocumentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedDocument
        fields = [
            "id",
            "title",
            "category",
            "project_code",
            "current_status",
            "uid",
            "file",
            "uploaded_by",
            "approved_by",
            "created_at",
            "approved_at",
            "is_read_only",
        ]
        read_only_fields = ["uid", "approved_by", "approved_at", "is_read_only", "created_at"]

# -------------------------------
# GET serializer for DocumentAudit (expand FK)
# -------------------------------
class DocumentAuditReadSerializer(serializers.ModelSerializer):
    action_by = UserNestedSerializer(read_only=True)
    old_category = CategoryNestedSerializer(read_only=True)
    new_category = CategoryNestedSerializer(read_only=True)

    class Meta:
        model = DocumentAudit
        fields = "__all__"

# -------------------------------
# Default serializer for DocumentAudit create/update
# -------------------------------
class DocumentAuditWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAudit
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        
        
class ProjectCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCode
        fields = "__all__"