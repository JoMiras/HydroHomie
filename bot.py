import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# Initialize bot
intents = discord.Intents.default()
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
    channel = discord.utils.get(bot.get_all_channels(), name='general')  # Replace with your channel name
    if channel:
        await channel.send("I'm online and ready to assist!")
    print(f'{bot.user} has connected to Discord!')

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
    await channel.send("Remember to drink water!")

# Event to handle user joining or leaving voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    if (before.channel is None and after.channel is not None) or (before.channel is not None and after.channel is None):
        if not check_voice_channel.is_running():
            check_voice_channel.start()

# Custom reminder command
@bot.command(name='remindMe')
async def remind_me(ctx, time: str, *, reminder: str):
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
    await ctx.send(f"Reminder set for {time}: {reminder}. I'll remind you!")

async def send_custom_reminder(channel, user, reminder):
    await channel.send(f"{user.mention}, reminder: {reminder}")


