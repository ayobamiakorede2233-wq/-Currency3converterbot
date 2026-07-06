"""
Currency3 Converter Bot - A Telegram bot for real-time currency conversion
Deployed on Railway with GitHub integration
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

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
# CONFIGURATION
# ============================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set!")

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
# LOGGING
# ============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def parse_conversion(text: str) -> Optional[Tuple[float, str, str]]:
    """
    Parse user input for currency conversion.
    Returns: (amount, from_currency, to_currency) or None if invalid
    """
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
    """
    Fetch exchange rate from API
    Returns: dict with rate and date, or None if error
    """
    try:
        response = requests.get(f"{API_URL}{from_currency}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if to_currency not in data.get("rates", {}):
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
    """Format the conversion result message"""
    converted = amount * rate
    return (
        f"💱 *Conversion Result*\n\n"
        f"💰 {amount:,.2f} {from_curr} = **{converted:,.2f} {to_curr}**\n\n"
        f"📊 Rate: 1 {from_curr} = {rate:.6f} {to_curr}\n"
        f"🕐 Updated: {date}\n\n"
        f"💡 Try: `{amount + 10:,.0f} {from_curr} {to_curr}`"
    )

def create_keyboard(buttons: list, columns: int = 2) -> InlineKeyboardMarkup:
    """Create a grid keyboard from button list"""
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
    """Handle /start command"""
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
    
    await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
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
    """Handle /rates command"""
    # Show currencies in a grid format
    currencies = " • ".join(SUPPORTED_CURRENCIES)
    text = (
        f"📊 *Supported Currencies*\n\n"
        f"{currencies}\n\n"
        f"✅ Total: *{len(SUPPORTED_CURRENCIES)}* currencies\n\n"
        "💡 Use: `100 USD EUR` to convert"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /convert command - Show popular pairs"""
    buttons = [
        (f"{base}→{target}", f"pair_{base}_{target}")
        for base, target in POPULAR_PAIRS
    ]
    # Add custom option
    buttons.append(("✏️ Custom", "custom_convert"))
    
    keyboard = create_keyboard(buttons, columns=2)
    
    await update.message.reply_text(
        "💱 *Choose a currency pair:*\n\n"
        "Select a pair below or tap 'Custom' to type your own.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    about_text = (
        "ℹ️ *About Currency3 Converter*\n\n"
        "🤖 Version: 1.0.0\n"
        "📅 Created: July 2026\n"
        "🔧 Built with: Python + python-telegram-bot\n"
        "🚀 Hosted on: Railway\n"
        "📊 API: ExchangeRate-API.com\n\n"
        "👨‍💻 Open Source - Deploy your own!\n"
        "📦 GitHub: [Your Repository Link]"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")

# ============================================
# CALLBACK QUERY HANDLERS
# ============================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
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
            rates_data = result["rate"]
            # Show top 10 rates
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
    """Handle text messages for currency conversion"""
    text = update.message.text.strip()
    
    # Skip if it's a command
    if text.startswith("/"):
        return
    
    # Parse the conversion
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
    
    # Show processing message
    processing = await update.message.reply_text(
        f"🔄 Converting {amount:,.2f} {from_curr} → {to_curr}..."
    )
    
    # Get exchange rate
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
    """Log errors and notify user"""
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred. Please try again later."
        )

# ============================================
# MAIN APPLICATION
# ============================================

def main() -> None:
    """Start the bot"""
    logger.info("🚀 Starting Currency3 Converter Bot...")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
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
    
    # Start polling (works on Railway)
    logger.info("✅ Bot is running and listening for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
