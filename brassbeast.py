import discord
import json
import logging
import datetime
import re
from music import *
from database import *

class ScheduleBot(discord.Client):

    async def on_ready(self):
        logger.info('Bot is running.')
        logger.info(f'Logged in as: "{self.user}"')
        for server in self.guilds:
            logger.info(f'Logged into server: "{server.name}" (id: {server.id}, members: {server.member_count})')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!brassbeast help"))

    async def on_server_join(self, server):
        logger.info(f'Joined new server: "{server.name}" (id: {server.id}, members: {server.member_count})')

    async def on_message(self, message):
        # Don't respond to message from itself
        if message.author == self.user:
            return
        # Don't respond to messages from other bots
        if message.author.bot:
            return

        bot_message_prefix_list = ['!bb', '!brassbeast']
        if message.content.startswith(tuple(bot_message_prefix_list)):
            args = message.content.split(' ')

            try:
                command = args[1]
            except IndexError:
                command = ''
                await message.channel.send('Incorrect command.')

            if command == 'help':
                help_message = (':robot: **Brass Beast Heavy**\n\n'
                                'Brass Beast Heavy is firing backwards into spawn.\n'
                                'More information: https://github.com/rpower/brass-beast-bot')
                logger.info(f'Listed help message in server {message.guild.id}')
                await message.channel.send(help_message)
            elif command == 'rolesmessage':
                # If Brass Beast server or sandbox server
                allow_list_servers = credentials['allow_list_servers']
                allow_list_servers = {int(key): value for key, value in allow_list_servers.items()}
                if message.guild.id in allow_list_servers:
                    if message.channel.id != allow_list_servers[message.guild.id]['reaction_channel']:
                        return

                list_of_relevant_roles = {
                    'Among Us': '🔪',
                    'Apex Legends': '🤖',
                    'Board Gamers': '🎲',
                    'Minecraft': '🪓'
                }
                server_role_list = message.guild.roles
                server_role_name_list = [x.name for x in server_role_list]

                roles_to_add_to_description = []
                relevant_reactions = []

                for server_role in server_role_list:
                    for relevant_role in list_of_relevant_roles.keys():
                        if relevant_role in server_role.name:
                            roles_to_add_to_description.append(list_of_relevant_roles[relevant_role] + ' ' + server_role.mention)
                            relevant_reactions.append(list_of_relevant_roles[relevant_role])

                roles_to_add_to_description = '\n'.join(roles_to_add_to_description)

                description = 'React to this message for roles\n\n' + roles_to_add_to_description
                embed = discord.Embed(color=12745742, description=description)
                embed.set_author(name='React for roles')
                embed.set_footer(text='')
                embed.add_field(
                    name='How do I add a role?',
                    value='https://github.com/rpower/brass-beast-bot',
                    inline=False
                )
                new_message = await message.channel.send(embed=embed)

                # Add reactions to original message
                for emoji in relevant_reactions:
                    await new_message.add_reaction(emoji)

                # Delete original message
                await message.delete()
            elif command == 'addrole':
                content = " ".join(args[2:])
                role_emoji = content[0]
                role_name = content[2:]

                # Create role
                await message.guild.create_role(name=role_name, mentionable=True)
                newly_created_role = discord.utils.get(message.guild.roles, name=role_name)
                # Look for role react main message
                fetchMessage = await message.channel.history().find(lambda m: (m.author == self.user))
                if fetchMessage.embeds[0].author.name == 'React for roles':
                    role_react_message_id = fetchMessage.id
                    role_react_message = await message.channel.fetch_message(role_react_message_id)
                    role_react_message_contents = role_react_message.embeds[0].description

                    original_message_contents = role_react_message_contents.split('\n')[:2]
                    roles_in_message = role_react_message_contents.split('\n')[2:]
                    roles_in_message.append(role_emoji + ' ' + newly_created_role.mention)

                    new_description = original_message_contents + roles_in_message
                    new_description = '\n'.join(new_description)
                    embed = discord.Embed(color=12745742, description=new_description)
                    embed.set_author(name='React for roles')
                    embed.set_footer(text='')
                    embed.add_field(
                        name='How do I add a role?',
                        value='https://github.com/rpower/brass-beast-bot',
                        inline=False
                    )
                    await role_react_message.edit(embed=embed)

                    # Add text channel
                    # Convert role name into text channel name
                    new_role_channel_name = role_name.lower().replace(' ', '-')

                    # Get 'Vidya Game' text channel category
                    new_role_channel_category_name = 'Vidya Games'
                    new_role_channel_category = discord.utils.get(message.guild.categories, name=new_role_channel_category_name)

                    # Create text channel
                    overwrites = {
                        message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        newly_created_role: discord.PermissionOverwrite(read_messages=True)
                    }
                    await message.guild.create_text_channel(new_role_channel_name, category=new_role_channel_category, overwrites=overwrites)

                    # Add reaction
                    await role_react_message.add_reaction(role_emoji)

                    # Delete original message
                    await message.delete()
            elif command == 'removerole':
                role_name_to_delete = " ".join(args[2:])

                list_of_protected_roles = [
                    'Admins',
                    'Heavies',
                    'Brass Beast Heavy',
                    'Pancake',
                    'Server Booster',
                    'Randos',
                    'Event Scheduler',
                    '@everyone'
                ]

                # If role to delete is in protected list, then ignore
                if role_name_to_delete in list_of_protected_roles:
                    return

                # Look for role react main message
                fetchMessage = await message.channel.history().find(lambda m: (m.author == self.user))

                if fetchMessage.embeds[0].author.name == 'React for roles':
                    role_react_message_id = fetchMessage.id
                    role_react_message = await message.channel.fetch_message(role_react_message_id)
                    role_react_message_contents = role_react_message.embeds[0].description

                    original_message_contents = role_react_message_contents.split('\n')[:1]
                    roles_in_message = role_react_message_contents.split('\n')[1:]

                    list_of_roles = message.guild.roles
                    for role in list_of_roles:
                        if role.name == role_name_to_delete:
                            role_id_to_remove = str(role.id)
                            # Remove role
                            await role.delete()
                            for role in roles_in_message:
                                if role_id_to_remove in role:
                                    roles_in_message.remove(role)

                                    # Clear reactions
                                    emoji_to_remove = role[0]
                                    await role_react_message.clear_reaction(emoji_to_remove)

                    new_description = original_message_contents + roles_in_message
                    new_description = '\n'.join(new_description)
                    embed = discord.Embed(color=12745742, description=new_description)
                    embed.set_author(name='React for roles')
                    embed.set_footer(text='')
                    embed.add_field(
                        name='How do I add a role?',
                        value='https://github.com/rpower/brass-beast-bot',
                        inline=False
                    )
                    await role_react_message.edit(embed=embed)

                # Delete original message
                await message.delete()
            elif command == 'cleanup':
                try:
                    # Look for role react main message
                    fetchMessage = await message.channel.history().find(lambda m: (m.author == self.user))

                    if fetchMessage.embeds[0].author.name == 'React for roles':
                        role_react_message_id = fetchMessage.id
                        role_react_message = await message.channel.fetch_message(role_react_message_id)
                        role_react_message_contents = role_react_message.embeds[0].description

                        original_message_contents = role_react_message_contents.split('\n')[:1]
                        roles_in_message = role_react_message_contents.split('\n')[1:]
                        list_of_roles = message.guild.roles
                        list_of_roles_ids_in_server = []

                        for role in list_of_roles:
                            list_of_roles_ids_in_server.append(str(role.id))

                        logger.info(f'Cleaning up. roles_in_message = {roles_in_message}')
                        logger.info(f'Cleaning up. list_of_roles_ids_in_server = {list_of_roles_ids_in_server}')

                        for role in roles_in_message:
                            logger.info(f'Cleaning up. role = {role}')
                            if role != '':
                                role_id_in_message = re.match('.*<@&(.*)>.*', role).group(1)
                                if role_id_in_message not in list_of_roles_ids_in_server:
                                    roles_in_message.remove(role)

                        new_description = original_message_contents + roles_in_message
                        new_description = '\n'.join(new_description)
                        embed = discord.Embed(color=12745742, description=new_description)
                        embed.set_author(name='React for roles')
                        embed.set_footer(text='')
                        embed.add_field(
                            name = 'How do I add a role?',
                            value = 'https://github.com/rpower/brass-beast-bot',
                            inline = False
                        )
                        await role_react_message.edit(embed=embed)
                    # Delete original message
                    await message.delete()
                except Exception as e:
                    logger.info(f'Error cleaning up in {message.guild.id}. Error: {e}')
            elif command == 'sendmemberdm':
                dm_message = ('Hey! :wave:\n\n'
                              'This is just a friendly automated message from one of the bots on the **TF2 Brass Beasts Heavies** Discord server. In the last 2 months you haven\'t used any of the text chats or the voice chats.\n\n'
                              'You haven\'t done anything wrong and are still well-loved but we try to keep the member list in the server up-to-date. If you want to stay in the server drop a message in one of the text chats or use one of the voice chats, we\'re reviewing the member list in a couple of weeks so you\'ve got plenty of time!\n\n'
                              '~ :robot:  Brass Beast Heavy Bot')

                # Delete original message
                await message.delete()

                # Send DMs
                list_of_members_to_dm = args[2:]
                for member_to_dm in list_of_members_to_dm:
                    member_to_dm_id = int(re.search(r'\d+', member_to_dm).group(0))
                    member_to_dm_user = await self.fetch_user(member_to_dm_id)
                    # Don't try to send DMs to bots
                    if not member_to_dm_user.bot:
                        logger.info(f'Sent DM to {member_to_dm_user}')
                        await member_to_dm_user.send(dm_message)
            elif command == 'play':
                allow_list_servers = credentials['allow_list_servers']
                allow_list_servers = {int(key): value for key, value in allow_list_servers.items()}

                try:
                    url = args[2]
                    # Check URL domain
                    yt_url_regex = r'.*www\.youtube\.com\/watch\?v=.*|.*youtu\.be\/.*'
                    yt_url_match = re.match(yt_url_regex, url)
                    if message.channel.id != allow_list_servers[message.guild.id]['music_channel']:
                        incorrect_channel_message = f'Incorrect channel, try <#{allow_list_servers[message.guild.id]["music_channel"]}>.'
                        await message.channel.send(incorrect_channel_message)
                    elif yt_url_match:
                        await self.join_voice_channel(message, url)
                    else:
                        incorrect_url_message = 'Incorrect URL, make sure it\'s a `youtube.com` or `youtu.be` link.'
                        await message.channel.send(incorrect_url_message)
                except IndexError:
                    await message.channel.send(incorrect_url_message)
            elif command == 'stop':
                await self.stop_music(message)
            else:
                logger.info(f'Invalid command in server {message.guild.id}. Attempted message: "{message.content}"')

        # Flag warning if trying to use old music prefix
        old_pancake_prefix_list = ['p!', '!play']
        if message.content.startswith(tuple(old_pancake_prefix_list)):
            await message.channel.send(
                ':pancakes: :wave: Pancake is no more! ' \
                'Use `!bb play` or `!bb stop` to play / stop music. ' \
                'Example: `!bb play https://www.youtube.com/watch?v=2yf35s55Uyg`'
            )

        # Log to server
        add_log_entry(datetime.datetime.now(), message.guild.id, 'message', message.author.id, message.author.display_name, message.channel.id)
        logger.info(f'Logged message in server {message.guild.id}')

    async def join_voice_channel(self, message, url):
        logger.info(f'Trying to play music in server {message.guild.id}')
        if message.author.voice:
            destination = message.author.voice.channel
            if destination:
                bot_connection = message.author.guild.voice_client
                if bot_connection:
                    # Move to new channel if bot was connected to a previous one
                    await bot_connection.move_to(destination)
                else:
                    # If bot was not connected, connect it
                    await destination.connect()
            try:
                await self.play_music(message, url)
            except Exception as e:
                logger.info(f'Error playing message in server {message.guild.id}. Error: {e}')
                await message.channel.send(f'Couldn\'t play music: {e}')
                try:
                    await message.author.guild.voice_client.disconnect()
                except Exception as e:
                    logger.info(f'Error leaving voice channel in server {message.guild.id}. Error: {e}')
        else:
            await message.channel.send('Need to be in a voice channel.')
        return

    async def play_music(self, message, url):
        try:
            source = await YTDLSource.create_source(message, url)
        except YTDLError as e:
            await message.channel.send(
                'An error occurred while processing this request: {}'.format(str(e)))
        else:
            now_playing = discord.FFmpegPCMAudio(source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
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

    async def stop_music(self, message):
        voice_client = message.author.guild.voice_client
        if not voice_client:
            await message.channel.send('I\'m not in a voice channel.')
        elif message.author.voice:
            voice_client.stop()
            await voice_client.disconnect()
        else:
            await message.channel.send('Need to be in a voice channel.')
        return

    async def on_voice_state_update(self, member, before, after):
        # Don't listen to other bots
        if member.bot:
            return

        # Joined voice channel
        if before.channel is None and after.channel is not None:
            # Log to server
            add_log_entry(datetime.datetime.now(), after.channel.guild.id, 'voice', member.id, member.display_name, after.channel.id)
            logger.info(f'Logged voice in server {after.channel.guild.id}')

        # User leaves voice channel
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

    async def on_member_join(self, member):
        # Log to server
        add_log_entry(datetime.datetime.now(), member.guild.id, 'join', member.id, member.display_name, None)
        logger.info(f'Logged join to server {member.guild.id}')

        # If Brass Beast server or sandbox server
        allow_list_servers = credentials['allow_list_servers']
        allow_list_servers = {int(key): value for key, value in allow_list_servers.items()}
        if member.guild.id in allow_list_servers:
            # Send message in channel
            join_notification_channel_id = allow_list_servers[member.guild.id]['channel_id']
            join_notification_channel = self.get_channel(join_notification_channel_id)
            if join_notification_channel == None:
                logger.info(f'Trying to log new member joining. Could not find channel {join_notification_channel_id} in server {member.guild.id}')
            else:
                embed = discord.Embed(color = 12745742, description = f'{member.mention} {member}')
                embed.set_author(name = 'Member joined', icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                new_member_in_days = 30
                days_since_account_created = (datetime.datetime.now() - member.created_at).days
                if (days_since_account_created <= new_member_in_days):
                    embed.add_field(name = 'New Account', value = f'Created: {member.created_at.strftime("%Y-%m-%d %H:%M:%S")}', inline = False)
                embed.set_footer(text = f'ID: {member.id}')
                await join_notification_channel.send(embed = embed)

            # Give role
            new_member_role = member.guild.get_role(allow_list_servers[member.guild.id]['role_id'])
            if new_member_role == None:
                logger.info(f'Trying to assign new member role. Could not find role in server {member.guild.id}')
            else:
                await member.add_roles(new_member_role)

    async def reaction_role_change(self, payload, add_or_remove):
        channel = await self.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await self.fetch_user(payload.user_id)
        emoji = payload.emoji
        # Don't listen to other bots
        if user.bot:
            return

        # If Brass Beast server or sandbox server
        allow_list_servers = credentials['allow_list_servers']
        allow_list_servers = {int(key): value for key, value in allow_list_servers.items()}
        if message.guild.id in allow_list_servers:
            if message.channel.id != allow_list_servers[message.guild.id]['reaction_channel']:
                return

        # Look for role react main message
        fetchMessage = await message.channel.history().find(lambda m: (m.author == self.user))
        if fetchMessage.embeds[0].author.name == 'React for roles':
            role_react_message_id = fetchMessage.id

            # Ignore reacts on messages which aren't the role react message
            if message.id != role_react_message_id:
                return

            role_react_message = await message.channel.fetch_message(role_react_message_id)
            role_react_message_contents = role_react_message.embeds[0].description

            original_message_contents = role_react_message_contents.split('\n')[:1]
            roles_in_message = role_react_message_contents.split('\n')[1:]

            for role in roles_in_message:
                if str(emoji) in role:
                    role_id = int(re.search(r'\d+', role).group(0))

                    member = await channel.guild.fetch_member(payload.user_id)
                    relevant_role = member.guild.get_role(role_id)
                    if add_or_remove == 'add':
                        await member.add_roles(relevant_role)
                    elif add_or_remove == 'remove':
                        await member.remove_roles(relevant_role)

    async def on_raw_reaction_add(self, payload):
        await self.reaction_role_change(payload, 'add')

    async def on_raw_reaction_remove(self, payload):
        await self.reaction_role_change(payload, 'remove')

    async def on_invite_create(self, payload):
        invite_creator = payload.inviter
        invite_code = payload.id

        # If Brass Beast server or sandbox server
        allow_list_servers = credentials['allow_list_servers']
        allow_list_servers = {int(key): value for key, value in allow_list_servers.items()}
        if payload.guild.id in allow_list_servers:
            # Send message in channel
            invite_notification_channel_id = allow_list_servers[payload.guild.id]['channel_id']
            invite_notification_channel = self.get_channel(invite_notification_channel_id)
            embed = discord.Embed(color=255, description=f'{invite_creator.mention} {invite_creator}')
            embed.set_author(name='Invite created', icon_url=invite_creator.avatar_url)
            embed.set_thumbnail(url=invite_creator.avatar_url)
            embed.set_footer(text=f'Invite ID: {invite_code}')
            await invite_notification_channel.send(embed=embed)

with open('credentials.json') as credentials_file:
    intents = discord.Intents.default()
    intents.members = True

    credentials = json.loads(credentials_file.read())

    # Logging
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    handler = logging.FileHandler('bot.log')
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    bot = ScheduleBot(intents=intents)
    application = bot
    bot.run(credentials['discord']['bot_token'])

