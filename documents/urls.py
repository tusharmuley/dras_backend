from django.urls import re_path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path(r"^documents/?$", UploadDocumentView.as_view()),
    
]
# serve media in development only
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )