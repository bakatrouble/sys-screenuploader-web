"""Shared test infrastructure for the screenuploader test suite.

All tests must run without Redis, S3, or any network access, so every
TestCase here derives from :class:`LocalTestCase`, which swaps the cache
for locmem, sessions for the DB backend, storage for the local filesystem,
and points MEDIA_ROOT at a per-test tempdir.
"""

import shutil
import tempfile
from io import BytesIO
from urllib.parse import quote

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from PIL import Image

from app.models import Destination
from app.modules.group import DestinationModuleConfigGroup
from users.models import User

#: Datetime prefix used in upload filenames (YYYYMMDDhhmmss + 2 digits,
#: matching the 16-digit Nintendo Switch capture filenames the view expects).
DT = '2020010215040500'
#: Known application hash used in upload filenames (32 uppercase hex chars).
KNOWN_HASH = '0123456789ABCDEF0123456789ABCDEF'
#: Hash with no matching TitleEntry.
UNKNOWN_HASH = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'


class LocalTestCase(TestCase):
    """TestCase with local-only cache/session/storage settings."""

    def setUp(self):
        super().setUp()
        self.media_dir = tempfile.mkdtemp(prefix='screenuploader-tests-')
        self._settings_override = override_settings(
            CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
            SESSION_ENGINE='django.contrib.sessions.backends.db',
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
            },
            MEDIA_ROOT=self.media_dir,
        )
        self._settings_override.enable()
        self.addCleanup(self._settings_override.disable)
        self.addCleanup(shutil.rmtree, self.media_dir, True)


def make_user(email='user@example.com', password='pass12345'):
    return User.objects.create_user(email=email, password=password)


def make_destination(owner, title='Test destination', shared=False):
    config = DestinationModuleConfigGroup.objects.create()
    content_type = ContentType.objects.get_for_model(DestinationModuleConfigGroup)
    return Destination.objects.create(
        owner=owner, title=title, shared=shared,
        config_type=content_type, config_id=config.pk,
    )


def upload_url(destination_id, filename, caption=None):
    url = '/upload/{}/?filename={}'.format(destination_id, filename)
    if caption is not None:
        url += '&caption=' + quote(caption, safe='')
    return url


def upload_filename(dt=DT, hsh=KNOWN_HASH, ext='jpg'):
    return '{dt}-{hash}.{ext}'.format(dt=dt, hash=hsh, ext=ext)


def make_jpeg_bytes(size=(100, 100), color='red'):
    buf = BytesIO()
    Image.new('RGB', size, color).save(buf, format='JPEG')
    return buf.getvalue()


def make_png_bytes(size=(100, 100), color='blue'):
    buf = BytesIO()
    Image.new('RGB', size, color).save(buf, format='PNG')
    return buf.getvalue()


def make_animated_gif_bytes():
    frames = [Image.new('RGB', (50, 50), color) for color in ('red', 'blue')]
    buf = BytesIO()
    frames[0].save(buf, format='GIF', save_all=True, append_images=frames[1:], loop=0)
    return buf.getvalue()


def make_bmp_bytes(size=(50, 50)):
    buf = BytesIO()
    Image.new('RGB', size, 'green').save(buf, format='BMP')
    return buf.getvalue()
