import logging
import traceback

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
        media.log = repr(e)
        traceback.print_exc()

    media.save()
