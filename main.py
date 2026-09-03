import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

# Tiny web server to keep Render awake
app = Flask('')
@app.route('/')
def home(): return "Olo bot is alive!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# Setup Bot and Slash Commands
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "olo_channels.json"

def load_channels():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_channels(channels):
    with open(DATA_FILE, "w") as f:
        json.dump(channels, f)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Logged in as {bot.user.name} and monitoring olo channels!")

# SLASH COMMAND TO SET THE CHANNEL
@bot.tree.command(name="setchannel", description="Set a channel for strict olo-only counting.")
@app_commands.describe(channel="The text channel to turn into an olo-only channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    channels = load_channels()
    if channel.id not in channels:
        channels.append(channel.id)
        save_channels(channels)
        await interaction.response.send_message(f"🔒 {channel.mention} is now a strict **olo-only** channel!", ephemeral=True)
    else:
        await interaction.response.send_message(f"ℹ️ {channel.mention} is already an olo-only channel.", ephemeral=True)

# SLASH COMMAND TO REMOVE THE CHANNEL RULE
@bot.tree.command(name="removechannel", description="Remove the olo-only rule from a channel.")
@app_commands.describe(channel="The channel to disable the olo rule on")
@app_commands.checks.has_permissions(manage_channels=True)
async def removechannel(interaction: discord.Interaction, channel: discord.TextChannel):
    channels = load_channels()
    if channel.id in channels:
        channels.remove(channel.id)
        save_channels(channels)
        await interaction.response.send_message(f"🔓 Removed olo restrictions from {channel.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"ℹ️ {channel.mention} does not have the olo rule active.", ephemeral=True)

@setchannel.error
@removechannel.error
async def channel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You need 'Manage Channels' permissions to use this command!", ephemeral=True)

# MESSAGE MONITORING LOGIC WITH CUSTOM EMOJI CHECK
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    olo_channels = load_channels()
    
    if message.channel.id in olo_channels:
        words = message.content.lower().split()

        if len(words) > 0 and words[0] == "olo":
            # Default reaction is the checkmark
            reaction = "✅"
            
            # Look for a custom server emoji named exactly "olo"
            custom_emoji = discord.utils.get(message.guild.emojis, name="olo")
            if custom_emoji:
                reaction = custom_emoji

            try:
                await message.add_reaction(reaction)
            except discord.DiscordException:
                pass
        else:
            try:
                await message.delete()
            except discord.Forbidden:
                print(f"Error: Missing permissions to delete messages in {message.channel.name}")
            except discord.NotFound:
                pass

    await bot.process_commands(message)

keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
