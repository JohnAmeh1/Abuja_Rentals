
import random
import string
import bcrypt
from django.utils import timezone


class OTPService:
    def __str__(self):
        return f"OTP {self.code} for {self.user.email}"

    @classmethod
    def generate_code(cls):
        code =  "".join(random.choices(string.digits, k=6))
        return bytes(code, "utf-8")

    @classmethod
    def create_otp(cls, user):
        otp_code = cls.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=10)  
        hash = bcrypt.hashpw(otp_code,bcrypt.gensalt()).__str__()
        otp, created = cls.objects.update_or_create(
            user=user,
            defaults={
                'code': hash[2:len(hash)-1],
                'expires_at': expires_at,
            }
        )
        otp.code = otp_code.__str__()[2:len(otp_code.__str__())-1]
        return otp


    def is_valid(self):
        return timezone.now() < self.expires_at

    def verify(self, code):
        if self.is_valid() and bcrypt.checkpw(bytes(code, "utf-8"), bytes(self.code, "utf-8")):
            self.delete()
            return True
        return False
