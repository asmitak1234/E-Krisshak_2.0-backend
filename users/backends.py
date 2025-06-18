from django.contrib.auth.backends import BaseBackend
from users.models import CustomUser, StateAdminProfile, DistrictAdminProfile

class CodeOrEmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None

        # Check if it's a State Admin trying to log in using state_code
        try:
            state_admin = StateAdminProfile.objects.select_related('user').get(state_code=username)
            if state_admin.user.check_password(password):
                return state_admin.user
        except StateAdminProfile.DoesNotExist:
            pass

        # Check if it's a District Admin trying to log in using district_code
        try:
            district_admin = DistrictAdminProfile.objects.select_related('user').get(district_code=username)
            if district_admin.user.check_password(password):
                return district_admin.user
        except DistrictAdminProfile.DoesNotExist:
            pass

        # Otherwise, fall back to email
        try:
            user = CustomUser.objects.get(email=username)
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
