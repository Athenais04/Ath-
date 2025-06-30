import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

print("Python version:", sys.version)

# Chargement des variables d'environnement
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

linked_accounts = {}

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.command()
async def link(ctx, platform: str, *, username: str):
    linked_accounts[ctx.author.id] = (platform, username)
    await ctx.send(f"✅ Compte lié à `{username}` sur `{platform}`")

@bot.command()
async def rank(ctx, member: discord.Member = None):
    user = member or ctx.author
    if user.id not in linked_accounts:
        return await ctx.send("❌ Aucun compte lié. Utilise `!link <plateforme> <pseudo>`")

    platform, username = linked_accounts[user.id]
    url = f"https://rocketleague.tracker.network/rocket-league/profile/{platform}/{username}/overview"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    
    time.sleep(5)  # Attend que la page charge

    ranks = driver.find_elements(By.CLASS_NAME, 'playlist')
    if not ranks:
        await ctx.send("❌ Impossible de trouver les données sur la page.")
        driver.quit()
        return

    output = f"**Ranks Rocket League de {user.display_name}**\n"
    for rank in ranks:
        try:
            playlist = rank.find_element(By.CLASS_NAME, 'playlist__name').text
            tier = rank.find_element(By.CLASS_NAME, 'playlist__rank').text
            mmr = rank.find_element(By.CLASS_NAME, 'playlist__rating').text
            output += f"➡️ {playlist} : **{tier}** ({mmr})\n"
        except:
            continue

    await ctx.send(output)
    driver.quit()

if __name__ == "__main__":
    try:
        keep_alive()
    except:
        pass
    bot.run(DISCORD_TOKEN)
