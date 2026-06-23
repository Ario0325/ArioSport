from django.apps import AppConfig


class AccountsModuleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Accounts_Module"
    verbose_name = "حساب کاربری و مدیریت"

    def ready(self):
        from . import signals  # noqa
