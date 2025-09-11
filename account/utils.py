from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings

def make_password_setup_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base = settings.FRONTEND_URL.rstrip('/')
    return f"{base}/set-password?uid={uid}&token={token}"

def decode_uid(uidb64):
    return force_str(urlsafe_base64_decode(uidb64))
