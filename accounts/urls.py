from django.urls import path
from .views import SignupView, LoginView, TokenValidationView, LogoutView, RefreshTokenView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('validate-token/', TokenValidationView.as_view(), name='token-validation'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
]