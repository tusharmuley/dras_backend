from django.shortcuts import render
# Create your views here.
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from rest_framework import status
import sys
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from accounts.serializers import EmployeeSerializer, AuthDataSerializer
import random
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from documents.utils import CustomPagination
from django.db.models import Q

from .tasks import send_otp_email_task

class LoginView(APIView):
    authentication_classes = []   # 🔥 disable JWT here
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                return Response({"message": "username and password are required","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

            # username OR email login
            user_obj = (
                User.objects.filter(username=username).first()
                or User.objects.filter(email=username).first()
            )

            if not user_obj:
                return Response({"message": "Invalid credentials","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

            user = authenticate(username=user_obj.username, password=password )

            if not user:
                return Response({"message": "Invalid credentials","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)

            token = RefreshToken.for_user(user)
            serializer = AuthDataSerializer(user)
            
            response_data = serializer.data
            response_data["access"] = str(token.access_token)
            response_data["refresh"] = str(token)
            response_data["message"] = "Logged in successfully"
            response_data["status"] = status.HTTP_200_OK

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message":"something went wrong", "error": str(e),"line_number": line_number, "status":status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AuthDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user  # ✅ authenticated user
            serializer = AuthDataSerializer(user)
            
            response_data = serializer.data
            response_data["message"] = "Auth data fetched successfully"
            response_data["status"] = status.HTTP_200_OK

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )



class CreateAdminView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.user.role != "super_admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            queryset = User.objects.filter(Q(role="admin") | Q(role="employee"), is_active=True).order_by("-created_datetime")
            # Pagination
            paginator = CustomPagination()
            page = paginator.paginate_queryset(queryset, request)
            serializer = EmployeeSerializer(page, many=True)
            data = serializer.data
            ab= paginator.get_paginated_response(data)
            serializer = EmployeeSerializer(queryset, many=True)
            return Response({"data": ab.data,"message": "Admins fetched successfully", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            if request.user.role != "super_admin":
                return Response({"message": "Permission denied", "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            data = request.data
            email = data.get("email", "")
            employee_id = data.get("employee_id", "")
            username = data.get("username", "")
            password = data.get("password", "")
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            
            if not email or not employee_id or not username or not password or not first_name:
                return Response({"message": "All fields are required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(username=username).exists():
                return Response({"message": "Username already exists", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(employee_id=employee_id).exists():
                return Response({"message": "Employee ID already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=email).exists():
                return Response({"message": "Email already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,  
                        last_name=last_name,
                        email=email,
                        role="admin",
                        created_by=request.user
                    )
                    return Response({"message": "Admin created successfully", "status":status.HTTP_201_CREATED}, status.HTTP_201_CREATED)
            except Exception as e:
                line_number = sys.exc_info()[2].tb_lineno
                return Response({"message": "Admin creation failed", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )
        
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )
   
    def put(self, request):
        try:
            if request.user.role != "super_admin" and request.user.role != "admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            
            data = request.data
            user_id = data.get("user_id", None)
            
            if not user_id:
                return Response({"message": "User ID is required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "status":status.HTTP_404_NOT_FOUND}, status.HTTP_404_NOT_FOUND)
            
            # Validation: Admin can only update their own profile
            if request.user.role == "admin" and user_id != request.user.id:
                return Response({"message": "Permission denied. Admin can only update their own profile.", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            
            email = data.get("email", None)
            employee_id = data.get("employee_id", None)
            username = data.get("username", None)
            password = data.get("password", None)
            
            if request.user.role == "super_admin" and user.role == "employee" and data.get("role", None) != "admin":
                created_by_id = data.get("admin_id", None)
                try:
                    created_by = User.objects.get(id=created_by_id , is_active=True, role="admin")
                except User.DoesNotExist:
                    return Response({"message": "Admin not found or is not active", "status":status.HTTP_404_NOT_FOUND}, status.HTTP_404_NOT_FOUND)
                data["created_by_id"] = created_by.id

            if password:
                user.set_password(password)
                user.save()
            
            if username and User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({"message": "Username already exists", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if employee_id and User.objects.filter(employee_id=employee_id).exclude(id=user.id).exists():
                return Response({"message": "Employee ID already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if email and User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({"message": "Email already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            serializer = EmployeeSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Admin updated successfully","user": serializer.data, "status":status.HTTP_200_OK}, status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid data","serializer_errors": serializer.errors, "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno 
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request):
        try:
            if request.user.role != "super_admin" and request.user.role != "admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            user_id = request.data.get("user_id", None)
            if not user_id:
                return Response({"message": "User ID is required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if request.user.role == "admin" and request.user.id != user_id:
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "status":status.HTTP_404_NOT_FOUND}, status.HTTP_404_NOT_FOUND)
            
            user.is_active = False
            user.save()
            return Response({"message": "Admin deleted successfully", "status":status.HTTP_200_OK}, status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateEmployeeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.user.role != "admin" and request.user.role != "super_admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            
            if request.user.role == "super_admin":
                queryset = User.objects.filter(role="employee", is_active=True).order_by("-created_datetime")
            else:
                queryset = User.objects.filter(role="employee",created_by=request.user, is_active=True).order_by("-created_datetime")
            # Pagination
            paginator = CustomPagination()
            page = paginator.paginate_queryset(queryset, request)
            serializer = EmployeeSerializer(page, many=True)
            data = serializer.data
            ab= paginator.get_paginated_response(data)
            return Response({"data": ab.data,"message": "Employees fetched successfully", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            if request.user.role != "admin" and request.user.role != "super_admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)

            data = request.data
            username = data.get("username", "")
            employee_id = data.get("employee_id", "")
            email = data.get("email", "")
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            middle_name = data.get("middle_name", None)
            mobile = data.get("mobile", "")
            password = data.get("password", "")
            blood_group = data.get("blood_group", None)
            date_of_birth = data.get("date_of_birth", None)
            date_of_joining = data.get("date_of_joining", None)
            gender = data.get("gender", None)
            
            if not username or not employee_id or not email or not first_name or not password:
                return Response({"message": "All fields are required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(username=username).exists():
                return Response({"message": "Username already exists", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(employee_id=employee_id).exists():
                return Response({"message": "Employee ID already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=email).exists():
                return Response({"message": "Email already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            if request.user.role == "super_admin":
                created_by_id = data.get("admin_id", None)
                if not created_by_id:
                    return Response({"message": "admin_id is required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
                try:
                    created_by = User.objects.get(id=created_by_id , is_active=True, role="admin")
                except User.DoesNotExist:
                    return Response({"message": "Approval not found or is not active", "status":status.HTTP_404_NOT_FOUND}, status.HTTP_404_NOT_FOUND)
            else:
                created_by = request.user
            try:
                with transaction.atomic():
                    User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        middle_name=middle_name,
                        last_name=last_name,
                        email=email,
                        role="employee",
                        mobile=mobile,
                        employee_id=employee_id,
                        blood_group=blood_group,
                        date_of_birth=date_of_birth,
                        date_of_joining=date_of_joining,
                        gender=gender,
                        created_by=created_by
                    )
                    return Response({"message": "Employee created successfully", "status":status.HTTP_201_CREATED}, status.HTTP_201_CREATED)
            except Exception as e:
                line_number = sys.exc_info()[2].tb_lineno
                return Response({"message": "Employee creation failed", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

    def put(self, request):
        try:
            if request.user.role != "admin" and request.user.role != "employee":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            
            data = request.data
            user_id = data.get("user_id", None)
            username = data.get("username", None)
            employee_id = data.get("employee_id", None)
            email = data.get("email", None)
            first_name = data.get("first_name", None)
            last_name = data.get("last_name", None)
            mobile = data.get("mobile", None)
            password = data.get("password", None)
            
            if not user_id:
                return Response({"message": "User ID is required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            # Validation: Employee can only update their own profile
            if request.user.role == "employee" and user_id != request.user.id:
                return Response({"message": "Permission denied. Employees can only update their own profile.", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "status":status.HTTP_404_NOT_FOUND}, status.HTTP_404_NOT_FOUND)
            
            # Validation: Admin can update their own profile or employees they created
            if request.user.role == "admin":
                if user_id != request.user.id and user.created_by != request.user:
                    return Response({"message": "Permission denied. Admin can only update their own profile or employees they created.", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)

            if username and User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({"message": "Username already exists", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if employee_id and User.objects.filter(employee_id=employee_id).exclude(id=user.id).exists():
                return Response({"message": "Employee ID already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if email and User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({"message": "Email already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            if password:
                user.set_password(password)
            serializer = EmployeeSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Employee updated successfully","user": serializer.data, "status":status.HTTP_200_OK}, status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid data","serializer_errors": serializer.errors, "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )
    
    def delete(self, request):
        
        try:
            print("request.user.role", request.user.role)
            print("request.user.id", request.user.id)
            # Only super_admin and admin can delete employees
            if request.user.role != "super_admin" and request.user.role != "admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get("user_id", None)
            if not user_id:
                return Response({"message": "User ID is required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            try:
                user = User.objects.get(id=user_id, created_by=request.user.id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "status":status.HTTP_404_NOT_FOUND}, status.HTTP_404_NOT_FOUND)
            
            user.is_active = False
            user.save()
            return Response({"message": "Employee deleted successfully", "status":status.HTTP_200_OK}, status.HTTP_200_OK)
        
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        


User = get_user_model()

# Temporary OTP storage (use DB/Redis in production)
OTP_STORAGE = {}  # {email: {"otp": 123456, "expiry": datetime}}

# 🔥 All views allow unauthenticated access
class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"message": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
            otp = random.randint(100000, 999999)
            expiry = timezone.now() + datetime.timedelta(minutes=10)
            OTP_STORAGE[email] = {"otp": otp, "expiry": expiry}

            # Send OTP asynchronously via Celery
            send_otp_email_task.delay(email, otp, user.first_name)

            return Response({"message": "OTP sent to email (check your inbox)", "status": status.HTTP_200_OK})
        
        except Exception as e:
            return Response({"message": "Something went wrong", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not email or not otp:
            return Response({"message": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        record = OTP_STORAGE.get(email)
        if not record or str(record["otp"]) != str(otp):
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.now() > record["expiry"]:
            return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "OTP verified", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    authentication_classes = []  
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not email or not otp or not password or not confirm_password:
            return Response(
                {"message": "Email, OTP, password, and confirm_password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != confirm_password:
            return Response(
                {"message": "Password and confirm_password do not match"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = OTP_STORAGE.get(email)
        if not record or str(record["otp"]) != str(otp):
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > record["expiry"]:
            return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Set new password
        user.set_password(password)
        user.save()

        # Remove OTP after successful reset
        OTP_STORAGE.pop(email, None)

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
    
    
class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            if not user:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            old_password = request.data.get("old_password")
            new_password = request.data.get("new_password")
            confirm_password = request.data.get("confirm_password")
            if not old_password or not new_password or not confirm_password:
                return Response({"message": "All fields are required", "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            if new_password != confirm_password:
                return Response({"message": "New password and confirm password do not match", "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            if not old_password or not new_password:
                return Response({"message": "Old password and new password are required", "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(old_password):
                return Response({"message": "Old password is incorrect", "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        
class UserProfileDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            user = request.user
            data = dict(request.data)  # Create a mutable copy
            user_id = data.get("id", None)
            
            # Validate user_id is provided and matches authenticated user
            if not user_id:
                return Response({"message": "User ID is required", "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            
            # Ensure user can only update their own profile
            if str(user_id) != str(user.id):
                return Response({"message": "Permission denied. You can only update your own profile.", "status": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            
            # Remove read-only fields that should not be updated via profile update
            read_only_fields = ["role", "is_active", "created_by", "id", "password", "created_datetime", "updated_datetime"]
            for field in read_only_fields:
                data.pop(field, None)
            
            # Filter out empty/null values - don't update fields with empty strings, None, or null
            data = {k: v for k, v in data.items() if v not in (None, "", "null", "NULL") and v is not None}
            
            username = data.get("username", None)
            email = data.get("email", None)
            employee_id = data.get("employee_id", None)
            if username and User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({"message": "Username already exists", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if employee_id and User.objects.filter(employee_id=employee_id).exclude(id=user.id).exists():
                return Response({"message": "Employee ID already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if email and User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({"message": "Email already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            # Update user profile using serializer
            serializer = AuthDataSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "User profile updated successfully", "data": serializer.data, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid data", "errors": serializer.errors, "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number, "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)