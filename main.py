import os
import asyncio
import logging
from discord.ext import commands
import discord
from config import BOT_TOKEN, DATABASE_PATH
from database import init_database

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProdutividadeBot(commands.Bot):
    """Bot principal de produtividade para Discord"""
    
    def __init__(self):
        # Configuração de intents necessários
        intents = discord.Intents.default()
        intents.reactions = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        """Configuração inicial do bot"""
        logger.info("Iniciando configuração do bot...")
        
        # Inicializar banco de dados
        await init_database()
        
        # Carregar cogs (módulos de funcionalidades)
        cogs_to_load = [
            'cogs.enquetes',
            'cogs.lembretes', 
            'cogs.mensagens_programadas',
            'cogs.contadores',
            'cogs.tarefas'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Cog {cog} carregado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao carregar cog {cog}: {e}")
        
        # Sincronizar comandos slash
        try:
            synced = await self.tree.sync()
            logger.info(f"Sincronizados {len(synced)} comandos slash")
        except Exception as e:
            logger.error(f"Erro ao sincronizar comandos: {e}")
    
    async def on_ready(self):
        """Evento disparado quando o bot está pronto"""
        logger.info(f'{self.user} está online e funcionando!')
        logger.info(f'Bot conectado em {len(self.guilds)} servidor(es)')
        
        # Definir status do bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="sua produtividade 📈"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """Tratamento global de erros"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        logger.error(f"Erro no comando {ctx.command}: {error}")
        
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Ocorreu um erro: {str(error)}",
            color=discord.Color.red()
        )
        
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass

async def main():
    """Função principal para executar o bot"""
    bot = ProdutividadeBot()
    
    # Verificar se o token está configurado
    if not BOT_TOKEN:
        logger.error("TOKEN do bot não configurado! Verifique as variáveis de ambiente.")
        return
    
    try:
        await bot.start(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Token inválido! Verifique o token do bot.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot desligado pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
