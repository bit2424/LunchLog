from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = "Set up periodic tasks for restaurant updates"

    def handle(self, *args, **options):
        # Create crontab schedule for every 2 days at 2 AM UTC
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_week="*",
            day_of_month="*/2",  # Every 2 days
            month_of_year="*",
        )

        # Create or update the periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name="Update all restaurants",
            defaults={
                "crontab": schedule,
                "task": "apps.restaurants.tasks.update_all_restaurants",
                "kwargs": json.dumps({}),
                "enabled": True,
                "description": "Update restaurant information from Google Places API every 2 days",
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully created periodic task "Update all restaurants"'
                )
            )
        else:
            # Update existing task
            task.crontab = schedule
            task.enabled = True
            task.save()
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully updated periodic task "Update all restaurants"'
                )
            )

        self.stdout.write(
            self.style.SUCCESS("All periodic tasks have been set up successfully!")
        )
