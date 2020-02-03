import logging
import traceback

import sentry_sdk

from app.models import UploadedMedia
from config.celery import app


@app.task(name='process_upload')
def process_upload(media_id: int):
    media = UploadedMedia.objects.get(pk=media_id)
    logging.warning(f'Media #{media_id} is being processed...')

    try:
        media.destination.config.send_media(media)
        media.status = True
    except Exception as e:
        media.status = False
        media.log = repr(e) + ': ' + str(e)
        traceback.print_exc()
        sentry_sdk.capture_exception()

    media.save()
