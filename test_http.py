import io
import secrets

# from datetime import datetime, timezone, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.parsers import JSONParser

from ..serializers import MessageLevelSerializer, MessageSerializer
from ..models import Device

_PASSW0RDS = ["passw0rd1", "passw0rd2"]
_MODELS = ["testmodel1"]
_PLATFORMS = ["testOS1"]
_MACS = ["00:1B:44:11:3A:B7"]


class AuthenticationTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Populate Messages table from saved json file if it's unpopulated.
        # TODO It didn't work. had to add `--parallel 2` to `python manage.py test` to fix

        with open(
            settings.CDN_LOCAL_DIR + "messagelevels.json",
            "rb",
        ) as f:
            content = f.read()

        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serialized = MessageLevelSerializer(data=data, many=True)
        serialized.is_valid()
        serialized.save()

        with open(settings.CDN_LOCAL_DIR + "messages.json", "rb") as f:
            content = f.read()

        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serialized = MessageSerializer(data=data, many=True)
        serialized.is_valid()
        serialized.save()

        return super().setUpTestData()

    def test_user_signup(self):
        response = self.client.post(
            reverse("signup"),
            data={
                "email": "user@example.com",
                "password": _PASSW0RDS[0],
                "mac": _MACS[0],
                "model": _MODELS[0],
                "platform": _PLATFORMS[0],
            },
        )
        user = get_user_model().objects.last()
        device = Device.objects.get(user=user)
        msg_id = "inf_user_signedup"
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(user.id, response.data["id"])
        self.assertEqual(user.email, response.data["email"])
        self.assertEqual(
            user.date_joined,
            response.data["date_joined"],
        )
        self.assertEqual(device.mac, response.data["mac"])
        self.assertEqual(device.model, response.data["model"])
        self.assertEqual(device.platform, response.data["platform"])
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_signup_confirm(self):
        user = self._create_user()
        response = self.client.post(
            reverse("signup_confirm"),
            data={
                "user_id": user.id,
                "confirm_code": user.confirm_code,
            },
        )
        msg_id = "inf_user_activated"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_signup_anonymous(self):
        response = self.client.post(
            reverse("signup_anon"),
            data={
                "mac": _MACS[0],
                "model": _MODELS[0],
                "platform": _PLATFORMS[0],
            },
        )
        user = get_user_model().objects.last()
        device = Device.objects.get(user=user)
        msg_id = "inf_anon_loggedin"
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(user.id, response.data["id"])
        self.assertEqual(user.email, response.data["email"])
        self.assertEqual(
            user.date_joined,
            response.data["date_joined"],
        )
        self.assertEqual(device.mac, response.data["mac"])
        self.assertEqual(device.model, response.data["model"])
        self.assertEqual(device.platform, response.data["platform"])
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_login(self):
        user = self._create_user()
        response = self.client.post(
            reverse("login"),
            data={
                "email": user.email,
                "password": _PASSW0RDS[0],
                "mac": _MACS[0],
                "model": _MODELS[0],
                "platform": _PLATFORMS[0],
            },
        )
        token = Token.objects.get(user=user)
        device = Device.objects.filter(user=user).last()
        msg_id = "inf_user_loggedin"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(token.key, response.data["token"])
        self.assertEqual(device.mac, response.data["mac"])
        self.assertEqual(device.model, response.data["model"])
        self.assertEqual(device.platform, response.data["platform"])
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_get_profile(self):
        user = self._create_user()
        self._activate_user(user)
        token, _created = Token.objects.get_or_create(user=user)
        response = self.client.get(
            reverse("profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        user = get_user_model().objects.get(pk=user.pk)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(user.email, response.data["email"])
        self.assertEqual(user.first_name, response.data["first_name"])
        self.assertEqual(user.last_name, response.data["last_name"])
        self.assertEqual(user.birth_date, response.data["birth_date"])
        self.assertEqual(user.phone, response.data["phone"])

    def test_user_put_profile(self):
        user = self._create_user()
        self._activate_user(user)
        token, _created = Token.objects.get_or_create(user=user)
        response = self.client.put(
            reverse("profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            data={
                "email": "user_edited@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "birth_date": "2000-01-01",
                "phone": "09123456789",
            },
        )
        user = get_user_model().objects.get(pk=user.pk)
        msg_id = "inf_profile_updated"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(user.email, response.data["email"])
        self.assertEqual(user.first_name, response.data["first_name"])
        self.assertEqual(user.last_name, response.data["last_name"])
        self.assertEqual(
            str(user.birth_date),
            response.data["birth_date"],
        )
        self.assertEqual(user.phone, response.data["phone"])
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_logout(self):
        user = self._create_user()
        self._activate_user(user)
        token, _created = Token.objects.get_or_create(user=user)
        response = self.client.post(
            reverse("logout"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        tokenQueryset = Token.objects.filter(user=user)
        msg_id = "inf_user_loggedout"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(msg_id, response.data["detail"])
        self.assertEqual(tokenQueryset.count(), 0)

    def test_user_password_change(self):
        user = self._create_user()
        self._activate_user(user)
        token, _created = Token.objects.get_or_create(user=user)
        response = self.client.post(
            reverse("pass_change"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            data={
                "password": _PASSW0RDS[0],
                "new_password": _PASSW0RDS[1],
            },
        )
        user = get_user_model().objects.get(pk=user.pk)
        msg_id = "inf_password_changed"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(check_password(_PASSW0RDS[1], user.password), True)
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_password_reset_request(self):
        user = self._create_user()
        self._activate_user(user)
        current_confirm_code = user.confirm_code
        response = self.client.post(
            reverse("pass_reset_request"), data={"email": user.email}
        )
        user = get_user_model().objects.get(pk=user.pk)
        msg_id = "inf_passwordresetrequest_sent"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(user.confirm_code == current_confirm_code)
        self.assertEqual(msg_id, response.data["detail"])

    def test_user_password_reset_confirm(self):
        user = self._create_user()
        self._activate_user(user)
        self.client.post(reverse("pass_reset_request"), data={"email": user.email})
        user = get_user_model().objects.get(pk=user.pk)
        response = self.client.post(
            reverse("pass_reset_confirm"),
            data={
                "email": user.email,
                "confirm_code": user.confirm_code,
                "new_password": _PASSW0RDS[1],
            },
        )
        user = get_user_model().objects.get(pk=user.pk)
        msg_id = "inf_password_changed"
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(check_password(_PASSW0RDS[1], user.password), True)
        self.assertEqual(msg_id, response.data["detail"])

    def _create_user(self):

        email = "user@example.com"
        password = _PASSW0RDS[0]
        mac = _MACS[0]
        model = _MODELS[0]
        platform = _PLATFORMS[0]

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            confirm_code=secrets.randbits(16),
        )
        device = Device.objects.create(
            mac=mac,
            model=model,
            platform=platform,
            user=user,
        )
        user.save()
        device.save()
        return user

    def _activate_user(self, user):
        user.is_active = True
        user.save()
