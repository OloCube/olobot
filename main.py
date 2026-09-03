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
last_olo_users = {}

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

# INTERACTIVE BUTTONS FOR THE LORE
class HistoryPaginator(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.page = 1
        self.pages = {
            1: "📜 **The Olo History (Page 1/2)**\n\nOlo was created when Kribit sent a meme and said 'ppougj try not to say lol challenge(impossible)', to which ppougj replied 'olo'",
            2: "📜 **The Olo History (Page 2/2)**\n\nolo the second was a small boy, he didnt know anything about the world but he knew he was a direct descendant of olo the first, he saw that the world did not want to be associated with the olo name, and therefore building hatred against mankind, in order to build a better olo from his pride"
        }

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            button.disabled = (self.page == 1)
            self.children[1].disabled = False # Enable Next button
            await interaction.response.edit_message(content=self.pages[self.page], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < 2:
            self.page += 1
            button.disabled = (self.page == 2)
            self.children[0].disabled = False # Enable Back button
            await interaction.response.edit_message(content=self.pages[self.page], view=self)

@bot.event
async def on_ready():
    # Show "Playing olo" status
    await bot.change_presence(activity=discord.Game(name="olo"))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Logged in as {bot.user.name} and monitoring olo channels!")

# OLO HISTORY COMMAND
@bot.tree.command(name="olohistory", description="Learn about the epic lore and history of Olo.")
async def olohistory(interaction: discord.Interaction):
    view = HistoryPaginator()
    await interaction.response.send_message(view.pages[1], view=view)

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

# MESSAGE MONITORING LOGIC
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    olo_channels = load_channels()
    
    if message.channel.id in olo_channels:
        # Turn message into list of lowercase words
        words = message.content.strip().lower().split()

        # FIXED logic: Check if there are words and the very FIRST word is exactly "olo"
        if len(words) > 0 and words[0] == "olo":
            channel_id = message.channel.id
            
            # Anti-spam: Check if this user was the last one to olo here
            if channel_id in last_olo_users and last_olo_users[channel_id] == message.author.id:
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass
                return

            # Log this user as the last one to speak
            last_olo_users[channel_id] = message.author.id

            # Determine reaction (Custom :olo: or standard ✅)
            reaction = "✅"
            custom_emoji = discord.utils.get(message.guild.emojis, name="olo")
            if custom_emoji:
                reaction = custom_emoji

            try:
                await message.add_reaction(reaction)
            except discord.DiscordException:
                pass
        else:
            # First word wasn't "olo" -> Vaporize it!
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

    await bot.process_commands(message)

keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
