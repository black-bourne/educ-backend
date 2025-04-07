# accounts/urls.py
from django.urls import path
from .views import login_view, verify_otp, reset_password_view, request_reset_view

urlpatterns = [
    path('auth/login', login_view, name='login'),
    path('auth/verify-otp', verify_otp, name='verify_token'),
    path('auth/reset', reset_password_view, name='password_reset'),
    path("auth/reset-email", request_reset_view, name="request_reset"),
]
