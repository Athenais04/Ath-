import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import sys
from keep_alive import keep_alive  # importe ta fonction keep_alive

print("Python version:", sys.version)

load_dotenv()
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

# Base de données en mémoire pour stocker les pseudos RL (tu peux remplacer par SQLite, JSON, etc.)
linked_accounts = {}

@bot.command()
async def link(ctx, platform: str, *, username: str):
    """Lie ton compte Rocket League (plateforme: steam, epic, psn, xbox)"""
    linked_accounts[ctx.author.id] = (platform, username)
    await ctx.send(f"✅ Compte lié à {username} sur {platform}")

@bot.command()
async def rank(ctx, member: discord.Member = None):
    """Affiche les ranks d’un joueur (ou toi si non spécifié)"""
    user = member or ctx.author
    if user.id not in linked_accounts:
        return await ctx.send("❌ Aucun compte lié. Utilise `!link <plateforme> <pseudo>`")

    platform, username = linked_accounts[user.id]
    url = f"https://public-api.tracker.gg/v2/rocket-league/standard/profile/{platform}/{username}"

    headers = {
        "TRN-Api-Key": TRN_API_KEY,
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Impossible de récupérer les données. Vérifie ton pseudo.")

            data = await resp.json()
            segments = data.get("data", {}).get("segments", [])

            if not segments:
                return await ctx.send("Aucune donnée trouvée.")

            output = f"**Ranks Rocket League de {user.display_name}**\n"
            for segment in segments:
                if segment["type"] == "playlist":
                    playlist = segment["metadata"]["name"]
                    rank = segment["stats"]["tier"]["metadata"]["name"]
                    div = segment["stats"]["division"]["metadata"]["name"]
                    mmr = segment["stats"]["rating"]["value"]
                    output += f"➡️ {playlist} : **{rank} {div}** ({mmr} MMR)\n"

            await ctx.send(output)


token = os.getenv("DISCORD_BOT_TOKEN")

if __name__ == "__main__":
    keep_alive()  # démarre Flask en thread séparé pour UptimeRobot
    bot.run(token)
