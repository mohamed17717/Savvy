from django.contrib.auth import login

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_204_NO_CONTENT

from knox.views import LoginView as KnoxLoginView

from Users import serializers


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
