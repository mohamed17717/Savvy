from django.conf import settings
from django.contrib.auth import login
from knox import views as knox_views
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from common.utils.drf.viewsets import RUViewSet
from realtime.common import jwt_utils
from Users import controllers, serializers


def setup_serializer(view, request, **kwargs):
    serializer = view.serializer_class(
        data=request.data, context={"request": request}, **kwargs
    )
    serializer.is_valid(raise_exception=True)
    return serializer


class LoginAPI(knox_views.LoginView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = serializers.UserSerializer.Login

    def post(self, request):
        serializer = setup_serializer(self, request)
        user = serializer.validated_data["user"]

        login(request, user)
        return super().post(request, format=None)


class ResetPasswordAPI(knox_views.LoginView):
    permission_classes = []
    serializer_class = serializers.UserSerializer.ResetPassword

    def post(self, request):
        serializer = setup_serializer(self, request)

        user = serializer.validated_data["user"]
        password = serializer.validated_data["password"]
        user.set_password(password)
        user.save()

        login(request, user)
        return super().post(request, format=None)


class AskForOTPCodeAPI(GenericAPIView):
    permission_classes = []
    serializer_class = serializers.AskForOTPCodeSerializer

    def post(self, request):
        serializer = setup_serializer(self, request)

        user = serializer.validated_data["user"]
        otp_type = serializer.validated_data["otp_type"]

        otp_code = controllers.OTPManager(user).send(otp_type)
        if settings.DEBUG:
            return Response({"otp_code": otp_code})

        return Response(status=HTTP_204_NO_CONTENT)


class RegisterAPI(knox_views.LoginView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = serializers.UserSerializer.Register

    def post(self, request):
        serializer = setup_serializer(self, request)
        user = serializer.save()

        login(request, user)
        return super().post(request, format=None)


class UserProfileAPI(RUViewSet):
    def get_serializer_class(self):
        return (
            serializers.UserSerializer.Update
            if self.action == "update"
            else serializers.UserSerializer
        )

    def get_object(self):
        return self.request.user


class LogoutAPI(knox_views.LogoutView):
    def post(self, request, format=None):
        response = super().post(request, format)
        jwt_utils.JwtManager.remove_cookie(response)

        return response

    def get(self, request, format=None):
        return self.post(request, format)


class LogoutAllAPI(knox_views.LogoutAllView):
    def post(self, request, format=None):
        response = super().post(request, format)
        jwt_utils.JwtManager.remove_cookie(response)

        return response

    def get(self, request, format=None):
        return self.post(request, format)
