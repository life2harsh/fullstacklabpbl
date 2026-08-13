from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["report_type", "target_id", "reason", "details"]


class ModerationFilterForm(forms.Form):
    status = forms.ChoiceField(choices=[("", "All statuses"), *Report.STATUS_CHOICES], required=False)
