from devworks_mail.mail import email_notify
from django.conf import settings
from django.template.loader import render_to_string
from django.urls.base import reverse


def account_created(request, to_email, token):
    url = request.build_absolute_uri(
        reverse('activate-account', kwargs={"token": token})
    )
    subject = "Activate your DevWorks Account"
    get_next = request.GET.get('next')

    if get_next:
        url = "{}?next={}".format(url, get_next)

    data = {"request": request, "subject": subject, "url": url}
    plain_text = render_to_string("account/activation/email.message.txt", data)
    html_message = render_to_string("account/activation/email.message.html", data)
    email_notify(to_email, subject, plain_text, html_message)


def account_deleted(to_email):
    subject = "DevWorks Account Deleted"
    notify_us = "support@example.com"
    data = {"subject": subject, "notify_us": notify_us}
    plain_text = render_to_string("account/delete/mail.message.txt", data)
    html_message = render_to_string("account/delete/mail.message.html", data)
    email_notify(to_email, subject, plain_text, html_message)


def account_password_change(to_email):
    subject = "DevWorks Account Update Notification"
    notify_us = "support@example.com"
    data = {"subject": subject, "notify_us": notify_us}
    plain_text = render_to_string("account/password_change/email.message.txt", data)
    html_message = render_to_string("account/password_change/email.message.html", data)
    email_notify(to_email, subject, plain_text, html_message)


def account_email_changed(to_email, old_email):
    subject = "DevWorks Email Address Change"
    plain_text = """
    Your email (and login) has change from {} to {}.

    If you didn't request this change please contact {}.

    Sincerely,
    The DevWorks Team

    """.format(old_email, to_email, settings.SERVER_EMAIL)
    email_notify(to_email, subject, plain_text)
    email_notify(old_email, subject, plain_text)
