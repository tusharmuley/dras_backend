# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework import status
# from accounts.models import User
# from django.db import transaction
# from .models import Document, DocumentReview
# import sys


# from .serializers import DocumentSerializer

# class UploadDocumentView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
            
#             user = request.user

#             if user.role == "employee":
#                 queryset = Document.objects.filter(created_by=user)

#             elif user.role == "admin":
#                 employees = User.objects.filter(created_by=user)
#                 queryset = Document.objects.filter(created_by__in=employees)

#             elif user.role == "super_admin":
#                 queryset = Document.objects.all()

#             else:
#                 return Response({"message": "Permission denied"}, status=403)

#             serializer = DocumentSerializer(
#                 queryset,
#                 many=True,
#                 context={"request": request}
#             )

#             return Response({"documents": serializer.data, 'message': "Documents fetched successfully", "status":status.HTTP_200_OK}, status=status.HTTP_200_OK)
#         except Exception as e:
#             line_number = sys.exc_info()[2].tb_lineno
#             return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

        
#     def post(self, request):
#         try: 
#             user = request.user
#             # 🔒 Only employee can upload
#             if user.role != "employee":
#                 return Response({"message": "Only employees can upload documents", "status":status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

#             title = request.data.get("title")
#             site_code = request.data.get("site_code")
#             category = request.data.get("category")
#             status_value = request.data.get("status")
#             file = request.FILES.get("file")

#             # ✅ Validation
#             if not all([title, site_code, category, status_value, file]):
#                 return Response({"message": "All fields are required", "status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

#             if status_value not in ["draft", "pending"]:
#                 return Response({"message": "Invalid status. Allowed: draft, pending", "status":status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

#             # 💾 Save document
#             try:
#                 with transaction.atomic():
#                     document = Document.objects.create(
#                         title=title,
#                         site_code=site_code,
#                         category=category,
#                         file=file,
#                         current_status=status_value,
#                         created_by=user
#                     )
#             except Exception as e:
#                 line_number = sys.exc_info()[2].tb_lineno
#                 return Response({"message": "something went wrong in upload file", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

#             # 📝 If directly submitted, add review log
#             if status_value == "pending":
#                 DocumentReview.objects.create(
#                     document=document,
#                     action="submitted",
#                     action_by=user,
#                     file_path=document.file.name
#                 )

#             return Response({ "message": "Document uploaded successfully", "document_id": document.id, "status": document.current_status, "file_url": document.file.url}, status=status.HTTP_201_CREATED)
        
#         except Exception as e:
#             line_number = sys.exc_info()[2].tb_lineno
#             return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import FileResponse
import uuid
from uuid import uuid4
import os

from accounts.models import User
from .models import *
from .serializers import *
from .utils import *
from .tasks import send_document_approval_email_task, send_document_rejection_email_task
from dcs_backend.permissions import *
import sys


# ===========================
# Document View: List / Detail / Upload / Approve / Reject / Delete
# ===========================
class DocumentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = CustomPagination

    # GET → List / Detail
    def get(self, request, document_id=None):
        try:
            user = request.user

            if document_id:
                document = get_object_or_404(UploadedDocument, id=document_id)
                serializer = UploadedDocumentReadSerializer(document, context={"request": request})
                return Response(
                    {"message": "Document retrieved successfully",
                     "data": serializer.data,
                     "status": status.HTTP_200_OK},
                    status=status.HTTP_200_OK
                )

            # Role-based queryset
            if user.role == "employee":
                queryset = UploadedDocument.objects.filter(uploaded_by=user)
            elif user.role == "admin":
                employees = User.objects.filter(created_by=user, is_active=True)
                employees_ids = employees.values_list('id', flat=True)
                employees_ids = list(employees_ids)
                # Get all documents from employees and admin
                queryset = UploadedDocument.objects.filter(uploaded_by__in=employees_ids + [user.id])
                # Exclude employee's draft documents (but keep admin's own drafts)
                queryset = queryset.exclude(
                    Q(current_status="DRAFT") & Q(uploaded_by__in=employees_ids)
                )
            elif user.role == "super_admin":
                # Show all documents, but exclude drafts that are NOT uploaded by super_admin
                queryset = UploadedDocument.objects.all()
                queryset = queryset.exclude(
                    Q(current_status="DRAFT") & ~Q(uploaded_by=user)
                )
            else:
                return Response(
                    {"message": "You do not have permission to view documents",
                     "data": None,
                     "status": status.HTTP_403_FORBIDDEN},
                    status=status.HTTP_403_FORBIDDEN
                )
            full_queryset = queryset

            # Filters
            search = request.GET.get("q")
            status_filter = request.GET.get("status")
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")

            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(uid__icontains=search) |
                    Q(project_code__icontains=search)
                )

            if status_filter:
                queryset = queryset.filter(current_status=status_filter)

            if start_date and end_date:
                queryset = queryset.filter(
                    created_at__date__range=[start_date, end_date]
                )

            all_status_count = {    
                "all": full_queryset.count(),
                "pending": full_queryset.filter(current_status="PENDING").count(),
                "approved": full_queryset.filter(current_status="APPROVED").count(),
                "rejected": full_queryset.filter(current_status="REJECTED").count(),
                "draft": full_queryset.filter(current_status="DRAFT").count(),
            }

            # Pagination
            paginator = CustomPagination()
            page = paginator.paginate_queryset(queryset, request)
            serializer = UploadedDocumentReadSerializer(page, many=True)
            data = serializer.data
            ab= paginator.get_paginated_response(data)
            return Response(
                {"message": "Documents retrieved successfully",
                 "data": ab.data,
                 "status": status.HTTP_200_OK,
                 "all_status_count": all_status_count},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Failed to retrieve documents",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST → Upload Document
    def post(self, request):
        try:
            user = request.user
            if user.role != "employee" and user.role != "admin":
                return Response({"message": "Only employees and admins can upload documents", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            title = request.data.get("title")
            print('title: ', title)
            category_id = request.data.get("category")
            print('category: ', category_id)
            project_code = request.data.get("project_code")
            print('project_code: ', project_code)
            file = request.FILES.get("file")
            print('file: ', file)
            document_status = request.data.get("document_status")

            
            STATUS_CHOICES = [
            "DRAFT",
            "PENDING",
            "APPROVED",
            "REJECTED"
            ]
            if document_status not in STATUS_CHOICES:
                return Response(
                    {"message": "Invalid document status",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not all([title, category_id, project_code, file, document_status]):
                return Response(
                    {"message": "All fields are required to upload a document",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate category exists and is active
            try:
                category_obj = Category.objects.get(id=category_id, is_active=True)
            except Category.DoesNotExist:
                return Response(
                    {"message": "Invalid category ID or category is not active",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                document = UploadedDocument.objects.create(
                    title=title,
                    category=category_obj,
                    project_code=project_code,
                    file=file,
                    uploaded_by=user,
                    current_status=document_status
                )

                DocumentAudit.objects.create(
                    document=document,
                    action="SUBMITTED",
                    action_by=user
                )

            return Response(
                {"message": "Document uploaded successfully",
                 "data": {"document_id": document.id, "status": document.current_status},
                 "status": status.HTTP_201_CREATED},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"message": "Failed to upload document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # PUT → Approve / Reject / Change Category
    def put(self, request, document_id):
        try:
            user = request.user
            document = get_object_or_404(UploadedDocument, id=document_id)

            # if user.role not in ["manager", "admin", "super_admin" ]:
            #     return Response(
            #         {"message": "You do not have permission to modify this document",
            #          "data": None,
            #          "status": status.HTTP_403_FORBIDDEN},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
                

            if document.is_read_only:
                return Response(
                    {"message": "Approved documents are read-only and cannot be modified",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            action = request.data.get("action")
            
            if user.role in ["super_admin", "admin"]:
                if action == "approve":
                    try:
                        with transaction.atomic():
                            uid = f"BVG-{uuid4().hex[:8].upper()}"
                            document.uid = uid
                            document.current_status = "APPROVED"
                            document.is_read_only = True
                            document.approved_by = user
                            document.approved_at = timezone.now()
                            document.save()
                            
                            # Ensure document is PDF (convert DOCX if needed)
                            final_pdf_path = ensure_pdf_file(document)
                            
                            # Stamp the PDF with UID
                            stamp_pdf_with_uid(final_pdf_path, uid)

                            DocumentAudit.objects.create(
                                document=document,
                                action="APPROVED",
                                action_by=user
                            )

                            # Send approval email to employee asynchronously via Celery
                            employee = document.uploaded_by
                            employee_name = employee.first_name or employee.username
                            approver_name = user.first_name or user.username
                            approved_date = document.approved_at.strftime('%d-%m-%Y %I:%M %p') if document.approved_at else timezone.now().strftime('%d-%m-%Y %I:%M %p')
                            
                            send_document_approval_email_task.delay(
                                employee_email=employee.email,
                                employee_name=employee_name,
                                document_title=document.title,
                                document_uid=uid,
                                approved_date=approved_date,
                                approver_name=approver_name
                            )

                            return Response(
                                {"message": "Document approved successfully",
                                "data": {"uid": uid, "status": document.current_status},
                                "status": status.HTTP_200_OK},
                                status=status.HTTP_200_OK
                        )
                    except Exception as e:
                        line_number = sys.exc_info()[2].tb_lineno
                        return Response({"message": "Failed to approve document", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        
                elif action == "reject":
                    try:
                        remarks = request.data.get("remarks")
                        document.current_status = "REJECTED"
                        document.save()

                        DocumentAudit.objects.create(
                            document=document,
                            action="REJECTED",
                            action_by=user,
                            remarks=remarks
                        )

                        # Send rejection email to employee asynchronously via Celery
                        employee = document.uploaded_by
                        if not employee or not employee.email:
                            print(f"Warning: Employee or email not found for document rejection. Document ID: {document.id}")
                        else:
                            employee_name = employee.first_name or employee.username
                            approver_name = user.first_name or user.username
                            rejected_date = timezone.now().strftime('%d-%m-%Y %I:%M %p')
                            
                            print(f"Attempting to send rejection email to {employee.email} for document: {document.title}")
                            send_document_rejection_email_task.delay(
                                employee_email=employee.email,
                                employee_name=employee_name,
                                document_title=document.title,
                                rejected_date=rejected_date,
                                approver_name=approver_name,
                                remarks=remarks
                            )
                            print(f"Rejection email task queued successfully for {employee.email}")

                        return Response(
                            {"message": "Document rejected successfully",
                            "data": {"status": document.current_status},
                            "status": status.HTTP_200_OK},
                            status=status.HTTP_200_OK
                        )
                    except Exception as e:
                        line_number = sys.exc_info()[2].tb_lineno
                        print(f"Error in rejection process: {str(e)}, line: {line_number}")
                        return Response({"message": "Failed to reject document", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                elif action == "draft":
                    try:
                        remarks = request.data.get("remarks")
                        document.current_status = "DRAFT"
                        document.save()

                        DocumentAudit.objects.create(
                            document=document,
                            action="DRAFT",
                            action_by=user,
                            remarks=remarks
                        )

                        # Send rejection email to employee asynchronously via Celery (same as reject action)
                        employee = document.uploaded_by
                        if not employee or not employee.email:
                            print(f"Warning: Employee or email not found for document draft. Document ID: {document.id}")
                        else:
                            employee_name = employee.first_name or employee.username
                            approver_name = user.first_name or user.username
                            rejected_date = timezone.now().strftime('%d-%m-%Y %I:%M %p')
                            
                            print(f"Attempting to send rejection email (draft) to {employee.email} for document: {document.title}")
                            send_document_rejection_email_task.delay(
                                employee_email=employee.email,
                                employee_name=employee_name,
                                document_title=document.title,
                                rejected_date=rejected_date,
                                approver_name=approver_name,
                                remarks=remarks
                            )
                            print(f"Rejection email task queued successfully (draft) for {employee.email}")

                        return Response(
                            {"message": "Document moved to draft successfully",
                            "data": {"status": document.current_status},
                            "status": status.HTTP_200_OK},
                            status=status.HTTP_200_OK
                        )
                    except Exception as e:
                        line_number = sys.exc_info()[2].tb_lineno
                        print(f"Error in draft process: {str(e)}, line: {line_number}")
                        return Response({"message": "Failed to move document to draft", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                elif action == "pending":
                    try:
                        document.current_status = "PENDING"
                        document.save()
                        DocumentAudit.objects.create(
                            document=document,
                            action="PENDING",
                            action_by=user
                        )
                        return Response({"message": "Document moved to pending successfully","data": {"status": document.current_status},"status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
                    except Exception as e:
                        line_number = sys.exc_info()[2].tb_lineno
                        print(f"Error in pending process: {str(e)}, line: {line_number}")
                        return Response({"message": "Failed to move document to pending", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                elif action == "change_category":
                    category_id = request.data.get("category")
                    
                    if not category_id:
                        return Response(
                            {"message": "Category ID is required",
                            "data": None,
                            "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Validate category exists and is active
                    try:
                        new_category_obj = Category.objects.get(id=category_id, is_active=True)
                    except Category.DoesNotExist:
                        return Response(
                            {"message": "Invalid category ID or category is not active",
                            "data": None,
                            "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Store old category before updating
                    old_category_obj = document.category
                    
                    document.category = new_category_obj
                    document.save()

                    DocumentAudit.objects.create(
                        document=document,
                        action="CATEGORY_CHANGED",
                        action_by=user,
                        old_category=old_category_obj,
                        new_category=new_category_obj,
                        remarks=request.data.get("remarks")
                    )

                    return Response(
                        {"message": "Document category updated successfully",
                        "data": {"category_id": str(new_category_obj.id), "category": new_category_obj.category},
                        "status": status.HTTP_200_OK},
                        status=status.HTTP_200_OK
                    )

                elif action == "update_content":
                    file = request.FILES.get("file")
                    if not file:
                        return Response({"message": "File is required to update content", "data": None, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
                    document.file = file
                    document.save()
                    DocumentAudit.objects.create(
                        document=document,
                        action="CONTENT_UPDATED",
                        action_by=user
                    )
                    return Response({"message": "Document content updated successfully", "status": status.HTTP_200_OK},status=status.HTTP_200_OK)
                
                else:
                    return Response({"message": "Invalid action specified", "data": None, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            
            elif user.role == "employee" and action in ["pending","update_content"]:
                if action == "pending":
                    try:
                        document.current_status = "PENDING"
                        document.save()
                        DocumentAudit.objects.create(document=document, action="PENDING", action_by=user)
                        return Response({"message": "Document moved to pending successfully","data": {"status": document.current_status},"status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
                    except Exception as e:
                        line_number = sys.exc_info()[2].tb_lineno
                        print(f"Error in pending process: {str(e)}, line: {line_number}")
                        return Response({"message": "Failed to move document to pending", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                elif action == "update_content":
                    try:
                        if user.id != document.uploaded_by.id:
                            return Response({"message": "You do not have permission to update this document","data": None,"status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
                        
                        file = request.FILES.get("file")
                        if not file:
                            return Response({"message": "File is required to update content", "data": None, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
                        document.file = file
                        document.save()
                        DocumentAudit.objects.create(document=document, action="CONTENT_UPDATED", action_by=user)
                        return Response({"message": "Document content updated successfully", "status": status.HTTP_200_OK},status=status.HTTP_200_OK)
                    except Exception as e:
                        line_number = sys.exc_info()[2].tb_lineno
                        print(f"Error in update content process: {str(e)}, line: {line_number}")
                        return Response({"message": "Failed to update document content", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({"message": "Invalid action specified", "data": None, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

            if document.is_read_only or document.current_status == "APPROVED":
                return Response(
                    {"message": "Approved documents cannot be deleted",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if document.uploaded_by != user and user.role != "super_admin":
                return Response(
                    {"message": "You do not have permission to delete this document",
                     "data": None,
                     "status": status.HTTP_403_FORBIDDEN},
                    status=status.HTTP_403_FORBIDDEN
                )

            document.delete()
            return Response(
                {"message": "Document deleted successfully",
                 "data": None,
                 "status": status.HTTP_200_OK},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Failed to delete document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
# Document Resubmit
# ===========================
class DocumentResubmitView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmployee]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, document_id):
        try:
            document = get_object_or_404(
                UploadedDocument,
                id=document_id,
                uploaded_by=request.user
            )

            if document.is_read_only:
                return Response(
                    {"message": "Approved documents cannot be resubmitted",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if document.current_status != "REJECTED":
                return Response(
                    {"message": "Only rejected documents can be resubmitted",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES.get("file")
            if not file:
                return Response(
                    {"message": "File is required for resubmission",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            DocumentVersion.objects.create(
                document=document,
                file=file,
                version_type="REVISED",
                uploaded_by=request.user
            )

            document.current_status = "PENDING"
            document.save(update_fields=["current_status"])

            DocumentAudit.objects.create(
                document=document,
                action="RESUBMITTED",
                action_by=request.user
            )

            return Response(
                {"message": "Document resubmitted successfully",
                 "data": {"status": document.current_status},
                 "status": status.HTTP_200_OK},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Failed to resubmit document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
# Document Edit Content
# ===========================
class DocumentEditContentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsApprover]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, document_id):
        try:
            document = get_object_or_404(UploadedDocument, id=document_id)

            if document.is_read_only or document.current_status == "APPROVED":
                return Response(
                    {"message": "Approved documents cannot be edited",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES.get("file")
            if not file:
                return Response(
                    {"message": "File is required to update content",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            DocumentVersion.objects.create(
                document=document,
                file=file,
                version_type="REVISED",
                uploaded_by=request.user
            )

            DocumentAudit.objects.create(
                document=document,
                action="EDITED",
                action_by=request.user
            )

            return Response(
                {"message": "Document content updated successfully",
                 "data": None,
                 "status": status.HTTP_200_OK},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Failed to edit document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
# Document Download
# ===========================
class DocumentDownloadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            document = get_object_or_404(UploadedDocument, id=document_id)

            if request.user.role == "employee" and document.uploaded_by != request.user:
                return Response(
                    {"message": "You do not have permission to download this document",
                     "data": None,
                     "status": status.HTTP_403_FORBIDDEN},
                    status=status.HTTP_403_FORBIDDEN
                )

            DocumentAccessLog.objects.create(
                document=document,
                action="DOWNLOADED",
                action_by=request.user
            )

            return FileResponse(
                document.file.open("rb"),
                as_attachment=True,
                filename=document.file.name
            )

        except Exception as e:
            return Response(
                {"message": "Failed to download document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
# Document Share
# ===========================
class DocumentShareView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        try:
            document = get_object_or_404(UploadedDocument, id=document_id)
            email = request.data.get("email")

            if not email:
                return Response(
                    {"message": "Recipient email is required to share document",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            DocumentAccessLog.objects.create(
                document=document,
                action="SHARED",
                action_by=request.user,
                shared_with=email
            )

            return Response(
                {"message": f"Document shared successfully with {email}",
                 "data": None,
                 "status": status.HTTP_200_OK},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Failed to share document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
# Upload Signed Document
# ===========================
class DocumentUploadSignedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmployee]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, document_id):
        try:
            document = get_object_or_404(
                UploadedDocument,
                id=document_id,
                uploaded_by=request.user
            )

            if document.current_status != "APPROVED":
                return Response(
                    {"message": "Signed copy can only be uploaded after approval",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES.get("file")
            if not file:
                return Response(
                    {"message": "File is required for signed document upload",
                     "data": None,
                     "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            DocumentVersion.objects.create(
                document=document,
                file=file,
                version_type="SIGNED",
                uploaded_by=request.user
            )

            DocumentAudit.objects.create(
                document=document,
                action="SIGNED_UPLOADED",
                action_by=request.user
            )

            return Response(
                {"message": "Signed copy uploaded successfully",
                 "data": None,
                 "status": status.HTTP_200_OK},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Failed to upload signed document",
                 "data": str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CategoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            categories = Category.objects.filter(is_active=True)
            # Pagination
            paginator = CustomPagination()
            page = paginator.paginate_queryset(categories, request)
            serializer = CategorySerializer(page, many=True)
            data = serializer.data
            ab= paginator.get_paginated_response(data)
            return Response({"message": "Categories fetched successfully", "data": ab.data, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Failed to get categories", "data": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            if request.user.role != "super_admin" and request.user.role != "admin":
                return Response({"message": "You do not have permission to create categories", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            category = request.data.get("category")
            if not category:
                return Response({"message": "Category is required", "data": None, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            created_by = request.user
            category = Category.objects.create(category=category, created_by=created_by)
            return Response({"message": "Category created successfully", "data": category.id, "status": status.HTTP_201_CREATED}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": "Failed to create category", "data": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    def put(self, request, category_id):
        try:
            if request.user.role != "super_admin" and request.user.role != "admin":
                return Response({"message": "You do not have permission to update categories", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            category = get_object_or_404(Category, id=category_id, is_active=True)
            if not category:
                return Response({"message": "Category not found", "data": None, "status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            category.category = request.data.get("category")
            category.save()
            return Response({"message": "Category updated successfully", "data": category.id, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Failed to update category", "data": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    def delete(self, request, category_id):
        try:
            if request.user.role != "super_admin" and request.user.role != "admin":
                return Response({"message": "You do not have permission to delete categories", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            category = get_object_or_404(Category, id=category_id, is_active=True)
            if not category:
                return Response({"message": "Category not found", "data": None, "status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            category.is_active = False
            category.save()
            return Response({"message": "Category deleted successfully", "data": category.id, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Failed to delete category", "data": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectCodeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            project_codes = ProjectCode.objects.filter(is_active=True)
            # Pagination
            paginator = CustomPagination()
            page = paginator.paginate_queryset(project_codes, request)
            serializer = ProjectCodeSerializer(page, many=True)
            data = serializer.data
            ab= paginator.get_paginated_response(data)
            return Response({"message": "Project codes fetched successfully", "data": ab.data, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Failed to get project codes", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
            if request.user.role != "super_admin":
                return Response({"message": "You do not have permission to create project codes", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            project_code = request.data.get("project_code")
            if not project_code:
                return Response({"message": "Project code is required", "data": None, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            created_by = request.user
            project_code = ProjectCode.objects.create(project_code=project_code, created_by=created_by)
            return Response({"message": "Project code created successfully", "data": project_code.id, "status": status.HTTP_201_CREATED}, status=status.HTTP_201_CREATED)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Failed to create project code", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    def put(self, request, project_code_id):
        try:
            if request.user.role != "super_admin":
                return Response({"message": "You do not have permission to update project codes", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            project_code = get_object_or_404(ProjectCode, id=project_code_id, is_active=True)
            if not project_code:
                return Response({"message": "Project code not found", "data": None, "status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            project_code.project_code = request.data.get("project_code")
            project_code.save()
            return Response({"message": "Project code updated successfully", "data": project_code.id, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Failed to update project code", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    def delete(self, request, project_code_id):
        try:
            if request.user.role != "super_admin":
                return Response({"message": "You do not have permission to delete project codes", "data": None, "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            project_code = get_object_or_404(ProjectCode, id=project_code_id, is_active=True)
            if not project_code:
                return Response({"message": "Project code not found", "data": None, "status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            project_code.is_active = False
            project_code.save()
            return Response({"message": "Project code deleted successfully", "data": project_code.id, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Failed to delete project code", "data": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        