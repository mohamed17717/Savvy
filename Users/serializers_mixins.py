from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

User = get_user_model()


class ValidatePasswordMixin(serializers.Serializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise ValidationError("Password and confirm password do not match")

        return attrs


class GetUserByEmailMixin(serializers.Serializer):
    email = serializers.CharField(required=True)

    def get_user(self, email):
        request = self.context.get("request")
        user = request.user

        if not user.is_authenticated:
            user = User.objects.filter(email=email).first()
            if user is None:
                raise PermissionDenied("Not valid user data.")

        return user
