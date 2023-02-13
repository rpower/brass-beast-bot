import disnake
import logging
import re
import datetime

# Logging
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler = logging.FileHandler('bot.log')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

github_link = 'https://github.com/rpower/brass-beast-bot'

async def display_help_message(ctx, slash_command=False):
    embed_title = ':robot: Brass Beast Heavy'
    embed_description = f"""
        Brass Beast Heavy is firing backwards into spawn.
        
        **COMMANDS**
        `/bb help` - Show help message.
        `/bb play https://www.youtube.com/watch?v=6lgo08Sg-fw` - Play YouTube video in voice chat.
        `/bb stop` - Stops anything playing.

        Information and examples: {github_link}
        """
    embed = disnake.Embed(title=embed_title, description=embed_description, color=disnake.Colour.from_rgb(252, 186, 3))
    if slash_command:
        logger.info(f'Listed help message in server "{ctx.guild.name}" (id: {ctx.guild.id}) '
                    f'for member "{ctx.author.name}" (id: {ctx.author.id})')
        await ctx.send(embed=embed)
    else:
        logger.info(f'Listed help message in server "{ctx.message.guild.name}" (id: {ctx.message.guild.id}) '
                    f'for member "{ctx.message.author.name}" (id: {ctx.message.author.id})')
        await ctx.message.channel.send(embed=embed)

async def generate_roles_message(ctx):
    logger.info(f'Generating roles message in server "{ctx.message.guild.name}" (id: {ctx.message.guild.id}) '
                f'for member "{ctx.message.author.name}" (id: {ctx.message.author.id})')

    list_of_relevant_roles = {
        'Among Us': '🔪',
        'Apex Legends': '🤖',
        'Board Gamers': '🎲',
        'Minecraft': '🪓'
    }
    server_role_list = ctx.message.guild.roles

    roles_to_add_to_description = []
    relevant_reactions = []

    for server_role in server_role_list:
        for relevant_role in list_of_relevant_roles.keys():
            if relevant_role in server_role.name:
                roles_to_add_to_description.append(list_of_relevant_roles[relevant_role] + ' ' + server_role.mention)
                relevant_reactions.append(list_of_relevant_roles[relevant_role])

    roles_to_add_to_description = '\n'.join(roles_to_add_to_description)

    description = 'React to this message for roles\n\n' + roles_to_add_to_description
    embed = disnake.Embed(color=12745742, description=description)
    embed.set_author(name='React for roles')
    embed.set_footer(text='')
    embed.add_field(
        name='How do I add a role?',
        value=f'{github_link}',
        inline=False
    )
    new_message = await ctx.message.channel.send(embed=embed)

    # Add reactions to original message
    for emoji in relevant_reactions:
        await new_message.add_reaction(emoji)

    # Delete original message
    await ctx.message.delete()

async def add_role(ctx, emoji, role_name):
    # Delete original message
    await ctx.message.delete()

    # Create role
    await ctx.message.guild.create_role(name=role_name, mentionable=True)
    newly_created_role = disnake.utils.get(ctx.message.guild.roles, name=role_name)
    # Look for role react main message
    fetch_message = await ctx.message.channel.history().find(lambda m: (m.author.id == m.guild.me.id))
    if fetch_message.embeds[0].author.name == 'React for roles':
        role_react_message_id = fetch_message.id
        role_react_message = await ctx.message.channel.fetch_message(role_react_message_id)
        role_react_message_contents = role_react_message.embeds[0].description

        original_message_contents = role_react_message_contents.split('\n')[:2]
        roles_in_message = role_react_message_contents.split('\n')[2:]
        roles_in_message.append(emoji + ' ' + newly_created_role.mention)

        new_description = original_message_contents + roles_in_message
        new_description = '\n'.join(new_description)
        embed = disnake.Embed(color=12745742, description=new_description)
        embed.set_author(name='React for roles')
        embed.set_footer(text='')
        embed.add_field(
            name='How do I add a role?',
            value=f'{github_link}',
            inline=False
        )
        await role_react_message.edit(embed=embed)

        # Add reaction to roles message
        await role_react_message.add_reaction(emoji)

        # Add text channel
        # Convert role name into text channel name
        new_role_channel_name = role_name.lower().replace(' ', '-')

        # Get 'Vidya Game' text channel category
        new_role_channel_category_name = 'Vidya Games'
        new_role_channel_category = disnake.utils.get(ctx.message.guild.categories, name=new_role_channel_category_name)

        # Create text channel
        overwrites = {
            ctx.message.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            newly_created_role: disnake.PermissionOverwrite(read_messages=True)
        }
        await ctx.message.guild.create_text_channel(
            new_role_channel_name,
            category=new_role_channel_category,
            overwrites=overwrites
        )

    logger.info(f'Adding role "{role_name}" in server "{ctx.message.guild.name}" (id: {ctx.message.guild.id}) '
                f'for member "{ctx.message.author.name}" (id: {ctx.message.author.id})')

async def add_role_slash(ctx, role_name, role_emoji):
    # Create role
    await ctx.guild.create_role(name=role_name, mentionable=True)
    newly_created_role = disnake.utils.get(ctx.guild.roles, name=role_name)
    # Look for role react main message
    fetch_message = await ctx.channel.history().find(lambda m: (m.author.id == m.guild.me.id))
    if fetch_message.embeds[0].author.name == 'React for roles':
        role_react_message_id = fetch_message.id
        role_react_message = await ctx.channel.fetch_message(role_react_message_id)
        role_react_message_contents = role_react_message.embeds[0].description

        original_message_contents = role_react_message_contents.split('\n')[:2]
        roles_in_message = role_react_message_contents.split('\n')[2:]
        roles_in_message.append(role_emoji + ' ' + newly_created_role.mention)

        new_description = original_message_contents + roles_in_message
        new_description = '\n'.join(new_description)
        embed = disnake.Embed(color=12745742, description=new_description)
        embed.set_author(name='React for roles')
        embed.set_footer(text='')
        embed.add_field(
            name='How do I add a role?',
            value=f'{github_link}',
            inline=False
        )
        await role_react_message.edit(embed=embed)

        # Add reaction to roles message
        await role_react_message.add_reaction(role_emoji)

        # Add text channel
        # Convert role name into text channel name
        new_role_channel_name = role_name.lower().replace(' ', '-')

        # Get 'Vidya Game' text channel category
        new_role_channel_category_name = 'Vidya Games'
        new_role_channel_category = disnake.utils.get(ctx.guild.categories, name=new_role_channel_category_name)

        # Create text channel
        overwrites = {
            ctx.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            newly_created_role: disnake.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_text_channel(
            new_role_channel_name,
            category=new_role_channel_category,
            overwrites=overwrites
        )

        response = f'Added role {role_name}.'
        await ctx.send(response, ephemeral=True)

    logger.info(f'Adding role "{role_name}" in server "{ctx.guild.name}" (id: {ctx.guild.id}) '
                f'for member "{ctx.author.name}" (id: {ctx.author.id})')

async def remove_role(ctx, role_name):
    # Delete original message
    await ctx.message.delete()

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
    if role_name in list_of_protected_roles:
        return

    # Look for role react main message
    fetch_message = await ctx.message.channel.history().find(lambda m: (m.author.id == m.guild.me.id))

    if fetch_message.embeds[0].author.name == 'React for roles':
        role_react_message_id = fetch_message.id
        role_react_message = await ctx.message.channel.fetch_message(role_react_message_id)
        role_react_message_contents = role_react_message.embeds[0].description

        original_message_contents = role_react_message_contents.split('\n')[:1]
        roles_in_message = role_react_message_contents.split('\n')[1:]

        list_of_roles = ctx.message.guild.roles
        for role in list_of_roles:
            if role.name == role_name:
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
        embed = disnake.Embed(color=12745742, description=new_description)
        embed.set_author(name='React for roles')
        embed.set_footer(text='')
        embed.add_field(
            name='How do I add a role?',
            value=f'{github_link}',
            inline=False
        )
        await role_react_message.edit(embed=embed)

    logger.info(f'Removing role "{role_name}" in server "{ctx.message.guild.name}" (id: {ctx.message.guild.id}) '
                f'for member "{ctx.message.author.name}" (id: {ctx.message.author.id})')

async def remove_role_slash(ctx, role_name):
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
    if role_name in list_of_protected_roles:
        return

    # Look for role react main message
    fetch_message = await ctx.channel.history().find(lambda m: (m.author.id == m.guild.me.id))

    if fetch_message.embeds[0].author.name == 'React for roles':
        role_react_message_id = fetch_message.id
        role_react_message = await ctx.channel.fetch_message(role_react_message_id)
        role_react_message_contents = role_react_message.embeds[0].description

        original_message_contents = role_react_message_contents.split('\n')[:1]
        roles_in_message = role_react_message_contents.split('\n')[1:]

        list_of_roles = ctx.guild.roles
        for role in list_of_roles:
            if role.name == role_name:
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
        embed = disnake.Embed(color=12745742, description=new_description)
        embed.set_author(name='React for roles')
        embed.set_footer(text='')
        embed.add_field(
            name='How do I add a role?',
            value=f'{github_link}',
            inline=False
        )
        await role_react_message.edit(embed=embed)

        response = f'Removed role {role_name}.'
        await ctx.send(response, ephemeral=True)

    logger.info(f'Removing role "{role_name}" in server "{ctx.guild.name}" (id: {ctx.guild.id}) '
                f'for member "{ctx.author.name}" (id: {ctx.author.id})')

async def cleanup_roles_message(ctx):
    logger.info(f'Cleaning up roles message in server "{ctx.message.guild.name}" (id: {ctx.message.guild.id}) '
                f'for member "{ctx.message.author.name}" (id: {ctx.message.author.id})')

    try:
        # Delete original message
        await ctx.message.delete()

        # Look for role react main message
        fetch_message = await ctx.message.channel.history().find(lambda m: (m.author.id == m.guild.me.id))

        if fetch_message.embeds[0].author.name == 'React for roles':
            role_react_message_id = fetch_message.id
            role_react_message = await ctx.message.channel.fetch_message(role_react_message_id)
            role_react_message_contents = role_react_message.embeds[0].description

            original_message_contents = role_react_message_contents.split('\n')[:1]
            roles_in_message = role_react_message_contents.split('\n')[1:]
            list_of_roles = ctx.message.guild.roles
            list_of_roles_ids_in_server = []

            for role in list_of_roles:
                list_of_roles_ids_in_server.append(str(role.id))

            for role in roles_in_message:
                if role != '':
                    role_id_in_message = re.match('.*<@&(.*)>.*', role).group(1)
                    if role_id_in_message not in list_of_roles_ids_in_server:
                        roles_in_message.remove(role)

            new_description = original_message_contents + roles_in_message
            new_description = '\n'.join(new_description)
            embed = disnake.Embed(color=12745742, description=new_description)
            embed.set_author(name='React for roles')
            embed.set_footer(text='')
            embed.add_field(
                name = 'How do I add a role?',
                value = f'{github_link}',
                inline = False
            )
            await role_react_message.edit(embed=embed)
    except Exception as e:
        logger.info(f'Error cleaning up roles message in server "{ctx.message.guild.name}" (id: {ctx.message.guild.id}) '
                    f'for member "{ctx.message.author.name}" (id: {ctx.message.author.id}). Error: {e}')

async def send_invite_notification(payload, allowed_channel_ids):
    invite_creator = payload.inviter
    invite_code = payload.id
    invite_guild = payload.guild

    for channel_id in allowed_channel_ids:
        channel_id = int(channel_id)
        notification_channel = invite_guild.get_channel(channel_id)
        if notification_channel:
            # Send notification in channel
            embed = disnake.Embed(color=255, description=f'{invite_creator.mention} {invite_creator}')
            embed.set_author(name='Invite created', icon_url=invite_creator.display_avatar)
            embed.set_thumbnail(url=invite_creator.display_avatar)
            embed.set_footer(text=f'Invite ID: {invite_code}')
            await notification_channel.send(embed=embed)
            logger.info(f'Invite created by member "{invite_creator}"')

async def send_new_member_notification(member, allowed_channel_ids, new_role_ids):
    member_guild = member.guild

    for channel_id in allowed_channel_ids:
        channel_id = int(channel_id)
        notification_channel = member_guild.get_channel(channel_id)
        if notification_channel:
            # Send notification in channel
            embed = disnake.Embed(color = 12745742, description = f'{member.mention} {member}')
            embed.set_author(name = 'Member joined', icon_url = member.display_avatar)
            embed.set_thumbnail(url = member.display_avatar)
            new_member_in_days = 30
            days_since_account_created = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days
            if days_since_account_created <= new_member_in_days:
                embed.add_field(name = 'New Account', value = f'Created: {member.created_at.strftime("%Y-%m-%d %H:%M:%S")}', inline = False)
            embed.set_footer(text = f'ID: {member.id}')
            await notification_channel.send(embed = embed)

    # Give new role
    for role_id in new_role_ids:
        role_id = int(role_id)
        new_role = member.guild.get_role(role_id)
        if new_role:
            await member.add_roles(new_role)

    logger.info(f'New member "{member.name}" (id: {member.id}) '
                f'joined server "{member.guild.name}" (id: {member.guild.id})')

async def change_role(bot, payload, is_add):
    emoji = payload.emoji
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await bot.fetch_user(payload.user_id)

    # Don't listen to other bots
    if user.bot:
        return

    # Look for role react main message
    fetch_message = await message.channel.history().find(lambda m: (m.author.id == m.guild.me.id))
    if fetch_message.embeds[0].author.name == 'React for roles':
        role_react_message_id = fetch_message.id

        # Ignore reacts on messages which aren't the role react message
        if message.id != role_react_message_id:
            return

        role_react_message = await message.channel.fetch_message(role_react_message_id)
        role_react_message_contents = role_react_message.embeds[0].description
        roles_in_message = role_react_message_contents.split('\n')[1:]

        for role in roles_in_message:
            if str(emoji) in role:
                role_id = int(re.search(r'\d+', role).group(0))

                member = await channel.guild.fetch_member(payload.user_id)
                relevant_role = member.guild.get_role(role_id)
                if is_add:
                    await member.add_roles(relevant_role)
                else:
                    await member.remove_roles(relevant_role)

    if is_add:
        logger_phrase = 'Adding'
    else:
        logger_phrase = 'Removing'
    logger.info(f'{logger_phrase} member id {payload.user_id} from role "" '
                f'in server id {payload.guild_id}')