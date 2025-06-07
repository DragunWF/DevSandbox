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

# Globals
deleted_message_count = 0


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Monitoring messages from author ID: {TARGET_AUTHOR_ID}')


@client.event
async def on_message(message):
    global deleted_message_count

    if message.author == client.user:
        return

    if message.author.id == TARGET_AUTHOR_ID:
        try:
            await message.delete()
            deleted_message_count += 1
            count_display = f"{deleted_message_count}{get_ordinal(deleted_message_count)}"
            print(
                f'Deleted the {count_display} message from {message.author.name} user'
            )
        except discord.Forbidden:
            print(
                f'No permission to delete message in #{message.channel.name}')
        except discord.NotFound:
            print('Message was already deleted')
        except Exception as e:
            print(f'Error deleting message: {e}')


def get_ordinal(n):
    last_digit = str(n)[-1]
    if last_digit == "1":
        return "st"
    elif last_digit == "2":
        return "nd"
    elif last_digit == "3":
        return "rd"
    return "th"


# Run the bot
client.run(os.getenv("ELDRASIL_DISCORD_BOT_TOKEN"))
