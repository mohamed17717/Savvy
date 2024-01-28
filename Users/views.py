from django.contrib.auth import login
from django.conf import settings

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_204_NO_CONTENT

from knox.views import LoginView as KnoxLoginView

from Users import serializers, controllers


def setup_serializer(view, request, **kwargs):
    serializer = view.serializer_class(
        data=request.data, context={'request': request}, **kwargs
    )
    serializer.is_valid(raise_exception=True)
    return serializer


class LoginAPI(KnoxLoginView):
    authentication_classes = []
    permission_classes = [AllowAny]
    request_serializer = serializers.UserSerializer.Login

    def post(self, request):
        serializer = setup_serializer(self, request)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginAPI, self).post(request, format=None)


class ResetPasswordAPI(GenericAPIView):
    permission_classes = []
    serializer_class = serializers.UserSerializer.ResetPassword

    def post(self, request):
        serializer = setup_serializer(self, request)

        user = serializer.validated_data['user']
        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return Response(status=HTTP_204_NO_CONTENT)


class AskForOTPCodeAPI(GenericAPIView):
    permission_classes = []
    serializer_class = serializers.AskForOTPCodeSerializer

    def post(self, request):
        serializer = setup_serializer(self, request)

        user = serializer.validated_data['user']
        otp_type = serializer.validated_data['otp_type']

        otp_code = controllers.OTPManager(user).send(otp_type)
        if settings.DEBUG:
            return Response({'otp_code': otp_code})

        return Response(status=HTTP_204_NO_CONTENT)


class RegisterAPI(GenericAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.UserSerializer.Register

    def post(self, request):
        serializer = setup_serializer(self, request)
        user = serializer.save()

        return Response(serializers.UserSerializer(user).data)


class UserProfileAPI(GenericAPIView):
    serializer_class = serializers.UserSerializer

    def get(self, request):
        user = request.user
        return Response(serializers.UserSerializer(user).data)


class UpdateUserProfileAPI(GenericAPIView):
    serializer_class = serializers.UserSerializer.Update

    def post(self, request):
        serializer = setup_serializer(self, request, instance=request.user)
        user = serializer.save()
        return Response(serializers.UserSerializer(user).data)
