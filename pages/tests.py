from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from moods.models import Mood
from utils.testing import create_fake_user


class HomePageTests(TestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_url_available_by_name(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_template_name_correct(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "pages/home.html")


class SettingsPageTests(TestCase):
    def setUp(self):
        self.credentials, self.user = create_fake_user()
        self.url = reverse("settings")

    def test_authenticated_user_can_access_view(self):
        self.client.login(**self.credentials)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/settings.html")

    def test_not_authenticated_user_cannot_access_view(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class StatisticsPageTests(TestCase):
    def setUp(self):
        self.credentials, self.user = create_fake_user()
        self.url = reverse("statistics")

    def test_authenticated_user_can_access_view(self):
        self.client.login(**self.credentials)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/statistics.html")
        self.assertContains(response, "No moods to summarize yet")

    def test_not_authenticated_user_cannot_access_view(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_statistics_include_user_moods(self):
        self.client.login(**self.credentials)
        Mood.objects.create(
            user=self.user,
            mood=2,
            note_title="Great day",
            date=timezone.now().date(),
            time=timezone.now().time(),
        )

        response = self.client.get(self.url)

        self.assertContains(response, "Very happy")
        self.assertContains(response, "Last 30 days")
        self.assertNotContains(response, "still in construction")

    def test_statistics_exclude_other_users_moods(self):
        Mood.objects.create(
            user=self.user,
            mood=2,
            note_title="Owner only",
            date=timezone.now().date(),
            time=timezone.now().time(),
        )
        other_credentials, _ = create_fake_user()
        self.client.login(**other_credentials)

        response = self.client.get(self.url)

        self.assertContains(response, "No moods to summarize yet")
        self.assertNotContains(response, "Owner only")


class RobotsTxtTests(TestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)

    def test_url_available_by_name(self):
        response = self.client.get(reverse("robots"))
        self.assertEqual(response.status_code, 200)
        assert response["content-type"] == "text/plain"

    def test_template_name_correct(self):
        response = self.client.get(reverse("robots"))
        self.assertTemplateUsed(response, "pages/robots.txt")
