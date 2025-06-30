import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw, ImageFont
import io
import time

print("Python version:", sys.version)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.all()
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
    time.sleep(5)

    ranks = driver.find_elements(By.CLASS_NAME, 'playlist')
    if not ranks:
        await ctx.send("❌ Impossible de trouver les données sur la page.")
        driver.quit()
        return

    rank_data = []
    user_roles = []
    for rank in ranks:
        try:
            playlist = rank.find_element(By.CLASS_NAME, 'playlist__name').text
            tier = rank.find_element(By.CLASS_NAME, 'playlist__rank').text
            mmr = rank.find_element(By.CLASS_NAME, 'playlist__rating').text
            rank_data.append((playlist, tier, mmr))
            role_name = f"RL {tier}"  # Exemple: RL Champion II
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role and role not in user.roles:
                await user.add_roles(role)
                user_roles.append(role.name)
        except:
            continue

    driver.quit()

    img = Image.new('RGB', (500, 200 + len(rank_data)*50), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((20, 20), f"Ranks de {username}", fill=(255, 255, 255), font=font)

    y = 60
    for playlist, tier, mmr in rank_data:
        draw.text((20, y), f"{playlist}: {tier} ({mmr} MMR)", fill=(200, 200, 200), font=font)
        y += 40

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    file = discord.File(fp=buffer, filename="rank.png")
    embed = discord.Embed(title=f"Ranks Rocket League de {username}", color=0x3498db)
    embed.set_image(url="attachment://rank.png")
    if user_roles:
        embed.add_field(name="Rôles attribués", value=", ".join(user_roles))

    await ctx.send(embed=embed, file=file)

if __name__ == "__main__":
    try:
        keep_alive()
    except:
        pass
    bot.run(DISCORD_TOKEN)
