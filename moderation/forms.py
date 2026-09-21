from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "details"]
        widgets = {"details": forms.Textarea(attrs={"rows": 3, "placeholder": "Anything the moderators should know?"})}


class ModerationFilterForm(forms.Form):
    status = forms.ChoiceField(choices=[("", "All statuses"), *Report.STATUS_CHOICES], required=False)
    kind = forms.ChoiceField(choices=[("", "All types"), ("post", "Posts"), ("comment", "Comments"), ("user", "Users")], required=False)
