import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class GDRPValidator(object):

    def __init__(self, min_digits=0, min_upper=0, min_lower=0, min_special=0):
        self.min_upper = min_upper
        self.min_lower = min_lower
        self.min_digits = min_digits
        self.min_special = min_special

    def validate(self, password, user=None):
        errors = []
        if not len(re.findall(r'[A-Z]', password)) >= self.min_upper:
            errors.append(
                "{} uppercase letter(s) A-Z".format(self.min_upper)
            )
        if not len(re.findall(r'[a-z]', password)) >= self.min_lower:
            errors.append(
                _("{} lowercase letter(s) a-z".format(self.min_lower))
            )

        if not len(re.findall(r'[0-9]', password)) >= self.min_digits:
            errors.append(
                _("{} digit(s) 0-9".format(self.min_digits))
            )

        if not len(re.findall(r'[^a-z0-9]', password)) >= self.min_special:
            errors.append(
                _("{} character(s) not a letter or numeric (ie: -,.,$,!)".format(self.min_special)),
            )
        if len(errors) > 0:
            messages = ", ".join([str(x) for x in errors])
            raise ValidationError(
                _("The password must contain at least {}".format(messages)),
                code='password_not_gdrp'
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least: "
            " %(min_upper)d uppercase letter(s)"
            " %(min_lower)d lowercase letter(s)"
            " %(min_digits)d digit(s)"
            " %(min_special)d non alphanumeric(s)" % {
                'min_upper': self.min_upper,
                'min_lower': self.min_lower,
                'min_digits': self.min_digits,
                'min_special': self.min_special
            }
        )
