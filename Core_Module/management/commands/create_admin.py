from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create or update a superuser."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="Admin")
        parser.add_argument("--email", default="admin@ariosport.local")
        parser.add_argument("--password", required=True)

    def handle(self, *args, **opts):
        username = opts["username"]
        email = opts["email"]
        password = opts["password"]

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email = email
            user.first_name = "مدیر"
            user.last_name = "سایت"
            user.save()
            self.stdout.write(self.style.WARNING(f"User '{username}' updated."))
        else:
            user = User.objects.create_superuser(username, email, password)
            user.first_name = "مدیر"
            user.last_name = "سایت"
            user.save()
            if hasattr(user, "profile"):
                user.profile.role = "مدیر ارشد"
                user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
