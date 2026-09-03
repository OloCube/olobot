import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. This small web server tricks Render into keeping your bot online
app = Flask('')

@app.route('/')
def home():
    return "Olo bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Your actual Discord Bot Logic
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and monitoring 'olo'!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    words = message.content.lower().split()

    if len(words) > 0 and words[0] == "olo":
        try:
            await message.add_reaction("✅")
        except discord.DiscordException:
            pass
    else:
        try:
            await message.delete()
        except discord.Forbidden:
            print("Error: Give the bot 'Manage Messages' permission in Discord!")
        except discord.NotFound:
            pass

    await bot.process_commands(message)

# Start the web server and run the bot
keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
