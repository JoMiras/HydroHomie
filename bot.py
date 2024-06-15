import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging
import os

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot with intents necessary
intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
scheduler = AsyncIOScheduler()

# Global variable to keep track of voice channel status
voice_channel_active = False

# Announce bot is online
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name='Bot Testing')  # Replace with your guild name
    if guild:
        channel = discord.utils.get(guild.channels, name='general')  # Replace with your channel name
        if channel:
            await channel.send("I'm online and ready to assist!")
        logger.info(f'{bot.user} has connected to Discord!')
    else:
        logger.error("Guild not found! Bot is not connected to the correct guild.")

# Check voice channel status
@tasks.loop(minutes=1)
async def check_voice_channel():
    global voice_channel_active
    guild = discord.utils.get(bot.guilds, name='YOUR_GUILD_NAME')  # Replace with your guild name
    if guild:
        for channel in guild.voice_channels:
            if len(channel.members) > 1:
                if not voice_channel_active:
                    voice_channel_active = True
                    if not send_hydrate_reminder.is_running():
                        send_hydrate_reminder.start(channel)
                return
    voice_channel_active = False
    if send_hydrate_reminder.is_running():
        send_hydrate_reminder.stop()

# Hydrate reminder task
@tasks.loop(minutes=30)
async def send_hydrate_reminder(channel):
    await channel.send("Just reminding you to drink water! ^.^ ")

# Event to handle user joining or leaving voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    if (before.channel is None and after.channel is not None) or (before.channel is not None and after.channel is None):
        if not check_voice_channel.is_running():
            check_voice_channel.start()

# Custom reminder command
@bot.command(name='remindMe')
async def remind_me(ctx, time: str, *, reminder: str):
    await ctx.send(f"Received remindMe command with time: {time} and reminder: {reminder}")
    user = ctx.message.author
    delay = int(time[:-1])
    unit = time[-1]

    if unit == 's':
        delta = timedelta(seconds=delay)
    elif unit == 'm':
        delta = timedelta(minutes=delay)
    elif unit == 'h':
        delta = timedelta(hours=delay)
    else:
        await ctx.send("Invalid time unit! Use 's' for seconds, 'm' for minutes, or 'h' for hours.")
        return

    remind_time = datetime.now() + delta
    scheduler.add_job(send_custom_reminder, 'date', run_date=remind_time, args=[ctx.channel, user, reminder])
    logger.info(f"Scheduled reminder for {user} at {remind_time} with message: {reminder}")
    await ctx.send(f"Reminder set for {time}: {reminder}. I'll remind you!")

async def send_custom_reminder(channel, user, reminder):
    logger.info(f"Sending reminder to {user} with message: {reminder}")
    await channel.send(f"{user.mention}, reminder: {reminder}")

scheduler.start()

# Retrieve the token from the environment variable and run the bot
token = os.getenv('DISCORD_TOKEN')
print(token)  # Temporarily print the token to verify it's being read correctly
bot.run(token)