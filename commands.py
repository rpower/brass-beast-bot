import discord


async def help(bot, args, message):
    help_message = (':robot: **Brass Beast Heavy**\n\n'
        'Brass Beast Heavy is firing backwards into spawn.\n'
        'More information: https://github.com/rpower/discord-server-logs')
    bot.logger.info(f'Listed help message in server {message.guild.id}')
    await message.channel.send(help_message)

commands_list = {
    'help': help
}