import discord
import os
from dotenv import load_dotenv

load_dotenv()

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Confessions Bot
TARGET_AUTHOR_ID = 712011923176030229  # User bot


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Monitoring messages from author ID: {TARGET_AUTHOR_ID}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == TARGET_AUTHOR_ID:
        try:
            await message.delete()
            print(
                f'Deleted message from {message.author.name}: "{message.content}"')
        except discord.Forbidden:
            print(
                f'No permission to delete message in #{message.channel.name}')
        except discord.NotFound:
            print('Message was already deleted')
        except Exception as e:
            print(f'Error deleting message: {e}')

# Run the bot
client.run(os.getenv("ELDRASIL_DISCORD_BOT_TOKEN"))
