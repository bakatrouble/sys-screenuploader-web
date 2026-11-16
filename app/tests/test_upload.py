import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from PIL import Image

from app.models import TitleEntry, UploadedMedia
from app.tests import (
    DT, KNOWN_HASH, UNKNOWN_HASH, LocalTestCase,
    make_animated_gif_bytes, make_bmp_bytes, make_destination,
    make_jpeg_bytes, make_png_bytes, make_user,
    upload_filename, upload_url,
)


def parse_json(response):
    return json.loads(response.content.decode('utf-8'))


class UploadViewTest(LocalTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.destination = make_destination(self.user)
        self.body = make_jpeg_bytes()

    def post_upload(self, filename, body=None, caption=None, destination_id=None):
        if destination_id is None:
            destination_id = self.destination.pk
        url = upload_url(destination_id, filename, caption=caption)
        return self.client.post(url, data=body if body is not None else self.body,
                                content_type='application/octet-stream')

    def test_missing_filename_returns_400(self):
        response = self.client.post('/upload/{}/'.format(self.destination.pk), data=self.body,
                                    content_type='application/octet-stream')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'filename is missing')

    def test_malformed_filename_returns_400(self):
        bad_names = [
            'photo.jpg',  # no datetime-hash structure at all
            '2020010215040-{}.jpg'.format(KNOWN_HASH),  # 13-digit datetime
            '20200102150405-{}.jpg'.format(KNOWN_HASH),  # 14-digit datetime, view requires 16
            '{}-{}.jpg'.format(DT, KNOWN_HASH.lower()),  # lowercase hash
            '{}-{}.jpg'.format(DT, KNOWN_HASH[:16]),  # short hash
        ]
        for name in bad_names:
            with self.subTest(filename=name):
                response = self.post_upload(name)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(parse_json(response)['message'], 'incorrect filename')

    def test_unsupported_extension_returns_400(self):
        response = self.post_upload(upload_filename(ext='gif'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'incorrect file extension')

    def test_unknown_destination_returns_404(self):
        response = self.post_upload(upload_filename(), destination_id='12345678-1234-1234-1234-123456789abc')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(parse_json(response)['message'], 'wrong destination id')

    def test_undefined_destination_without_shared_returns_404(self):
        # NOTE: 'undefined' never reaches UploadView: the URL pattern only accepts
        # UUIDs (config/urls.py:23), so Django's URL resolver returns its own
        # HTML 404 before the view's 'undefined' branch (app/views.py:59-62) runs.
        response = self.post_upload(upload_filename(), destination_id='undefined')
        self.assertEqual(response.status_code, 404)

    @unittest.expectedFailure
    def test_undefined_destination_resolves_to_first_shared(self):
        # BUG (config/urls.py:23): the upload path uses <uuid:destination_id>, so
        # 'undefined' can never match and the view branch that resolves 'undefined'
        # to the first shared destination (app/views.py:59-62) is dead code.
        # Expected-correct behavior per the view: 200 with media on the shared dest.
        shared = make_destination(self.user, title='Shared', shared=True)
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_upload(upload_filename(), destination_id='undefined')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_json(response), {'status': 'ok'})
        media = UploadedMedia.objects.get()
        self.assertEqual(media.destination_id, shared.pk)

    def test_valid_jpeg_upload_creates_media(self):
        with mock.patch('app.views.process_upload.apply_async') as apply_async:
            response = self.post_upload(upload_filename())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_json(response), {'status': 'ok'})
        media = UploadedMedia.objects.get()
        self.assertEqual(media.destination_id, self.destination.pk)
        self.assertFalse(media.is_video)
        # The stored file lives under the test MEDIA_ROOT tempdir and is a JPEG.
        self.assertTrue(media.file.path.startswith(self.media_dir))
        self.assertTrue(os.path.exists(media.file.path))
        with Image.open(media.file.path) as stored:
            self.assertEqual(stored.format, 'JPEG')
        apply_async.assert_called_once_with(args=(media.pk,), shadow=str(media))

    def test_valid_png_upload_accepted(self):
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_upload(upload_filename(ext='png'), body=make_png_bytes())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_json(response), {'status': 'ok'})
        media = UploadedMedia.objects.get()
        self.assertFalse(media.is_video)
        # PNG uploads are re-encoded; the stored file is a JPEG.
        with Image.open(media.file.path) as stored:
            self.assertEqual(stored.format, 'JPEG')

    def test_animated_gif_rejected(self):
        response = self.post_upload(upload_filename(ext='gif').replace('.gif', '.jpg'),
                                    body=make_animated_gif_bytes())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'invalid image file')

    def test_bmp_rejected(self):
        response = self.post_upload(upload_filename(), body=make_bmp_bytes())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'invalid image file')

    def test_oversized_image_rejected(self):
        response = self.post_upload(upload_filename(), body=make_jpeg_bytes(size=(2000, 100)))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'invalid image file')

    def test_non_image_bytes_rejected(self):
        response = self.post_upload(upload_filename(), body=b'this is not an image at all' * 10)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'invalid image file')

    def test_caption_with_known_title(self):
        TitleEntry.objects.create(name='MyApp', hash=KNOWN_HASH)
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_upload(upload_filename(), caption='{title} screenshot')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UploadedMedia.objects.get().caption, 'MyApp screenshot')

    def test_caption_with_unknown_title(self):
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_upload(upload_filename(hsh=UNKNOWN_HASH), caption='{title} screenshot')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UploadedMedia.objects.get().caption, '[Unknown application] screenshot')

    def test_caption_date_and_time_substitutions(self):
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_upload(upload_filename(), caption='{date} {time}')
        self.assertEqual(response.status_code, 200)
        # DT = 20200102150405 -> 2020-01-02 15:04:05.
        self.assertEqual(UploadedMedia.objects.get().caption, '2020-01-02 15:04:05')

    def test_caption_datetime_format_substitution(self):
        # `{datetime:FORMAT}` tokens are replaced with strftime output.
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_upload(upload_filename(), caption='Year {datetime:%Y}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UploadedMedia.objects.get().caption, 'Year 2020')


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg not on PATH')
class VideoUploadTest(LocalTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.video_dir = tempfile.mkdtemp(prefix='screenuploader-videos-')
        cls.addClassCleanup(shutil.rmtree, cls.video_dir, True)
        cls.good_video = os.path.join(cls.video_dir, 'good.mp4')
        cls.small_video = os.path.join(cls.video_dir, 'small.mp4')
        cls._make_video(cls.good_video, '1280x720')
        cls._make_video(cls.small_video, '640x480')

    @staticmethod
    def _make_video(path, size):
        subprocess.run(
            ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'testsrc=size={}:rate=30'.format(size),
             '-t', '2', '-pix_fmt', 'yuv420p', '-c:v', 'libx264', path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.destination = make_destination(self.user)

    def post_video(self, path, filename):
        with open(path, 'rb') as f:
            body = f.read()
        url = upload_url(self.destination.pk, filename)
        return self.client.post(url, data=body, content_type='application/octet-stream')

    def test_valid_1280x720_video_accepted(self):
        with mock.patch('app.views.process_upload.apply_async'):
            response = self.post_video(self.good_video, upload_filename(ext='mp4'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_json(response), {'status': 'ok'})
        media = UploadedMedia.objects.get()
        self.assertTrue(media.is_video)
        self.assertEqual(media.video_width, 1280)
        self.assertEqual(media.video_height, 720)
        self.assertTrue(media.thumb)
        self.assertTrue(os.path.exists(media.thumb.path))

    def test_wrong_size_video_rejected(self):
        with mock.patch('app.views.process_upload.apply_async') as apply_async:
            response = self.post_video(self.small_video, upload_filename(ext='mp4'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(parse_json(response)['message'], 'invalid video file')
        self.assertEqual(UploadedMedia.objects.count(), 0)
        apply_async.assert_not_called()
