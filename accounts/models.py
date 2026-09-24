import hashlib
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    pass

    def __str__(self) -> str:
        return str(self.email)


class ApiToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )
    name = models.CharField(max_length=100, blank=True)
    key_prefix = models.CharField(max_length=8, editable=False)
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        label = self.name or "API token"
        return f"{label} ({self.key_prefix}…)"

    @classmethod
    def create_for_user(cls, user, name=""):
        raw_key = secrets.token_urlsafe(32)
        token = cls.objects.create(
            user=user,
            name=name,
            key_prefix=raw_key[:8],
            key_hash=cls.hash_key(raw_key),
        )
        return token, raw_key

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def authenticate(cls, raw_key):
        if not raw_key:
            return None

        try:
            token = cls.objects.select_related("user").get(
                key_hash=cls.hash_key(raw_key)
            )
        except cls.DoesNotExist:
            return None

        cls.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
        return token.user
