import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context
from django.conf import settings
from django.core.management import BaseCommand


def create_bot() -> Bot:
    # discord.py 2.x requires explicit intents. Default intents cover
    # guild/DM message events; message_content (privileged) is additionally
    # needed so prefix commands such as !chatid can read message text.
    # members/presences are not needed and stay disabled.
    intents = discord.Intents.default()
    intents.message_content = True
    bot = Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print('Logged on as', bot.user)

    @bot.command(help='Get DM chat ID')
    @commands.dm_only()
    async def chatid(ctx: Context):
        dm_channel = await ctx.author.create_dm()
        await ctx.send(f'`{dm_channel.id}`')

    return bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = create_bot()
        bot.run(settings.DISCORD_BOT_TOKEN)
