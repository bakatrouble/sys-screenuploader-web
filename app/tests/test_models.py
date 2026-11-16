from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from app.models import Destination, TitleEntry, UploadedMedia
from app.modules.group import DestinationModuleConfigGroup
from app.tests import KNOWN_HASH, LocalTestCase, make_destination, make_jpeg_bytes, make_user


class DestinationQueryTest(LocalTestCase):
    def test_get_user_destinations_includes_own_and_shared(self):
        owner = make_user('owner@example.com')
        other = make_user('other@example.com')
        own_private = make_destination(owner, title='Own private')
        own_shared = make_destination(owner, title='Own shared', shared=True)
        others_shared = make_destination(other, title='Other shared', shared=True)
        others_private = make_destination(other, title='Other private')

        visible = set(Destination.get_user_destinations(owner).values_list('pk', flat=True))
        self.assertEqual(visible, {own_private.pk, own_shared.pk, others_shared.pk})
        self.assertNotIn(others_private.pk, visible)

    def test_get_user_destinations_excludes_private_of_others(self):
        owner = make_user('owner@example.com')
        other = make_user('other@example.com')
        private = make_destination(owner, title='Private')
        self.assertNotIn(private.pk,
                         set(Destination.get_user_destinations(other).values_list('pk', flat=True)))


class ModelStrTest(LocalTestCase):
    def test_destination_str_is_title(self):
        user = make_user()
        destination = make_destination(user, title='My channel')
        self.assertEqual(str(destination), 'My channel')

    def test_group_config_str_names_destination_and_module(self):
        user = make_user()
        destination = make_destination(user, title='My channel')
        content_type = ContentType.objects.get_for_model(DestinationModuleConfigGroup)
        config = content_type.get_object_for_this_type(pk=destination.config_id)
        self.assertEqual(str(config), 'My channel (module Group)')

    def test_uploaded_media_str_contains_pk_and_filename(self):
        user = make_user()
        destination = make_destination(user)
        media = UploadedMedia(destination=destination, is_video=False)
        media.file.save('shot.jpg', SimpleUploadedFile('shot.jpg', make_jpeg_bytes()), save=False)
        media.save()
        self.assertEqual(str(media), '#{} {}'.format(media.pk, media.file.name))

    def test_title_entry_str_contains_name_and_hash(self):
        entry = TitleEntry.objects.create(name='MyApp', hash=KNOWN_HASH)
        self.assertEqual(str(entry), 'MyApp [{}]'.format(KNOWN_HASH))
