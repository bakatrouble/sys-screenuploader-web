from app.models import UploadedMedia
from users.models import User


def media_count(request):
    ctx = {
        'media_count': UploadedMedia.objects.count(),
        'user_count': User.objects.filter(destinations__media__isnull=False).distinct().count()
    }
    return ctx
