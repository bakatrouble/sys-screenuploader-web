import json

import requests
from django.conf import settings
from django.db import models

from app.file_upload import uploader_options, uploaders
from app.models import DestinationModuleConfig, UploadedMedia


HELP_TEXT = '''\
<h6>DM sending</h5>
<ul>
    <li>Join <a href="https://discord.gg/k7YYK8b" target="_blank">my Discord server</a></li>
    <li>Open DM with bot, send <code>!chatid</code> there, the response will contain channel ID</li>
</ul>

<h6>Channel sending</h5>
<ul>
    <li>Add bot to the server using <a href="https://discordapp.com/api/oauth2/authorize?client_id=668958356450312192&permissions=0&scope=bot" target="_blank">this link</a></li>
    <li>Use channel ID that you can obtain from Discord interface</li>
</ul>
'''


def get_api_session():
    api_session = requests.Session()
    api_session.headers = {'Authorization': 'Bot {}'.format(settings.DISCORD_BOT_TOKEN)}
    return api_session


class DestinationModuleConfigDiscord(DestinationModuleConfig):
    channel_id = models.CharField(max_length=32)
    # uploader = models.CharField(max_length=32, default='streamable', choices=uploader_options)

    MODULE_NAME = 'Discord'
    HELP_TEXT = HELP_TEXT

    def get_uploader(self):
        return uploaders[self.uploader]

    def send_media(self, media: UploadedMedia):
        url = 'https://discordapp.com/api/v6/channels/{}/messages'.format(self.channel_id)

        if media.is_video:
            # upload_url = self.get_uploader().upload(media)
            file_url: str = media.file.url
            if '?' in file_url:
                file_url = file_url[:file_url.find('?')]
            content = '{}\n||Clip will be removed after a week||\n{}'.format(file_url, (media.caption or '')[:128])
            r = get_api_session().post(url, {'payload_json': json.dumps({'content': content})},
                                       files={'file': media.thumb.open('rb')})
            if r.status_code != 200:
                raise RuntimeError(r.text)
        else:
            r = get_api_session().post(url, {'payload_json': json.dumps({'content': (media.caption or '')[:1024]})},
                                       files={'file': media.file.open('rb')})
            if r.status_code != 200:
                raise RuntimeError(r.text)

    class Meta:
        verbose_name = verbose_name_plural = 'Destination module config Discord'
