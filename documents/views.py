from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from accounts.models import User
from django.db import transaction
from .models import Document, DocumentReview
import sys


from .serializers import DocumentSerializer

class UploadDocumentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            
            user = request.user

            if user.role == "employee":
                queryset = Document.objects.filter(created_by=user)

            elif user.role == "admin":
                employees = User.objects.filter(created_by=user)
                queryset = Document.objects.filter(created_by__in=employees)

            elif user.role == "super_admin":
                queryset = Document.objects.all()

            else:
                return Response({"message": "Permission denied"}, status=403)

            serializer = DocumentSerializer(
                queryset,
                many=True,
                context={"request": request}
            )

            return Response({"documents": serializer.data, 'message': "Documents fetched successfully", "status":status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

        
    def post(self, request):
        try: 
            user = request.user
            # 🔒 Only employee can upload
            if user.role != "employee":
                return Response({"message": "Only employees can upload documents", "status":status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            title = request.data.get("title")
            site_code = request.data.get("site_code")
            category = request.data.get("category")
            status_value = request.data.get("status")
            file = request.FILES.get("file")

            # ✅ Validation
            if not all([title, site_code, category, status_value, file]):
                return Response({"message": "All fields are required", "status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

            if status_value not in ["draft", "pending"]:
                return Response({"message": "Invalid status. Allowed: draft, pending", "status":status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

            # 💾 Save document
            try:
                with transaction.atomic():
                    document = Document.objects.create(
                        title=title,
                        site_code=site_code,
                        category=category,
                        file=file,
                        current_status=status_value,
                        created_by=user
                    )
            except Exception as e:
                line_number = sys.exc_info()[2].tb_lineno
                return Response({"message": "something went wrong in upload file", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

            # 📝 If directly submitted, add review log
            if status_value == "pending":
                DocumentReview.objects.create(
                    document=document,
                    action="submitted",
                    action_by=user,
                    file_path=document.file.name
                )

            return Response({ "message": "Document uploaded successfully", "document_id": document.id, "status": document.current_status, "file_url": document.file.url}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )