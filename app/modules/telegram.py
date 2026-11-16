import asyncio
import os
from tempfile import TemporaryDirectory

from PIL import Image
from django.conf import settings
from django.db import models
from telegram import Bot
from telegram.constants import MessageLimit

from app.models import DestinationModuleConfig, UploadedMedia


HELP_TEXT = '''\
<ul>
    <li>Create a bot using <a href="https://t.me/botfather" target="_blank">@botfather</a>, you will get its <b>token</b></li>
    <li>Create a channel or a group and add your bot to it (as admin for channels)</li>
    <li>
        <b>For channels:</b> Send a message to the channel and forward it to 
        <a href="https://t.me/getmyid_bot" target="_blank">@getmyid_bot</a>, you will get your <b>chat ID</b> 
        (minus sign for private channels included)
    </li>
    <li>
        <b>For groups:</b> Add <a href="https://t.me/getmyid_bot" target="_blank">@getmyid_bot</a> to your group and 
        you will immediately get you <b>chat ID</b> 
        (minus sign for private groups included)<br>
        Now @getmyid_bot can be removed from the group
    </li>
</ul>
'''


class DestinationModuleConfigTelegram(DestinationModuleConfig):
    bot_token = models.CharField(max_length=64)
    chat_id = models.CharField(max_length=32)
    send_as_documents = models.BooleanField(default=False)

    MODULE_NAME = 'Telegram'
    HELP_TEXT = HELP_TEXT

    def send_media(self, media: UploadedMedia):
        media_file = media.file.open('rb')  # if settings.DEBUG else media.file.url

        async def _send():
            bot = Bot(self.bot_token)
            await bot.initialize()
            try:
                if self.send_as_documents:
                    await bot.send_document(self.chat_id, media_file, filename=media.file.name)
                else:
                    if media.is_video:
                        im = Image.open(media.thumb)
                        im.thumbnail((320, 320), Image.LANCZOS)
                        with TemporaryDirectory() as d:
                            thumb = os.path.join(d, 'thumb.jpg')
                            im.save(thumb)
                            await bot.send_video(
                                self.chat_id, media_file, media.video_length,
                                (media.caption or '')[:128],
                                width=media.video_width, height=media.video_height,
                                supports_streaming=True,
                                thumbnail=media.thumb.open('rb'),
                                read_timeout=60, write_timeout=60)
                    else:
                        await bot.send_photo(
                            self.chat_id, media_file,
                            (media.caption or '')[:MessageLimit.CAPTION_LENGTH])
            finally:
                await bot.shutdown()

        # The caller is a synchronous Celery task running in a prefork worker
        # with no running event loop, so a fresh loop per call is safe.
        asyncio.run(_send())

    class Meta:
        verbose_name = verbose_name_plural = 'Destination module config Telegram'
