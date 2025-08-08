import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
from database import DatabaseManager
from config import EMOJIS, DEFAULT_COLOR, MAX_MESSAGE_LENGTH
import logging
import re

logger = logging.getLogger(__name__)

class MensagensProgramadasCog(commands.Cog):
    """Sistema de mensagens programadas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.verificar_mensagens.start()
    
    def cog_unload(self):
        self.verificar_mensagens.cancel()
    
    @app_commands.command(name="agendar_mensagem", description="Agendar uma mensagem para ser enviada")
    @app_commands.describe(
        canal="Canal onde a mensagem será enviada",
        tempo="Quando enviar (ex: 30m, 2h, 1d)",
        mensagem="Mensagem a ser enviada",
        repetir="Repetir a cada X tempo (opcional, ex: 1d para diário)"
    )
    async def agendar_mensagem(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        tempo: str,
        mensagem: str,
        repetir: str = None
    ):
        """Agenda uma mensagem para ser enviada"""
        try:
            # Verificar permissões
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Você precisa da permissão 'Gerenciar Mensagens' para usar este comando!",
                    ephemeral=True
                )
                return
            
            # Verificar se o bot pode enviar mensagens no canal
            if not canal.permissions_for(interaction.guild.me).send_messages:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Não tenho permissão para enviar mensagens em {canal.mention}!",
                    ephemeral=True
                )
                return
            
            # Validar tamanho da mensagem
            if len(mensagem) > MAX_MESSAGE_LENGTH:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} A mensagem não pode ter mais que {MAX_MESSAGE_LENGTH} caracteres!",
                    ephemeral=True
                )
                return
            
            # Parsear o tempo
            tempo_delta = self.parse_tempo(tempo)
            if not tempo_delta:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Formato de tempo inválido! Use: 5m, 2h, 1d, etc.",
                    ephemeral=True
                )
                return
            
            # Validar intervalo de repetição se fornecido
            repeat_interval = None
            if repetir:
                repeat_delta = self.parse_tempo(repetir)
                if not repeat_delta:
                    await interaction.response.send_message(
                        f"{EMOJIS['cross']} Formato de repetição inválido!",
                        ephemeral=True
                    )
                    return
                repeat_interval = repetir
            
            # Calcular data de envio
            send_at = datetime.now() + tempo_delta
            
            # Salvar no banco de dados
            await DatabaseManager.execute_query(
                '''INSERT INTO scheduled_messages 
                   (guild_id, channel_id, author_id, message, send_at, repeat_interval)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    interaction.guild_id,
                    canal.id,
                    interaction.user.id,
                    mensagem,
                    send_at,
                    repeat_interval
                )
            )
            
            # Criar embed de confirmação
            embed = discord.Embed(
                title=f"{EMOJIS['message']} Mensagem Agendada",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Canal:", value=canal.mention, inline=True)
            embed.add_field(
                name="Envio em:", 
                value=f"<t:{int(send_at.timestamp())}:F>", 
                inline=True
            )
            
            if repeat_interval:
                embed.add_field(name="Repetir:", value=f"A cada {repetir}", inline=True)
            
            # Truncar mensagem para preview
            preview = mensagem[:200] + "..." if len(mensagem) > 200 else mensagem
            embed.add_field(name="Mensagem:", value=f"```{preview}```", inline=False)
            
            embed.set_footer(text=f"Agendado por {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f"Mensagem agendada por {interaction.user} para {send_at}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar mensagem: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao agendar mensagem: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="mensagens_agendadas", description="Ver mensagens agendadas")
    async def mensagens_agendadas(self, interaction: discord.Interaction):
        """Mostra as mensagens agendadas do servidor"""
        try:
            # Verificar permissões
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Você precisa da permissão 'Gerenciar Mensagens' para usar este comando!",
                    ephemeral=True
                )
                return
            
            # Buscar mensagens agendadas
            mensagens = await DatabaseManager.fetch_all(
                '''SELECT id, channel_id, author_id, message, send_at, repeat_interval 
                   FROM scheduled_messages 
                   WHERE guild_id = ? AND is_sent = 0 
                   ORDER BY send_at ASC''',
                (interaction.guild_id,)
            )
            
            if not mensagens:
                embed = discord.Embed(
                    title=f"{EMOJIS['info']} Mensagens Agendadas",
                    description="Não há mensagens agendadas neste servidor.",
                    color=DEFAULT_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"{EMOJIS['message']} Mensagens Agendadas",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            for i, (msg_id, channel_id, author_id, mensagem, send_at, repeat_interval) in enumerate(mensagens[:10], 1):
                send_datetime = datetime.fromisoformat(send_at.replace('Z', '+00:00'))
                canal = self.bot.get_channel(channel_id)
                autor = self.bot.get_user(author_id)
                
                canal_nome = canal.name if canal else "Canal removido"
                autor_nome = autor.display_name if autor else "Usuário desconhecido"
                
                valor = f"**Canal:** #{canal_nome}\n"
                valor += f"**Autor:** {autor_nome}\n"
                valor += f"**Quando:** <t:{int(send_datetime.timestamp())}:R>\n"
                
                if repeat_interval:
                    valor += f"**Repetir:** A cada {repeat_interval}\n"
                
                # Preview da mensagem
                preview = mensagem[:50] + "..." if len(mensagem) > 50 else mensagem
                valor += f"**Mensagem:** {preview}"
                
                embed.add_field(
                    name=f"{i}. ID: {msg_id}",
                    value=valor,
                    inline=False
                )
            
            if len(mensagens) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(mensagens)} mensagens")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens agendadas: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao buscar mensagens: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="cancelar_mensagem", description="Cancelar uma mensagem agendada")
    @app_commands.describe(mensagem_id="ID da mensagem para cancelar")
    async def cancelar_mensagem(self, interaction: discord.Interaction, mensagem_id: int):
        """Cancela uma mensagem agendada"""
        try:
            # Verificar permissões
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Você precisa da permissão 'Gerenciar Mensagens' para usar este comando!",
                    ephemeral=True
                )
                return
            
            # Verificar se a mensagem existe
            mensagem = await DatabaseManager.fetch_one(
                '''SELECT message FROM scheduled_messages 
                   WHERE id = ? AND guild_id = ? AND is_sent = 0''',
                (mensagem_id, interaction.guild_id)
            )
            
            if not mensagem:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Mensagem não encontrada ou já foi enviada!",
                    ephemeral=True
                )
                return
            
            # Marcar como enviada (cancelada)
            await DatabaseManager.execute_query(
                "UPDATE scheduled_messages SET is_sent = 1 WHERE id = ?",
                (mensagem_id,)
            )
            
            embed = discord.Embed(
                title=f"{EMOJIS['check']} Mensagem Cancelada",
                description=f"Mensagem agendada foi cancelada com sucesso.",
                color=DEFAULT_COLOR
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Mensagem agendada {mensagem_id} cancelada por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao cancelar mensagem: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao cancelar mensagem: {str(e)}",
                ephemeral=True
            )
    
    @tasks.loop(seconds=60)  # Verificar a cada minuto
    async def verificar_mensagens(self):
        """Task que verifica mensagens que devem ser enviadas"""
        try:
            # Buscar mensagens que devem ser enviadas
            mensagens = await DatabaseManager.fetch_all(
                '''SELECT id, guild_id, channel_id, message, send_at, repeat_interval 
                   FROM scheduled_messages 
                   WHERE send_at <= ? AND is_sent = 0''',
                (datetime.now(),)
            )
            
            for mensagem in mensagens:
                await self.enviar_mensagem_programada(mensagem)
                
        except Exception as e:
            logger.error(f"Erro ao verificar mensagens programadas: {e}")
    
    @verificar_mensagens.before_loop
    async def before_verificar_mensagens(self):
        await self.bot.wait_until_ready()
    
    async def enviar_mensagem_programada(self, mensagem_data):
        """Envia uma mensagem programada"""
        try:
            msg_id, guild_id, channel_id, mensagem, send_at, repeat_interval = mensagem_data
            
            # Buscar canal
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.warning(f"Canal não encontrado para mensagem {msg_id}")
                await self.marcar_mensagem_enviada(msg_id)
                return
            
            # Tentar enviar mensagem
            try:
                await channel.send(mensagem)
                logger.info(f"Mensagem programada {msg_id} enviada")
            except discord.Forbidden:
                logger.warning(f"Sem permissão para enviar mensagem {msg_id}")
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem {msg_id}: {e}")
            
            # Se tem repetição, agendar próximo envio
            if repeat_interval:
                await self.reagendar_mensagem(msg_id, repeat_interval)
            else:
                await self.marcar_mensagem_enviada(msg_id)
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem programada: {e}")
    
    async def reagendar_mensagem(self, msg_id, repeat_interval):
        """Reagenda uma mensagem repetitiva"""
        try:
            # Calcular próximo envio
            tempo_delta = self.parse_tempo(repeat_interval)
            if tempo_delta:
                next_send = datetime.now() + tempo_delta
                
                await DatabaseManager.execute_query(
                    "UPDATE scheduled_messages SET send_at = ? WHERE id = ?",
                    (next_send, msg_id)
                )
                
                logger.info(f"Mensagem {msg_id} reagendada para {next_send}")
            else:
                await self.marcar_mensagem_enviada(msg_id)
                
        except Exception as e:
            logger.error(f"Erro ao reagendar mensagem: {e}")
    
    async def marcar_mensagem_enviada(self, msg_id):
        """Marca uma mensagem como enviada"""
        await DatabaseManager.execute_query(
            "UPDATE scheduled_messages SET is_sent = 1 WHERE id = ?",
            (msg_id,)
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

async def setup(bot):
    await bot.add_cog(MensagensProgramadasCog(bot))
