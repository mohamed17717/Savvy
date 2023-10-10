from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import serializers

from Users.controllers import OTPManager


class LoginAuthSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = authenticate(request, **attrs)

        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise ValidationError({'error': msg}, code='authorization')

        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True)

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    def get_user(self, email):
        request = self.context.get('request')
        user = request.user

        if user.is_authenticated:
            pass
        elif email:
            User = get_user_model()
            user = User.objects.filter(email=email).first()
            if user is None:
                raise PermissionDenied('Not valid user data.')
        else:
            raise PermissionDenied('Not valid user data.')

        return user

    def validate(self, attrs):
        user = self.get_user(attrs['email'])

        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                "Password and confirm password do not match")

        if not OTPManager(user).confirm(attrs['otp_code']):
            raise ValidationError({'error': 'Not Valid OTP code.'})

        attrs['user'] = user

        return attrs
