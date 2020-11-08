import mysql.connector
import discord
import asyncio
import json
import os
import logging
import datetime
import re


class ScheduleBot(discord.Client):

    async def on_ready(self):
        logger.info('Bot is running.')
        logger.info(f'Logged in as: "{self.user}"')
        for server in self.guilds:
            logger.info(f'Logged into server: "{server.name}" (id: {server.id}, members: {server.member_count})')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!brassbeast help"))

    async def on_server_join(self, server):
        logger.info(f'Joined new server: "{server.name}" (id: {server.id}, members: {server.member_count})')

    def db_insert(self, sql, values):
        mycursor = database.cursor()
        mycursor.execute(f"""set @@session.time_zone = '{credentials['sql_details']['time_zone']}'""")
        mycursor.execute(sql, values)
        database.commit()
        mycursor.close()

    def db_select(self, sql, values):
        mycursor = database.cursor()
        mycursor.execute(f"""set @@session.time_zone = '{credentials['sql_details']['time_zone']}'""")
        mycursor.execute(sql, values)
        result = mycursor.fetchall()
        mycursor.close()
        return result

    async def on_message(self, message):
        # Don't respond to message from itself
        if message.author == self.user:
            return
        # Don't respond to messages from other bots
        if message.author.bot:
            return

        bot_message_prefix = '!brassbeast'
        if message.content.startswith(bot_message_prefix):
            args = message.content[len(bot_message_prefix) + 1:].split(' ')
            command = args[0]
            if command == 'help':
                help_message = (':robot: **Brass Beast Heavy**\n\n'
                                'Brass Beast Heavy is firing backwards into spawn.\n'
                                'More information: https://github.com/rpower/brass-beast-bot')
                logger.info(f'Listed help message in server {message.guild.id}')
                await message.channel.send(help_message)
            elif command == 'testsend':
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
                embed.set_footer(text="Use !brassbeast addrole [emoji] [role name] or !brassbeast removerole [role name] to add or remove roles from this list")
                new_message = await message.channel.send(embed=embed)

                # Add reactions to original message
                for emoji in relevant_reactions:
                    await new_message.add_reaction(emoji)

                # Delete original message
                await message.delete()
            elif command == 'addrole':
                content = " ".join(args[1:])
                role_emoji = content[0]
                role_name = content[2:]

                # Create role
                await message.guild.create_role(name=role_name)
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
                    embed.set_footer(
                        text="Use !brassbeast addrole [emoji] [role name] or !brassbeast removerole [role name] to add or remove roles from this list")
                    await role_react_message.edit(embed=embed)

                    # Add reaction
                    await role_react_message.add_reaction(role_emoji)

                    # Delete original message
                    await message.delete()
            elif command == 'removerole':
                role_name_to_delete = " ".join(args[1:])

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

                # If person making request is not admin, then ignore
                if not message.author.top_role.permissions.administrator:
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
                    embed.set_footer(
                        text="Use !brassbeast addrole [emoji] [role name] or !brassbeast removerole [role name] to add or remove roles from this list")
                    await role_react_message.edit(embed=embed)

                # Delete original message
                await message.delete()
            else:
                logger.info(f'Invalid command in server {message.guild.id}. Attempted message: "{message.content}"')

        # Log to server
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = f"""
        insert into {credentials['sql_details']['table_name']} (datetime, server, action, user_id, user_name, channel) values (%s, %s, %s, %s, %s, %s)
        """
        val = (current_time, message.guild.id, 'message', message.author.id, message.author.display_name, message.channel.id)
        logger.info(f'Logged message in server {message.guild.id}')
        self.db_insert(sql, val)

    async def on_voice_state_update(self, member, before, after):
        # Don't listen to other bots
        if member.bot:
            return

        # Joined voice channel
        if before.channel is None and after.channel is not None:
            # Log to server
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = f"""
                insert into {credentials['sql_details']['table_name']} (datetime, server, action, user_id, user_name, channel) values (%s, %s, %s, %s, %s, %s)
                """
            val = (current_time, after.channel.guild.id, 'voice', member.id, member.display_name, after.channel.id)
            logger.info(f'Logged voice in server {after.channel.guild.id}')
            self.db_insert(sql, val)

    async def on_member_join(self, member):
        # Don't listen to other bots
        if member.bot:
           return

        # Log to server
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = f"""
            insert into {credentials['sql_details']['table_name']} (datetime, server, action, user_id, user_name, channel) values (%s, %s, %s, %s, %s, %s)
            """
        val = (current_time, member.guild.id, 'join', member.id, member.display_name, None)
        logger.info(f'Logged join to server {member.guild.id}')
        self.db_insert(sql, val)

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

if os.path.isfile('credentials.json'):
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

        # Database
        database = mysql.connector.connect(
            host=credentials['sql_details']['host'],
            user=credentials['sql_details']['username'],
            passwd=credentials['sql_details']['pw'],
            database=credentials['sql_details']['db_name']
        )

        bot = ScheduleBot(intents=intents)
        application = bot
        bot.run(credentials['discord']['bot_token'])
else:
    logger.info(f'Could not find credentials.json')

