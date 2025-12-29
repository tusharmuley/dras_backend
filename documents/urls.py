from django.urls import re_path,  path
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # ==========================================================
    # DOCUMENT LIST & UPLOAD
    # ==========================================================
    # GET  → List documents (role based + filters + pagination)
    # POST → Upload new document (Maker / Employee only)
    path(
        "documents/",
        DocumentView.as_view(),
        name="documents"
    ),

    # ==========================================================
    # DOCUMENT DETAIL / REVIEW ACTIONS
    # ==========================================================
    # GET    → View single document details
    # PUT    → Approve / Reject / Change category (Approver only)
    # DELETE → Delete draft / rejected document (Maker / Super Admin)
    path(
        "documents/<uuid:document_id>/",
        DocumentView.as_view(),
        name="document-detail"
    ),

    # ==========================================================
    # RESUBMIT DOCUMENT (AFTER REJECTION)
    # ==========================================================
    # POST → Resubmit rejected document with updated file
    # Only allowed when:
    #   - User = Maker (Employee)
    #   - Document status = REJECTED
    path(
        "documents/<uuid:document_id>/resubmit/",
        DocumentResubmitView.as_view(),
        name="document-resubmit"
    ),

    # ==========================================================
    # APPROVER EDIT DOCUMENT CONTENT
    # ==========================================================
    # PUT → Approver uploads revised version before approval
    # Rules:
    #   - Allowed only for Manager / Admin / Super Admin
    #   - Not allowed once document is APPROVED
    path(
        "documents/<uuid:document_id>/edit-content/",
        DocumentEditContentView.as_view(),
        name="document-edit-content"
    ),

    # ==========================================================
    # DOWNLOAD DOCUMENT (WITH AUDIT LOG)
    # ==========================================================
    # GET → Download document file
    # System logs:
    #   - Who downloaded
    #   - When downloaded
    path(
        "documents/<uuid:document_id>/download/",
        DocumentDownloadView.as_view(),
        name="document-download"
    ),

    # ==========================================================
    # SHARE DOCUMENT VIA EMAIL (WITH AUDIT LOG)
    # ==========================================================
    # POST → Share document with external/internal email
    # System logs:
    #   - Who shared
    #   - Shared with which email
    #   - Timestamp
    path(
        "documents/<uuid:document_id>/share/",
        DocumentShareView.as_view(),
        name="document-share"
    ),
    # ==========================================================
    # UPLOAD SIGNED VIEW
    # ==========================================================
    # POST → Upload signed document after approval
    # System logs:
    #   - Who uploaded
    #   - Which document
    #   - Timestamp
    path(
    "documents/<uuid:document_id>/upload-signed/",
    DocumentUploadSignedView.as_view(),
    name="document-upload-signed"
),

    path("category/", CategoryView.as_view(), name="categories"),
    path("category/<uuid:category_id>/", CategoryView.as_view(), name="categories"),
]

# serve media in development only
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )