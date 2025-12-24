from django.urls import path, re_path
from .views import *


urlpatterns = [
    re_path(r"^login/?$", LoginView.as_view()),
    re_path(r"^auth_data/?$", AuthDataView.as_view()),
    re_path(r"^admin/?$", CreateAdminView.as_view()),
    re_path(r"^employee/?$", CreateEmployeeView.as_view()),
    # re_path(r"^employee_list/?$", MyEmployeesView.as_view()),
]

