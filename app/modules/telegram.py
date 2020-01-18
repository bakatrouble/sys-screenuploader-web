import os
from tempfile import TemporaryDirectory

from PIL import Image
from django.conf import settings
from django.db import models
from telegram import Bot

from app.models import DestinationModuleConfig, UploadedMedia


class TelegramDestinationModuleConfig(DestinationModuleConfig):
    bot_token = models.CharField(max_length=64)
    chat_id = models.CharField(max_length=32)

    MODULE_NAME = 'Telegram'

    def send_media(self, media: UploadedMedia):
        media_file = media.file.open('rb') if settings.DEBUG else media.file.url
        bot = Bot(self.bot_token)
        if media.is_video:
            im = Image.open(media.thumb)
            im.thumbnail((320, 320), Image.ANTIALIAS)
            with TemporaryDirectory() as d:
                thumb = os.path.join(d, 'thumb.jpg')
                im.save(thumb)
                bot.send_video(self.chat_id, media_file, media.video_length,
                               width=media.video_width, height=media.video_height, supports_streaming=True,
                               thumb=media.thumb.open('rb'), timeout=60)
        else:
            bot.send_photo(self.chat_id, media_file)
