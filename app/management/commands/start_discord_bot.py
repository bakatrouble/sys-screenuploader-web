from discord.ext import commands
from discord.ext.commands import Bot, Context
from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = Bot('!')

        @bot.event
        async def on_ready():
            print('Logged on as', bot.user)

        @bot.command(help='Get DM chat ID')
        @commands.dm_only()
        async def chatid(ctx: Context):
            dm_channel = await ctx.author.create_dm()
            await ctx.send(f'`{dm_channel.id}`')

        bot.run(settings.DISCORD_BOT_TOKEN)
