import discord
from discord import app_commands
from discord.ext import commands
from youtube_dl import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue.pop(0)['source']
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0]['source']
            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0]['channel'].connect()
            else:
                await self.vc.move_to(self.music_queue[0]['channel'])
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @app_commands.command(name="play", description="Toca uma música do YouTube.")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer(thinking=True)
        try:
            voice_channel = interaction.user.voice.channel
        except AttributeError:
            await interaction.followup.send("Você precisa estar em um canal de voz para tocar música.")
            return
        song = self.search_yt(busca)
        if not song:
            await interaction.followup.send("Não consegui encontrar a música, tente novamente.")
        else:
            self.music_queue.append({'source': song['source'], 'title': song['title'], 'channel': voice_channel})
            await interaction.followup.send(f"Adicionado à fila: **{song['title']}**")
            if not self.is_playing:
                await self.play_music()

    @app_commands.command(name="fila", description="Mostra a fila de músicas.")
    async def fila(self, interaction: discord.Interaction):
        if len(self.music_queue) > 0:
            fila = "\n".join([f"{i+1}. {m['title']}" for i, m in enumerate(self.music_queue)])
            await interaction.response.send_message(f"Fila atual:\n{fila}")
        else:
            await interaction.response.send_message("A fila está vazia.")

    @app_commands.command(name="pular", description="Pula para a próxima música.")
    async def pular(self, interaction: discord.Interaction):
        if self.vc is not None and self.vc.is_playing():
            self.vc.stop()
            await self.play_music()
            await interaction.response.send_message("Música pulada.")
        else:
            await interaction.response.send_message("Não há nenhuma música tocando no momento.")

    @app_commands.command(name="parar", description="Para a música e desconecta o bot.")
    async def parar(self, interaction: discord.Interaction):
        if self.vc is not None and self.vc.is_connected():
            await self.vc.disconnect()
            self.vc = None
            self.is_playing = False
            self.music_queue = []
            await interaction.response.send_message("Bot desconectado e música parada.")
        else:
            await interaction.response.send_message("O bot não está conectado a nenhum canal de voz.")
