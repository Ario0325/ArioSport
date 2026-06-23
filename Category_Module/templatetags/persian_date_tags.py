"""Persian (Jalali) date & digit helpers as template filters."""
from django import template

register = template.Library()

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_FA_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
_FA_WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]


def _gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1
    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    g_day_no += g_d_m[gm2] + gd2
    if gm > 2 and ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        g_day_no += 1
    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    if j_day_no < 186:
        jm = 1 + j_day_no // 31
        jd = 1 + j_day_no % 31
    else:
        jm = 7 + (j_day_no - 186) // 30
        jd = 1 + (j_day_no - 186) % 30
    return jy, jm, jd


@register.filter(name="fa_digits")
def fa_digits(value):
    if value is None:
        return ""
    return str(value).translate(_FA_DIGITS)


@register.filter(name="jalali")
def jalali(value, fmt="full"):
    """Convert a date/datetime to a Jalali (Shamsi) string in Persian digits.
    fmt: 'full' -> ۱۸ خرداد ۱۴۰۵ ; 'short' -> ۱۴۰۵/۰۳/۱۸
    """
    if not value:
        return ""
    try:
        jy, jm, jd = _gregorian_to_jalali(value.year, value.month, value.day)
    except Exception:
        return str(value)
    if fmt == "short":
        s = f"{jy}/{jm:02d}/{jd:02d}"
    else:
        s = f"{jd} {_FA_MONTHS[jm - 1]} {jy}"
    return s.translate(_FA_DIGITS)
