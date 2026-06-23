from django import forms
from Blog_Module.models import Post, Tag
from Category_Module.models import Category
from Core_Module.models import SiteSetting
from ckeditor_uploader.widgets import CKEditorUploadingWidget

FC = "fc-input"


class AdminPostForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditorUploadingWidget(config_name="default"),
        label="متن کامل مقاله"
    )

    class Meta:
        model = Post
        fields = ["title", "slug", "category", "excerpt", "content",
                  "cover_image", "tags", "status", "is_featured"]
        widgets = {
            "title": forms.TextInput(attrs={"class": FC, "placeholder": "عنوان مقاله"}),
            "slug": forms.TextInput(attrs={"class": FC, "placeholder": "خودکار از عنوان ساخته می‌شود"}),
            "category": forms.Select(attrs={"class": FC}),
            "excerpt": forms.Textarea(attrs={"class": FC, "rows": 3,
                                             "placeholder": "خلاصه کوتاه مقاله"}),
            "tags": forms.SelectMultiple(attrs={"class": FC}),
            "status": forms.Select(attrs={"class": FC}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["tags"].required = False


class AdminCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "icon", "description", "order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": FC, "placeholder": "نام دسته"}),
            "slug": forms.TextInput(attrs={"class": FC, "placeholder": "خودکار ساخته می‌شود"}),
            "icon": forms.TextInput(attrs={"class": FC, "placeholder": "goal, dumbbell, ..."}),
            "description": forms.Textarea(attrs={"class": FC, "rows": 3}),
            "order": forms.NumberInput(attrs={"class": FC}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False


class AdminSiteSettingForm(forms.ModelForm):
    about_short = forms.CharField(widget=CKEditorUploadingWidget(), label="درباره کوتاه (فوتر)", required=False)
    about_full = forms.CharField(widget=CKEditorUploadingWidget(), label="متن کامل صفحه درباره ما", required=False)

    class Meta:
        model = SiteSetting
        exclude = ["updated_at"]
        widgets = {f: forms.TextInput(attrs={"class": FC}) for f in
                   ["site_name", "tagline", "email", "phone", "address",
                    "instagram", "telegram", "twitter", "youtube", "footer_text"]}


class AdminUserForm(forms.Form):
    first_name = forms.CharField(label="نام", required=False,
        widget=forms.TextInput(attrs={"class": FC}))
    last_name = forms.CharField(label="نام خانوادگی", required=False,
        widget=forms.TextInput(attrs={"class": FC}))
    email = forms.EmailField(label="ایمیل",
        widget=forms.EmailInput(attrs={"class": FC}))
    is_staff = forms.BooleanField(label="دسترسی به پنل مدیریت", required=False)
    is_active = forms.BooleanField(label="حساب فعال", required=False)


class AdminTagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": FC, "placeholder": "نام برچسب"}),
        }
