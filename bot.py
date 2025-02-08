import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Global variables for queue system
queue = []
current_song = None

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and ready!")

@bot.command(name="join")
async def join(ctx):
    """Bot ko voice channel me join karne ke liye"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send("🔊 Joined the voice channel!")
        else:
            await ctx.send("✅ Already in a voice channel!")
    else:
        await ctx.send("❌ Pehle kisi voice channel me jao!")

@bot.command(name="leave")
async def leave(ctx):
    """Bot ko voice channel se nikalne ke liye"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
        await ctx.send("👋 Left the voice channel and cleared the queue!")
    else:
        await ctx.send("❌ Main kisi channel me nahi hoon!")

@bot.command(name="play")
async def play(ctx, *, search: str):
    """YouTube se song bajane ke liye"""
    global current_song

    if not ctx.voice_client:
        await ctx.invoke(join)

    # Search YouTube for the song
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "default_search": "ytsearch",
        "extract_flat": True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        if "entries" in info:
            url = info["entries"][0]["url"]
            title = info["entries"][0]["title"]
        else:
            url = info["url"]
            title = info["title"]

    queue.append((url, title))

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"📌 Added to queue: {title}")

async def play_next(ctx):
    """Queue me se next song bajane ke liye"""
    global current_song

    if queue:
        url, title = queue.pop(0)
        current_song = title

        ctx.voice_client.stop()
        ffmpeg_options = {"options": "-vn"}

        ctx.voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"🎶 Now playing: {title}")
    else:
        current_song = None

@bot.command(name="queue")
async def show_queue(ctx):
    """Queue dikhane ke liye"""
    if queue:
        queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(queue)])
        await ctx.send(f"📜 **Song Queue:**\n{queue_list}")
    else:
        await ctx.send("📭 Queue is empty!")

@bot.command(name="now")
async def now(ctx):
    """Current playing song dikhane ke liye"""
    if current_song:
        await ctx.send(f"🎧 **Now Playing:** {current_song}")
    else:
        await ctx.send("🔇 No song is currently playing!")

@bot.command(name="skip")
@commands.has_permissions(administrator=True)
async def skip(ctx):
    """Admin ke liye next song play karne ka option"""
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped! Playing next song...")
        await play_next(ctx)
    else:
        await ctx.send("❌ Nothing is playing right now!")

@bot.command(name="restart")
@commands.has_permissions(administrator=True)
async def restart(ctx):
    """Bot ko restart karne ka option (Admin only)"""
    await ctx.send("🔄 Restarting bot...")
    os.system("kill 1")

bot.run(TOKEN)
