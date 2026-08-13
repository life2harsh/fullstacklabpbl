from django import forms


class ActivityReportForm(forms.Form):
    include_comments = forms.BooleanField(required=False, initial=True)
    days = forms.IntegerField(min_value=1, max_value=365, initial=30)
