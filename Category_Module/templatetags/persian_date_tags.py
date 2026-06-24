"""Persian (Jalali) date & digit helpers as template filters."""
import jdatetime
from django import template

register = template.Library()

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_FA_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


@register.filter(name="fa_digits")
def fa_digits(value):
    if value is None:
        return ""
    return str(value).translate(_FA_DIGITS)


@register.filter(name="jalali")
def jalali(value, fmt="full"):
    if not value:
        return ""
    try:
        if hasattr(value, "year"):
            j = jdatetime.date.fromgregorian(date=value)
        else:
            return str(value)
    except Exception:
        return str(value)
    if fmt == "short":
        s = f"{j.year:04d}/{j.month:02d}/{j.day:02d}"
    elif fmt == "medium":
        s = f"{j.day} {_FA_MONTHS[j.month - 1]} {j.year}"
    else:
        s = f"{j.day} {_FA_MONTHS[j.month - 1]} {j.year}"
    return s.translate(_FA_DIGITS)


@register.filter(name="jalali_datetime")
def jalali_datetime(value, fmt="full"):
    if not value:
        return ""
    try:
        if hasattr(value, "year"):
            j = jdatetime.datetime.fromgregorian(datetime=value)
        else:
            return str(value)
    except Exception:
        return str(value)
    time_str = f"{j.hour:02d}:{j.minute:02d}"
    date_str = jalali(value, fmt)
    if fmt == "short":
        return f"{date_str} - {time_str}".translate(_FA_DIGITS)
    return f"{date_str} - {time_str}".translate(_FA_DIGITS)
