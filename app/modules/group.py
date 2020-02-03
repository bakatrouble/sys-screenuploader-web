import traceback

import sentry_sdk
from django.db import models

from ..models import DestinationModuleConfig, UploadedMedia, Destination


HELP_TEXT = '''\
Select multiple destinations to send media simultaneously
'''


class DestinationModuleConfigGroup(DestinationModuleConfig):
    destinations = models.ManyToManyField(Destination)

    MODULE_NAME = 'Group'
    HELP_TEXT = HELP_TEXT

    @staticmethod
    def INIT_HOOK(form, *args, request, ct, **kwargs):
        form.fields['destinations'].queryset = Destination.get_user_destinations(request.user)\
            .exclude(config_id=form.instance.pk if form.instance else None, config_type=ct)

    def send_media(self, media: UploadedMedia):
        errors = []
        for dest in self.destinations.all():
            try:
                dest.config.send_media(media)
            except Exception as e:
                errors.append(f'Destination {dest} | {e!r}: {e!s}')
                traceback.print_exc()
                sentry_sdk.capture_exception()
        if errors:
            if len(errors) != self.destinations.count():
                errors = ['Partial', ''] + errors
            raise RuntimeError(';\n'.join(errors))

    class Meta:
        verbose_name = verbose_name_plural = 'Destination module config Group'
