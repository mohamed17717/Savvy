from django.contrib.auth import login
from django.conf import settings

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_204_NO_CONTENT

from knox.views import LoginView as KnoxLoginView

from Users import serializers, controllers


class LoginView(KnoxLoginView):
    authentication_classes = []
    permission_classes = [AllowAny]
    request_serializer = serializers.LoginAuthSerializer

    def post(self, request, format=None):
        serializer = self.request_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        login(request, user)
        return super(LoginView, self).post(request, format=None)


class ResetPasswordView(GenericAPIView):
    permission_classes = []
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        password = serializer.validated_data['password']

        user.set_password(password)
        user.save()

        return Response({'message': 'OK'}, status=HTTP_204_NO_CONTENT)


class AskForOTPCodeAPI(GenericAPIView):
    permission_classes = []
    serializer_class = serializers.AskForOTPCodeSerializer

    def post(self, request):
        s = self.serializer_class(
            data=request.data, context={'request': request})
        s.is_valid(raise_exception=True)

        user = s.validated_data['user']
        otp_type = s.validated_data['otp_type']

        otp_code = controllers.OTPManager(user).send(otp_type)
        if settings.DEBUG:
            return Response({'otp_code': otp_code})

        return Response(status=HTTP_204_NO_CONTENT)


class RegisterView(GenericAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.UserRegisterSerializer

    def post(self, request):
        user_serializer = self.serializer_class(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        return Response(serializers.UserSerializer(user).data)
