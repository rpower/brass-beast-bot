import yt_dlp
import re
import disnake
import logging
import asyncio
import functools
from disnake.ext import commands

# Logging
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler = logging.FileHandler('bot.log')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Silence useless bug reports messages
yt_dlp.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(disnake.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, message, source: disnake.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = message.author
        self.channel = message.channel
        self.stream_url = data.get('url')
        self.title = data.get('title')

    def __str__(self):
        return '**{0.title}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, disnake.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

async def play_music(message, youtube_url, slash_command=False):
    if slash_command:
        # Slash command
        try:
            source = await YTDLSource.create_source(message, youtube_url)
        except YTDLError as e:
            await message.send(
                'An error occurred while processing this request: {}'.format(str(e)))
        else:
            now_playing = disnake.FFmpegPCMAudio(source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
            voice_client = message.guild.voice_client

            if voice_client:
                # Stops current playing song if there is one
                voice_client.stop()
                # Starts playing song
                voice_client.play(now_playing)

                youtube_video_title = str(source)
                await message.send(f'Playing {youtube_video_title}\n\n{youtube_url}')

            while voice_client.is_playing():
                await asyncio.sleep(1)
            try:
                await voice_client.disconnect()
                voice_client.stop()
            except AttributeError:
                pass
    else:
        # Legacy command
        try:
            source = await YTDLSource.create_source(message, youtube_url)
        except YTDLError as e:
            await message.channel.send(
                'An error occurred while processing this request: {}'.format(str(e)))
        else:
            now_playing = disnake.FFmpegPCMAudio(source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
            voice_client = message.author.guild.voice_client

            if voice_client:
                # Stops current playing song if there is one
                voice_client.stop()
                # Starts playing song
                voice_client.play(now_playing)

                await message.channel.send('Playing {}'.format(str(source)))

            while voice_client.is_playing():
                await asyncio.sleep(1)
            try:
                await voice_client.disconnect()
                voice_client.stop()
            except AttributeError:
                pass

async def stop_music(ctx, slash_command=False):
    if slash_command:
        voice_client = ctx.author.guild.voice_client
        if not voice_client:
            await ctx.send('I\'m not in a voice channel.')
        elif ctx.author.voice:
            voice_client.stop()
            await voice_client.disconnect()
            await ctx.send('Stopped :pinching_hand:')
        else:
            await ctx.send('Need to be in a voice channel.')
        return
    else:
        voice_client = ctx.message.author.guild.voice_client
        if not voice_client:
            await ctx.message.channel.send('I\'m not in a voice channel.')
        elif ctx.message.author.voice:
            voice_client.stop()
            await voice_client.disconnect()
        else:
            await ctx.message.channel.send('Need to be in a voice channel.')
        return

async def join_voice_channel(ctx, youtube_url, slash_command=False):
    if slash_command:
        if ctx.author.voice:
            destination = ctx.author.voice.channel
            if destination:
                bot_connection = ctx.author.guild.voice_client
                if bot_connection:
                    # Move to new channel if bot was connected to a previous one
                    await bot_connection.move_to(destination)
                else:
                    # If bot was not connected, connect it
                    await destination.connect()
            try:
                await ctx.response.defer()
                await play_music(ctx, youtube_url, slash_command=slash_command)
            except Exception as e:
                logger.info(f'Error playing message in server {ctx.guild.id}. Error: {e}')
                await ctx.send(f'Couldn\'t play music: {e}')
                try:
                    await ctx.author.guild.voice_client.disconnect()
                except Exception as e:
                    logger.info(f'Error leaving voice channel in server {ctx.guild.id}. Error: {e}')
        else:
            await ctx.send('Need to be in a voice channel.')
    else:
        if ctx.message.author.voice:
            destination = ctx.message.author.voice.channel
            if destination:
                bot_connection = ctx.message.author.guild.voice_client
                if bot_connection:
                    # Move to new channel if bot was connected to a previous one
                    await bot_connection.move_to(destination)
                else:
                    # If bot was not connected, connect it
                    await destination.connect()
            try:
                await play_music(ctx.message, youtube_url)
            except Exception as e:
                logger.info(f'Error playing message in server {ctx.message.guild.id}. Error: {e}')
                await ctx.message.channel.send(f'Couldn\'t play music: {e}')
                try:
                    await ctx.message.author.guild.voice_client.disconnect()
                except Exception as e:
                    logger.info(f'Error leaving voice channel in server {ctx.message.guild.id}. Error: {e}')
        else:
            await ctx.message.channel.send('Need to be in a voice channel.')

async def check_music(bot, ctx, youtube_url, music_channel_ids, slash_command=False):
    music_channel_ids = [int(i) for i in music_channel_ids]
    yt_url_regex = r'.*www\.youtube\.com\/watch\?v=.*|.*youtu\.be\/.*'
    yt_url_match = re.match(yt_url_regex, youtube_url)
    if slash_command:
        if ctx.channel.id not in music_channel_ids:
            incorrect_channel_message = f'Incorrect channel.'
            await ctx.send(incorrect_channel_message)
        elif not yt_url_match:
            incorrect_url_message = 'Incorrect URL, make sure it\'s a `youtube.com` or `youtu.be` link.'
            await ctx.send(incorrect_url_message)
        else:
            await join_voice_channel(ctx, youtube_url, slash_command=slash_command)
    else:
        if ctx.message.channel.id not in music_channel_ids:
            incorrect_channel_message = f'Incorrect channel.'
            await ctx.message.channel.send(incorrect_channel_message)
        elif not yt_url_match:
            incorrect_url_message = 'Incorrect URL, make sure it\'s a `youtube.com` or `youtu.be` link.'
            await ctx.message.channel.send(incorrect_url_message)
        else:
            await join_voice_channel(ctx, youtube_url)

async def check_for_listeners(before):
    if before.channel is not None:
        bot_connection = before.channel.guild.voice_client
        if bot_connection:
            members_in_voice_channel = before.channel.members
            count_non_bots_in_voice_channel = 0
            for voice_chatter in members_in_voice_channel:
                if not voice_chatter.bot:
                    count_non_bots_in_voice_channel += 1
            if count_non_bots_in_voice_channel == 0:
                await bot_connection.disconnect()