import requests
from django.conf import settings

from app.file_upload import Uploader
from app.models import UploadedMedia


class GfycatUploader(Uploader):
    UPLOADER_NAME = 'Gfycat'
    SLUG = 'gfycat'

    @staticmethod
    def upload(media: UploadedMedia):
        token_data = requests.post('https://api.gfycat.com/v1/oauth/token', json={
            "client_id": settings.GFYCAT_CLIENT_ID,
            "client_secret": settings.GFYCAT_SECRET,
            "grant_type": "client_credentials"
        }).json()

        upload_params = {'private': True, 'keepAudio': True, 'noMd5': True}
        if not settings.DEBUG:
            upload_params['fetchUrl'] = media.file.url
        upload_data = requests.post('https://api.gfycat.com/v1/gfycats', json=upload_params, headers={
            'Authorization': f'Bearer {token_data["access_token"]}'
        }).json()

        if settings.DEBUG:
            fupload_res = requests.put(f'https://filedrop.gfycat.com/{upload_data["gfyname"]}',
                                       data=media.file.open('rb'), timeout=60)
            if fupload_res.status_code != 200:
                raise RuntimeError(f'Upload HTTP code: {fupload_res.status_code}')
        return f'https://gfycat.com/{upload_data["gfyname"]}'
