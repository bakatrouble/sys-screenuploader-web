import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from app.file_upload import Uploader
from app.models import UploadedMedia


class VideobinUploader(Uploader):
    UPLOADER_NAME = 'Videobin'
    SLUG = 'videobin'

    @staticmethod
    def upload(media: UploadedMedia):
        link = requests.post(
            'https://videobin.org/add',
            {'api': 1, 'email': media.destination.owner.email},
            files={'videoFile': media.file.open('rb')},
            auth=HTTPBasicAuth(settings.STREAMABLE_EMAIL, settings.STREAMABLE_PASSWORD)
        ).text
        return link.replace('html', 'ogg')
