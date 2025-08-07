import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
from database import DatabaseManager
from config import EMOJIS, DEFAULT_COLOR, MAX_REMINDER_DAYS
import logging
import re

logger = logging.getLogger(__name__)

class LembretesCog(commands.Cog):
    """Sistema de lembretes e notificações"""
    
    def __init__(self, bot):
        self.bot = bot
        self.verificar_lembretes.start()
    
    def cog_unload(self):
        self.verificar_lembretes.cancel()
    
    @app_commands.command(name="lembrete", description="Criar um lembrete")
    @app_commands.describe(
        tempo="Tempo para o lembrete (ex: 5m, 2h, 1d)",
        mensagem="Mensagem do lembrete"
    )
    async def criar_lembrete(
        self, 
        interaction: discord.Interaction, 
        tempo: str, 
        mensagem: str
    ):
        """Cria um novo lembrete"""
        try:
            # Parsear o tempo
            tempo_delta = self.parse_tempo(tempo)
            
            if not tempo_delta:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Formato de tempo inválido! Use: 5m, 2h, 1d, etc.",
                    ephemeral=True
                )
                return
            
            # Verificar limite máximo
            if tempo_delta.total_seconds() > MAX_REMINDER_DAYS * 24 * 3600:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} O lembrete não pode ser superior a {MAX_REMINDER_DAYS} dias!",
                    ephemeral=True
                )
                return
            
            # Calcular data do lembrete
            remind_at = datetime.now() + tempo_delta
            
            # Salvar no banco de dados
            await DatabaseManager.execute_query(
                '''INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (
                    interaction.user.id,
                    interaction.guild_id,
                    interaction.channel_id,
                    mensagem,
                    remind_at
                )
            )
            
            # Criar embed de confirmação
            embed = discord.Embed(
                title=f"{EMOJIS['reminder']} Lembrete Criado",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Mensagem:", value=mensagem, inline=False)
            embed.add_field(
                name="Será enviado em:", 
                value=f"<t:{int(remind_at.timestamp())}:F>", 
                inline=False
            )
            embed.add_field(
                name="Tempo:", 
                value=self.format_tempo(tempo_delta), 
                inline=True
            )
            
            embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f"Lembrete criado por {interaction.user} para {remind_at}")
            
        except Exception as e:
            logger.error(f"Erro ao criar lembrete: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao criar lembrete: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="meus_lembretes", description="Ver seus lembretes ativos")
    async def meus_lembretes(self, interaction: discord.Interaction):
        """Mostra os lembretes ativos do usuário"""
        try:
            # Buscar lembretes do usuário
            lembretes = await DatabaseManager.fetch_all(
                '''SELECT id, message, remind_at FROM reminders 
                   WHERE user_id = ? AND guild_id = ? AND is_sent = 0
                   ORDER BY remind_at ASC''',
                (interaction.user.id, interaction.guild_id)
            )
            
            if not lembretes:
                embed = discord.Embed(
                    title=f"{EMOJIS['info']} Seus Lembretes",
                    description="Você não tem lembretes ativos.",
                    color=DEFAULT_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"{EMOJIS['reminder']} Seus Lembretes Ativos",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            for i, (lembrete_id, mensagem, remind_at) in enumerate(lembretes[:10], 1):
                remind_datetime = datetime.fromisoformat(remind_at.replace('Z', '+00:00'))
                
                embed.add_field(
                    name=f"{i}. ID: {lembrete_id}",
                    value=f"**Mensagem:** {mensagem[:100]}{'...' if len(mensagem) > 100 else ''}\n"
                          f"**Quando:** <t:{int(remind_datetime.timestamp())}:R>",
                    inline=False
                )
            
            if len(lembretes) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(lembretes)} lembretes")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao buscar lembretes: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao buscar lembretes: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="cancelar_lembrete", description="Cancelar um lembrete")
    @app_commands.describe(lembrete_id="ID do lembrete para cancelar")
    async def cancelar_lembrete(self, interaction: discord.Interaction, lembrete_id: int):
        """Cancela um lembrete específico"""
        try:
            # Verificar se o lembrete existe e pertence ao usuário
            lembrete = await DatabaseManager.fetch_one(
                '''SELECT message FROM reminders 
                   WHERE id = ? AND user_id = ? AND guild_id = ? AND is_sent = 0''',
                (lembrete_id, interaction.user.id, interaction.guild_id)
            )
            
            if not lembrete:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Lembrete não encontrado ou já foi enviado!",
                    ephemeral=True
                )
                return
            
            # Marcar como enviado (cancelado)
            await DatabaseManager.execute_query(
                "UPDATE reminders SET is_sent = 1 WHERE id = ?",
                (lembrete_id,)
            )
            
            embed = discord.Embed(
                title=f"{EMOJIS['check']} Lembrete Cancelado",
                description=f"Lembrete **{lembrete[0][:100]}** foi cancelado com sucesso.",
                color=DEFAULT_COLOR
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Lembrete {lembrete_id} cancelado por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao cancelar lembrete: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao cancelar lembrete: {str(e)}",
                ephemeral=True
            )
    
    @tasks.loop(seconds=60)  # Verificar a cada minuto
    async def verificar_lembretes(self):
        """Task que verifica lembretes que devem ser enviados"""
        try:
            # Buscar lembretes que devem ser enviados
            lembretes = await DatabaseManager.fetch_all(
                '''SELECT id, user_id, guild_id, channel_id, message, remind_at 
                   FROM reminders 
                   WHERE remind_at <= ? AND is_sent = 0''',
                (datetime.now(),)
            )
            
            for lembrete in lembretes:
                await self.enviar_lembrete(lembrete)
                
        except Exception as e:
            logger.error(f"Erro ao verificar lembretes: {e}")
    
    @verificar_lembretes.before_loop
    async def before_verificar_lembretes(self):
        await self.bot.wait_until_ready()
    
    async def enviar_lembrete(self, lembrete_data):
        """Envia um lembrete específico"""
        try:
            lembrete_id, user_id, guild_id, channel_id, mensagem, remind_at = lembrete_data
            
            # Buscar usuário e canal
            user = self.bot.get_user(user_id)
            channel = self.bot.get_channel(channel_id)
            
            if not user or not channel:
                logger.warning(f"Usuário ou canal não encontrado para lembrete {lembrete_id}")
                await self.marcar_lembrete_enviado(lembrete_id)
                return
            
            # Criar embed do lembrete
            embed = discord.Embed(
                title=f"{EMOJIS['reminder']} Lembrete!",
                description=mensagem,
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            embed.set_footer(text=f"Lembrete para {user.display_name}")
            
            # Tentar enviar no canal
            try:
                await channel.send(f"{user.mention}", embed=embed)
            except discord.Forbidden:
                # Se não conseguir enviar no canal, tentar DM
                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    logger.warning(f"Não foi possível enviar lembrete {lembrete_id}")
            
            # Marcar como enviado
            await self.marcar_lembrete_enviado(lembrete_id)
            logger.info(f"Lembrete {lembrete_id} enviado para {user}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete: {e}")
    
    async def marcar_lembrete_enviado(self, lembrete_id):
        """Marca um lembrete como enviado"""
        await DatabaseManager.execute_query(
            "UPDATE reminders SET is_sent = 1 WHERE id = ?",
            (lembrete_id,)
        )
    
    def parse_tempo(self, tempo_str):
        """Converte string de tempo em timedelta"""
        # Regex para capturar número e unidade
        pattern = r'(\d+)([smhd])'
        match = re.match(pattern, tempo_str.lower())
        
        if not match:
            return None
        
        valor, unidade = match.groups()
        valor = int(valor)
        
        if unidade == 's':
            return timedelta(seconds=valor)
        elif unidade == 'm':
            return timedelta(minutes=valor)
        elif unidade == 'h':
            return timedelta(hours=valor)
        elif unidade == 'd':
            return timedelta(days=valor)
        
        return None
    
    def format_tempo(self, tempo_delta):
        """Formata timedelta em string legível"""
        segundos = int(tempo_delta.total_seconds())
        
        if segundos < 60:
            return f"{segundos} segundo(s)"
        elif segundos < 3600:
            return f"{segundos // 60} minuto(s)"
        elif segundos < 86400:
            return f"{segundos // 3600} hora(s)"
        else:
            return f"{segundos // 86400} dia(s)"

async def setup(bot):
    await bot.add_cog(LembretesCog(bot))
