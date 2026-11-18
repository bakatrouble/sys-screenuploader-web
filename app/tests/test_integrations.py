"""Offline tests for the Telegram and Discord integrations (no network)."""

from unittest.mock import AsyncMock, patch

from django.core.files.base import ContentFile
from telegram.constants import MessageLimit

from app.management.commands.start_discord_bot import create_bot
from app.models import UploadedMedia
from app.modules.telegram import DestinationModuleConfigTelegram
from app.tests import LocalTestCase, make_jpeg_bytes


def make_media(is_video=False, caption=None, with_thumb=False):
    media = UploadedMedia(is_video=is_video, caption=caption)
    media.file.save('shot.jpg', ContentFile(make_jpeg_bytes()), save=False)
    if with_thumb:
        media.thumb.save('thumb.jpg', ContentFile(make_jpeg_bytes(size=(640, 480))), save=False)
    return media


class TelegramModuleTests(LocalTestCase):
    def patch_bot(self, mock_bot_cls):
        """Return a mock Bot whose coroutine methods are AsyncMocks."""
        bot = mock_bot_cls.return_value
        bot.initialize = AsyncMock()
        bot.shutdown = AsyncMock()
        bot.send_photo = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_video = AsyncMock()
        return bot

    def test_send_photo_truncates_caption(self):
        config = DestinationModuleConfigTelegram(
            bot_token='token', chat_id='123', send_as_documents=False)
        media = make_media(caption='x' * (MessageLimit.CAPTION_LENGTH + 500))
        with patch('app.modules.telegram.Bot') as mock_bot_cls:
            bot = self.patch_bot(mock_bot_cls)
            config.send_media(media)
        bot.send_photo.assert_called_once()
        args, kwargs = bot.send_photo.call_args
        self.assertEqual(args[0], '123')
        self.assertEqual(args[2], 'x' * MessageLimit.CAPTION_LENGTH)
        bot.send_document.assert_not_called()
        bot.send_video.assert_not_called()
        bot.initialize.assert_awaited_once()
        bot.shutdown.assert_awaited_once()

    def test_send_as_document(self):
        config = DestinationModuleConfigTelegram(
            bot_token='token', chat_id='123', send_as_documents=True)
        media = make_media()
        with patch('app.modules.telegram.Bot') as mock_bot_cls:
            bot = self.patch_bot(mock_bot_cls)
            config.send_media(media)
        bot.send_document.assert_called_once()
        args, kwargs = bot.send_document.call_args
        self.assertEqual(args[0], '123')
        self.assertEqual(kwargs.get('filename'), media.file.name)
        bot.send_photo.assert_not_called()
        bot.send_video.assert_not_called()
        bot.initialize.assert_awaited_once()
        bot.shutdown.assert_awaited_once()

    def test_send_video_uses_lanczos_thumbnail(self):
        config = DestinationModuleConfigTelegram(
            bot_token='token', chat_id='123', send_as_documents=False)
        media = make_media(is_video=True, caption='clip', with_thumb=True)
        media.video_length = 10
        media.video_width = 640
        media.video_height = 480
        with patch('app.modules.telegram.Bot') as mock_bot_cls:
            bot = self.patch_bot(mock_bot_cls)
            config.send_media(media)  # raises AttributeError on Pillow>=10 if ANTIALIAS is used
        bot.send_video.assert_called_once()
        args, kwargs = bot.send_video.call_args
        self.assertEqual(args[0], '123')
        self.assertEqual(args[2], 10)
        self.assertEqual(kwargs.get('width'), 640)
        self.assertEqual(kwargs.get('height'), 480)
        self.assertTrue(kwargs.get('supports_streaming'))
        self.assertEqual(kwargs.get('read_timeout'), 60)
        self.assertEqual(kwargs.get('write_timeout'), 60)
        self.assertIn('thumbnail', kwargs)
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        bot.initialize.assert_awaited_once()
        bot.shutdown.assert_awaited_once()


class DiscordBotTests(LocalTestCase):
    def test_command_set_registered_without_connecting(self):
        bot = create_bot()
        self.assertEqual(bot.command_prefix, '!')
        # chatid is a slash command, so it lives on the app command tree.
        self.assertIsNotNone(bot.tree.get_command('chatid'))
        # No privileged intents: slash commands do not read message content.
        self.assertFalse(bot.intents.message_content)
        self.assertFalse(bot.intents.members)
        self.assertFalse(bot.intents.presences)
