"""
Currency3 Converter Bot - Telegram Bot for Real-time Currency Conversion
Deployed on Railway with GitHub Integration
"""

import os
import sys
import re
import logging
import time
from typing import Dict, Optional, Tuple

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ============================================
# LOGGING - SET TO DEBUG FOR MORE INFO
# ============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # Changed to DEBUG for more info
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_TOKEN environment variable is not set!")
    sys.exit(1)

logger.info(f"✅ Token loaded: {TOKEN[:10]}... (hidden for security)")

API_URL = "https://api.exchangerate-api.com/v4/latest/"
SUPPORTED_CURRENCIES = [
    "AED", "AUD", "BRL", "CAD", "CHF", "CNY", "EGP", "EUR", "GBP", "HKD",
    "IDR", "INR", "JPY", "KRW", "MXN", "MYR", "NGN", "NOK", "NZD", "PKR",
    "PHP", "RUB", "SAR", "SEK", "SGD", "THB", "TRY", "USD", "VND", "ZAR",
]

POPULAR_PAIRS = [
    ("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY"),
    ("EUR", "USD"), ("GBP", "USD"), ("USD", "NGN"),
    ("EUR", "NGN"), ("USD", "INR"), ("USD", "PKR"),
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def parse_conversion(text: str) -> Optional[Tuple[float, str, str]]:
    """Parse user input for currency conversion."""
    patterns = [
        r"^(?:convert\s+)?([\d.]+)\s+([A-Z]{3})\s+(?:to\s+)?([A-Z]{3})$",
        r"^(?:convert\s+)?([\d.]+)\s+([A-Z]{3})\s+in\s+([A-Z]{3})$",
        r"^(?:convert\s+)?([\d.]+)\s+([A-Z]{3})\s+to\s+([A-Z]{3})$",
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text.strip().upper(), re.IGNORECASE)
        if match:
            amount = float(match.group(1))
            from_curr = match.group(2).upper()
            to_curr = match.group(3).upper()
            
            if from_curr in SUPPORTED_CURRENCIES and to_curr in SUPPORTED_CURRENCIES:
                return (amount, from_curr, to_curr)
    return None

def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[Dict]:
    """Fetch exchange rate from API."""
    try:
        logger.debug(f"Fetching rate for {from_currency} to {to_currency}")
        response = requests.get(f"{API_URL}{from_currency}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if to_currency not in data.get("rates", {}):
            logger.error(f"Currency {to_currency} not found in rates")
            return None
            
        return {
            "rate": data["rates"][to_currency],
            "date": data.get("date", "N/A"),
            "base": from_currency,
        }
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

def format_conversion_result(amount: float, from_curr: str, to_curr: str, rate: float, date: str) -> str:
    """Format the conversion result message."""
    converted = amount * rate
    return (
        f"💱 *Conversion Result*\n\n"
        f"💰 {amount:,.2f} {from_curr} = **{converted:,.2f} {to_curr}**\n\n"
        f"📊 Rate: 1 {from_curr} = {rate:.6f} {to_curr}\n"
        f"🕐 Updated: {date}\n\n"
        f"💡 Try: `{amount + 10:,.0f} {from_curr} {to_curr}`"
    )

def create_keyboard(buttons: list, columns: int = 2) -> InlineKeyboardMarkup:
    """Create a grid keyboard from button list."""
    keyboard = []
    row = []
    for i, (text, callback) in enumerate(buttons):
        row.append(InlineKeyboardButton(text, callback_data=callback))
        if len(row) == columns:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    logger.info(f"Start command received from user {update.effective_user.id}")
    user = update.effective_user
    welcome = (
        f"👋 Welcome *{user.first_name}* to Currency3 Converter!\n\n"
        "💰 *Real-time Currency Conversion*\n"
        f"📊 Supports {len(SUPPORTED_CURRENCIES)} currencies\n\n"
        "📌 *Quick Usage:*\n"
        "• `100 USD EUR`\n"
        "• `50 GBP to JPY`\n"
        "• `convert 1000 NGN USD`\n\n"
        "🔍 *Commands:*\n"
        "/start - Show this menu\n"
        "/help - Detailed help\n"
        "/rates - List all currencies\n"
        "/convert - Start conversion\n"
        "/about - About this bot"
    )
    
    buttons = [
        ("💱 Quick Convert", "quick_convert"),
        ("📊 View Rates", "view_rates"),
        ("❓ Help", "help"),
        ("🔄 Swap", "swap"),
    ]
    keyboard = create_keyboard(buttons, columns=2)
    
    try:
        await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode="Markdown")
        logger.info("✅ Start message sent successfully")
    except Exception as e:
        logger.error(f"❌ Failed to send start message: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    logger.info(f"Help command from user {update.effective_user.id}")
    help_text = (
        "📖 *Currency3 Converter - Help*\n\n"
        "*Supported Formats:*\n"
        "• `[amount] [from] [to]`\n"
        "• `[amount] [from] to [to]`\n"
        "• `convert [amount] [from] [to]`\n\n"
        "*Examples:*\n"
        "• `100 USD EUR` → Convert USD to EUR\n"
        "• `50 GBP to JPY` → 50 GBP to Japanese Yen\n"
        "• `convert 1000 NGN USD` → 1000 Naira to Dollars\n\n"
        "*Commands:*\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/rates - All supported currencies\n"
        "/convert - Interactive conversion\n"
        "/about - Bot information\n\n"
        "🔗 *Data Source:* ExchangeRate-API.com"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def rates_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /rates command."""
    logger.info(f"Rates command from user {update.effective_user.id}")
    currencies = " • ".join(SUPPORTED_CURRENCIES)
    text = (
        f"📊 *Supported Currencies*\n\n"
        f"{currencies}\n\n"
        f"✅ Total: *{len(SUPPORTED_CURRENCIES)}* currencies\n\n"
        "💡 Use: `100 USD EUR` to convert"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /convert command."""
    buttons = [
        (f"{base}→{target}", f"pair_{base}_{target}")
        for base, target in POPULAR_PAIRS
    ]
    buttons.append(("✏️ Custom", "custom_convert"))
    
    keyboard = create_keyboard(buttons, columns=2)
    
    await update.message.reply_text(
        "💱 *Choose a currency pair:*\n\n"
        "Select a pair below or tap 'Custom' to type your own.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command."""
    about_text = (
        "ℹ️ *About Currency3 Converter*\n\n"
        "🤖 Version: 1.0.0\n"
        "📅 Created: July 2026\n"
        "🔧 Built with: Python + python-telegram-bot\n"
        "🚀 Hosted on: Railway\n"
        "📊 API: ExchangeRate-API.com\n\n"
        "👨‍💻 Open Source - Deploy your own!"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")

# ============================================
# CALLBACK QUERY HANDLERS
# ============================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.debug(f"Callback received: {data}")
    
    if data == "quick_convert":
        buttons = [
            (f"{base}→{target}", f"pair_{base}_{target}")
            for base, target in POPULAR_PAIRS[:8]
        ]
        buttons.append(("🔙 Back", "back"))
        keyboard = create_keyboard(buttons, columns=2)
        await query.edit_message_text(
            "💱 *Quick Convert*\n\nSelect a pair to convert 1 unit:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    
    elif data == "view_rates":
        await query.edit_message_text("📊 *Fetching latest rates...*", parse_mode="Markdown")
        
        result = get_exchange_rate("USD", "EUR")
        if result:
            top = ["EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR", "NGN", "PKR"]
            text = "📊 *Exchange Rates (Base: USD)*\n\n"
            
            for currency in top:
                rate_data = get_exchange_rate("USD", currency)
                if rate_data:
                    rate = rate_data["rate"]
                    text += f"• 1 USD = {rate:.4f} {currency}\n"
            
            text += f"\n🕐 Updated: {result['date']}"
            buttons = [("🔙 Back", "back")]
            keyboard = create_keyboard(buttons, columns=1)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Could not fetch rates. Please try again.")
    
    elif data == "swap":
        buttons = [
            (f"{target}→{base}", f"pair_{target}_{base}")
            for base, target in POPULAR_PAIRS[:8]
        ]
        buttons.append(("🔙 Back", "back"))
        keyboard = create_keyboard(buttons, columns=2)
        await query.edit_message_text(
            "🔄 *Swapped Pairs*\n\nReverse conversions:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    
    elif data == "help":
        help_text = (
            "📖 *How to use:*\n\n"
            "Just type: `[amount] [from] [to]`\n\n"
            "Examples:\n"
            "• `100 USD EUR`\n"
            "• `50 GBP to JPY`\n"
            "• `1000 NGN USD`\n\n"
            "🔙 Tap Back to return."
        )
        buttons = [("🔙 Back", "back")]
        keyboard = create_keyboard(buttons, columns=1)
        await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "back":
        buttons = [
            ("💱 Quick Convert", "quick_convert"),
            ("📊 View Rates", "view_rates"),
            ("❓ Help", "help"),
            ("🔄 Swap", "swap"),
        ]
        keyboard = create_keyboard(buttons, columns=2)
        await query.edit_message_text(
            "🔙 *Main Menu*\n\nWhat would you like to do?",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    
    elif data == "custom_convert":
        await query.edit_message_text(
            "✏️ *Custom Conversion*\n\n"
            "Send a message in this format:\n"
            "`[amount] [from] [to]`\n\n"
            "Example: `250 USD EUR`\n\n"
            "Use /rates to see all supported currencies.",
            parse_mode="Markdown",
        )
    
    elif data.startswith("pair_"):
        _, from_curr, to_curr = data.split("_")
        result = get_exchange_rate(from_curr, to_curr)
        
        if result:
            formatted = format_conversion_result(
                1, from_curr, to_curr, 
                result["rate"], result["date"]
            )
            buttons = [("🔄 Reverse", f"pair_{to_curr}_{from_curr}")]
            keyboard = create_keyboard(buttons, columns=1)
            await query.edit_message_text(
                formatted, reply_markup=keyboard, parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Conversion failed. Please try again.")

# ============================================
# MESSAGE HANDLER
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages for currency conversion."""
    text = update.message.text.strip()
    logger.info(f"Message received: {text}")
    
    if text.startswith("/"):
        return
    
    parsed = parse_conversion(text)
    if not parsed:
        await update.message.reply_text(
            "🤔 I didn't understand that.\n\n"
            "Please use: `[amount] [from] [to]`\n"
            "Example: `100 USD EUR`\n\n"
            "Send /help for more examples.",
            parse_mode="Markdown",
        )
        return
    
    amount, from_curr, to_curr = parsed
    
    processing = await update.message.reply_text(
        f"🔄 Converting {amount:,.2f} {from_curr} → {to_curr}..."
    )
    
    result = get_exchange_rate(from_curr, to_curr)
    
    if result:
        formatted = format_conversion_result(
            amount, from_curr, to_curr, 
            result["rate"], result["date"]
        )
        buttons = [("🔄 Reverse", f"pair_{to_curr}_{from_curr}")]
        keyboard = create_keyboard(buttons, columns=1)
        await processing.edit_text(formatted, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await processing.edit_text(
            f"❌ Conversion failed.\n\n"
            f"Check if both currencies are supported.\n"
            f"Use /rates to see all available currencies."
        )

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

# ============================================
# MAIN APPLICATION - WITH DEBUGGING
# ============================================

def main():
    """Start the bot with proper error handling for Railway."""
    logger.info("=" * 50)
    logger.info("🚀 Starting Currency3 Converter Bot...")
    logger.info("=" * 50)
    
    # Log environment info
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Current directory: {os.getcwd()}")
    logger.info(f"📂 Files in directory: {os.listdir('.')}")
    
    # Check token
    if not TOKEN:
        logger.error("❌ TELEGRAM_TOKEN environment variable is not set!")
        sys.exit(1)
    
    logger.info(f"✅ Token found: {TOKEN[:10]}... (first 10 chars)")
    
    try:
        # Create the Application
        logger.info("🔨 Building Application...")
        application = Application.builder().token(TOKEN).build()
        logger.info("✅ Application built successfully")
        
        # Add command handlers
        logger.info("📝 Registering handlers...")
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("rates", rates_command))
        application.add_handler(CommandHandler("convert", convert_command))
        application.add_handler(CommandHandler("about", about_command))
        
        # Add callback and message handlers
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )
        
        # Add error handler
        application.add_error_handler(error_handler)
        logger.info("✅ Handlers registered successfully")
        
        # Start the bot with polling
        logger.info("🔄 Starting polling (this is where it waits for messages)...")
        logger.info("💡 The bot is now listening for messages on Telegram")
        logger.info("=" * 50)
        
        # Run polling - this will block and keep the bot running
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=1.0,  # Check for updates every second
            timeout=60  # Long polling timeout
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()
        
        # Keep the process alive for Railway to show the error
        logger.info("⏳ Keeping process alive for 1 hour to show logs...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
