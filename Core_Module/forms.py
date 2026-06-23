from django import forms
from .models import ContactMessage, NewsletterSubscriber


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "نام شما"}),
            "email": forms.EmailInput(attrs={"class": "input en", "placeholder": "you@email.com"}),
            "subject": forms.TextInput(attrs={"class": "input", "placeholder": "موضوع پیام"}),
            "message": forms.Textarea(attrs={"class": "input", "placeholder": "پیام خود را بنویسید..."}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "ایمیل شما", "required": True}),
        }
