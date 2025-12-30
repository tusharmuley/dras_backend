from django.urls import path, re_path
from .views import *

# urlpatterns = [
#     path("login/", LoginView.as_view()),
#     path("create-admin/", CreateAdminView.as_view()),
#     path("create-employee/", CreateEmployeeView.as_view()),
#     path("employee_list/", MyEmployeesView.as_view()),
# ]

urlpatterns = [
    re_path(r"^login/?$", LoginView.as_view()),
    re_path(r"^auth_data/?$", AuthDataView.as_view()),
    re_path(r"^admin/?$", CreateAdminView.as_view()),
    re_path(r"^employee/?$", CreateEmployeeView.as_view()),
    re_path(r"^profile/?$", UserProfileDetailView.as_view()),
    # re_path(r"^employee_list/?$", MyEmployeesView.as_view()),

    # RESET PASSWORD URLS
    re_path(r"^forgot-password/?$", ForgotPasswordView.as_view()),
    re_path(r"^verify-otp/?$", VerifyOTPView.as_view()),
    re_path(r"^reset-password/?$", ResetPasswordView.as_view()),
    re_path(r"^change-password/?$", ChangePasswordView.as_view()),
]

