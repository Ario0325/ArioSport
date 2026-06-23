from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "نام شما"}),
            "email": forms.EmailInput(attrs={"class": "input en", "placeholder": "ایمیل (نمایش داده نمی‌شود)"}),
            "body": forms.Textarea(attrs={"class": "input", "rows": 4,
                                          "placeholder": "دیدگاه خود را بنویسید..."}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["name"].required = False
            self.fields["email"].required = False
