from django.db import models
from accounts.models import User

class Document(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("pending", "Pending Review"),
        ("rejected", "Rejected"),
        ("approved", "Approved"),
    )

    title = models.CharField(max_length=255)
    site_code = models.CharField(max_length=100)
    file = models.FileField(upload_to="documents/", null=True, blank=True)
    # simple charfield for now (as you decided)
    category = models.CharField(max_length=100)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_datetime = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = "documents_tbl"
        indexes = [
            models.Index(fields=["current_status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["site_code"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return self.title



class DocumentReview(models.Model):

    ACTION_CHOICES = (
        ("submitted", "Submitted"),
        ("rejected", "Rejected"),
        ("approved", "Approved"),
    )

    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    file_path = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # Reject reason / approval note / general comments
    action_notes = models.TextField(blank=True, null=True)
    # UID only for approved documents
    uid = models.CharField(max_length=100, blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_datetime = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = "document_reviews_tbl"
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["document"]),
            models.Index(fields=["action_by"]),
        ]

    def __str__(self):
        return f"{self.document_id} - {self.action}"
