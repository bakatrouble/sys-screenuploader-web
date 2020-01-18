from uuid import uuid4

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Destination(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='destinations')
    title = models.CharField(max_length=128)

    config_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    config_id = models.PositiveIntegerField()
    config = GenericForeignKey('config_type', 'config_id')


class DestinationModuleConfig(models.Model):
    _destination = GenericRelation(Destination, content_type_field='config_type', object_id_field='config_id')

    MODULE_NAME = '<Not set>'

    @property
    def destination(self):
        return self._destination.get()

    @property
    def content_type(self):
        return ContentType.objects.get_for_model(self.__class__)

    def send_media(self, media: 'UploadedMedia'):
        raise NotImplementedError()

    class Meta:
        abstract = True


class UploadedMedia(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    destination = models.ForeignKey(Destination, null=True, blank=True, on_delete=models.SET_NULL, related_name='media')
    is_video = models.BooleanField()
    file = models.FileField()
    thumb = models.FileField(null=True, blank=True)
    video_length = models.PositiveSmallIntegerField(null=True, blank=True)
    video_width = models.PositiveSmallIntegerField(null=True, blank=True)
    video_height = models.PositiveSmallIntegerField(null=True, blank=True)

    status = models.NullBooleanField()
    log = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'#{self.pk} {self.file.name}'


from .modules import DESTINATION_MODULES
