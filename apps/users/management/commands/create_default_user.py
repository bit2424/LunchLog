from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config


class Command(BaseCommand):
    help = "Create a default basic user from environment variables if not exists."

    def handle(self, *args, **options):
        User = get_user_model()

        email = config("DEFAULT_USER_EMAIL", default="basic@example.com")
        password = config("DEFAULT_USER_PASSWORD", default="basic123")
        is_staff = config("DEFAULT_USER_IS_STAFF", default=False, cast=bool)
        is_superuser = config("DEFAULT_USER_IS_SUPERUSER", default=False, cast=bool)

        if not email:
            self.stdout.write(
                self.style.WARNING(
                    "DEFAULT_USER_EMAIL not set; skipping default user creation."
                )
            )
            return

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created default user: {email}"))
        else:
            # Ensure flags and password are updated if changed
            updates = []
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                updates.append("is_staff")
            if user.is_superuser != is_superuser:
                user.is_superuser = is_superuser
                updates.append("is_superuser")
            if password:
                user.set_password(password)
                updates.append("password")
            if updates:
                user.save(update_fields=list(set(updates)))
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated default user: {email} ({", ".join(updates)})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Default user already exists and is up-to-date: {email}"
                    )
                )
