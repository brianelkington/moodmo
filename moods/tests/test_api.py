from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ApiToken
from moods.models import Activity, Mood
from utils.testing import create_fake_activity, create_fake_mood, create_fake_user


class ApiTokenModelTest(TestCase):
    def setUp(self):
        _, self.user = create_fake_user()

    def test_create_and_authenticate_token(self):
        _, raw_key = ApiToken.create_for_user(self.user, name="PARA sync")

        self.assertEqual(ApiToken.authenticate(raw_key), self.user)
        self.assertIsNone(ApiToken.authenticate("invalid-token"))


class MoodApiTest(TestCase):
    def setUp(self):
        self.credentials, self.user = create_fake_user()
        _, self.raw_key = ApiToken.create_for_user(self.user, name="test")
        self.other_credentials, self.other_user = create_fake_user()
        self.mood = create_fake_mood(self.user)
        self.activity = create_fake_activity(self.user)
        self.mood.activities.add(self.activity)

    def auth_headers(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.raw_key}"}

    def test_mood_list_requires_auth(self):
        response = self.client.get(reverse("api_mood_list"))
        self.assertEqual(response.status_code, 401)

    def test_mood_list_returns_user_moods(self):
        create_fake_mood(self.other_user)

        response = self.client.get(reverse("api_mood_list"), **self.auth_headers())
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(len(payload["results"]), 1)

        mood_data = payload["results"][0]
        self.assertEqual(mood_data["sqid"], self.mood.sqid)
        self.assertEqual(mood_data["mood"], self.mood.mood)
        self.assertEqual(mood_data["note_title"], self.mood.note_title)
        self.assertEqual(mood_data["activities"], [self.activity.name])
        self.assertEqual(mood_data["date"], self.mood.date.strftime("%Y-%m-%d"))
        self.assertEqual(mood_data["time"], self.mood.time.strftime("%H:%M:%S"))
        self.assertIn("last_modified", mood_data)

    def test_mood_list_filters_by_since(self):
        old_mood = Mood.objects.create(
            user=self.user,
            mood=0,
            date=timezone.now().date(),
            time=timezone.now().time(),
        )
        Mood.objects.filter(pk=old_mood.pk).update(
            last_modified=timezone.now() - timedelta(days=2)
        )

        since = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.get(
            reverse("api_mood_list"),
            {"since": since},
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        sqids = {item["sqid"] for item in response.json()["results"]}
        self.assertIn(self.mood.sqid, sqids)
        self.assertNotIn(old_mood.sqid, sqids)

    def test_mood_list_rejects_invalid_since(self):
        response = self.client.get(
            reverse("api_mood_list"),
            {"since": "not-a-date"},
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 400)

    def test_mood_detail_returns_single_mood(self):
        response = self.client.get(
            reverse("api_mood_detail", kwargs={"sqid": self.mood.sqid}),
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sqid"], self.mood.sqid)

    def test_mood_detail_returns_404_for_other_user(self):
        other_mood = create_fake_mood(self.other_user)
        response = self.client.get(
            reverse("api_mood_detail", kwargs={"sqid": other_mood.sqid}),
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 404)

    def test_api_key_header_auth(self):
        response = self.client.get(
            reverse("api_mood_list"),
            HTTP_X_API_KEY=self.raw_key,
        )
        self.assertEqual(response.status_code, 200)


class ActivityApiTest(TestCase):
    def setUp(self):
        _, self.user = create_fake_user()
        _, self.raw_key = ApiToken.create_for_user(self.user, name="test")
        self.activity = create_fake_activity(self.user)

    def test_activity_list_returns_user_activities(self):
        response = self.client.get(
            reverse("api_activity_list"),
            HTTP_AUTHORIZATION=f"Bearer {self.raw_key}",
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["sqid"], self.activity.sqid)
        self.assertEqual(payload["results"][0]["name"], self.activity.name)
