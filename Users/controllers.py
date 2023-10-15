import random
import string
import humanize
from datetime import timedelta

from django.core.cache import cache

from rest_framework.exceptions import ValidationError


class OTPManager:
    """
    Features
        - Send number for user channel (email / phone)
        - Confirm channel to is_valid by the code
    Description
        - its revolve around the user
    """

    LIFE_TIME = 10 * 60  # 10 minutes

    def __init__(self, user):
        self.user = user

    def __cache_code(self, code, otp_type):
        # 10 minutes
        cache_data = {'user': self.user.id, 'otp_type': otp_type}
        cache.set(f'otp_{code}', cache_data, self.LIFE_TIME)

    def __get_message(self, code):
        time = humanize.naturaldelta(timedelta(seconds=self.LIFE_TIME))
        return f'The OTP code is `{code}` and its valid for {time}.'

    def __get_code(self):
        return ''.join(random.choices(string.digits, k=6))

    def __send_by_email(self, message: str):
        self.user.send_email('OTP Code', message)

    def send(self, otp_type):
        code = self.__get_code()
        message = self.__get_message(code)

        self.__cache_code(code, otp_type)

        otp_method = {'email': self.__send_by_email}.get(otp_type)

        if otp_method is None:
            raise ValidationError({'error': 'Not valid `otp_type`.'})

        otp_method(message)
        return code

    def confirm(self, code):
        data = cache.get(f'otp_{code}')

        if data is None or data['user'] != self.user.id:
            raise ValidationError({'error': 'not valid code'})

        cache.delete(f'otp_{code}')
        if data['otp_type'] == 'email':
            self.user.email_verified = True
            self.user.save()
        else:
            raise ValidationError({'error': 'Not valid `otp_type`.'})

        return True
