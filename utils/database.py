"""Simple JSON database for Obsidian Marketplace Bot"""
import json
import os
import aiofiles
from typing import Any, Dict, Optional
import asyncio

class Database:
    """Async JSON database handler"""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._cache = {}
        self._lock = asyncio.Lock()

    def _get_path(self, guild_id: int, name: str) -> str:
        """Get file path for guild data"""
        guild_dir = os.path.join(self.data_dir, str(guild_id))
        os.makedirs(guild_dir, exist_ok=True)
        return os.path.join(guild_dir, f'{name}.json')

    async def _read(self, path: str) -> Dict:
        """Read JSON file"""
        if not os.path.exists(path):
            return {}
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except:
            return {}

    async def _write(self, path: str, data: Dict):
        """Write JSON file"""
        async with self._lock:
            async with aiofiles.open(path, 'w') as f:
                await f.write(json.dumps(data, indent=2))

    async def get(self, guild_id: int, key: str, default: Any = None) -> Any:
        """Get value from guild database"""
        path = self._get_path(guild_id, 'config')
        data = await self._read(path)
        return data.get(key, default)

    async def set(self, guild_id: int, key: str, value: Any):
        """Set value in guild database"""
        path = self._get_path(guild_id, 'config')
        data = await self._read(path)
        data[key] = value
        await self._write(path, data)

    async def delete(self, guild_id: int, key: str):
        """Delete key from guild database"""
        path = self._get_path(guild_id, 'config')
        data = await self._read(path)
        data.pop(key, None)
        await self._write(path, data)

    async def get_all(self, guild_id: int) -> Dict:
        """Get all guild config"""
        path = self._get_path(guild_id, 'config')
        return await self._read(path)

    async def init_guild(self, guild_id: int):
        """Initialize default guild settings"""
        from utils.config import Config

        path = self._get_path(guild_id, 'config')
        if not os.path.exists(path):
            default_config = {
                'automod': Config.AUTOMOD_DEFAULTS.copy(),
                'antinuke': Config.ANTINUKE_DEFAULTS.copy(),
                'welcome': Config.WELCOME_DEFAULTS.copy(),
                'tickets': Config.TICKET_DEFAULTS.copy(),
                'payments': {},
                'logs_channel': None,
                'mod_role': None,
                'admin_role': None
            }
            await self._write(path, default_config)

    # Specific helpers
    async def get_automod(self, guild_id: int) -> Dict:
        return await self.get(guild_id, 'automod', {})

    async def get_antinuke(self, guild_id: int) -> Dict:
        return await self.get(guild_id, 'antinuke', {})

    async def get_welcome(self, guild_id: int) -> Dict:
        return await self.get(guild_id, 'welcome', {})

    async def get_tickets(self, guild_id: int) -> Dict:
        return await self.get(guild_id, 'tickets', {})

    async def get_payments(self, guild_id: int) -> Dict:
        return await self.get(guild_id, 'payments', {})

    async def add_warn(self, guild_id: int, user_id: int, reason: str, moderator_id: int):
        """Add a warning to user"""
        path = self._get_path(guild_id, 'warnings')
        data = await self._read(path)

        user_warns = data.get(str(user_id), [])
        user_warns.append({
            'reason': reason,
            'moderator': moderator_id,
            'timestamp': str(datetime.utcnow())
        })
        data[str(user_id)] = user_warns
        await self._write(path, data)
        return len(user_warns)

    async def get_warns(self, guild_id: int, user_id: int) -> list:
        """Get user warnings"""
        path = self._get_path(guild_id, 'warnings')
        data = await self._read(path)
        return data.get(str(user_id), [])

    async def clear_warns(self, guild_id: int, user_id: int):
        """Clear user warnings"""
        path = self._get_path(guild_id, 'warnings')
        data = await self._read(path)
        data.pop(str(user_id), None)
        await self._write(path, data)

    async def log_event(self, guild_id: int, event_type: str, data: Dict):
        """Log an event"""
        path = self._get_path(guild_id, 'logs')
        logs = await self._read(path)

        if 'events' not in logs:
            logs['events'] = []

        logs['events'].append({
            'type': event_type,
            'data': data,
            'timestamp': str(datetime.utcnow())
        })

        # Keep only last 1000 events
        logs['events'] = logs['events'][-1000:]
        await self._write(path, logs)
