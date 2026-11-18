import discord
from discord.ext.commands import Bot
from django.conf import settings
from django.core.management import BaseCommand


def create_bot() -> Bot:
    # Slash commands do not read message content, so no privileged intent is
    # needed. Default intents are enough; members/presences stay disabled.
    intents = discord.Intents.default()
    bot = Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print('Logged on as', bot.user)
        await bot.tree.sync()

    @bot.tree.command(name='chatid', description='Get DM chat ID')
    async def chatid(interaction: discord.Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                'Use this command in a DM with the bot.', ephemeral=True
            )
            return
        dm_channel = await interaction.user.create_dm()
        await interaction.response.send_message(f'`{dm_channel.id}`', ephemeral=True)

    return bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = create_bot()
        bot.run(settings.DISCORD_BOT_TOKEN)
