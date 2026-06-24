from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile

INPUT = {"class": "input"}
INPUT_EN = {"class": "input en"}
INPUT_OTP = {"class": "input otp-input", "maxlength": "6", "autocomplete": "one-time-code",
             "inputmode": "numeric", "placeholder": "------", "dir": "ltr"}


class RegisterForm(forms.ModelForm):
    full_name = forms.CharField(label="نام کامل", max_length=150,
        widget=forms.TextInput(attrs={**INPUT, "placeholder": "نام و نام خانوادگی"}))
    email = forms.EmailField(label="ایمیل",
        widget=forms.EmailInput(attrs={**INPUT_EN, "placeholder": "you@email.com"}))
    password = forms.CharField(label="رمز عبور",
        widget=forms.PasswordInput(attrs={**INPUT, "placeholder": "حداقل ۸ کاراکتر"}))
    agree = forms.BooleanField(label="قوانین را می‌پذیرم", required=True)

    class Meta:
        model = User
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return email

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        full = self.cleaned_data["full_name"].strip()
        first, _, last = full.partition(" ")
        user = User(username=email, email=email, first_name=first, last_name=last)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class OTPVerificationForm(forms.Form):
    code = forms.CharField(
        label="کد تایید",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs=INPUT_OTP),
    )

    def clean_code(self):
        code = self.cleaned_data["code"]
        if not code.isdigit():
            raise forms.ValidationError("کد تایید باید فقط شامل اعداد باشد.")
        return code


class PasswordChangeRequestForm(forms.Form):
    pass


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={**INPUT_EN, "placeholder": "you@email.com", "autofocus": True}),
    )


class CustomSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={**INPUT, "placeholder": "حداقل ۸ کاراکتر", "autofocus": True}),
    )
    new_password2 = forms.CharField(
        label="تکرار رمز عبور جدید",
        widget=forms.PasswordInput(attrs={**INPUT, "placeholder": "رمز عبور را دوباره وارد کنید"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمزهای عبور مطابقت ندارند.")
        from django.contrib.auth.password_validation import validate_password
        validate_password(p2, self.user)
        return p2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data["new_password1"])
        if commit:
            self.user.save()
        return self.user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="ایمیل",
        widget=forms.TextInput(attrs={**INPUT_EN, "placeholder": "you@email.com", "autofocus": True}))
    password = forms.CharField(label="رمز عبور",
        widget=forms.PasswordInput(attrs={**INPUT, "placeholder": "••••••••"}))


class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="نام", max_length=80, required=False,
        widget=forms.TextInput(attrs=INPUT))
    last_name = forms.CharField(label="نام خانوادگی", max_length=80, required=False,
        widget=forms.TextInput(attrs=INPUT))
    email = forms.EmailField(label="ایمیل", widget=forms.EmailInput(attrs=INPUT_EN))

    class Meta:
        model = Profile
        fields = ["avatar", "role", "bio", "phone"]
        widgets = {
            "role": forms.TextInput(attrs=INPUT),
            "bio": forms.Textarea(attrs={**INPUT, "rows": 4}),
            "phone": forms.TextInput(attrs={**INPUT_EN}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            u = self.instance.user
            self.fields["first_name"].initial = u.first_name
            self.fields["last_name"].initial = u.last_name
            self.fields["email"].initial = u.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        u = profile.user
        u.first_name = self.cleaned_data["first_name"]
        u.last_name = self.cleaned_data["last_name"]
        u.email = self.cleaned_data["email"]
        if commit:
            u.save()
            profile.save()
        return profile
