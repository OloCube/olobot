import os, discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

# Web Server Workaround
app = Flask('')
@app.route('/')
def home(): return "Olo bot is alive!"
def keep_alive(): Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
olo_channels, last_olo_users = set(), {}
MY_ID = 989971920441180160  
TAG = "[YOU MAY ONLY TYPE OLO IN THIS CHANNEL!]"

def is_staff():
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.manage_channels: return True
        return any(r.name == "Trial Mod" for r in interaction.user.roles) if isinstance(interaction.user, discord.Member) else False
    return app_commands.check(predicate)

class HistoryPaginator(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.page = 1
        self.pages = {
            1: "📜 **The Olo History (Page 1/2)**\n\nOlo was created when Kribit sent a meme and said 'ppougj try not to say lol challenge(impossible)', to which ppougj replied 'olo'",
            2: "📜 **The Olo History (Page 2/2)**\n\nolo the second was a small boy, he didnt know anything about the world but he knew he was a direct descendant of olo the first, he saw that the world did not want to be associated with the olo name, and therefore building hatred against mankind, in order to build a better olo from his pride"
        }

    async def update_page(self, interaction: discord.Interaction):
        # Safely changes button states using explicit list mapping
        self.children[0].disabled = (self.page == 1)
        self.children[1].disabled = (self.page == 2)
        await interaction.response.edit_message(content=self.pages[self.page], view=self)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if self.page > 1: self.page -= 1; await self.update_page(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if self.page < 2: self.page += 1; await self.update_page(interaction)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="olo"))
    olo_channels.clear()
    for g in bot.guilds:
        for c in g.text_channels:
            if c.topic and TAG in c.topic: olo_channels.add(c.id)
    try: await bot.tree.sync()
    except Exception as e: print(f"Sync error: {e}")
    print(f"Logged in as {bot.user.name}")

@bot.tree.command(name="olohistory", description="Learn about the epic lore and history of Olo.")
async def olohistory(interaction: discord.Interaction):
    await interaction.response.send_message(HistoryPaginator().pages[1], view=HistoryPaginator())

@bot.tree.command(name="support", description="Get troubleshooting steps.")
async def support(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🛠️ **OloBot Fixes:**\n1️⃣ Kick and re-add bot.\n2️⃣ Check **Manage Messages** & **Add Reactions** permissions.\n"
        "3️⃣ Run `/setchannel` inside your active olo room.\n4️⃣ Upload an emoji named exactly `olo` (lowercase).\n\n"
        "💬 **DM this bot directly** to speak with our support staff!\n👉 Support Server: https://discord.gg/NZW7ahevDJ"
    )

@bot.tree.command(name="setchannel", description="Lock down an olo room.")
@is_staff()
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    olo_channels.add(channel.id)
    topic = channel.topic if channel.topic else ""
    if TAG not in topic:
        try: await channel.edit(topic=f"{topic} {TAG}".strip())
        except discord.Forbidden: pass
    await interaction.followup.send(f"🔒 {channel.mention} activated!")

@bot.tree.command(name="removechannel", description="Unlock a channel.")
@is_staff()
async def removechannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    olo_channels.discard(channel.id)
    if channel.topic and TAG in channel.topic:
        try: await channel.edit(topic=channel.topic.replace(TAG, "").strip())
        except discord.Forbidden: pass
    await interaction.followup.send(f"🔓 {channel.mention} deactivated.")

@setchannel.error
@removechannel.error
async def perm_err(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if interaction.response.is_done():
        await interaction.followup.send("❌ Missing permissions or 'Trial Mod' role!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Missing permissions or 'Trial Mod' role!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    if isinstance(message.channel, discord.DMChannel):
        if message.author.id == MY_ID and message.content.startswith("!reply "):
            try:
                p = message.content.split(" ", 2)
                u = await bot.fetch_user(int(p[1]))
                emb = discord.Embed(description=p[2], color=discord.Color.green()).set_author(name="OloBot Support")
                await u.send(embed=emb)
                await message.channel.send("✅ Delivered")
            except Exception as e: await message.channel.send(f"❌ Error: {e}")
            return
        try:
            me = await bot.fetch_user(MY_ID)
            emb = discord.Embed(title="📬 Help Request", description=message.content, color=discord.Color.blue())
            emb.set_author(name=f"{message.author} (ID: {message.author.id})").set_footer(text=f"To reply: !reply {message.author.id} [text]")
            await me.send(embed=emb)
        except: pass
        return

    if message.channel.id in olo_channels:
        raw = message.content.strip().lower()
        w = raw.split()
        if len(w) > 0 and "olo" in w[0] and len(raw) <= 30:
            if message.channel.id in last_olo_users and last_olo_users[message.channel.id] == message.author.id:
                try: await message.delete()
                except: pass
                return
            last_olo_users[message.channel.id] = message.author.id
            reac = discord.utils.get(message.guild.emojis, name="olo") or "✅"
            try: await message.add_reaction(reac)
            except: pass
        else:
            try: await message.delete()
            except: pass
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
