import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import sys
from discord.ext import commands, tasks
import aiohttp
import aiosqlite
from config import DISCORD_BOT_TOKEN, TRN_API_KEY, REFRESH_INTERVAL_HOURS
from keep_alive import keep_alive  # importe ta fonction keep_alive

print("Python version:", sys.version)

load_dotenv()

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- DB SETUP ----------

async def init_db():
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                user_id INTEGER PRIMARY KEY,
                platform TEXT,
                username TEXT,
                last_mmr INTEGER
            )
        """)
        await db.commit()

# ---------- BOT EVENTS ----------

@bot.event
async def on_ready():
    await init_db()
    refresh_ranks.start()
    print(f"✅ Connecté en tant que {bot.user}")

# ---------- API CALL ----------

async def fetch_rank(platform, username):
    url = f"https://public-api.tracker.gg/v2/rocket-league/standard/profile/{platform}/{username}"
    headers = {"TRN-Api-Key": TRN_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

# ---------- COMMANDES ----------

@bot.command()
async def link(ctx, platform: str, *, username: str):
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("""
            INSERT OR REPLACE INTO accounts (user_id, platform, username, last_mmr)
            VALUES (?, ?, ?, ?)
        """, (ctx.author.id, platform, username, 0))
        await db.commit()
    await ctx.send(f"✅ {ctx.author.mention}, compte lié à `{username}` sur `{platform}`")

@bot.command()
async def rank(ctx, member: discord.Member = None):
    user = member or ctx.author
    async with aiosqlite.connect("db.sqlite3") as db:
        async with db.execute("SELECT platform, username FROM accounts WHERE user_id = ?", (user.id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return await ctx.send("❌ Aucun compte lié. Utilise `!link`")

            platform, username = row
            data = await fetch_rank(platform, username)
            if not data:
                return await ctx.send("⚠️ Données introuvables.")

            segments = data["data"]["segments"]
            embed = discord.Embed(title=f"Ranks Rocket League de {user.display_name}", color=discord.Color.blue())
            for s in segments:
                if s["type"] == "playlist":
                    name = s["metadata"]["name"]
                    tier = s["stats"]["tier"]["metadata"]["name"]
                    div = s["stats"]["division"]["metadata"]["name"]
                    mmr = s["stats"]["rating"]["value"]
                    embed.add_field(name=name, value=f"{tier} {div} ({mmr} MMR)", inline=False)

            await ctx.send(embed=embed)

# ---------- RANK REFRESH AUTO ----------

@tasks.loop(hours=REFRESH_INTERVAL_HOURS)
async def refresh_ranks():
    async with aiosqlite.connect("db.sqlite3") as db:
        async with db.execute("SELECT user_id, platform, username, last_mmr FROM accounts") as cursor:
            async for user_id, platform, username, last_mmr in cursor:
                data = await fetch_rank(platform, username)
                if not data:
                    continue

                for s in data["data"]["segments"]:
                    if s["type"] == "playlist" and s["metadata"]["name"] == "Ranked Doubles 2v2":
                        current_mmr = s["stats"]["rating"]["value"]
                        if current_mmr != last_mmr:
                            user = await bot.fetch_user(user_id)
                            direction = "🔺 monté" if current_mmr > last_mmr else "🔻 descendu"
                            msg = f"{user.mention} est {direction} en 2v2 : {last_mmr} → {current_mmr} MMR"
                            channel = discord.utils.get(bot.get_all_channels(), name="rocket-league")
                            if channel:
                                await channel.send(msg)
                            await db.execute("UPDATE accounts SET last_mmr = ? WHERE user_id = ?", (current_mmr, user_id))
                            await db.commit()

# ---------- LEADERBOARD ----------

@bot.command()
async def leaderboard(ctx):
    async with aiosqlite.connect("db.sqlite3") as db:
        async with db.execute("""
            SELECT username, last_mmr FROM accounts
            ORDER BY last_mmr DESC LIMIT 10
        """) as cursor:
            rows = await cursor.fetchall()
            if not rows:
                return await ctx.send("Aucun joueur trouvé.")

            embed = discord.Embed(title="🏆 Leaderboard Rocket League 2v2", color=discord.Color.gold())
            for i, (username, mmr) in enumerate(rows, start=1):
                embed.add_field(name=f"{i}. {username}", value=f"{mmr} MMR", inline=False)
            await ctx.send(embed=embed)

token = os.getenv("DISCORD_BOT_TOKEN")

if __name__ == "__main__":
    keep_alive()  # démarre Flask en thread séparé pour UptimeRobot
    bot.run(token)
