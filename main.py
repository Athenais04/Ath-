const express = require('express');
const { Client, Intents } = require('discord.js');
const dotenv = require('dotenv');
dotenv.config();

// === Express pour le ping ===
const app = express();
app.get('/', (req, res) => {
  console.log(`Ping reçu de ${req.ip}`);
  res.send('Bot is running!');
});
app.listen(process.env.PORT || 3000, () => {
  console.log('Serveur Express en ligne');
});

// === Discord.js v13 ===
const client = new Client({
  intents: [
    Intents.FLAGS.GUILDS,
    Intents.FLAGS.GUILD_MEMBERS,
    Intents.FLAGS.GUILD_MESSAGES,
    Intents.FLAGS.GUILD_MESSAGE_CONTENT, // si tu as l'intent activé dans le portail
  ]
});

const ROLE_NAME_TO_WATCH = "RL en attente";
const ROLE_TO_PING = "RL STAFF";
const CHANNEL_ID = "1382315923427295275";

client.once('ready', () => {
  console.log(`Bot prêt : ${client.user.tag}`);
});

client.on('guildMemberUpdate', async (before, after) => {
  const addedRoles = after.roles.cache.filter(role => !before.roles.cache.has(role.id));
  const targetRole = addedRoles.find(role => role.name === ROLE_NAME_TO_WATCH);

  if (targetRole) {
    const channel = await client.channels.fetch(CHANNEL_ID).catch(() => null);
    const staffRole = after.guild.roles.cache.find(role => role.name === ROLE_TO_PING);
    if (channel && staffRole) {
      await channel.send(`${staffRole} : ${after} a reçu le rôle **${ROLE_NAME_TO_WATCH}** !`);
    }
  }
});

client.login(process.env.DISCORD_BOT_TOKEN);
