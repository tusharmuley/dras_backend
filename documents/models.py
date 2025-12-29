# from django.db import models
# from accounts.models import User

# class Document(models.Model):
#     STATUS_CHOICES = (
#         ("draft", "Draft"),
#         ("pending", "Pending Review"),
#         ("rejected", "Rejected"),
#         ("approved", "Approved"),
#     )

#     title = models.CharField(max_length=255)
#     site_code = models.CharField(max_length=100)
#     file = models.FileField(upload_to="documents/", null=True, blank=True)
#     # simple charfield for now (as you decided)
#     category = models.CharField(max_length=100)
#     current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     created_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     updated_datetime = models.DateTimeField(auto_now=True, null=True, blank=True)

#     class Meta:
#         db_table = "documents_tbl"
#         indexes = [
#             models.Index(fields=["current_status"]),
#             models.Index(fields=["category"]),
#             models.Index(fields=["site_code"]),
#             models.Index(fields=["created_by"]),
#         ]

#     def __str__(self):
#         return self.title



# class DocumentReview(models.Model):

#     ACTION_CHOICES = (
#         ("submitted", "Submitted"),
#         ("rejected", "Rejected"),
#         ("approved", "Approved"),
#     )

#     document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
#     file_path = models.CharField(max_length=255, null=True, blank=True)
#     action = models.CharField(max_length=20, choices=ACTION_CHOICES)
#     action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     # Reject reason / approval note / general comments
#     action_notes = models.TextField(blank=True, null=True)
#     # UID only for approved documents
#     uid = models.CharField(max_length=100, blank=True, null=True)
#     created_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     updated_datetime = models.DateTimeField(auto_now=True, null=True, blank=True)

#     class Meta:
#         db_table = "document_reviews_tbl"
#         indexes = [
#             models.Index(fields=["action"]),
#             models.Index(fields=["document"]),
#             models.Index(fields=["action_by"]),
#         ]

#     def __str__(self):
#         return f"{self.document_id} - {self.action}"



from django.db import models
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL


class UploadedDocument(models.Model):

    STATUS_CHOICES = (
    ("DRAFT", "Draft"),
    ("PENDING", "Pending Review"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)

    file = models.FileField(upload_to="dcs/documents/")

    category = models.CharField(max_length=100)

    project_code = models.CharField(max_length=100)

    current_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )

    uid = models.CharField(
        max_length=50, unique=True, null=True, blank=True
    )  # Generated only after approval

    is_read_only = models.BooleanField(default=False)

    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="documents_uploaded"
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_approved"
    )

    approved_at = models.DateTimeField(null=True, blank=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dcs_documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title



# DocumentVersion (for Edit / Resubmit / Signed Copy)
class DocumentVersion(models.Model):
    VERSION_TYPE = (
        ("DRAFT", "Draft"),
        ("REVISED", "Revised"),
        ("SIGNED", "Signed Final"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        UploadedDocument, on_delete=models.CASCADE, related_name="versions"
    )
    file = models.FileField(upload_to="dcs/document_versions/")
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dcs_document_versions"
        ordering = ["-created_at"]

class DocumentAudit(models.Model):

    ACTION_CHOICES = (
        ("REJECTED", "Rejected"),
        ("APPROVED", "Approved"),
        ("CATEGORY_CHANGED", "Category Changed"),
        ("EDITED", "Content Edited"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document = models.ForeignKey(
        UploadedDocument, on_delete=models.CASCADE, related_name="reviews"
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    remarks = models.TextField(null=True, blank=True)

    old_category = models.CharField(max_length=100, null=True, blank=True)
    new_category = models.CharField(max_length=100, null=True, blank=True)

    action_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="document_actions"
    )

    action_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dcs_document_reviews"
        ordering = ["-action_at"]

    def __str__(self):
        return f"{self.document.title} - {self.action}"



class DocumentAccessLog(models.Model):
    ACTION_CHOICES = (
        ("DOWNLOADED", "Downloaded"),
        ("SHARED", "Shared"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_by = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_with = models.EmailField(null=True, blank=True)
    action_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dcs_document_access_logs"
        
        
        
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_datetime = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = "dcs_categories"
        ordering = ["-created_datetime"]
        
    def __str__(self):
        return self.category
    