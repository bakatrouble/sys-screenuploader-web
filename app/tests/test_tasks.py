from unittest import mock

from app.models import UploadedMedia
from app.tasks import process_upload
from app.tests import LocalTestCase, make_destination, make_user


class ProcessUploadTaskTest(LocalTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.destination = make_destination(self.user)
        self.media = UploadedMedia.objects.create(destination=self.destination, is_video=False)

    def test_success_marks_status_true_and_leaves_log(self):
        with mock.patch('app.modules.group.DestinationModuleConfigGroup.send_media', return_value=None):
            process_upload(self.media.pk)
        self.media.refresh_from_db()
        self.assertTrue(self.media.status)
        self.assertIsNone(self.media.log)

    def test_send_media_error_marks_status_false_and_reports(self):
        error = RuntimeError('boom')
        with mock.patch('app.modules.group.DestinationModuleConfigGroup.send_media', side_effect=error):
            process_upload(self.media.pk)
        self.media.refresh_from_db()
        self.assertFalse(self.media.status)
        self.assertIn(repr(error), self.media.log)
        self.assertIn(str(error), self.media.log)

    def test_missing_media_raises_does_not_exist(self):
        with self.assertRaises(UploadedMedia.DoesNotExist):
            process_upload(123456789)
