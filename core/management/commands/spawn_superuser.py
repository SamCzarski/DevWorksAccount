
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
import getpass


def main(options):
    user_profile = get_user_model()
    email = options.get("email")
    password = options.get("password")

    if not email:
        email = input("Email: ")

    if not password:
        new_password = None
        for _attempt in range(3):
            new_password = getpass.getpass("New Password: ")
            confirm_password = getpass.getpass("Confirm Password: ")
            if new_password != confirm_password:
                print(f"Error: Passwords do not match. ({_attempt+1}/3)")
            elif new_password == "":
                print(f"Error: Passwords cannot be blank. ({_attempt+1}/3)")
            else:
                break
            if _attempt == 2:
                print("Error: Too many failed attempts. Exiting.")
                return

        if new_password:
            password = new_password
        else:
            print("Error: Password failed to set. Exiting.")
            return

    try:
        user = user_profile.objects.get(email=email)
        user.set_password(password)
    except user_profile.DoesNotExist:
        user = user_profile.objects.create_superuser(
            email=email,
            password=password
        )
    user.active = True
    user.save()


class Command(BaseCommand):
    help = "Create or update a superuser with the given email and password"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=False,
            help="Email address for the superuser",
        )
        parser.add_argument(
            "--password",
            type=str,
            required=False,
            help="Password for the superuser",
        )

    def handle(self, **options):
        main(options)
