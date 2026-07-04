"""Configuration for Obsidian Marketplace Bot"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot configuration"""

    # Bot Token (from .env file)
    TOKEN = os.getenv('DISCORD_TOKEN')

    # Bot Settings
    PREFIX = 'o!'
    OWNER_IDS = [int(x) for x in os.getenv('OWNER_IDS', '0').split(',') if x]

    # Colors (Obsidian Theme - Dark purple/black)
    PRIMARY_COLOR = 0x2D1B4E      # Deep purple
    SECONDARY_COLOR = 0x1A1A2E    # Dark navy
    SUCCESS_COLOR = 0x00D9A5       # Teal green
    ERROR_COLOR = 0xFF4757         # Red
    WARNING_COLOR = 0xFFA502       # Orange
    INFO_COLOR = 0x70A1FF          # Light blue
    GOLD_COLOR = 0xFFD700          # Gold

    # Emojis
    EMOJI_CHECK = '✅'
    EMOJI_X = '❌'
    EMOJI_WARNING = '⚠️'
    EMOJI_INFO = 'ℹ️'
    EMOJI_SHIELD = '🛡️'
    EMOJI_LOCK = '🔒'
    EMOJI_UNLOCK = '🔓'
    EMOJI_CART = '🛒'
    EMOJI_MONEY = '💰'
    EMOJI_TICKET = '🎫'
    EMOJI_STAR = '⭐'
    EMOJI_FIRE = '🔥'
    EMOJI_HAMMER = '🔨'
    EMOJI_BELL = '🔔'

    # AutoMod Settings
    AUTOMOD_DEFAULTS = {
        'max_mentions': 5,
        'max_emojis': 10,
        'max_caps_percent': 70,
        'max_repeated_chars': 10,
        'spam_threshold': 5,
        'spam_interval': 5,  # seconds
        'invite_filter': True,
        'link_filter': False,
        'bad_words': [
            'nigger', 'nigga', 'faggot', 'retard',
            'kys', 'kill yourself', 'die',
        ]
    }

    # Anti-Nuke Settings
    ANTINUKE_DEFAULTS = {
        'enabled': True,
        'channel_delete_limit': 3,
        'channel_create_limit': 3,
        'role_delete_limit': 3,
        'role_create_limit': 3,
        'ban_limit': 3,
        'kick_limit': 5,
        'webhook_limit': 2,
        'time_window': 10,  # seconds
        'punishment': 'ban'  # ban, kick, strip
    }

    # Welcome Settings
    WELCOME_DEFAULTS = {
        'enabled': True,
        'message': 'Welcome {user} to **{server}**! You are member **#{count}**.',
        'dm_message': 'Thanks for joining {server}! Make sure to read the rules.',
        'auto_role': None
    }

    # Ticket Settings
    TICKET_DEFAULTS = {
        'category': None,
        'transcript_channel': None,
        'support_roles': [],
        'max_tickets_per_user': 3
    }

    # Payment Methods (supported)
    PAYMENT_METHODS = {
        'paypal': {'name': 'PayPal', 'emoji': '<:paypal:>'},
        'cashapp': {'name': 'CashApp', 'emoji': '<:cashapp:>'},
        'venmo': {'name': 'Venmo', 'emoji': '<:venmo:>'},
        'crypto': {'name': 'Cryptocurrency', 'emoji': '₿'},
        'robux': {'name': 'Robux', 'emoji': '<:robux:>'},
        'giftcard': {'name': 'Gift Card', 'emoji': '🎁'}
    }
