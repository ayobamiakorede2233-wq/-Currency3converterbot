"""
Configuration settings for Currency3 Converter Bot
"""

import os

# Bot Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is required!")

# API Configuration
API_URL = "https://api.exchangerate-api.com/v4/latest/"
API_TIMEOUT = 10  # seconds

# Currency Configuration
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

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
