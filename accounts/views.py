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
from accounts.serializers import EmployeeSerializer


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

            return Response({
                "access": str(token.access_token),
                "refresh": str(token),

                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,

                "employee_id": getattr(user, "employee_id", None),
                "mobile": getattr(user, "mobile", None),

                "created_by": user.created_by.id if user.created_by else None,
                "created_datetime": user.created_datetime.isoformat() if user.created_datetime else None,
                "updated_datetime": user.updated_datetime.isoformat() if user.updated_datetime else None,
                "status":status.HTTP_200_OK,
                "message": "Logged in successfully"

            }, status=status.HTTP_200_OK)

        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message":"something went wrong", "error": str(e),"line_number": line_number, "status":status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AuthDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user  # ✅ authenticated user

            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,

                "employee_id": getattr(user, "employee_id", None),
                "mobile": getattr(user, "mobile", None),

                "created_by": user.created_by.id if user.created_by else None,
                "created_datetime": user.created_datetime.isoformat() if user.created_datetime else None,
                "updated_datetime": user.updated_datetime.isoformat() if user.updated_datetime else None,

                "message": "Auth data fetched successfully",
                "status":status.HTTP_200_OK

            }, status=status.HTTP_200_OK)

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
            queryset = User.objects.filter(role="admin")
            serializer = EmployeeSerializer(queryset, many=True)
            return Response({"admins": serializer.data,"message": "Admins fetched successfully", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
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
   

class CreateEmployeeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.user.role != "admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)
            queryset = User.objects.filter(role="employee",created_by=request.user)
            serializer = EmployeeSerializer(queryset, many=True)
            return Response({"employees": serializer.data,"message": "Employees fetched successfully", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            if request.user.role != "admin":
                return Response({"message": "Permission denied", "status":status.HTTP_403_FORBIDDEN}, status.HTTP_403_FORBIDDEN)

            data = request.data
            username = data.get("username", "")
            employee_id = data.get("employee_id", "")
            email = data.get("email", "")
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            mobile = data.get("mobile", "")
            password = data.get("password", "")
            
            if not username or not employee_id or not email or not first_name or not last_name or not mobile or not password:
                return Response({"message": "All fields are required", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(username=data["username"]).exists():
                return Response({"message": "Username already exists", "status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(employee_id=data["employee_id"]).exists():
                return Response({"message": "Employee ID already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=data["email"]).exists():
                return Response({"message": "Email already exists","status":status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
            
            try:
                with transaction.atomic():
                    User.objects.create_user(
                        username=data["username"],
                        password=data["password"],
                        first_name=data.get("first_name", ""),
                        last_name=data.get("last_name", ""),
                        email=data.get("email", ""),
                        role="employee",
                        mobile=data.get("mobile", ""),
                        employee_id=data.get("employee_id", ""),
                        created_by=request.user
                    )
                    return Response({"message": "Employee created successfully", "status":status.HTTP_201_CREATED}, status.HTTP_201_CREATED)
            except Exception as e:
                line_number = sys.exc_info()[2].tb_lineno
                return Response({"message": "Employee creation failed", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )

        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e),"line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR )


class MyEmployeesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role == "super_admin":
                queryset = User.objects.filter(role="admin")
            elif request.user.role == "admin":
                queryset = User.objects.filter(role="employee",created_by=request.user)
            else:
                return Response({"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            serializer = EmployeeSerializer(queryset, many=True)

            return Response({"employees": serializer.data,"message": "Employees fetched successfully", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)

        except Exception as e:
            line_number = sys.exc_info()[2].tb_lineno
            return Response({"message": "Something went wrong", "error": str(e), "line_number": line_number },status=status.HTTP_500_INTERNAL_SERVER_ERROR)