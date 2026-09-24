from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from moods.api_auth import api_token_required
from moods.models import Activity, Mood
from moods.serializers import serialize_activity, serialize_mood


def parse_since(value):
    if not value:
        return None

    since = parse_datetime(value)
    if since is None:
        raise ValueError("Invalid since parameter; use ISO 8601 format.")

    if timezone.is_naive(since):
        since = timezone.make_aware(since)

    return since


@api_token_required
def mood_list(request):
    try:
        since = parse_since(request.GET.get("since", ""))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    moods = Mood.objects.filter(user=request.api_user).prefetch_related("activities")
    if since is not None:
        moods = moods.filter(last_modified__gte=since)

    results = [serialize_mood(mood) for mood in moods]
    return JsonResponse({"count": len(results), "results": results})


@api_token_required
def mood_detail(request, sqid):
    try:
        mood = Mood.objects.prefetch_related("activities").get(
            user=request.api_user,
            sqid=sqid,
        )
    except Mood.DoesNotExist:
        return JsonResponse({"error": "Mood not found"}, status=404)

    return JsonResponse(serialize_mood(mood))


@api_token_required
def activity_list(request):
    try:
        since = parse_since(request.GET.get("since", ""))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    activities = Activity.objects.filter(user=request.api_user)
    if since is not None:
        activities = activities.filter(last_modified__gte=since)

    results = [serialize_activity(activity) for activity in activities]
    return JsonResponse({"count": len(results), "results": results})
