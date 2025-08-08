import sqlite3
import aiosqlite
import asyncio
import logging
from datetime import datetime
from config import DATABASE_PATH, DB_CONFIG

logger = logging.getLogger(__name__)

async def init_database():
    """Inicializa o banco de dados e cria as tabelas necessárias"""
    try:
        async with aiosqlite.connect(DATABASE_PATH, **DB_CONFIG) as db:
            # Tabela de enquetes
            await db.execute('''
                CREATE TABLE IF NOT EXISTS polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    options TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabela de votos das enquetes
            await db.execute('''
                CREATE TABLE IF NOT EXISTS poll_votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poll_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    option_index INTEGER NOT NULL,
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (poll_id) REFERENCES polls (id),
                    UNIQUE(poll_id, user_id)
                )
            ''')
            
            # Tabela de lembretes
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER, -- REMOVIDO: NOT NULL para permitir lembretes em DMs
                    channel_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    remind_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sent BOOLEAN DEFAULT 0
                )
            ''')
            
            # Tabela de mensagens programadas
            await db.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    send_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sent BOOLEAN DEFAULT 0,
                    repeat_interval TEXT
                )
            ''')
            
            # Tabela de contadores regressivos
            await db.execute('''
                CREATE TABLE IF NOT EXISTS countdowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    target_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabela de tarefas
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    is_completed BOOLEAN DEFAULT 0,
                    priority INTEGER DEFAULT 1,
                    due_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            await db.commit()
            logger.info("Banco de dados inicializado com sucesso")
            
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

class DatabaseManager:
    """Gerenciador de operações do banco de dados"""
    
    @staticmethod
    async def execute_query(query, params=None):
        """Executa uma query SQL"""
        try:
            async with aiosqlite.connect(DATABASE_PATH, **DB_CONFIG) as db:
                if params:
                    cursor = await db.execute(query, params)
                else:
                    cursor = await db.execute(query)
                await db.commit()
                return cursor
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            raise
    
    @staticmethod
    async def fetch_one(query, params=None):
        """Busca um registro"""
        try:
            async with aiosqlite.connect(DATABASE_PATH, **DB_CONFIG) as db:
                if params:
                    cursor = await db.execute(query, params)
                else:
                    cursor = await db.execute(query)
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Erro ao buscar registro: {e}")
            return None
    
    @staticmethod
    async def fetch_all(query, params=None):
        """Busca todos os registros"""
        try:
            async with aiosqlite.connect(DATABASE_PATH, **DB_CONFIG) as db:
                if params:
                    cursor = await db.execute(query, params)
                else:
                    cursor = await db.execute(query)
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao buscar registros: {e}")
            return []

