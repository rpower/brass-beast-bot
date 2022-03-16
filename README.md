# Brass Beast Bot

A self-hosted [disnake](https://github.com/DisnakeDev/disnake) bot written in Python that automates some of the admin in our private Discord server.

## Installation

1. Clone this repository using `git clone https://github.com/rpower/brass-beast-bot`
2. Install required packages using `pip install -r requirements.txt`
3. Create two environment variables:
   1. `BOT_TOKEN` - containing the API token for your Discord bot
   2. `BOT_NOTIFICATIONS_CHANNEL_IDS` - IDs associated with channels the bot will send notifications to
   3. `NEW_ROLE_IDS` - IDs associated with roles assigned to new members
   4. `MUSIC_CHANNEL_IDS` - IDs associated with channels which music can be played from

## Commands

All commands begin with `!bb` and then the command you want to use.

## Get your roles

### Adding a role

```!bb addrole 🍎 Apples```

### Removing a role

```!bb removerole Apples```

Roles added via the bot should be removed via the bot.

## Music

### Play music

```!bb play https://www.youtube.com/watch?v=oS-A-wqZ2RI```

### Stop playing music

```!bb stop```

## Other commands

### Show link to GitHub

```!bb help```

### Cleanup Get Your Roles message

```!bb cleanup```