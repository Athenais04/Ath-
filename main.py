import os
import sys
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive  # utile sur Replit

# Debug
print("Python version:", sys.version)

# Chargement des variables d'environnement
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TRN_API_KEY = os.getenv("TRN_API_KEY")

# Configuration du bot Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

# Base de données temporaire (RAM)
linked_accounts = {}

@bot.command()
async def link(ctx, platform: str, *, username: str):
    """Lie ton compte Rocket League (plateforme: steam, epic, psn, xbox)"""
    linked_accounts[ctx.author.id] = (platform, username)
    await ctx.send(f"✅ Compte lié à `{username}` sur `{platform}`")

@bot.command()
async def rank(ctx, member: discord.Member = None):
    """Affiche les ranks Rocket League du joueur"""
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
                return await ctx.send("❌ Impossible de récupérer les données. Vérifie ton pseudo ou la plateforme.")

            data = await resp.json()
            segments = data.get("data", {}).get("segments", [])

            if not segments:
                return await ctx.send("❌ Aucune donnée trouvée.")

            output = f"**Ranks Rocket League de {user.display_name}**\n"
            for segment in segments:
                if segment["type"] == "playlist":
                    playlist = segment["metadata"]["name"]
                    rank = segment["stats"]["tier"]["metadata"]["name"]
                    div = segment["stats"]["division"]["metadata"]["name"]
                    mmr = segment["stats"]["rating"]["value"]
                    output += f"➡️ {playlist} : **{rank} {div}** ({mmr} MMR)\n"

            await ctx.send(output)

# Lancement du serveur + du bot
if __name__ == "__main__":
    try:
        keep_alive()
    except:
        pass  # Sur Render, ce module est ignoré
    bot.run(DISCORD_BOT_TOKEN)
