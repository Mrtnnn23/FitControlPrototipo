from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class CorreoBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        try:
            user = User.objects.get(email__iexact=username.strip())
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
