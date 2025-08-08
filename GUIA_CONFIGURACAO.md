# 📚 Guia Completo de Configuração - Bot Discord de Produtividade

Este guia te ajudará a configurar e fazer o deploy do bot Discord de produtividade no Railway.com, mesmo sem conhecimento técnico.

## 🎯 Passo 1: Criando o Bot no Discord

### 1.1 Acessar o Discord Developer Portal

1. Acesse [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Faça login com sua conta Discord
3. Clique em **"New Application"**
4. Digite um nome para sua aplicação (ex: "Bot Produtividade")
5. Clique em **"Create"**

### 1.2 Configurar o Bot

1. No menu lateral, clique em **"Bot"**
2. Clique em **"Add Bot"** (se aparecer)
3. Confirme clicando em **"Yes, do it!"**

### 1.3 Obter o Token do Bot

⚠️ **IMPORTANTE**: O token é como uma senha secreta. NUNCA compartilhe!

1. Na seção "Token", clique em **"Reset Token"**
2. Confirme a ação
3. Clique em **"Copy"** para copiar o token
4. **Guarde este token em local seguro** - você precisará dele depois

### 1.4 Configurar Permissões

1. Ainda na aba "Bot", role para baixo até "Privileged Gateway Intents"
2. Ative as seguintes opções:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent** 
   - ✅ **Message Content Intent**

### 1.5 Gerar Link de Convite

1. No menu lateral, clique em **"OAuth2"** → **"URL Generator"**
2. Em **"Scopes"**, marque:
   - ✅ **bot**
   - ✅ **applications.commands**

3. Em **"Bot Permissions"**, marque:
   - ✅ **Send Messages**
   - ✅ **Use Slash Commands**
   - ✅ **Add Reactions**
   - ✅ **Manage Messages**
   - ✅ **Embed Links**
   - ✅ **Use External Emojis**
   - ✅ **Read Message History**

4. Copie a URL gerada na parte inferior
5. Abra essa URL em uma nova aba
6. Selecione seu servidor Discord
7. Clique em **"Autorizar"**

## 🚂 Passo 2: Configurando o Railway.com

### 2.1 Criar Conta no Railway

1. Acesse [https://railway.app](https://railway.app)
2. Clique em **"Login"**
3. Escolha **"Login with GitHub"** (recomendado)
4. Autorize o Railway a acessar sua conta GitHub

### 2.2 Criar um Novo Projeto

1. No dashboard do Railway, clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Clique em **"Configure GitHub App"**
4. Autorize o Railway a acessar seus repositórios

### 2.3 Preparar o Código no GitHub

Você tem duas opções:

#### Opção A: Fork do Repositório (Mais Fácil)
1. Acesse o repositório do bot no GitHub
2. Clique em **"Fork"** no canto superior direito
3. Confirme a criação do fork

#### Opção B: Criar Repositório do Zero
1. Vá para [https://github.com/new](https://github.com/new)
2. Digite um nome (ex: "discord-bot-produtividade")
3. Marque **"Add a README file"**
4. Clique em **"Create repository"**
5. Faça upload de todos os arquivos do bot

### 2.4 Deploy no Railway

1. De volta ao Railway, clique em **"Deploy from GitHub repo"**
2. Selecione o repositório que você criou/fez fork
3. Clique em **"Deploy Now"**

## ⚙️ Passo 3: Configurar Variáveis de Ambiente

### 3.1 Adicionar o Token do Bot

1. No projeto do Railway, clique na aba **"Variables"**
2. Clique em **"New Variable"**
3. Configure:
   - **Name**: `DISCORD_BOT_TOKEN`
   - **Value**: Cole o token que você copiou do Discord
4. Clique em **"Add"**

### 3.2 Configurar Outras Variáveis (Opcional)

Adicione estas variáveis se quiser personalizar:

