import io
import random
import uuid
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from PIL import Image

from apps.restaurants.models import (
    Cuisine,
    Restaurant,
    UserRestaurantVisit,
    UserCuisineStat,
)
from apps.receipts.models import Receipt


class Command(BaseCommand):
    help = "Seed demo cuisines, restaurants, visits, cuisine stats, and receipts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing demo data for the demo user before seeding",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            user = self._get_or_create_demo_user()

            if options.get("fresh"):
                self.stdout.write("Fresh flag provided: deleting existing demo data…")
                self._delete_demo_data(user)

            cuisines = self._ensure_cuisines()
            restaurants = self._ensure_restaurants(cuisines)
            self._ensure_visits_and_cuisine_stats(user, restaurants, cuisines)
            self._ensure_receipts(user, restaurants)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    # --- helpers ---
    def _get_or_create_demo_user(self):
        User = get_user_model()
        user, created = User.objects.get_or_create(email="basic@example.com")
        if created:
            user.set_password("basic123")
            user.save()
            self.stdout.write(
                "Created demo user basic@example.com with password 'basic123'"
            )
        else:
            self.stdout.write("Found existing demo user basic@example.com")
        return user

    def _delete_demo_data(self, user):
        Receipt.objects.filter(user=user).delete()
        UserRestaurantVisit.objects.filter(user=user).delete()
        UserCuisineStat.objects.filter(user=user).delete()
        self.stdout.write(
            "Deleted existing receipts, visits and cuisine stats for demo user"
        )

    def _ensure_cuisines(self):
        cuisine_names = [
            "Italian",
            "Mexican",
            "Japanese",
            "American",
            "Thai",
            "Indian",
            "Mediterranean",
        ]
        cuisines = {}
        for name in cuisine_names:
            cuisine, _ = Cuisine.objects.get_or_create(name=name)
            cuisines[name] = cuisine
        self.stdout.write(f"Ensured {len(cuisines)} cuisines")
        return cuisines

    def _ensure_restaurants(self, cuisines_by_name):
        demo_restaurants = [
            {
                "place_id": "ChIJ-good-italian-1",
                "name": "Trattoria Roma",
                "address": "123 Via Roma, Springfield, USA",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "rating": 4.6,
                "cuisines": ["Italian"],
            },
            {
                "place_id": "ChIJ-cheap-mexican-2",
                "name": "Taqueria El Sol",
                "address": "456 Fiesta Ave, Springfield, USA",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "rating": 4.2,
                "cuisines": ["Mexican"],
            },
            {
                "place_id": "ChIJ-good-japanese-3",
                "name": "Sakura Sushi",
                "address": "789 Cherry Blossom Rd, Springfield, USA",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "rating": 4.8,
                "cuisines": ["Japanese"],
            },
            {
                "place_id": "ChIJ-cuisine-match-4",
                "name": "Bombay Spice",
                "address": "321 Masala St, Springfield, USA",
                "latitude": 47.6062,
                "longitude": -122.3321,
                "rating": 4.5,
                "cuisines": ["Indian"],
            },
            {
                "place_id": "ChIJ-good-mediterranean-5",
                "name": "Aegean Breeze",
                "address": "654 Olive Grove Ln, Springfield, USA",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "rating": 4.7,
                "cuisines": ["Mediterranean"],
            },
        ]

        created_or_existing = []
        for r in demo_restaurants:
            restaurant, _ = Restaurant.objects.update_or_create(
                place_id=r["place_id"],
                defaults={
                    "name": r["name"],
                    "address": r["address"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "rating": r["rating"],
                },
            )
            # set cuisines
            cuisine_objects = [cuisines_by_name[name] for name in r["cuisines"]]
            restaurant.cuisines.set(cuisine_objects)
            created_or_existing.append(restaurant)

        self.stdout.write(f"Ensured {len(created_or_existing)} restaurants")
        return created_or_existing

    def _ensure_visits_and_cuisine_stats(self, user, restaurants, cuisines_by_name):
        # Simulate visit counts based on cuisine preferences
        preferred_cuisines = ["Japanese", "Mediterranean", "Italian"]
        cuisine_weights = {
            name: (5 if name in preferred_cuisines else 2) for name in cuisines_by_name
        }

        for cuisine_name, cuisine in cuisines_by_name.items():
            total_visits = random.randint(3, 12) * cuisine_weights[cuisine_name]
            stat, _ = UserCuisineStat.objects.get_or_create(user=user, cuisine=cuisine)
            stat.visit_count = total_visits
            stat.save()

        today = date.today()
        for restaurant in restaurants:
            base = cuisine_weights[restaurant.cuisines.first().name]
            visit_count = random.randint(3, 10) * base
            visit, _ = UserRestaurantVisit.objects.get_or_create(
                user=user, restaurant=restaurant
            )
            visit.visit_count = visit_count
            visit.last_visit = today - timedelta(days=random.randint(0, 60))
            visit.save()

        self.stdout.write("Ensured user visits and cuisine stats")

    def _ensure_receipts(self, user, restaurants):
        if Receipt.objects.filter(user=user).exists():
            self.stdout.write("Receipts already exist for demo user; skipping creation")
            return

        # Generate 18 receipts over the past 3 months
        today = date.today()
        created = 0
        for i in range(18):
            restaurant = random.choice(restaurants)
            purchase_date = today - timedelta(days=random.randint(0, 90))
            price = round(random.uniform(8.5, 42.0), 2)

            receipt = Receipt(
                user=user,
                date=purchase_date,
                price=price,
                restaurant=restaurant,
                restaurant_name=restaurant.name,
                address=restaurant.address,
            )

            # attach tiny image
            image_content = self._generate_tiny_image(
                color=(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
            )
            filename = f"receipt-{uuid.uuid4().hex[:8]}.png"
            receipt.image.save(filename, image_content, save=False)
            receipt.save()
            created += 1

        self.stdout.write(f"Created {created} receipts for demo user")

    def _generate_tiny_image(self, size=(32, 32), color=(200, 200, 200)):
        img = Image.new("RGB", size, color=color)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue(), name="receipt.png")
