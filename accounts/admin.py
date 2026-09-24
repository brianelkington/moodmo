from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import ApiToken, CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["email", "username"]


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "key_prefix", "created_at", "last_used_at"]
    list_filter = ["created_at", "last_used_at"]
    search_fields = ["name", "user__email", "key_prefix"]
    readonly_fields = ["user", "name", "key_prefix", "key_hash", "created_at", "last_used_at"]

    def has_add_permission(self, request):
        return False


admin.site.register(CustomUser, CustomUserAdmin)
