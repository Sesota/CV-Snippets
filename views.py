import uuid
import secrets

from datetime import datetime, timezone, timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import User, Device
from .validators import cleaned_email_to_insert, is_valid_password

from src.exceptions import MessagedException


class Signup(APIView):
    """
    User Signup
    - Input: POST:{"email", "password", "mac", "model", "platform"}
    - Output: POST:{user details, "detail"}
    - Next step: /Auth/signup/confirm/
    """

    def post(self, request):
        cleaned_email = cleaned_email_to_insert(request.data["email"])
        is_valid_password(request.data["password"])

        user = User.objects.create_user(
            email=cleaned_email,
            password=request.data["password"],
            confirm_code=secrets.randbits(16),
        )
        device = Device.objects.create(
            mac=request.data["mac"],
            model=request.data["model"],
            platform=request.data["platform"],
            user=user,
        )
        # device.save()
        try:
            user.email_user(
                "Daddy Check -- Email Confirmation Code",
                "Your confirmation code: " + str(user.confirm_code),
            )
        except Exception:
            # There's a problem with email service
            raise MessagedException()

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "date_joined": user.date_joined,
                "mac": device.mac,
                "model": device.model,
                "platform": device.platform,
                "detail": "inf_user_signedup",
            },
            status=status.HTTP_201_CREATED,
        )


class SignupConfirm(APIView):
    """
    Confirm Email
    - Input: POST:{"user_id", "confirm_code"}
    - Output: POST:{"detail"}
    - Next Step: Auth/login/
    """

    def post(self, request):
        user = User.objects.get(id=request.data["user_id"])
        if user.is_active:
            raise MessagedException(message="err_user_already_activated")
        if user.confirm_code == -1:
            raise MessagedException(message="err_user_anonymous")
        if user.confirm_code != int(request.data["confirm_code"]):
            raise MessagedException(message="err_code_invalid")
        if (datetime.now(timezone.utc) - user.date_joined) > timedelta(minutes=30):
            user.delete()
            raise MessagedException(message="err_code_expired")

        user.is_active = True
        user.save()

        return Response(
            {
                "detail": "inf_user_activated",
            },
            status=status.HTTP_200_OK,
        )


class SignupAnonymous(APIView):
    """
    Anonymous User Signup
    - Input: POST:{"mac", "model", "platform"}
    - Output: POST:{user's details, "token", "detail"}
    - Next step: varied
    """

    def post(self, request):
        email = f"anon_{str(uuid.uuid4()).replace('-', '')}@daddycheck.com"
        user = User.objects.create(
            email=email,
            password=str(uuid.uuid5(settings.UUID_ROOT, email)),
            confirm_code=-1,
            is_active=True,
        )
        device = Device.objects.create(
            mac=request.data["mac"],
            model=request.data["model"],
            platform=request.data["platform"],
            user=user,
        )
        # device.save()

        token, _created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "id": user.id,
                "email": user.email,
                "date_joined": user.date_joined,
                "mac": device.mac,
                "model": device.model,
                "platform": device.platform,
                "detail": "inf_anon_loggedin",
            },
            status=status.HTTP_201_CREATED,
        )


class Login(APIView):
    """
    User Login
    - Input: POST:{"email", "password", "mac", "model", "platform"}
    - Output: POST:{device details, "token", "detail"}
    - Next Step: varied
    """

    def post(self, request):
        try:
            user = User.objects.get(email=request.data["email"])
        except User.DoesNotExist:
            raise MessagedException(message="err_user_notfound")

        if not check_password(request.data["password"], user.password):
            raise MessagedException(message="err_password_incorrect")

        device = self._update_device(user, request)

        token, _created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "mac": device.mac,
                "model": device.model,
                "platform": device.platform,
                "detail": "inf_user_loggedin",
            },
            status=status.HTTP_200_OK,
        )

    def _update_device(self, user, request):
        device = Device.objects.filter(user=user, mac=request.data["mac"]).first()
        if device:
            return device

        new_device = Device.objects.create(
            user=user,
            mac=request.data["mac"],
            model=request.data["model"],
            platform=request.data["platform"],
        )
        new_device.save()
        return new_device


class Logout(APIView):
    """
    User Logout
    - Input: POST:{}
    - Output: POST:{"detail"}
    - Next Step: varied
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        token = Token.objects.get(key=request.user.auth_token.key)
        token.delete()
        return Response(
            {"detail": "inf_user_loggedout"},
            status=status.HTTP_200_OK,
        )


class Profile(APIView):
    """
    User profile
    - Input: GET:{}, PUT:{"email", "first_name", "last_name", "birth_date", "phone"}
    - Output: GET:{user's profile}, PUT:{user's profile, "detail"}
    - Next Step: varied
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.confirm_code == -1:
            raise MessagedException(message="err_user_anonymous")

        return Response(
            {
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "birth_date": request.user.birth_date,
                "phone": request.user.phone,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        if request.user.confirm_code == -1:
            raise MessagedException(message="err_user_anonymous")

        user = User.objects.get(pk=request.user.pk)

        self._change_email(user, request.data["email"])
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        user.birth_date = request.data["birth_date"]
        user.phone = request.data["phone"]
        user.save()
        return Response(
            {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "birth_date": user.birth_date,
                "phone": user.phone,
                "detail": "inf_profile_updated",
            },
            status=status.HTTP_200_OK,
        )

    def _change_email(self, user, email):
        if user.email == email:
            return
        user.email += "@temp"
        user.save()
        cleaned_email = cleaned_email_to_insert(email)
        user.email = cleaned_email
        user.save()
        return


class PasswordChange(APIView):
    """
    Change User's Password
    - Input: POST:{"password", "new_password"}
    - Output: POST:{"detail"}
    - Next Step: varied
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if request.user.confirm_code == -1:
            raise MessagedException(message="err_user_anonymous")
        if not check_password(request.data["password"], request.user.password):
            raise MessagedException(message="err_password_incorrect")

        is_valid_password(request.data["new_password"])
        user = User.objects.get(email=request.user.email)
        user.password = make_password(request.data["new_password"])
        user.save()
        return Response(
            {"detail": "inf_password_changed"},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequest(APIView):
    """
    Request a Password Reset
    - Input: POST:{"email"}
    - Output: POST:{"detail"}
    - Next Step: /Auth/password/reset/confirm/
    """

    # NOTE: User's "confirm_code" field has been used for password
    #   reset's code. This choice makes a few flaws in the system but
    #   is more space efficient
    #   Flaw:
    #   1- A user who has recently reset his password can use the same
    #       reset code to bypass password_reset_request and use it directly
    #       in password_reset_confirm API and reset the password again
    #       POSSIBLE ABUSE: Not registering the password request date in the
    #                       database and reset the password many times until
    #                       the code expires
    def post(self, request):
        user = User.objects.get(email=request.data["email"])
        if not user.is_active:
            raise MessagedException(message="err_user_not_activated")
        if user.confirm_code == -1:
            raise MessagedException(message="err_user_anonymous")

        user.confirm_code = secrets.randbits(16)
        user.pass_reset_req_date = datetime.now(timezone.utc)
        user.save()
        try:
            user.email_user(
                "Daddy Check -- Password Reset Code",
                "Your code: " + str(user.confirm_code),
            )
        except Exception:
            # There's a problem with email service
            raise MessagedException(message="err_service_unavailable")

        return Response(
            {"detail": "inf_passwordresetrequest_sent"},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirm(APIView):
    """
    Confirm a Password Reset Request and Change Password
    - Input: POST:{"email", "confirm_code", "new_password"}
    - Output: POST:{"detail"}
    - Next Step: /Auth/login/
    """

    def post(self, request):
        user = User.objects.get(email=request.data["email"])
        if user.confirm_code != int(request.data["confirm_code"]):
            raise MessagedException(message="err_code_invalid")
        if (datetime.now(timezone.utc) - user.pass_reset_req_date) > timedelta(
            minutes=30
        ):
            raise MessagedException(message="err_code_expired")
        is_valid_password(request.data["new_password"])
        user.password = make_password(request.data["new_password"])
        user.save()
        return Response(
            {"detail": "inf_password_changed"},
            status=status.HTTP_200_OK,
        )
