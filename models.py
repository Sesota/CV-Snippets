import io
import json

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.parsers import JSONParser

from src.bucket import push_file_task


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a user with the given email and password
        """
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=False")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=14, null=True, blank=True)

    pass_reset_req_date = models.DateTimeField(null=True, blank=True)
    confirm_code = models.BigIntegerField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Device(models.Model):
    mac = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    platform = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = [["mac", "user"]]

    def __str__(self):
        return f'{self.model} => {self.user.email}'


class MessageLevelManager(models.Manager):
    # Though unnecessary, just wrote it to save the uniformity of
    #   the code. TODO replace this with a code with better approach
    def get_export_to_cloud_task_sig(self, overwrite=True):
        # pylint: disable-msg=import-outside-toplevel
        from .serializers import MessageLevelSerializer

        queryset = MessageLevel.objects.all()
        serializer = MessageLevelSerializer(queryset, many=True)
        with open(settings.CDN_LOCAL_DIR + "messagelevels.json", "w") as f:
            json.dump(serializer.data, f)

        return push_file_task.signature(
            ("messagelevels.json", overwrite), immutable=True
        )


class MessageLevel(models.Model):
    title = models.CharField(max_length=10, unique=True, primary_key=True)

    objects = MessageLevelManager()

    def __str__(self):
        return self.title


class MessageManager(models.Manager):
    def get_export_to_cloud_task_sig(self, overwrite=True):
        # pylint: disable-msg=import-outside-toplevel

        from .serializers import MessageSerializer

        queryset = Message.objects.all()
        serializer = MessageSerializer(queryset, many=True)
        with open(settings.CDN_LOCAL_DIR + "messages.json", "w") as f:
            json.dump(serializer.data, f)

        return push_file_task.signature(("messages.json", overwrite), immutable=True)


class Message(models.Model):
    code = models.CharField(
        max_length=50,
        primary_key=True,
    )
    message_en = models.CharField(max_length=1000)
    message_fa = models.CharField(max_length=1000)
    level = models.ForeignKey(MessageLevel, on_delete=models.CASCADE)
    status_code = models.IntegerField(default=500)

    objects = MessageManager()

    def __str__(self):
        return "[" + str(self.level) + "]: " + self.code[4:].replace("_", " ")


class KeyManager(models.Manager):
    def import_keys(self):
        # pylint: disable-msg=import-outside-toplevel
        from .serializers import KeySerializer

        Key.objects.all().delete()
        with open(
            settings.CDN_LOCAL_DIR + "keylist.json",
            "rb",
        ) as f:
            content = f.read()

        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serialized = KeySerializer(data=data, many=True)
        if serialized.is_valid():
            serialized.save()
            return []
        return serialized.errors


class Key(models.Model):
    filename = models.CharField(max_length=50, primary_key=True)
    last_modified = models.DateTimeField()

    objects = KeyManager()

    def __str__(self):
        return self.filename