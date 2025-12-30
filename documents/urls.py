from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # ==========================================================
    # DOCUMENT LIST & UPLOAD
    # ==========================================================
    # GET  → List documents (role based + filters + pagination)
    # POST → Upload new document (Maker / Employee only)
    path("documents/",DocumentView.as_view(), name="documents"),
    path( "documents", DocumentView.as_view(), name="documents-no-slash"), #for without slash also accept request

    # ==========================================================
    # DOCUMENT DETAIL / REVIEW ACTIONS
    # ==========================================================
    # GET    → View single document details
    # PUT    → Approve / Reject / Change category (Approver only)
    # DELETE → Delete draft / rejected document (Maker / Super Admin)
    path("documents/<uuid:document_id>/",DocumentView.as_view(),name="document-detail"),
    path("documents/<uuid:document_id>",DocumentView.as_view(), name="document-detail-no-slash"), #for without slash also accept request

    # ==========================================================
    # RESUBMIT DOCUMENT (AFTER REJECTION)
    # ==========================================================
    # POST → Resubmit rejected document with updated file
    # Only allowed when:
    #   - User = Maker (Employee)
    #   - Document status = REJECTED
    path("documents/<uuid:document_id>/resubmit/", DocumentResubmitView.as_view(), name="document-resubmit"),
    path("documents/<uuid:document_id>/resubmit", DocumentResubmitView.as_view(), name="document-resubmit-no-slash"), #for without slash also accept request

    # ==========================================================
    # APPROVER EDIT DOCUMENT CONTENT
    # ==========================================================
    # PUT → Approver uploads revised version before approval
    # Rules:
    #   - Allowed only for Manager / Admin / Super Admin
    #   - Not allowed once document is APPROVED
    path("documents/<uuid:document_id>/edit-content/", DocumentEditContentView.as_view(), name="document-edit-content"),
    path("documents/<uuid:document_id>/edit-content", DocumentEditContentView.as_view(), name="document-edit-content-no-slash"), #for without slash also accept request

    # ==========================================================
    # DOWNLOAD DOCUMENT (WITH AUDIT LOG)
    # ==========================================================
    # GET → Download document file
    # System logs:
    #   - Who downloaded
    #   - When downloaded
    path("documents/<uuid:document_id>/download/",DocumentDownloadView.as_view(),name="document-download"),
    path("documents/<uuid:document_id>/download",DocumentDownloadView.as_view(),name="document-download-no-slash"),

    # ==========================================================
    # SHARE DOCUMENT VIA EMAIL (WITH AUDIT LOG)
    # ==========================================================
    # POST → Share document with external/internal email
    # System logs:
    #   - Who shared
    #   - Shared with which email
    #   - Timestamp
    path("documents/<uuid:document_id>/share/", DocumentShareView.as_view(),name="document-share"),
    path("documents/<uuid:document_id>/share",DocumentShareView.as_view(),name="document-share-no-slash"), #for without slash also accept request
    # ==========================================================
    # UPLOAD SIGNED VIEW
    # ==========================================================
    # POST → Upload signed document after approval
    # System logs:
    #   - Who uploaded
    #   - Which document
    #   - Timestamp
    path("documents/<uuid:document_id>/upload-signed/",DocumentUploadSignedView.as_view(),name="document-upload-signed"),
    path("documents/<uuid:document_id>/upload-signed",DocumentUploadSignedView.as_view(),name="document-upload-signed-no-slash"), #for without slash also accept request


    # for category urls 
    path("category/", CategoryView.as_view(), name="categories"),
    path("category", CategoryView.as_view(), name="categories-no-slash"), #for without slash also accept request
    path("category/<uuid:category_id>/", CategoryView.as_view(), name="category-detail"),
    path("category/<uuid:category_id>", CategoryView.as_view(), name="category-detail-no-slash"), #for without slash also accept request
]

# serve media in development only
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
