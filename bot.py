import logging
import asyncio
from discord.ext import commands
import discord
import os
from dotenv import load_dotenv

_log = logging.getLogger('discord.py')


async def get_all_active_voices(bot):
    voice_channels = await get_all_voice_members(bot)
    users = []
    for guild, channels in voice_channels.items():
        for channel, members in channels.items():
            for member in members:
                users.append(member)
    return set(users)


async def get_all_voice_members(bot: discord.Client) -> \
        dict[discord.Guild, dict[discord.VoiceChannel, list[discord.Member]]]:
    """Get all voice channels and their members on all guilds the bot can view."""
    voice_channels = {}
    for guild in bot.guilds:
        members = await get_voice_channels(guild)
        voice_channels[guild] = members
    return voice_channels


async def get_voice_channels(guild: discord.Guild) -> dict[discord.VoiceChannel, list[discord.Member]]:
    """Get all voice channels and their members in a guild."""
    voice_channels = {}
    for channel in guild.voice_channels:
        members = await get_voice_members(channel)
        voice_channels[channel] = members
    return voice_channels


async def get_voice_members(channel: discord.VoiceChannel) -> list[discord.Member]:
    """Get all members currently in a voice channel."""
    members = []
    for member in channel.members:
        # Check if member is connected to voice
        if member.voice and member.voice.channel == channel:
            members.append(member)
    return members


async def get_all_ghosts(bot):
    lurkers = []
    for user in await get_all_active_voices(bot):
        if user.status not in [discord.Status.idle, discord.Status.online, discord.Status.do_not_disturb]:
            lurkers.append(user)
    return lurkers


async def kick_ghost(lurkers):
    for member in lurkers:
        await member.send("Being a ghost. You have been kicked from the server.")
        await member.kick(reason="Being a ghost")


class AntiGhostBot(discord.ext.commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        self.timer_interval = 2  # Check for lurkers every 60 seconds
        self.timer_thread_r = True

    def __del__(self):
        self.timer_thread_r = False

    async def on_ready(self):
        _log.info('Logged on as {0}!'.format(self.user))
        self.loop.create_task(self.check_lurkers())

    async def check_lurkers(self):
        while self.timer_thread_r:
            # noinspection PyBroadException
            try:
                lurkers = await get_all_ghosts(self)
                if lurkers:
                    _log.info(f"Ghosts found: {', '.join(member.name for member in lurkers)}")
                    await kick_ghost(lurkers)
            except Exception as _:
                ...
            await asyncio.sleep(self.timer_interval)


if __name__ == "__main__":
    client = AntiGhostBot(command_prefix="!", intents=discord.Intents().all())
    load_dotenv('sample.env')
    client.run(os.getenv('BOT-TOKEN'))
