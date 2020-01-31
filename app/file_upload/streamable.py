import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from app.file_upload import Uploader
from app.models import UploadedMedia


class StreamableUploader(Uploader):
    UPLOADER_NAME = 'Streamable (blocked in Russia)'
    SLUG = 'streamable'

    @staticmethod
    def upload(media: UploadedMedia):
        if settings.DEBUG:
            upload_data = requests.post(
                'https://api.streamable.com/upload',
                files={'file': media.file.open('rb')},
                auth=HTTPBasicAuth(settings.STREAMABLE_EMAIL, settings.STREAMABLE_PASSWORD)
            ).json()
        else:
            upload_data = requests.get(
                'https://api.streamable.com/import',
                params={'url': media.file.url},
                auth=HTTPBasicAuth(settings.STREAMABLE_EMAIL, settings.STREAMABLE_PASSWORD)
            ).json()
        return f'https://streamable.com/{upload_data["shortcode"]}'
