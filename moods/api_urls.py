from django.urls import path

from moods import api_views

urlpatterns = [
    path("moods/", api_views.mood_list, name="api_mood_list"),
    path("moods/<slug:sqid>/", api_views.mood_detail, name="api_mood_detail"),
    path("activities/", api_views.activity_list, name="api_activity_list"),
]
