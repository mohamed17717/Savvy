from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from Users.controllers import OTPManager
from Users.serializers_mixins import GetUserByEmailMixin, ValidatePasswordMixin

User = get_user_model()


class AskForOTPCodeSerializer(GetUserByEmailMixin, serializers.Serializer):
    otp_type = serializers.ChoiceField(choices=['email'], required=True)

    def validate(self, attrs):
        attrs['user'] = self.get_user(attrs['email'])
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'groups', 'user_permissions', ]

    class Register(ValidatePasswordMixin, serializers.ModelSerializer):
        class Meta:
            model = User
            exclude = [
                'email_verified', 'is_staff', 'is_active', 'is_superuser']
            extra_kwargs = {
                'first_name': {'required': True},
                'last_name': {'required': True},
            }

        def create(self, validated_data):
            User = self.Meta.model
            validated_data.pop('confirm_password')

            return User.objects.create_user(**validated_data)

    class Update(serializers.ModelSerializer):
        class Meta:
            model = User
            exclude = [
                'username', 'email', 'email_verified',
                'is_staff', 'is_active', 'is_superuser',
            ]

    class Login(serializers.Serializer):
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

    class ResetPassword(GetUserByEmailMixin, ValidatePasswordMixin, serializers.Serializer):
        otp_code = serializers.CharField(required=True)

        def validate(self, attrs):
            super().validate(attrs)

            user = self.get_user(attrs['email'])
            if not OTPManager(user).confirm(attrs['otp_code']):
                raise ValidationError({'error': 'Not Valid OTP code.'})

            attrs['user'] = user
            return attrs
