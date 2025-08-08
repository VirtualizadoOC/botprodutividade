# Discord Productivity Bot

## Overview

This is a comprehensive Discord bot designed to enhance server productivity through multiple integrated features. The bot provides interactive polls, reminder systems, scheduled messaging, countdown timers, and task management capabilities. Built with Python using discord.py, it leverages SQLite for data persistence and implements a modular cog-based architecture for organized functionality distribution.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Discord.py Library**: Uses discord.py with command extensions for slash command support and event handling
- **Modular Cog System**: Functionality is split into separate cogs (enquetes, lembretes, mensagens_programadas, contadores, tarefas) for maintainability and organized feature separation
- **Async/Await Pattern**: Fully asynchronous architecture using asyncio for non-blocking operations and concurrent task handling

### Database Layer
- **SQLite Database**: Local file-based database for data persistence with aiosqlite for async operations
- **Database Manager**: Centralized database operations with connection pooling and error handling
- **Schema Design**: Normalized tables for polls, votes, reminders, scheduled messages, countdowns, and tasks with appropriate foreign key relationships

### Configuration Management
- **Environment Variables**: Secure token storage using dotenv for configuration management
- **Centralized Config**: Single config.py file containing bot settings, colors, emojis, and operational limits
- **Timezone Support**: Brazilian timezone (America/Sao_Paulo) configuration for accurate time-based operations

### Task Scheduling System
- **Discord.py Tasks**: Background task loops for periodic operations like reminder checking and countdown updates
- **Time Parsing**: Custom utilities for parsing time strings (5m, 2h, 1d format) into datetime objects
- **Automatic Cleanup**: Scheduled cleanup of expired polls, completed reminders, and sent scheduled messages

### Feature Architecture

#### Interactive Polls System
- Emoji-based voting mechanism with numbered reactions (1️⃣-🔟)
- Vote tracking with user uniqueness constraints
- Automatic poll closure with result visualization
- Support for timed polls with expiration handling

#### Reminder System
- Flexible time parsing supporting multiple formats
- User-specific reminder management with unique IDs
- Channel-specific or DM notification delivery
- Maximum duration limits for system stability

#### Scheduled Messages
- Permission-based access control (requires Manage Messages)
- Support for one-time and recurring message scheduling
- Channel-specific delivery with bot permission verification
- Advanced time parsing for scheduling flexibility

#### Countdown Timers
- Real-time countdown displays with periodic updates
- Event notification system when countdowns reach zero
- Visual countdown formatting with days/hours/minutes breakdown
- Multiple concurrent countdown support per server

#### Task Management
- Priority-based task organization (High/Medium/Low with color coding)
- Due date tracking with overdue notifications
- Task completion status tracking
- User-specific task limits for system performance

### Error Handling and Logging
- **Comprehensive Logging**: File and console logging with different severity levels
- **Graceful Error Handling**: Try-catch blocks around critical operations with user-friendly error messages
- **Permission Validation**: Proper permission checking before executing privileged operations
- **Input Validation**: Sanitization and validation of user inputs with appropriate feedback

### Security Considerations
- **Token Protection**: Environment-based token storage with no hardcoded credentials
- **Permission Checks**: Role and permission-based command access control
- **Input Sanitization**: Protection against SQL injection and malicious input
- **Rate Limiting**: Built-in Discord API rate limiting compliance

## External Dependencies

### Core Libraries
- **discord.py**: Main Discord API wrapper for bot functionality
- **aiosqlite**: Asynchronous SQLite database operations
- **python-dotenv**: Environment variable loading for configuration
- **asyncio**: Asynchronous programming support (Python standard library)

### Database
- **SQLite**: Local file-based database for data persistence
- **No external database server required**: Self-contained database solution

### Discord Platform
- **Discord Bot Token**: Requires bot application creation in Discord Developer Portal
- **Discord Gateway**: Real-time event receiving and command processing
- **Discord API**: Message sending, emoji reactions, and server interaction capabilities

### Deployment Platform
- **Railway.com**: Configured for Railway deployment with automatic environment variable handling
- **File System**: Local file storage for database and logs (persistent storage required)

### Time and Localization
- **Brazilian Timezone**: America/Sao_Paulo timezone configuration
- **Standard Python datetime**: No external time libraries required