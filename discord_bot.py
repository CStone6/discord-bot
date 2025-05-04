from typing import Final
import os
import discord
from discord import app_commands, Intents
from dotenv import load_dotenv
from pytubefix import YouTube
from pytubefix.cli import on_progress
import asyncio

# STEP 0: LOAD OUR TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
CHANNEL: Final[int] = int(os.getenv('DISCORD_CHANNEL'))

# STEP 1: BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'{self.user} is now running!')
        channel = self.get_channel(CHANNEL)
        if channel:
            await channel.send("Use `/cmd` to see available commands.")

client = MyClient()

# STEP 2: PLAY AUDIO FUNCTION
async def play_audio(voice_channel, audio, volume=0.4):
    vc = await voice_channel.connect()
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio, executable="B:/ffmpeg/bin/ffmpeg.exe"))
    source.volume = volume
    vc.play(source)
    while vc.is_playing():
        await asyncio.sleep(1)
    await vc.disconnect()

# STEP 3: SLASH COMMANDS

@client.tree.command(name="leave", description="Leaves the voice channel.")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        if os.path.isfile("audio.mp4a"):
            os.remove("audio.mp4a")
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Left the voice channel.")
    else:
        await interaction.response.send_message("I am not connected to a voice channel.")

@client.tree.command(name="cmd", description="Lists available commands.")
async def cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Commands:**\n"
        "`/leave` – Leaves the call.\n"
        "`/music <url> <volume>` – Play music from a YouTube link with optional volume (0.0 to 1.0)."
    )

@client.tree.command(name="music", description="Plays music from a YouTube URL.")
@app_commands.describe(
    url="YouTube video URL",
    volume="Volume level from 0.0 to 1.0 (optional)"
)
async def music(interaction: discord.Interaction, url: str, volume: float = 0.5):
    await interaction.response.defer()
    try:
        if not (0.0 <= volume <= 1.0):
            await interaction.followup.send("Volume must be between 0.0 and 1.0.")
            return

        yt = YouTube(url, on_progress_callback=on_progress)
        await interaction.followup.send(f"Loading and playing: {yt.title}")

        ys = yt.streams.get_audio_only()
        downloaded_file = ys.download()
        audio_file = "audio.mp4a"
        os.rename(downloaded_file, audio_file)

        await play_audio(interaction.user.voice.channel, audio_file, volume)
        os.remove(audio_file)

    except Exception as e:
        print(f"Error: {e}")
        if os.path.isfile("audio.mp4a"):
            os.remove("audio.mp4a")
        await interaction.followup.send("An error occurred while processing the YouTube video.")

# STEP 4: RUN BOT
if __name__ == '__main__':
    client.run(TOKEN)
