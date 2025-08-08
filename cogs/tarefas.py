import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from database import DatabaseManager
from config import EMOJIS, DEFAULT_COLOR, MAX_TASKS_PER_USER
import logging

logger = logging.getLogger(__name__)

class TarefasCog(commands.Cog):
    """Sistema de gerenciamento de tarefas (To-do list)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.priority_emojis = {
            1: "🔴",  # Alta
            2: "🟡",  # Média
            3: "🟢"   # Baixa
        }
        self.priority_names = {
            1: "Alta",
            2: "Média", 
            3: "Baixa"
        }
    
    @app_commands.command(name="adicionar_tarefa", description="Adicionar uma nova tarefa")
    @app_commands.describe(
        titulo="Título da tarefa",
        descricao="Descrição detalhada (opcional)",
        prioridade="Prioridade da tarefa",
        prazo="Prazo em dias (opcional)"
    )
    @app_commands.choices(prioridade=[
        app_commands.Choice(name="🔴 Alta", value=1),
        app_commands.Choice(name="🟡 Média", value=2),
        app_commands.Choice(name="🟢 Baixa", value=3)
    ])
    async def adicionar_tarefa(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descricao: str = None,
        prioridade: int = 2,
        prazo: int = None
    ):
        """Adiciona uma nova tarefa à lista do usuário"""
        try:
            # Verificar limite de tarefas por usuário
            count = await DatabaseManager.fetch_one(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND guild_id = ? AND is_completed = 0",
                (interaction.user.id, interaction.guild_id)
            )
            
            if count and count[0] >= MAX_TASKS_PER_USER:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Você já atingiu o limite de {MAX_TASKS_PER_USER} tarefas ativas!",
                    ephemeral=True
                )
                return
            
            # Calcular data de vencimento se fornecida
            due_date = None
            if prazo:
                due_date = datetime.now() + timedelta(days=prazo)
            
            # Adicionar tarefa ao banco
            cursor = await DatabaseManager.execute_query(
                '''INSERT INTO tasks (user_id, guild_id, title, description, priority, due_date)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    interaction.user.id,
                    interaction.guild_id,
                    titulo,
                    descricao,
                    prioridade,
                    due_date
                )
            )
            
            task_id = cursor.lastrowid
            
            # Criar embed de confirmação
            embed = discord.Embed(
                title=f"{EMOJIS['task']} Nova Tarefa Adicionada",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="ID:", value=str(task_id), inline=True)
            embed.add_field(
                name="Prioridade:", 
                value=f"{self.priority_emojis[prioridade]} {self.priority_names[prioridade]}", 
                inline=True
            )
            
            if due_date:
                embed.add_field(
                    name="Prazo:", 
                    value=f"<t:{int(due_date.timestamp())}:D>", 
                    inline=True
                )
            
            embed.add_field(name="Título:", value=titulo, inline=False)
            
            if descricao:
                embed.add_field(name="Descrição:", value=descricao[:500], inline=False)
            
            embed.set_footer(text=f"Criado por {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f"Tarefa {task_id} criada por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar tarefa: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao adicionar tarefa: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="minhas_tarefas", description="Ver suas tarefas")
    @app_commands.describe(
        status="Filtrar por status",
        prioridade="Filtrar por prioridade"
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(name="Pendentes", value="pending"),
            app_commands.Choice(name="Concluídas", value="completed"),
            app_commands.Choice(name="Todas", value="all")
        ],
        prioridade=[
            app_commands.Choice(name="🔴 Alta", value=1),
            app_commands.Choice(name="🟡 Média", value=2),
            app_commands.Choice(name="🟢 Baixa", value=3)
        ]
    )
    async def minhas_tarefas(
        self,
        interaction: discord.Interaction,
        status: str = "pending",
        prioridade: int = None
    ):
        """Mostra as tarefas do usuário"""
        try:
            # Construir query baseada nos filtros
            query = '''SELECT id, title, description, priority, due_date, is_completed, created_at 
                       FROM tasks WHERE user_id = ? AND guild_id = ?'''
            params = [interaction.user.id, interaction.guild_id]
            
            if status == "pending":
                query += " AND is_completed = 0"
            elif status == "completed":
                query += " AND is_completed = 1"
            
            if prioridade:
                query += " AND priority = ?"
                params.append(prioridade)
            
            query += " ORDER BY priority ASC, due_date ASC, created_at DESC"
            
            tarefas = await DatabaseManager.fetch_all(query, params)
            
            if not tarefas:
                status_text = {
                    "pending": "pendentes",
                    "completed": "concluídas", 
                    "all": ""
                }.get(status, "")
                
                embed = discord.Embed(
                    title=f"{EMOJIS['info']} Suas Tarefas",
                    description=f"Você não tem tarefas {status_text}.",
                    color=DEFAULT_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Criar embed com as tarefas
            embed = discord.Embed(
                title=f"{EMOJIS['task']} Suas Tarefas",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            # Estatísticas
            total = len(tarefas)
            concluidas = sum(1 for t in tarefas if t[5])  # is_completed
            pendentes = total - concluidas
            
            embed.add_field(name="📊 Estatísticas", 
                          value=f"Total: {total} | Pendentes: {pendentes} | Concluídas: {concluidas}",
                          inline=False)
            
            # Mostrar até 10 tarefas
            for i, tarefa in enumerate(tarefas[:10], 1):
                task_id, titulo, descricao, priority, due_date, is_completed, created_at = tarefa
                
                # Status
                status_icon = "✅" if is_completed else "⏳"
                priority_icon = self.priority_emojis[priority]
                
                valor = f"{status_icon} {priority_icon} **{titulo}**\n"
                
                if descricao:
                    desc_preview = descricao[:50] + "..." if len(descricao) > 50 else descricao
                    valor += f"*{desc_preview}*\n"
                
                if due_date and not is_completed:
                    due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    if due_datetime < datetime.now():
                        valor += f"🔥 **ATRASADA** - Prazo: <t:{int(due_datetime.timestamp())}:R>\n"
                    else:
                        valor += f"📅 Prazo: <t:{int(due_datetime.timestamp())}:R>\n"
                
                embed.add_field(
                    name=f"ID: {task_id}",
                    value=valor,
                    inline=False
                )
            
            if len(tarefas) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(tarefas)} tarefas")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao buscar tarefas: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao buscar tarefas: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="concluir_tarefa", description="Marcar tarefa como concluída")
    @app_commands.describe(tarefa_id="ID da tarefa para concluir")
    async def concluir_tarefa(self, interaction: discord.Interaction, tarefa_id: int):
        """Marca uma tarefa como concluída"""
        try:
            # Verificar se a tarefa existe e pertence ao usuário
            tarefa = await DatabaseManager.fetch_one(
                '''SELECT title, is_completed FROM tasks 
                   WHERE id = ? AND user_id = ? AND guild_id = ?''',
                (tarefa_id, interaction.user.id, interaction.guild_id)
            )
            
            if not tarefa:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Tarefa não encontrada!",
                    ephemeral=True
                )
                return
            
            if tarefa[1]:  # is_completed
                await interaction.response.send_message(
                    f"{EMOJIS['warning']} Esta tarefa já está concluída!",
                    ephemeral=True
                )
                return
            
            # Marcar como concluída
            await DatabaseManager.execute_query(
                "UPDATE tasks SET is_completed = 1, completed_at = ? WHERE id = ?",
                (datetime.now(), tarefa_id)
            )
            
            embed = discord.Embed(
                title=f"{EMOJIS['check']} Tarefa Concluída!",
                description=f"**{tarefa[0]}** foi marcada como concluída.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.set_footer(text="Parabéns pela produtividade! 🎉")
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f"Tarefa {tarefa_id} concluída por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao concluir tarefa: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao concluir tarefa: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="editar_tarefa", description="Editar uma tarefa existente")
    @app_commands.describe(
        tarefa_id="ID da tarefa para editar",
        novo_titulo="Novo título (opcional)",
        nova_descricao="Nova descrição (opcional)",
        nova_prioridade="Nova prioridade (opcional)"
    )
    @app_commands.choices(nova_prioridade=[
        app_commands.Choice(name="🔴 Alta", value=1),
        app_commands.Choice(name="🟡 Média", value=2),
        app_commands.Choice(name="🟢 Baixa", value=3)
    ])
    async def editar_tarefa(
        self,
        interaction: discord.Interaction,
        tarefa_id: int,
        novo_titulo: str = None,
        nova_descricao: str = None,
        nova_prioridade: int = None
    ):
        """Edita uma tarefa existente"""
        try:
            # Verificar se a tarefa existe e pertence ao usuário
            tarefa = await DatabaseManager.fetch_one(
                '''SELECT title, description, priority, is_completed FROM tasks 
                   WHERE id = ? AND user_id = ? AND guild_id = ?''',
                (tarefa_id, interaction.user.id, interaction.guild_id)
            )
            
            if not tarefa:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Tarefa não encontrada!",
                    ephemeral=True
                )
                return
            
            if tarefa[3]:  # is_completed
                await interaction.response.send_message(
                    f"{EMOJIS['warning']} Não é possível editar uma tarefa concluída!",
                    ephemeral=True
                )
                return
            
            # Preparar valores para atualização
            updates = []
            params = []
            
            if novo_titulo:
                updates.append("title = ?")
                params.append(novo_titulo)
            
            if nova_descricao is not None:  # Permitir string vazia
                updates.append("description = ?")
                params.append(nova_descricao)
            
            if nova_prioridade:
                updates.append("priority = ?")
                params.append(nova_prioridade)
            
            if not updates:
                await interaction.response.send_message(
                    f"{EMOJIS['warning']} Nenhuma alteração foi especificada!",
                    ephemeral=True
                )
                return
            
            # Atualizar tarefa
            params.append(tarefa_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            
            await DatabaseManager.execute_query(query, params)
            
            # Buscar tarefa atualizada
            tarefa_atualizada = await DatabaseManager.fetch_one(
                '''SELECT title, description, priority FROM tasks WHERE id = ?''',
                (tarefa_id,)
            )
            
            embed = discord.Embed(
                title=f"{EMOJIS['check']} Tarefa Editada",
                color=DEFAULT_COLOR,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="ID:", value=str(tarefa_id), inline=True)
            embed.add_field(
                name="Prioridade:", 
                value=f"{self.priority_emojis[tarefa_atualizada[2]]} {self.priority_names[tarefa_atualizada[2]]}", 
                inline=True
            )
            embed.add_field(name="Título:", value=tarefa_atualizada[0], inline=False)
            
            if tarefa_atualizada[1]:
                embed.add_field(name="Descrição:", value=tarefa_atualizada[1][:500], inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f"Tarefa {tarefa_id} editada por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao editar tarefa: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao editar tarefa: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="remover_tarefa", description="Remover uma tarefa")
    @app_commands.describe(tarefa_id="ID da tarefa para remover")
    async def remover_tarefa(self, interaction: discord.Interaction, tarefa_id: int):
        """Remove uma tarefa"""
        try:
            # Verificar se a tarefa existe e pertence ao usuário
            tarefa = await DatabaseManager.fetch_one(
                '''SELECT title FROM tasks 
                   WHERE id = ? AND user_id = ? AND guild_id = ?''',
                (tarefa_id, interaction.user.id, interaction.guild_id)
            )
            
            if not tarefa:
                await interaction.response.send_message(
                    f"{EMOJIS['cross']} Tarefa não encontrada!",
                    ephemeral=True
                )
                return
            
            # Remover tarefa
            await DatabaseManager.execute_query(
                "DELETE FROM tasks WHERE id = ?",
                (tarefa_id,)
            )
            
            embed = discord.Embed(
                title=f"{EMOJIS['check']} Tarefa Removida",
                description=f"**{tarefa[0]}** foi removida da sua lista.",
                color=DEFAULT_COLOR
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            logger.info(f"Tarefa {tarefa_id} removida por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Erro ao remover tarefa: {e}")
            await interaction.response.send_message(
                f"{EMOJIS['cross']} Erro ao remover tarefa: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(TarefasCog(bot))
