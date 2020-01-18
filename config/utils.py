from django.http import HttpRequest

from app.models import UploadedMedia


def turbolinks(request: HttpRequest):
    ctx = {}
    if request.META.get('HTTP_TURBOLINKS_REFERRER') is not None:
        ctx['is_turbolinks'] = True
    return ctx


def media_count(request: HttpRequest):
    ctx = {
        'media_count': UploadedMedia.objects.count(),
    }
    return ctx
