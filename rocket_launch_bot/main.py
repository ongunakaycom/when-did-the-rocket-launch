#!/usr/bin/env python3
"""
Rocket Launch Frame Detection Bot
Telegram bot that helps find the exact frame where a rocket launches
"""

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from handlers.command_handlers import (
    start_command, 
    handle_frame_response, 
    handle_restart
)
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    # Validate configuration
    if error := Config.validate():
        logger.error(f"Configuration error: {error}")
        return
    
    # Create Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_frame_response, pattern="^(yes|no)$"))
    application.add_handler(CallbackQueryHandler(handle_restart, pattern="^restart$"))
    
    # Start the Bot
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()