# Bot Discord de Produtividade 🤖

Um bot completo para Discord focado em produtividade, com funcionalidades de enquetes, lembretes, mensagens programadas, contadores regressivos e gerenciamento de tarefas.

## 🚀 Funcionalidades

### 📊 Enquetes Interativas
- Criação de enquetes com até 10 opções
- Sistema de votação com reações
- Controle de duração automática
- Resultados com gráficos visuais

### ⏰ Sistema de Lembretes
- Lembretes personalizados com tempo flexível
- Notificações automáticas no canal ou DM
- Gerenciamento de lembretes ativos
- Formatos de tempo: 5m, 2h, 1d, etc.

### 📅 Mensagens Programadas
- Agendamento de mensagens para canais específicos
- Suporte a mensagens recorrentes
- Controle total por moderadores
- Interface intuitiva de gerenciamento

### ⏳ Contadores Regressivos
- Contadores visuais para eventos
- Atualização automática a cada 5 minutos
- Notificações quando eventos chegam
- Suporte a múltiplos contadores

### 📝 Lista de Tarefas (To-do)
- Sistema completo de gerenciamento de tarefas
- Prioridades com cores (Alta 🔴, Média 🟡, Baixa 🟢)
- Prazos e notificações de atraso
- Estatísticas de produtividade

## 📋 Comandos Disponíveis

### Enquetes
- `/enquete <título> <opções> [duração]` - Criar uma enquete
- `/fechar_enquete <message_id>` - Fechar enquete manualmente

### Lembretes
- `/lembrete <tempo> <mensagem>` - Criar um lembrete
- `/meus_lembretes` - Ver lembretes ativos
- `/cancelar_lembrete <id>` - Cancelar lembrete

### Mensagens Programadas
- `/agendar_mensagem <canal> <tempo> <mensagem> [repetir]` - Agendar mensagem
- `/mensagens_agendadas` - Ver mensagens agendadas
- `/cancelar_mensagem <id>` - Cancelar mensagem

### Contadores
- `/contador <título> <data> [hora]` - Criar contador regressivo
- `/meus_contadores` - Ver contadores ativos
- `/parar_contador <id>` - Parar contador

### Tarefas
- `/adicionar_tarefa <título> [descrição] [prioridade] [prazo]` - Adicionar tarefa
- `/minhas_tarefas [status] [prioridade]` - Ver tarefas
- `/concluir_tarefa <id>` - Marcar como concluída
- `/editar_tarefa <id> [novo_título] [nova_descrição] [nova_prioridade]` - Editar
- `/remover_tarefa <id>` - Remover tarefa

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- **discord.py** - Biblioteca oficial do Discord
- **SQLite** - Banco de dados local
- **APScheduler** - Agendamento de tarefas
- **aiosqlite** - SQLite assíncrono

## 📦 Estrutura do Projeto

