def site_settings(request):
    """Expose the singleton SiteSetting object to all templates as `site`."""
    from .models import SiteSetting
    from django.db import OperationalError, ProgrammingError
    try:
        site = SiteSetting.load()
    except (OperationalError, ProgrammingError):
        site = None
    return {"site": site}
