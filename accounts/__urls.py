# from django.urls import path
# from accounts.views.company_views import (
#     MyCompaniesView,
#     CompanyDetailView,
#     CompanyCreateView,
#     SetActiveCompanyView,
# )
# from accounts.views.auth_view import RegisterView, LoginView
# from rest_framework_simplejwt.views import TokenRefreshView

# urlpatterns = [
#     path("my-companies/", MyCompaniesView.as_view(), name="my-companies"),
#     path("companies/", CompanyCreateView.as_view(), name="company-create"),
#     path("companies/<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
#     path("users/active-company/", SetActiveCompanyView.as_view(), name="set_active_company"),
    
#     path("auth/register/", RegisterView.as_view(), name="register"),
#     path("auth/login/", LoginView.as_view(), name="login"),
#     path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
# ]