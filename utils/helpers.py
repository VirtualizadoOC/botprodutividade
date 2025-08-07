from datetime import datetime, timedelta
import re
import discord
from config import EMOJIS

def format_datetime(dt):
    """Formata datetime para exibição amigável"""
    if not dt:
        return "Não definido"
    
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    return dt.strftime("%d/%m/%Y às %H:%M")

def parse_duration(duration_str):
    """
    Converte string de duração em timedelta
    Formatos aceitos: 5m, 2h, 1d, 30s
    """
    pattern = r'(\d+)([smhd])'
    match = re.match(pattern, duration_str.lower().strip())
    
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    units = {
        's': 'seconds',
        'm': 'minutes', 
        'h': 'hours',
        'd': 'days'
    }
    
    if unit in units:
        return timedelta(**{units[unit]: value})
    
    return None

def format_duration(td):
    """Formata timedelta em texto legível"""
    if not td:
        return "Duração inválida"
    
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} segundo(s)"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minuto(s)"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hora(s)"
    else:
        days = total_seconds // 86400
        return f"{days} dia(s)"

def create_progress_bar(current, total, length=20):
    """Cria uma barra de progresso visual"""
    if total == 0:
        return "░" * length
    
    progress = min(1.0, current / total)
    filled = int(progress * length)
    empty = length - filled
    
    return "█" * filled + "░" * empty

def truncate_text(text, max_length=100):
    """Trunca texto se for muito longo"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def create_embed_template(title, description=None, color=None):
    """Cria um embed base com formatação padrão"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    return embed

def get_emoji(emoji_name):
    """Retorna emoji configurado ou fallback"""
    return EMOJIS.get(emoji_name, "❓")

def validate_date_format(date_str):
    """Valida formato de data DD/MM/AAAA"""
    pattern = r'^(\d{1,2})/(\d{1,2})/(\d{4})$'
    match = re.match(pattern, date_str)
    
    if not match:
        return False
    
    day, month, year = map(int, match.groups())
    
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False

def validate_time_format(time_str):
    """Valida formato de hora HH:MM"""
    pattern = r'^(\d{1,2}):(\d{2})$'
    match = re.match(pattern, time_str)
    
    if not match:
        return False
    
    hour, minute = map(int, match.groups())
    
    return 0 <= hour <= 23 and 0 <= minute <= 59

def calculate_relative_time(target_datetime):
    """Calcula tempo relativo até uma data"""
    now = datetime.now()
    
    if target_datetime <= now:
        return "No passado"
    
    delta = target_datetime - now
    
    if delta.days > 0:
        return f"Em {delta.days} dia(s)"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"Em {hours} hora(s)"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"Em {minutes} minuto(s)"
    else:
        return "Em menos de 1 minuto"

def format_user_mention(user):
    """Formata menção de usuário de forma segura"""
    if not user:
        return "Usuário desconhecido"
    
    return f"{user.display_name} ({user.mention})"

def clean_string(text, max_length=None):
    """Limpa e formata string"""
    if not text:
        return ""
    
    # Remove caracteres de controle
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Remove espaços extras
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned

def get_priority_display(priority_level):
    """Retorna exibição formatada da prioridade"""
    priority_map = {
        1: "🔴 Alta",
        2: "🟡 Média", 
        3: "🟢 Baixa"
    }
    
    return priority_map.get(priority_level, "❓ Desconhecida")

def is_valid_discord_id(id_str):
    """Verifica se é um ID válido do Discord"""
    try:
        discord_id = int(id_str)
        # IDs do Discord são números de 64 bits
        return 0 < discord_id < 2**64
    except (ValueError, TypeError):
        return False

def format_list_items(items, max_items=10):
    """Formata lista de itens para exibição"""
    if not items:
        return "Nenhum item encontrado"
    
    formatted_items = []
    
    for i, item in enumerate(items[:max_items], 1):
        formatted_items.append(f"{i}. {item}")
    
    result = "\n".join(formatted_items)
    
    if len(items) > max_items:
        result += f"\n... e mais {len(items) - max_items} item(s)"
    
    return result
