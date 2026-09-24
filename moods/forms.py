from django import forms
from django.utils import timezone
from moods.models import Activity, Mood


class ActivityForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Name of the activity",
            },
        ),
    )

    class Meta:
        model = Activity
        fields = ["name"]


class MoodForm(forms.ModelForm):
    note_title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Add a quick summary",
            },
        ),
        required=False,
    )
    note = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "Add a note",
            },
        ),
        required=False,
    )
    activities = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Mood
        fields = [
            "mood",
            "note_title",
            "note",
            "activities",
            "date",
            "time",
        ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["activities"].queryset = Activity.objects.filter(user=user)
        # Allow omitting time in the UI; clean() fills it with "now" on submit.
        self.fields["time"].required = False

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("note_title") or ""
        note = cleaned_data.get("note") or ""
        max_title_length = Mood._meta.get_field("note_title").max_length

        # Quick-entry text is bound to note_title; longer journal entries need the
        # unbounded note field or Postgres rejects the varchar(255) write.
        if len(title) > max_title_length:
            if note:
                cleaned_data["note"] = f"{title}\n{note}"
            else:
                cleaned_data["note"] = title
            cleaned_data["note_title"] = title[:max_title_length]

        if not cleaned_data.get("time"):
            cleaned_data["time"] = timezone.localtime().time()

        return cleaned_data


class UploadFileForm(forms.Form):
    file = forms.FileField()


class ExportOptionsForm(forms.Form):
    export_format = forms.ChoiceField(
        choices=[
            ("csv", "CSV"),
            ("json", "JSON"),
        ],
    )
