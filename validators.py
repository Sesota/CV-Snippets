# import re

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import User
from src.exceptions import MessagedException


def is_valid_password(password):
    if len(password) < 8:
        raise MessagedException(message="err_password_tooshort")

    return True


def cleaned_email_to_insert(email):
    # NOTE for API Client:
    #   Should always send rstriped lowered email in requests.
    #   Server cleans the email only while inserting in database, to keep the
    #   database clean; but when retrieving information it doesn't alter
    #   the entered email address.
    email = email.rstrip().lower()
    try:
        validate_email(email)
    except ValidationError:
        raise MessagedException(message="err_email_invalid")
    # validator = re.compile("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+$)")
    # if not validator.match(email):
    #     raise MessagedException(message="err_email_invalid")

    user = User.objects.filter(email=email).first()
    if user and user.is_active:
        raise MessagedException(message="err_user_exists")
    if user and not user.is_active:
        user.delete()

    return email
