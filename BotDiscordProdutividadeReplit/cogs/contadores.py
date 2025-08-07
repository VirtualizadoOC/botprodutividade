import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
from database import DatabaseManager
from config import EMOJIS, DEFAULT_COLOR
import logging

logger = logging.getLogger(__name__)

class ContadoresCog(commands.Cog):
    """Sistema de contadores regressivos"""
    
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_contadores.start()
    
    def cog_unload(self):
        self.atualizar_contadores.cancel()
    
    @app_commands.command(name="contador", description="Criar um contador regressivo")
    @app_commands.describe(
        titulo="Título do evento",
        data="Data do evento (DD/MM/AAAA)",
        hora="Hora do evento (HH:MM, opcional)"
    )
    async def criar_contador(
        self,
        interaction: discord.Interaction,
        titulo: str,
        data: str,
        hora: str = "00:00"
    ):
        """Cria um novo contador regressivo"""
        try:
            # Parsear data e hora
            target_datetime = self.parse_datetime(data, hora)
            
            if not target_datetime:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Formato de data/hora inválido! Use DD/MM/AAAA para data e HH:MM para hora.",
                    ephemeral=True
                )
                return
            
            # Verificar se a data não é no passado
            if target_datetime <= datetime.now():
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} A data do evento deve ser no futuro!",
                    ephemeral=True
                )
                return
            
            # Criar embed inicial do contador
            embed = self.criar_embed_contador(titulo, target_datetime)
            
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            
            # Salvar no banco de dados
            await DatabaseManager.execute_query(
                '''INSERT INTO countdowns (guild_id, channel_id, message_id, author_id, title, target_date)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    interaction.guild_id,
                    interaction.channel_id,
                    message.id,
                    interaction.user.id,
                    titulo,
                    target_datetime
                )
            )
            
            logger.info(f"Contador criado por {interaction.user} para {target_datetime}")
            
        except Exception as e:
            logger.error(f"Erro ao criar contador: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao criar contador: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="meus_contadores", description="Ver seus contadores ativos")
    async def meus_contadores(self, interaction: discord.Interaction):
        """Mostra os contadores ativos do usuário"""
        try:
            # Buscar contadores do usuário
            contadores = await DatabaseManager.fetch_all(
                '''SELECT id, title, target_date FROM countdowns 
                   WHERE author_id = ? AND guild_id = ? AND is_active = 1
                   ORDER BY target_date ASC''',
                (interaction.user.id, interaction.guild_id)
            )
            
            if not contadores:
                embed = discord.Embed(
                    title=f"{EMOJIS['info']} Seus Contadores",
                    description="Você não tem contadores ativos.",
                    color=DEFAULT_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"{EMOJIS['countdown']} Seus Contadores Ativos",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            for i, (contador_id, titulo, target_date) in enumerate(contadores[:10], 1):
                target_datetime = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                tempo_restante = self.calcular_tempo_restante(target_datetime)
                
                embed.add_field(
                    name=f"{i}. {titulo} (ID: {contador_id})",
                    value=f"**Data:** <t:{int(target_datetime.timestamp())}:F>\n"
                          f"**Tempo restante:** {tempo_restante}",
                    inline=False
                )
            
            if len(contadores) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(contadores)} contadores")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao buscar contadores: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao buscar contadores: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="parar_contador", description="Parar um contador regressivo")
    @app_commands.describe(contador_id="ID do contador para parar")
    async def parar_contador(self, interaction: discord.Interaction, contador_id: int):
        """Para um contador específico"""
        try:
            # Verificar se o contador existe e pertence ao usuário
            contador = await DatabaseManager.fetch_one(
                '''SELECT title FROM countdowns 
                   WHERE id = ? AND author_id = ? AND guild_id = ? AND is_active = 1''',
                (contador_id, interaction.user.id, interaction.guild_id)
            )
            
            if not contador:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Contador não encontrado ou você não é o autor!",
                    ephemeral=True
                )
                return
            
            # Marcar como inativo
            await DatabaseManager.execute_query(
                "UPDATE countdowns SET is_active = 0 WHERE id = ?",
                (contador_id,)
            )
            
            embed = discord.Embed(
                title=f"{EMOJIS['check']} Contador Parado",
                description=f"Contador **{contador[0]}** foi parado com sucesso.",
                color=DEFAULT_COLOR
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Contador {contador_id} parado por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao parar contador: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao parar contador: {str(e)}",
                ephemeral=True
            )
    
    @tasks.loop(minutes=5)  # Atualizar a cada 5 minutos
    async def atualizar_contadores(self):
        """Task que atualiza os contadores regressivos"""
        try:
            # Buscar contadores ativos
            contadores = await DatabaseManager.fetch_all(
                '''SELECT id, guild_id, channel_id, message_id, title, target_date 
                   FROM countdowns 
                   WHERE is_active = 1'''
            )
            
            for contador in contadores:
                await self.atualizar_contador_individual(contador)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar contadores: {e}")
    
    @atualizar_contadores.before_loop
    async def before_atualizar_contadores(self):
        await self.bot.wait_until_ready()
    
    async def atualizar_contador_individual(self, contador_data):
        """Atualiza um contador individual"""
        try:
            contador_id, guild_id, channel_id, message_id, titulo, target_date = contador_data
            
            # Buscar canal e mensagem
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await self.desativar_contador(contador_id)
                return
            
            target_datetime = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            
            # Verificar se o evento já passou
            if target_datetime <= datetime.now():
                await self.finalizar_contador(contador_id, channel, titulo)
                return
            
            try:
                message = await channel.fetch_message(message_id)
                
                # Criar novo embed
                embed = self.criar_embed_contador(titulo, target_datetime)
                
                # Atualizar mensagem
                await message.edit(embed=embed)
                
            except discord.NotFound:
                # Mensagem foi deletada, desativar contador
                await self.desativar_contador(contador_id)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar contador individual: {e}")
    
    async def finalizar_contador(self, contador_id, channel, titulo):
        """Finaliza um contador quando o evento chega"""
        try:
            # Criar embed de evento finalizado
            embed = discord.Embed(
                title=f"{EMOJIS['countdown']} {titulo}",
                description="🎉 **O evento chegou!** 🎉",
                color=0xffd700,  # Dourado
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Status:",
                value="Evento em andamento!",
                inline=False
            )
            
            # Enviar notificação
            await channel.send("🎉 **EVENTO CHEGOU!** 🎉", embed=embed)
            
            # Desativar contador
            await self.desativar_contador(contador_id)
            
            logger.info(f"Contador {contador_id} finalizado")
            
        except Exception as e:
            logger.error(f"Erro ao finalizar contador: {e}")
    
    async def desativar_contador(self, contador_id):
        """Desativa um contador"""
        await DatabaseManager.execute_query(
            "UPDATE countdowns SET is_active = 0 WHERE id = ?",
            (contador_id,)
        )
    
    def criar_embed_contador(self, titulo, target_datetime):
        """Cria embed do contador"""
        tempo_restante = self.calcular_tempo_restante(target_datetime)
        
        embed = discord.Embed(
            title=f"{EMOJIS['countdown']} {titulo}",
            color=DEFAULT_COLOR,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Data do Evento:",
            value=f"<t:{int(target_datetime.timestamp())}:F>",
            inline=False
        )
        
        embed.add_field(
            name="Tempo Restante:",
            value=f"⏰ **{tempo_restante}**",
            inline=False
        )
        
        # Barra de progresso visual
        total_segundos = (target_datetime - datetime.now()).total_seconds()
        if total_segundos > 0:
            # Calcular progresso baseado em uma semana (exemplo)
            max_segundos = 7 * 24 * 3600  # 1 semana
            progresso = min(1.0, max(0.0, 1 - (total_segundos / max_segundos)))
            
            barra_size = 20
            preenchido = int(progresso * barra_size)
            vazio = barra_size - preenchido
            
            barra = "█" * preenchido + "░" * vazio
            embed.add_field(
                name="Progresso:",
                value=f"`{barra}` {progresso*100:.1f}%",
                inline=False
            )
        
        embed.set_footer(text="Atualizado automaticamente a cada 5 minutos")
        
        return embed
    
    def calcular_tempo_restante(self, target_datetime):
        """Calcula o tempo restante até o evento"""
        agora = datetime.now()
        
        if target_datetime <= agora:
            return "Evento chegou!"
        
        delta = target_datetime - agora
        
        dias = delta.days
        horas, resto = divmod(delta.seconds, 3600)
        minutos, segundos = divmod(resto, 60)
        
        partes = []
        
        if dias > 0:
            partes.append(f"{dias} dia{'s' if dias != 1 else ''}")
        
        if horas > 0:
            partes.append(f"{horas} hora{'s' if horas != 1 else ''}")
        
        if minutos > 0 and dias == 0:  # Só mostrar minutos se for menos de um dia
            partes.append(f"{minutos} minuto{'s' if minutos != 1 else ''}")
        
        if not partes:
            return "Menos de 1 minuto"
        
        return " e ".join(partes)
    
    def parse_datetime(self, data_str, hora_str):
        """Converte strings de data e hora em datetime"""
        try:
            # Parsear data DD/MM/AAAA
            dia, mes, ano = map(int, data_str.split('/'))
            
            # Parsear hora HH:MM
            hora, minuto = map(int, hora_str.split(':'))
            
            return datetime(ano, mes, dia, hora, minuto)
            
        except (ValueError, AttributeError):
            return None

async def setup(bot):
    await bot.add_cog(ContadoresCog(bot))
