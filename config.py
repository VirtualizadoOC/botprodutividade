import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# Configurações do bot
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')

# Configurações de agendamento
TIMEZONE = 'America/Sao_Paulo'

# Configurações de embed padrão
DEFAULT_COLOR = 0x00ff00  # Verde
ERROR_COLOR = 0xff0000    # Vermelho
WARNING_COLOR = 0xffff00  # Amarelo
INFO_COLOR = 0x0099ff     # Azul

# Emojis utilizados no bot
EMOJIS = {
    'check': '✅',
    'cross': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'clock': '⏰',
    'calendar': '📅',
    'task': '📝',
    'poll': '📊',
    'reminder': '🔔',
    'countdown': '⏳',
    'message': '💬'
}

# Configurações de limite
MAX_POLL_OPTIONS = 10
MAX_REMINDER_DAYS = 365
MAX_TASKS_PER_USER = 50
MAX_MESSAGE_LENGTH = 2000

# Configurações de banco de dados
DB_CONFIG = {
    'timeout': 30,
    'check_same_thread': False
}
