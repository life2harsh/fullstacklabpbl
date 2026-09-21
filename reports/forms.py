from datetime import timedelta

from django import forms
from django.utils import timezone


class ActivityReportForm(forms.Form):
    days = forms.IntegerField(min_value=1, max_value=365, initial=30, label="Last N days")
    include_comments = forms.BooleanField(required=False, initial=True)


class DateRangeForm(forms.Form):
    start = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, data=None):
        today = timezone.localdate()
        super().__init__(data or None, initial={"start": today - timedelta(days=29), "end": today})

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("start") and cleaned.get("end") and cleaned["start"] > cleaned["end"]:
            raise forms.ValidationError("Start date must be on or before the end date.")
        return cleaned

    def range(self):
        if self.is_valid():
            return self.cleaned_data["start"], self.cleaned_data["end"]
        return self.initial["start"], self.initial["end"]
