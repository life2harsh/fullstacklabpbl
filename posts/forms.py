from django import forms
from django.forms import inlineformset_factory

from .models import Comment, Poll, PollOption, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "media"]
        widgets = {"content": forms.Textarea(attrs={"rows": 5, "placeholder": "What's on your mind? Use @username to mention someone."})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content", "parent"]
        widgets = {"content": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a comment..."}), "parent": forms.HiddenInput}
        labels = {"content": ""}

    def __init__(self, *args, post=None, **kwargs):
        super().__init__(*args, **kwargs)
        if post is not None:
            self.fields["parent"].queryset = post.comments.all()


class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ["question"]
        labels = {"question": "Poll question (optional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["question"].required = False


PollOptionFormSet = inlineformset_factory(Poll, PollOption, fields=["text"], extra=4, max_num=6, can_delete=False, labels={"text": "Option"})


class VoteForm(forms.Form):
    option = forms.ModelChoiceField(queryset=PollOption.objects.none(), widget=forms.RadioSelect, empty_label=None)

    def __init__(self, *args, poll, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["option"].queryset = poll.options.all()
