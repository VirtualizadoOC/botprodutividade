import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
from datetime import datetime, timedelta
from database import DatabaseManager
from config import EMOJIS, DEFAULT_COLOR, MAX_POLL_OPTIONS
import logging

logger = logging.getLogger(__name__)

class EnquetesCog(commands.Cog):
    """Sistema de enquetes interativas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    @app_commands.command(name="enquete", description="Criar uma enquete interativa")
    @app_commands.describe(
        titulo="Título da enquete",
        opcoes="Opções separadas por | (até 10 opções)",
        duracao="Duração em minutos (opcional, padrão: sem limite)"
    )
    async def criar_enquete(
        self, 
        interaction: discord.Interaction, 
        titulo: str, 
        opcoes: str,
        duracao: int = None
    ):
        """Cria uma nova enquete"""
        try:
            # Validar opções
            lista_opcoes = [opcao.strip() for opcao in opcoes.split('|')]
            
            if len(lista_opcoes) < 2:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Você precisa fornecer pelo menos 2 opções!",
                    ephemeral=True
                )
                return
            
            if len(lista_opcoes) > MAX_POLL_OPTIONS:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Máximo de {MAX_POLL_OPTIONS} opções permitidas!",
                    ephemeral=True
                )
                return
            
            # Calcular data de expiração
            expires_at = None
            duracao_texto = "Sem limite de tempo"
            
            if duracao:
                expires_at = datetime.now() + timedelta(minutes=duracao)
                duracao_texto = f"{duracao} minutos"
            
            # Criar embed da enquete
            embed = discord.Embed(
                title=f"{EMOJIS['poll']} {titulo}",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            # Adicionar opções ao embed
            opcoes_texto = ""
            for i, opcao in enumerate(lista_opcoes):
                opcoes_texto += f"{self.number_emojis[i]} {opcao}\n"
            
            embed.add_field(name="Opções:", value=opcoes_texto, inline=False)
            embed.add_field(name="Duração:", value=duracao_texto, inline=True)
            embed.add_field(name="Votos:", value="0", inline=True)
            embed.set_footer(text=f"Criado por {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            
            # Adicionar reações
            for i in range(len(lista_opcoes)):
                await message.add_reaction(self.number_emojis[i])
            
            # Salvar no banco de dados
            await DatabaseManager.execute_query(
                '''INSERT INTO polls (guild_id, channel_id, message_id, author_id, title, options, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    interaction.guild_id,
                    interaction.channel_id,
                    message.id,
                    interaction.user.id,
                    titulo,
                    json.dumps(lista_opcoes),
                    expires_at
                )
            )
            
            logger.info(f"Enquete criada por {interaction.user} no servidor {interaction.guild.name}")
            
            # Agendar fechamento automático se houver duração
            if duracao:
                await asyncio.sleep(duracao * 60)
                await self.fechar_enquete_automaticamente(message.id)
                
        except Exception as e:
            logger.error(f"Erro ao criar enquete: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao criar enquete: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="fechar_enquete", description="Fechar uma enquete e mostrar resultados")
    @app_commands.describe(message_id="ID da mensagem da enquete")
    async def fechar_enquete(self, interaction: discord.Interaction, message_id: str):
        """Fecha uma enquete manualmente"""
        try:
            msg_id = int(message_id)
            
            # Buscar enquete no banco
            poll_data = await DatabaseManager.fetch_one(
                "SELECT * FROM polls WHERE message_id = ? AND guild_id = ? AND is_active = 1",
                (msg_id, interaction.guild_id)
            )
            
            if not poll_data:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Enquete não encontrada ou já finalizada!",
                    ephemeral=True
                )
                return
            
            # Verificar se o usuário pode fechar a enquete
            if poll_data[4] != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Apenas o criador da enquete ou moderadores podem fechá-la!",
                    ephemeral=True
                )
                return
            
            await self.finalizar_enquete(msg_id, interaction.channel)
            await interaction.response.send_message(
                f"{EMOJIS['check']} Enquete finalizada com sucesso!",
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                f"{EMOJIS['cross']} ID de mensagem inválido!",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro ao fechar enquete: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao fechar enquete: {str(e)}",
                ephemeral=True
            )
    
    async def fechar_enquete_automaticamente(self, message_id):
        """Fecha uma enquete automaticamente após o tempo limite"""
        try:
            # Buscar o canal da enquete
            poll_data = await DatabaseManager.fetch_one(
                "SELECT channel_id FROM polls WHERE message_id = ? AND is_active = 1",
                (message_id,)
            )
            
            if poll_data:
                channel = self.bot.get_channel(poll_data[0])
                if channel:
                    await self.finalizar_enquete(message_id, channel)
                    
        except Exception as e:
            logger.error(f"Erro ao fechar enquete automaticamente: {e}")
    
    async def finalizar_enquete(self, message_id, channel):
        """Finaliza uma enquete e mostra os resultados"""
        try:
            # Marcar como inativa
            await DatabaseManager.execute_query(
                "UPDATE polls SET is_active = 0 WHERE message_id = ?",
                (message_id,)
            )
            
            # Buscar dados da enquete
            poll_data = await DatabaseManager.fetch_one(
                "SELECT title, options FROM polls WHERE message_id = ?",
                (message_id,)
            )
            
            if not poll_data:
                return
            
            titulo, opcoes_json = poll_data
            opcoes = json.loads(opcoes_json)
            
            # Buscar a mensagem original
            try:
                message = await channel.fetch_message(message_id)
                
                # Contar votos
                votos = [0] * len(opcoes)
                total_votos = 0
                
                for i, emoji in enumerate(self.number_emojis[:len(opcoes)]):
                    for reaction in message.reactions:
                        if str(reaction.emoji) == emoji:
                            votos[i] = reaction.count - 1  # -1 para excluir a reação do bot
                            total_votos += votos[i]
                
                # Criar embed de resultados
                embed = discord.Embed(
                    title=f"{EMOJIS['poll']} Resultados da Enquete: {titulo}",
                    color=DEFAULT_COLOR,
                    timestamp=datetime.now()
                )
                
                resultados_texto = ""
                for i, (opcao, votos_opcao) in enumerate(zip(opcoes, votos)):
                    porcentagem = (votos_opcao / total_votos * 100) if total_votos > 0 else 0
                    barra = "█" * int(porcentagem / 10) + "░" * (10 - int(porcentagem / 10))
                    resultados_texto += f"{self.number_emojis[i]} **{opcao}**\n"
                    resultados_texto += f"`{barra}` {votos_opcao} votos ({porcentagem:.1f}%)\n\n"
                
                embed.add_field(name="Resultados:", value=resultados_texto, inline=False)
                embed.add_field(name="Total de Votos:", value=str(total_votos), inline=True)
                embed.set_footer(text="Enquete finalizada")
                
                await channel.send(embed=embed)
                
            except discord.NotFound:
                logger.warning(f"Mensagem da enquete {message_id} não encontrada")
                
        except Exception as e:
            logger.error(f"Erro ao finalizar enquete: {e}")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Monitora reações em enquetes"""
        if user.bot:
            return
            
        try:
            # Verificar se é uma enquete ativa
            poll_data = await DatabaseManager.fetch_one(
                "SELECT id, options FROM polls WHERE message_id = ? AND is_active = 1",
                (reaction.message.id,)
            )
            
            if not poll_data:
                return
            
            poll_id, opcoes_json = poll_data
            opcoes = json.loads(opcoes_json)
            
            # Verificar se a reação é válida
            emoji_str = str(reaction.emoji)
            if emoji_str in self.number_emojis[:len(opcoes)]:
                option_index = self.number_emojis.index(emoji_str)
                
                # Registrar ou atualizar voto
                await DatabaseManager.execute_query(
                    '''INSERT OR REPLACE INTO poll_votes (poll_id, user_id, option_index)
                       VALUES (?, ?, ?)''',
                    (poll_id, user.id, option_index)
                )
                
                # Remover outras reações do usuário
                for i, emoji in enumerate(self.number_emojis[:len(opcoes)]):
                    if i != option_index:
                        try:
                            await reaction.message.remove_reaction(emoji, user)
                        except:
                            pass
                            
        except Exception as e:
            logger.error(f"Erro ao processar reação: {e}")

async def setup(bot):
    await bot.add_cog(EnquetesCog(bot))
