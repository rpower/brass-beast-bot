import disnake
from disnake.ext import commands
import os
import logging
from dotenv import load_dotenv
import bot_commands
import music
import database

# Environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_NOTIFICATIONS_CHANNEL_IDS = os.getenv('BOT_NOTIFICATIONS_CHANNEL_IDS').split(',')
NEW_ROLE_IDS = os.getenv('NEW_ROLE_IDS').split(',')
MUSIC_CHANNEL_IDS = os.getenv('MUSIC_CHANNEL_IDS').split(',')

# Logging
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler = logging.FileHandler('bot.log')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Intents
intents = disnake.Intents.default()
intents.messages = True
intents.members = True

bot_command_prefix = 'bb'
bot = commands.Bot(command_prefix =f'!{bot_command_prefix} ', help_command = None, intents = intents)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        logger.info(f'Logged into server: "{guild.name}" (id: {guild.id}, members: {guild.member_count})')
    await bot.change_presence(activity=disnake.Activity(
        type=disnake.ActivityType.listening,
        name=f"!{bot_command_prefix} help"
    ))

@bot.event
async def on_guild_join(guild):
    logger.info(f'Joined server: "{guild.name}" (id: {guild.id}, members: {guild.member_count})')

@bot.event
async def on_invite_create(payload):
    await bot_commands.send_invite_notification(bot, payload, BOT_NOTIFICATIONS_CHANNEL_IDS)

@bot.event
async def on_member_join(member):
    await bot_commands.send_new_member_notification(bot, member, BOT_NOTIFICATIONS_CHANNEL_IDS, NEW_ROLE_IDS)

@bot.event
async def on_raw_reaction_add(payload):
    await bot_commands.change_role(bot, payload, is_add = True)

@bot.event
async def on_raw_reaction_remove(payload):
    await bot_commands.change_role(bot, payload, is_add = False)

@bot.event
async def on_message(message):
    await database.log_message(message)
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    await database.log_voice(member, before, after)
    await music.check_for_listeners(before)

@bot.command()
async def help(ctx):
    await bot_commands.display_help_message(ctx)

@bot.command()
async def rolesmessage(ctx):
    await bot_commands.generate_roles_message(ctx)

@bot.command()
async def addrole(ctx, arg1, arg2):
    await bot_commands.add_role(ctx, arg1, arg2)

@bot.command()
async def removerole(ctx, arg1):
    await bot_commands.remove_role(ctx, arg1)

@bot.command()
async def cleanup(ctx):
    await bot_commands.cleanup_roles_message(ctx)

@bot.command()
async def play(ctx, arg1):
    await music.check_music(bot, ctx, arg1, MUSIC_CHANNEL_IDS)

@bot.command()
async def stop(ctx):
    await music.stop_music(ctx)

bot.run(BOT_TOKEN)

