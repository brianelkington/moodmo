from datetime import timedelta
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView
from moods.models import Activity, Mood

MOOD_META = (
    (-2, "Very unhappy", "fa-face-sad-tear", "bg-cinnabar-500"),
    (-1, "Unhappy", "fa-face-frown", "bg-navajo-500"),
    (0, "Neutral", "fa-face-meh", "bg-primary-500"),
    (1, "Happy", "fa-face-smile", "bg-zomp-500"),
    (2, "Very happy", "fa-face-grin-stars", "bg-naples-500"),
)


def _nearest_mood(average):
    value, label, icon, color = min(MOOD_META, key=lambda item: abs(item[0] - average))
    return {
        "value": value,
        "label": label,
        "icon": icon,
        "color": color,
    }


def _streaks(dates):
    unique = sorted(set(dates))
    if not unique:
        return 0, 0

    longest = current_run = 1
    for previous, current in zip(unique, unique[1:]):
        if current - previous == timedelta(days=1):
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1

    today = timezone.localdate()
    unique_set = set(unique)
    cursor = today if today in unique_set else today - timedelta(days=1)
    current = 0
    if cursor in unique_set:
        while cursor in unique_set:
            current += 1
            cursor -= timedelta(days=1)

    return current, longest


def mood_statistics(user):
    moods = Mood.objects.filter(user=user)
    total = moods.count()
    stats = {
        "total": total,
        "days_tracked": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "this_week": 0,
        "this_month": 0,
        "average": None,
        "average_mood": None,
        "distribution": [],
        "recent_days": [],
        "top_activities": [],
    }

    if not total:
        return stats

    today = timezone.localdate()
    week_start = today - timedelta(days=6)
    month_start = today.replace(day=1)
    average = moods.aggregate(avg=Avg("mood"))["avg"]
    dates = list(moods.values_list("date", flat=True))
    current_streak, longest_streak = _streaks(dates)
    counts = {
        row["mood"]: row["total"]
        for row in moods.values("mood").annotate(total=Count("id"))
    }

    stats.update(
        {
            "days_tracked": len(set(dates)),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "this_week": moods.filter(date__gte=week_start).count(),
            "this_month": moods.filter(date__gte=month_start).count(),
            "average": round(average, 1),
            "average_mood": _nearest_mood(average),
        }
    )

    stats["distribution"] = [
        {
            "value": value,
            "label": label,
            "icon": icon,
            "color": color,
            "count": counts.get(value, 0),
            "percent": round(counts.get(value, 0) / total * 100),
        }
        for value, label, icon, color in MOOD_META
    ]

    range_start = today - timedelta(days=29)
    daily = {
        row["date"]: row
        for row in moods.filter(date__gte=range_start)
        .values("date")
        .annotate(avg=Avg("mood"), count=Count("id"))
    }
    recent_days = []
    for offset in range(30):
        day = range_start + timedelta(days=offset)
        row = daily.get(day)
        count = row["count"] if row else 0
        average_for_day = row["avg"] if row else None
        bar_height = 0
        if average_for_day is not None:
            bar_height = max(int(((average_for_day + 2) / 4) * 100), 12)
        recent_days.append(
            {
                "date": day,
                "count": count,
                "avg": round(average_for_day, 1) if average_for_day is not None else None,
                "bar_height": bar_height,
            }
        )
    stats["recent_days"] = recent_days

    stats["top_activities"] = list(
        Activity.objects.filter(user=user)
        .annotate(uses=Count("mood"))
        .filter(uses__gt=0)
        .order_by("-uses", "name")[:8]
    )
    return stats


class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("mood_list")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["canonical_url"] = settings.CANONICAL_URL
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "pages/settings.html"


class StatisticsPageView(LoginRequiredMixin, TemplateView):
    template_name = "pages/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(mood_statistics(self.request.user))
        return context
