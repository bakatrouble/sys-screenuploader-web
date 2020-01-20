from django.http import HttpRequest

from app.models import UploadedMedia
from users.models import User


def turbolinks(request: HttpRequest):
    ctx = {}
    if request.META.get('HTTP_TURBOLINKS_REFERRER') is not None:
        ctx['is_turbolinks'] = True
    return ctx


def media_count(request: HttpRequest):
    ctx = {
        'media_count': UploadedMedia.objects.count(),
        'user_count': User.objects.filter(destinations__media__isnull=False).distinct().count()
    }
    return ctx
