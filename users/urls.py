from django.urls import path
from .views import RegisterView, VerifyOTPView, ForgotPasswordView, ResetPasswordView, FilteredKrisshakListView,KrisshakProfileDetailUpdateView,FilteredBhooswamiListView,BhooswamiDetailView,RoleBasedLoginView, LogoutView , UpdateProfileView, rate_user, toggle_favorite, get_favorites, DistrictsByStateView
from rest_framework_simplejwt.views import TokenRefreshView ,TokenObtainPairView

urlpatterns = [
    # Registration & Security
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # Login
    path('login/', RoleBasedLoginView.as_view(), name='role-based-login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Logout
    path('logout/', LogoutView.as_view(), name='logout'),

    # User Profile, Rating , Favorites and State wise Districts
    path('user/profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('rate-user/', rate_user, name='rate-user'),
    path("favorites/toggle/", toggle_favorite, name="toggle_favorite"),
    path("favorites/", get_favorites, name="get_favorites"),
    path("api/districts/", DistrictsByStateView.as_view(), name="districts-by-state"),

    # Krisshak Views
    path('krisshaks/', FilteredKrisshakListView.as_view(), name='krisshak-list'),
    path('krisshaks/<int:pk>/', KrisshakProfileDetailUpdateView.as_view(), name='krisshak-detail'),
    path('krisshak/profile/', KrisshakProfileDetailUpdateView.as_view(), name='krisshak-profile-update'),

    # Bhooswami Views
    path('bhooswamis/', FilteredBhooswamiListView.as_view(), name='bhooswami-list'),
    path('bhooswamis/<int:pk>/', BhooswamiDetailView.as_view(), name='bhooswami-detail'),
]