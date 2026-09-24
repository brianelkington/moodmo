def serialize_activity(activity):
    return {
        "sqid": activity.sqid,
        "name": activity.name,
        "last_modified": activity.last_modified.isoformat(),
    }


def serialize_mood(mood):
    return {
        "sqid": mood.sqid,
        "mood": mood.mood,
        "note_title": mood.note_title,
        "note": mood.note,
        "activities": [activity.name for activity in mood.activities.all()],
        "date": mood.date.strftime("%Y-%m-%d"),
        "time": mood.time.strftime("%H:%M:%S"),
        "last_modified": mood.last_modified.isoformat(),
    }
