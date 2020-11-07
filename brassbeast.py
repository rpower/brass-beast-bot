import mysql.connector
import discord
import asyncio
import json
import os
import logging
import datetime


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
                                'More information: https://github.com/rpower/discord-server-logs')
                logger.info(f'Listed help message in server {message.guild.id}')
                await message.channel.send(help_message)
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

