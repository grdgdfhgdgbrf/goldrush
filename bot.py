import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, LabeledPrice, PreCheckoutQuery,
    SuccessfulPayment
)
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramForbiddenError
import os
import sys
import traceback
import gc
import math
from collections import defaultdict

# ========== НАСТРОЙКИ ==========
ADMIN_ID = 5356400377
ADMIN_USERNAME = "@hjklgf1"
BOT_TOKEN = "8269087933:AAE-lRMxUUdZJ3R085BUlbji6G0Rjoq7Hhg"
BOT_USERNAME = "@The_Gold_Rushbot"
GAME_NAME = "⛏️ The Gold Rush "
MINING_BASE_TIME = 240
GAME_CURRENCY = "🪙 Золотые слитки"
VERSION = "2.0.0"
MAX_LEVEL = 500
RESET_REWARD_LEVEL = 500
MIN_HIT_INTERVAL = 1.0
TIME_PER_UPGRADE = 600

LIMITED_ITEM_NAME = "👑 Королевский рубин"
LIMITED_ITEM_TOTAL = 500

MAX_MESSAGE_LENGTH = 4096
BATCH_SAVE_INTERVAL = 300
MAX_PLAYERS_IN_CACHE = 1000
MAX_ITEMS_IN_CACHE = 2000
CLEANUP_INTERVAL = 1800
MAX_CONCURRENT_TASKS = 200
BATCH_SEND_DELAY = 0.02
CACHE_TTL = 600
SESSION_TIMEOUT = 86400
MAX_INVENTORY_DISPLAY = 50
MAX_MARKET_OFFERS_DISPLAY = 30
RATE_LIMIT_WINDOW = 60
MAX_ACTIONS_PER_WINDOW = 30

PREMIUM_COIN_NAME = "💎 Premium Coin"

COOLDOWN_COMMANDS = {
    "start": 2,
    "mine": 3,
    "profile": 2,
    "daily": 86400,
    "donate": 2,
    "shop": 2,
    "inventory": 2,
    "gold": 2,
    "upgrades": 2,
    "cases": 2,
    "auto": 2,
    "collections": 2,
    "market": 2,
    "top": 2,
    "help": 1,
    "transfer": 3,
    "rul": 2,
    "promocode": 5,
    "callback": 1,
}

RESET_ITEMS = [
    "🏺 Древняя кирка",
    "⚱️ Золотая статуэтка",
    "📜 Свиток знаний",
    "🔮 Кристалл времени",
    "⚡ Ядро земли",
    "🌋 Сердце вулкана",
    "❄️ Вечная мерзлота",
    "💫 Звездная пыль",
    "🌌 Кусок вселенной",
    "👑 Корона создателя"
]

MINERAL_UNLOCK_LEVELS = {
    1: ["COAL"],
    2: ["IRON"],
    3: ["COPPER"],
    4: ["ALUMINUM"],
    5: ["ZINC"],
    6: ["TIN"],
    7: ["LEAD"],
    8: ["NICKEL"],
    9: ["OBSIDIAN"],
    10: ["SILVER"],
    11: ["COBALT"],
    12: ["LITHIUM"],
    13: ["GOLD"],
    14: ["TITANIUM"],
    15: ["CHROMIUM"],
    16: ["MANGANESE"],
    17: ["TUNGSTEN"],
    18: ["RUBY"],
    19: ["PLATINUM"],
    20: ["SAPPHIRE"],
    21: ["EMERALD"],
    22: ["URANIUM"],
    23: ["DIAMOND"],
    24: ["PALLADIUM"],
    25: ["RHODIUM"],
    26: ["OSMIUM"],
    27: ["IRIDIUM"],
    28: ["PROMETHIUM"],
    29: ["ACTINIUM"],
    30: ["NOBELIUM"],
    31: ["LAWRENCIUM"],
    32: ["RUTHERFORDIUM"],
    33: ["DUBNIUM"],
    34: ["SEABORGIUM"],
    35: ["BOHRIUM"],
    36: ["HASSIUM"],
    37: ["MEITNERIUM"],
    38: ["DARMSTADTIUM"],
    39: ["ROENTGENIUM"],
    40: ["COPERNICIUM"],
    41: ["NIHONIUM"],
    42: ["FLEROVIUM"],
    43: ["MOSCOVIUM"],
    44: ["LIVERMORIUM"],
    45: ["TENNESSINE"],
    46: ["OGANESSON"],
    47: ["QUANTIUM"],
    48: ["INFINIUM"],
    49: ["COSMIUM"],
    50: ["GODLIUM"]
}

class Cache:
    def __init__(self, ttl: int = CACHE_TTL, max_size: int = 10000):
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl
        self._max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str):
        async with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps[key] < self._ttl:
                    return self._cache[key]
                else:
                    del self._cache[key]
                    del self._timestamps[key]
            return None
    
    async def set(self, key: str, value):
        async with self._lock:
            if len(self._cache) >= self._max_size:
                oldest = sorted(self._timestamps.items(), key=lambda x: x[1])[:len(self._cache)//10]
                for k, _ in oldest:
                    if k in self._cache:
                        del self._cache[k]
                    if k in self._timestamps:
                        del self._timestamps[k]
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    async def delete(self, key: str):
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()

@dataclass
class PromoCode:
    code: str
    reward_type: str
    reward_value: Any
    max_uses: int
    used_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    min_level: int = 1
    description: str = ""

@dataclass
class PromoCodeActivation:
    user_id: int
    code: str
    activated_at: datetime = field(default_factory=datetime.now)

class RouletteBetType(Enum):
    RED = "🔴 Красное"
    BLACK = "⚫ Черное"

@dataclass
class RouletteBet:
    user_id: int
    bet_type: RouletteBetType
    amount: int
    created_at: datetime = field(default_factory=datetime.now)

class MineralType(Enum):
    COAL = "🪨 Уголь"
    IRON = "⚙️ Железо"
    COPPER = "🔩 Медь"
    ALUMINUM = "🥫 Алюминий"
    ZINC = "💎 Цинк"
    TIN = "🥄 Олово"
    LEAD = "🔨 Свинец"
    NICKEL = "🪙 Никель"
    SILVER = "🥈 Серебро"
    GOLD = "🪙 Золото"
    PLATINUM = "💍 Платина"
    TITANIUM = "🛡️ Титан"
    URANIUM = "☢️ Уран"
    DIAMOND = "💎 Алмаз"
    RUBY = "🔴 Рубин"
    SAPPHIRE = "🔷 Сапфир"
    EMERALD = "🟢 Изумруд"
    OBSIDIAN = "🌑 Обсидиан"
    COBALT = "🔵 Кобальт"
    LITHIUM = "🔋 Литий"
    CHROMIUM = "⚡ Хром"
    MANGANESE = "🧲 Марганец"
    TUNGSTEN = "⚒️ Вольфрам"
    PALLADIUM = "🏆 Палладий"
    RHODIUM = "💠 Родий"
    OSMIUM = "🧪 Осмий"
    IRIDIUM = "✨ Иридий"
    PROMETHIUM = "🔥 Прометий"
    ACTINIUM = "☢️ Актиний"
    NOBELIUM = "🔬 Нобелий"
    LAWRENCIUM = "⚛️ Лоуренсий"
    RUTHERFORDIUM = "🏛️ Резерфордий"
    DUBNIUM = "🔭 Дубний"
    SEABORGIUM = "🧪 Сиборгий"
    BOHRIUM = "🔬 Борий"
    HASSIUM = "💥 Хассий"
    MEITNERIUM = "👩‍🔬 Мейтнерий"
    DARMSTADTIUM = "🏢 Дармштадтий"
    ROENTGENIUM = "🩻 Рентгений"
    COPERNICIUM = "🌌 Коперниций"
    NIHONIUM = "🗾 Нихоний"
    FLEROVIUM = "🚀 Флеровий"
    MOSCOVIUM = "🇷🇺 Московий"
    LIVERMORIUM = "🧪 Ливерморий"
    TENNESSINE = "🇺🇸 Теннессин"
    OGANESSON = "🌟 Оганесон"
    QUANTIUM = "⚛️ Квантий"
    INFINIUM = "♾️ Инфиниум"
    COSMIUM = "🌌 Космий"
    GODLIUM = "👑 Годлиум"

class ItemRarity(Enum):
    COMMON = "Обычный"
    RARE = "Редкий"
    EPIC = "Эпический"
    LEGENDARY = "Легендарный"
    MYTHIC = "Мифический"
    LIMITED = "👑 Лимитированный"

class ItemType(Enum):
    MINING_TOOL = "⛏️ Кирка"
    LUCK_CHARM = "🍀 Талисман"
    MINERAL_CHIP = "💿 Чип"
    ENERGY_CORE = "🔋 Ядро"
    FUEL = "⛽ Топливо"
    CASE = "📦 Ящик"
    BOOSTER = "🚀 Бустер"
    COLLECTIBLE = "🏆 Сувенир"
    LIMITED = "👑 Лимитированный"

class CaseType(Enum):
    COMMON = "Обычный ящик"
    RARE = "Редкий ящик"
    EPIC = "Эпический ящик"
    LEGENDARY = "Легендарный ящик"
    MYTHIC = "Мифический ящик"

class CollectibleType(Enum):
    NUGGET = "🥨 Самородок"
    FOSSIL = "🦴 Окаменелость"
    GEODE = "🥚 Жеода"
    CRYSTAL = "🔮 Кристалл"
    METEORITE = "🌠 Метеорит"
    GEMSTONE = "💎 Драгоценный камень"
    ANCIENT_RELIC = "🏺 Древний артефакт"
    MINERAL_EGG = "🥚 Минеральное яйцо"

class BanType(Enum):
    TEMPORARY = "⏱️ Временный"
    PERMANENT = "🚫 Навсегда"
    CHAT_RESTRICTED = "🔇 Только чат"
    TRADE_RESTRICTED = "🏪 Без торговли"

class PickaxeMaterial(Enum):
    WOODEN = "Деревянная"
    STONE = "Каменная"
    IRON = "Железная"
    STEEL = "Стальная"
    GOLDEN = "Золотая"
    DIAMOND = "Алмазная"
    NETHERITE = "Незеритовая"
    TITANIUM = "Титановая"
    URANIUM = "Урановая"
    COBALT = "Кобальтовая"
    VOID = "Войд"
    INFINITY = "Бесконечности"

@dataclass
class Channel:
    id: str
    name: str
    url: str
    required_level: int
    reward: int
    is_active: bool = True
    bot_member: bool = False
    last_check: Optional[datetime] = None

@dataclass
class MiningSession:
    user_id: int
    mineral: MineralType
    start_time: datetime
    end_time: datetime
    active: bool = True
    base_reward_per_hit: float = 0
    total_hits: int = 10
    hits_done: int = 0
    mineral_multiplier: float = 1.0
    pickaxe_level: int = 0
    pickaxe_material: PickaxeMaterial = PickaxeMaterial.WOODEN
    last_hit_time: Optional[datetime] = None
    next_hit_time: Optional[datetime] = None
    hit_interval: float = 0
    total_mining_time: float = 0
    last_activity: datetime = field(default_factory=datetime.now)
    last_notification_time: Optional[datetime] = None

@dataclass
class AutoMiningSession:
    user_id: int
    minerals: List[MineralType]
    is_active: bool = True
    last_mine_time: Optional[datetime] = None
    interval_minutes: int = 5
    next_mine_time: Optional[datetime] = None
    fuel_left: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    last_notification_time: Optional[datetime] = None

@dataclass
class Item:
    item_id: str
    serial_number: str
    name: str
    item_type: ItemType
    rarity: ItemRarity
    description: str
    mining_bonus: float = 1.0
    luck_bonus: float = 0.0
    energy_bonus: float = 0.0
    buy_price: int = 0
    sell_price: int = 0
    is_tradable: bool = True
    owner_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    collectible_type: Optional[CollectibleType] = None
    is_collectible: bool = False
    fuel_amount: int = 0
    pickaxe_level: int = 0
    pickaxe_material: Optional[PickaxeMaterial] = None
    base_hits: int = 10
    pickaxe_upgrade_level: int = 0

@dataclass
class Case:
    case_id: str
    case_type: CaseType
    name: str
    description: str
    price: int
    min_items: int = 1
    max_items: int = 3
    drop_chances: Dict[ItemRarity, float] = field(default_factory=dict)
    collectible_chance: float = 0.008

@dataclass
class MarketOffer:
    offer_id: str
    item_id: str
    seller_id: int
    seller_name: str
    price: int
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class BanRecord:
    user_id: int
    admin_id: int
    reason: str
    ban_type: BanType
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True

@dataclass
class Player:
    user_id: int
    username: str
    first_name: str
    player_number: int = 0
    player_id_str: str = ""
    mineral_balance: Dict[str, float] = field(default_factory=dict)
    gold_balance: int = 0
    premium_coin_balance: int = 0
    miner_level: int = 1
    experience: int = 0
    total_experience: int = 0
    pickaxe_upgrade_level: int = 0
    mining_power_level: int = 0
    mining_time_level: int = 0
    mineral_multiplier_level: int = 0
    mineral_unlock_level: int = 1
    premium_chance_level: int = 0
    case_chance_level: int = 0
    collectible_chance_level: int = 0
    auto_mining_level: int = 0
    inventory: List[str] = field(default_factory=list)
    equipped_items: Dict[str, str] = field(default_factory=dict)
    mining_sessions: List[MiningSession] = field(default_factory=list)
    unlocked_minerals: List[str] = field(default_factory=list)
    subscribed_channels: List[str] = field(default_factory=list)
    last_mining_time: Optional[datetime] = None
    total_mined: float = 0
    total_gold_earned: int = 0
    total_premium_earned: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_daily: Optional[datetime] = None
    stats: Dict[str, Any] = field(default_factory=lambda: {
        "cases_opened": 0, "items_found": 0, "trades_completed": 0,
        "total_play_time": 0, "minerals_mined": 0, "collectibles_found": 0,
        "auto_mines": 0, "daily_streak": 0, "market_purchases": 0,
        "market_sales": 0, "times_reset": 0, "total_reset_bonus": 0,
        "premium_coins_found": 0, "hits_done": 0, "upgrades_bought": 0,
        "roulette_wins": 0, "roulette_losses": 0, "roulette_profit": 0
    })
    auto_mining_enabled: bool = False
    auto_mining_minerals: List[str] = field(default_factory=list)
    collectibles: Dict[str, int] = field(default_factory=dict)
    fuel: int = 0
    custom_name: str = ""
    notifications_enabled: bool = True
    market_notifications: bool = True
    mining_notifications: bool = True
    daily_notifications: bool = True
    is_banned: bool = False
    ban_record: Optional[BanRecord] = None
    reincarnation_level: int = 0
    reincarnation_multiplier: float = 1.0
    current_pickaxe_material: PickaxeMaterial = PickaxeMaterial.WOODEN
    current_pickaxe_upgrade: int = 0
    current_mining_session: Optional[str] = None
    next_hit_time: Optional[datetime] = None
    activated_promocodes: List[str] = field(default_factory=list)
    active_discounts: Dict[str, Any] = field(default_factory=dict)
    market_offers: List[str] = field(default_factory=list)
    last_command_time: Dict[str, float] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.now)
    notification_cooldown: float = 5.0

    def __post_init__(self):
        if not self.custom_name:
            self.custom_name = self.first_name
        for mineral in MineralType:
            if mineral.name not in self.mineral_balance:
                self.mineral_balance[mineral.name] = 0.0
        self._update_unlocked_minerals_by_level()
        for collectible_type in CollectibleType:
            if collectible_type.name not in self.collectibles:
                self.collectibles[collectible_type.name] = 0

    def _update_unlocked_minerals_by_level(self):
        if not self.unlocked_minerals:
            self.unlocked_minerals = []
        for level in range(1, self.mineral_unlock_level + 1):
            minerals = MINERAL_UNLOCK_LEVELS.get(level, [])
            for mineral in minerals:
                if mineral not in self.unlocked_minerals:
                    self.unlocked_minerals.append(mineral)
        mineral_order = {name: idx for idx, name in enumerate(MineralType.__members__.keys())}
        self.unlocked_minerals.sort(key=lambda x: mineral_order.get(x, 999))

    def get_visible_minerals_for_mining(self) -> List[str]:
        if self.mineral_unlock_level <= 1:
            return MINERAL_UNLOCK_LEVELS.get(1, ["COAL"])
        visible_minerals = []
        for level in range(max(1, self.mineral_unlock_level - 2), self.mineral_unlock_level + 1):
            minerals = MINERAL_UNLOCK_LEVELS.get(level, [])
            visible_minerals.extend(minerals)
        if self.mineral_unlock_level < 3:
            base_minerals = MINERAL_UNLOCK_LEVELS.get(1, ["COAL"])
            for mineral in base_minerals:
                if mineral not in visible_minerals:
                    visible_minerals.append(mineral)
        return visible_minerals[:8]

    def get_total_mineral_value(self) -> float:
        base_values = {
            "COAL": 0.2, "IRON": 0.5, "COPPER": 0.8, "ALUMINUM": 1.0,
            "ZINC": 1.2, "TIN": 1.5, "LEAD": 1.0, "NICKEL": 2.0,
            "SILVER": 5.0, "GOLD": 20.0, "PLATINUM": 30.0, "TITANIUM": 10.0,
            "URANIUM": 25.0, "DIAMOND": 50.0, "RUBY": 15.0, "SAPPHIRE": 12.0,
            "EMERALD": 18.0, "OBSIDIAN": 3.0, "COBALT": 4.0, "LITHIUM": 2.5,
            "CHROMIUM": 3.5, "MANGANESE": 2.0, "TUNGSTEN": 8.0, "PALLADIUM": 40.0,
            "RHODIUM": 60.0, "OSMIUM": 35.0, "IRIDIUM": 45.0, "PROMETHIUM": 100.0,
            "ACTINIUM": 150.0, "NOBELIUM": 200.0, "LAWRENCIUM": 250.0,
            "RUTHERFORDIUM": 300.0, "DUBNIUM": 350.0, "SEABORGIUM": 400.0,
            "BOHRIUM": 450.0, "HASSIUM": 500.0, "MEITNERIUM": 550.0,
            "DARMSTADTIUM": 600.0, "ROENTGENIUM": 650.0, "COPERNICIUM": 700.0,
            "NIHONIUM": 750.0, "FLEROVIUM": 800.0, "MOSCOVIUM": 850.0,
            "LIVERMORIUM": 900.0, "TENNESSINE": 950.0, "OGANESSON": 1000.0,
            "QUANTIUM": 1200.0, "INFINIUM": 1500.0, "COSMIUM": 2000.0,
            "GODLIUM": 5000.0
        }
        total = 0.0
        for mineral_name, amount in self.mineral_balance.items():
            total += amount * base_values.get(mineral_name, 0.0)
        return total

    def get_mining_power(self) -> float:
        base_power = 1.0
        power_bonus = self.mining_power_level * 0.01
        base_power *= (1 + power_bonus)
        return base_power

    def get_mineral_multiplier(self) -> float:
        mult = 1.0
        mult *= (1 + self.mineral_multiplier_level * 0.02)
        mult *= (1 + self.miner_level * 0.01)
        mult *= self.reincarnation_multiplier
        mult *= self.get_current_pickaxe_bonus()
        return mult

    def get_premium_coin_chance(self) -> float:
        base_chance = 0.005
        base_chance += self.premium_chance_level * 0.001
        base_chance *= self.reincarnation_multiplier
        return min(base_chance, 0.3)

    def get_case_chance(self) -> float:
        return 0.02 + self.case_chance_level * 0.001

    def get_collectible_chance(self) -> float:
        return 0.004 + self.collectible_chance_level * 0.0005

    def get_auto_mining_effect(self) -> float:
        return 1.0 + (self.auto_mining_level * 0.1)

    def can_use_auto_mining(self) -> bool:
        return self.auto_mining_level > 0

    def get_current_pickaxe_hits(self) -> int:
        base_hits_by_material = {
            PickaxeMaterial.WOODEN: 5,
            PickaxeMaterial.STONE: 8,
            PickaxeMaterial.IRON: 12,
            PickaxeMaterial.STEEL: 18,
            PickaxeMaterial.GOLDEN: 25,
            PickaxeMaterial.DIAMOND: 35,
            PickaxeMaterial.NETHERITE: 50,
            PickaxeMaterial.TITANIUM: 70,
            PickaxeMaterial.URANIUM: 100,
            PickaxeMaterial.COBALT: 150,
            PickaxeMaterial.VOID: 250,
            PickaxeMaterial.INFINITY: 500,
        }
        base_hits = base_hits_by_material.get(self.current_pickaxe_material, 5)
        upgrade_bonus = 1 + (self.current_pickaxe_upgrade * 0.2)
        mining_power_bonus = self.get_mining_power()
        return max(1, int(base_hits * upgrade_bonus * mining_power_bonus))

    def get_current_pickaxe_bonus(self) -> float:
        bonus_by_material = {
            PickaxeMaterial.WOODEN: 1.0,
            PickaxeMaterial.STONE: 1.2,
            PickaxeMaterial.IRON: 1.5,
            PickaxeMaterial.STEEL: 1.8,
            PickaxeMaterial.GOLDEN: 2.2,
            PickaxeMaterial.DIAMOND: 2.7,
            PickaxeMaterial.NETHERITE: 3.3,
            PickaxeMaterial.TITANIUM: 4.0,
            PickaxeMaterial.URANIUM: 5.0,
            PickaxeMaterial.COBALT: 6.0,
            PickaxeMaterial.VOID: 8.0,
            PickaxeMaterial.INFINITY: 10.0,
        }
        base_bonus = bonus_by_material.get(self.current_pickaxe_material, 1.0)
        upgrade_bonus = 1 + (self.current_pickaxe_upgrade * 0.1)
        return base_bonus * upgrade_bonus

    def get_current_pickaxe_luck(self) -> float:
        base_luck = 0.005 * (list(PickaxeMaterial).index(self.current_pickaxe_material) + 1)
        upgrade_bonus = self.current_pickaxe_upgrade * 0.002
        return base_luck + upgrade_bonus

    def upgrade_current_pickaxe(self) -> bool:
        if self.current_pickaxe_upgrade >= 4:
            materials = list(PickaxeMaterial)
            current_index = materials.index(self.current_pickaxe_material)
            if current_index < len(materials) - 1:
                self.current_pickaxe_material = materials[current_index + 1]
                self.current_pickaxe_upgrade = 0
                return True
            return False
        else:
            self.current_pickaxe_upgrade += 1
            return True

    def can_reset(self) -> bool:
        return self.miner_level >= RESET_REWARD_LEVEL

    def calculate_reset_bonus(self) -> int:
        base_bonus = 500000 + (self.reincarnation_level * 200000)
        bonus_mult = 1 + (self.reincarnation_level * 0.5)
        return int(base_bonus * bonus_mult)

    def get_required_reset_item(self) -> str:
        reset_level = self.reincarnation_level + 1
        if reset_level <= len(RESET_ITEMS):
            return RESET_ITEMS[reset_level - 1]
        return RESET_ITEMS[-1]

    def has_reset_item(self) -> bool:
        required_item = self.get_required_reset_item()
        for item_id in self.inventory:
            item = None
            if data_manager:
                item = data_manager.get_item(item_id)
            if item and item.is_collectible and item.name == required_item:
                return True
        return False

    def consume_reset_item(self) -> bool:
        required_item = self.get_required_reset_item()
        for item_id in self.inventory[:]:
            item = None
            if data_manager:
                item = data_manager.get_item(item_id)
            if item and item.is_collectible and item.name == required_item:
                self.inventory.remove(item_id)
                if item.collectible_type:
                    ct_name = item.collectible_type.name
                    if ct_name in self.collectibles:
                        self.collectibles[ct_name] -= 1
                if data_manager:
                    data_manager.delete_item(item_id)
                return True
        return False

    def get_hit_interval(self) -> float:
        total_hits = self.get_current_pickaxe_hits()
        if total_hits <= 0:
            total_hits = 1
        base_mining_time = MINING_BASE_TIME
        extra_time = self.mining_time_level * TIME_PER_UPGRADE
        total_mining_time = base_mining_time + extra_time
        if total_hits <= total_mining_time:
            interval = total_mining_time / total_hits
        else:
            interval = MIN_HIT_INTERVAL
        interval = max(MIN_HIT_INTERVAL, interval)
        return round(interval, 2)

    def get_total_mining_time(self) -> float:
        total_hits = self.get_current_pickaxe_hits()
        hit_interval = self.get_hit_interval()
        return total_hits * hit_interval

    def get_mineral_per_hit(self, base_reward: float) -> float:
        mineral_per_hit = base_reward * self.get_mineral_multiplier()
        return mineral_per_hit

    def has_activated_promocode(self, code: str) -> bool:
        return code in self.activated_promocodes

    def add_activated_promocode(self, code: str):
        if code not in self.activated_promocodes:
            self.activated_promocodes.append(code)

    def add_discount(self, discount_type: str, discount_value: int, source: str):
        if not hasattr(self, 'active_discounts'):
            self.active_discounts = {}
        self.active_discounts[discount_type] = {
            'value': discount_value,
            'source': source,
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }

    def get_discount(self, discount_type: str) -> int:
        if not hasattr(self, 'active_discounts'):
            return 0
        discount = self.active_discounts.get(discount_type)
        if discount:
            expires_at = None
            if isinstance(discount.get('expires_at'), str):
                try:
                    expires_at = datetime.fromisoformat(discount['expires_at'])
                except:
                    expires_at = None
            if expires_at and expires_at > datetime.now():
                return discount['value']
        return 0

    def is_item_on_market(self, item_id: str) -> bool:
        if not hasattr(self, 'market_offers'):
            self.market_offers = []
        return item_id in self.market_offers

    def add_market_offer(self, item_id: str):
        if not hasattr(self, 'market_offers'):
            self.market_offers = []
        if item_id not in self.market_offers:
            self.market_offers.append(item_id)

    def remove_market_offer(self, item_id: str):
        if hasattr(self, 'market_offers') and item_id in self.market_offers:
            self.market_offers.remove(item_id)

    def can_use_command(self, command: str) -> Tuple[bool, float]:
        now = time.time()
        last_time = self.last_command_time.get(command, 0)
        cooldown = COOLDOWN_COMMANDS.get(command, 1)
        if now - last_time < cooldown:
            return False, cooldown - (now - last_time)
        self.last_command_time[command] = now
        return True, 0

    def update_activity(self):
        self.last_activity = datetime.now()

    def can_send_notification(self) -> bool:
        if not self.notifications_enabled or not self.mining_notifications:
            return False
        now = datetime.now()
        if hasattr(self, 'last_notification_time') and self.last_notification_time:
            if (now - self.last_notification_time).total_seconds() < self.notification_cooldown:
                return False
        self.last_notification_time = now
        return True

class DataManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.players: Dict[int, Player] = {}
        self.channels: Dict[str, Channel] = {}
        self.items: Dict[str, Item] = {}
        self.cases: Dict[str, Case] = {}
        self.market_offers: Dict[str, MarketOffer] = {}
        self.active_mining_sessions: Dict[int, MiningSession] = {}
        self.auto_mining_sessions: Dict[int, AutoMiningSession] = {}
        self.bans: Dict[int, BanRecord] = {}
        self.promocodes: Dict[str, PromoCode] = {}
        self.promocode_activations: List[PromoCodeActivation] = []
        self.player_counter = 0
        self.limited_item_counter = 0
        self.ruby_price = 85
        self.ruby_total = LIMITED_ITEM_TOTAL
        self._save_lock = asyncio.Lock()
        self._last_auto_save = time.time()
        self._save_in_progress = False
        self._last_error_report = time.time()
        self._error_count = 0
        self._last_cleanup = time.time()
        self._task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        self._last_player_cleanup = time.time()
        self._player_last_access: Dict[int, float] = {}
        
        self.cache = Cache(ttl=CACHE_TTL, max_size=10000)
        self._mineral_cache: Dict[str, MineralType] = {m.name: m for m in MineralType}
        self._collectible_cache: Dict[str, CollectibleType] = {c.name: c for c in CollectibleType}
        self._item_type_cache: Dict[str, ItemType] = {t.value: t for t in ItemType}
        self._rarity_cache: Dict[str, ItemRarity] = {r.value: r for r in ItemRarity}
        
        self.stats = {
            "loads": 0,
            "saves": 0,
            "errors": 0,
        }
        
        self._save_queue = asyncio.Queue()
        self._save_worker_task = None
        
        self.load_data()
        self.initialize_game_data()
        self.initialize_promocodes()

    def initialize_promocodes(self):
        if not self.promocodes:
            self.promocodes["GOLD100"] = PromoCode(
                code="GOLD100",
                reward_type="gold",
                reward_value=1000,
                max_uses=10,
                description="1000 🪙 в подарок!"
            )
            self.promocodes["RUBY50"] = PromoCode(
                code="RUBY50",
                reward_type="ruby_discount",
                reward_value=50,
                max_uses=5,
                description="50% скидка на Королевский рубин!"
            )
            self.promocodes["DONATE20"] = PromoCode(
                code="DONATE20",
                reward_type="donate_bonus",
                reward_value=20,
                max_uses=10,
                description="20% скидка на любой донат!"
            )
            self.promocodes["RUBYITEM"] = PromoCode(
                code="RUBYITEM",
                reward_type="item",
                reward_value="👑 Королевский рубин",
                max_uses=2,
                description="Королевский рубин в подарок!"
            )
            self.promocodes["MYTHICBOX"] = PromoCode(
                code="MYTHICBOX",
                reward_type="case",
                reward_value="MYTHIC",
                max_uses=3,
                description="Мифический ящик в подарок!"
            )
            self.promocodes["LEVEL50"] = PromoCode(
                code="LEVEL50",
                reward_type="gold",
                reward_value=5000,
                max_uses=5,
                min_level=50,
                description="5000 🪙 для игроков 50+ уровня!"
            )
            self.promocodes["WEEKEND"] = PromoCode(
                code="WEEKEND",
                reward_type="gold",
                reward_value=2000,
                max_uses=20,
                expires_at=datetime.now() + timedelta(days=7),
                description="2000 🪙 (действителен 7 дней)"
            )
            self.promocodes["STARTERPACK"] = PromoCode(
                code="STARTERPACK",
                reward_type="package",
                reward_value="starter",
                max_uses=5,
                description="Стартовый пакет: 5000🪙 + эпик ящик + топливо 180мин"
            )
            self.promocodes["BUSINESSPACK"] = PromoCode(
                code="BUSINESSPACK",
                reward_type="package",
                reward_value="business",
                max_uses=3,
                description="Промышленный пакет: 12000🪙 + легенд ящик + топливо 300мин + эпик инструмент"
            )
            self.promocodes["PREMIUMPACK"] = PromoCode(
                code="PREMIUMPACK",
                reward_type="package",
                reward_value="premium",
                max_uses=2,
                description="Магнатский пакет: 30000🪙 + миф ящик + топливо 600мин + легенд инструмент"
            )

    async def start_save_worker(self):
        if self._save_worker_task is None:
            self._save_worker_task = asyncio.create_task(self._save_worker())

    async def _save_worker(self):
        while True:
            try:
                save_task = await self._save_queue.get()
                if save_task == "STOP":
                    break
                await self._perform_save()
                await asyncio.sleep(5)
            except Exception:
                pass

    async def queue_save(self):
        try:
            self._save_queue.put_nowait("SAVE")
        except asyncio.QueueFull:
            pass

    async def _perform_save(self):
        if self._save_in_progress:
            return
        async with self._save_lock:
            self._save_in_progress = True
            try:
                self.save_data()
                self._last_auto_save = time.time()
            except Exception:
                pass
            finally:
                self._save_in_progress = False

    def get_item(self, item_id: str) -> Optional[Item]:
        if not item_id:
            return None
        return self.items.get(item_id)

    def delete_item(self, item_id: str):
        if item_id in self.items:
            del self.items[item_id]

    async def check_bot_in_channel(self, channel_url: str) -> bool:
        try:
            if "t.me/" in channel_url:
                username = channel_url.split("t.me/")[-1].replace("@", "")
                if username:
                    try:
                        chat = await self.bot.get_chat(f"@{username}")
                        member = await self.bot.get_chat_member(chat.id, self.bot.id)
                        return member.status in ["administrator", "creator"]
                    except:
                        return False
            return False
        except Exception:
            return False

    async def batch_save(self):
        if time.time() - self._last_auto_save < 60:
            return
        await self.queue_save()

    def save_data(self):
        try:
            data = {
                'players': {},
                'channels': {},
                'items': {},
                'cases': {},
                'market_offers': {},
                'bans': {},
                'promocodes': {},
                'promocode_activations': [],
                'player_counter': self.player_counter,
                'limited_item_counter': self.limited_item_counter,
                'ruby_price': self.ruby_price,
                'ruby_total': self.ruby_total,
                'version': VERSION,
                'last_save': datetime.now().isoformat()
            }

            active_players = {}
            for user_id, player in list(self.players.items())[:MAX_PLAYERS_IN_CACHE]:
                try:
                    active_players[str(user_id)] = self._serialize_player(player)
                except:
                    continue
            data['players'] = active_players

            for channel_id, channel in self.channels.items():
                try:
                    data['channels'][channel_id] = self._serialize_channel(channel)
                except:
                    continue

            items_to_save = {}
            item_count = 0
            for item_id, item in list(self.items.items())[:MAX_ITEMS_IN_CACHE]:
                if item_count >= MAX_ITEMS_IN_CACHE:
                    break
                try:
                    items_to_save[item_id] = self._serialize_item(item)
                    item_count += 1
                except:
                    continue
            data['items'] = items_to_save

            for case_id, case in self.cases.items():
                try:
                    data['cases'][case_id] = self._serialize_case(case)
                except:
                    continue

            for offer_id, offer in list(self.market_offers.items())[:50]:
                try:
                    data['market_offers'][offer_id] = self._serialize_market_offer(offer)
                except:
                    continue

            for user_id, ban in self.bans.items():
                try:
                    data['bans'][str(user_id)] = self._serialize_ban(ban)
                except:
                    continue

            for code, promo in self.promocodes.items():
                try:
                    data['promocodes'][code] = self._serialize_promocode(promo)
                except:
                    continue

            activations_to_save = []
            for activation in self.promocode_activations[-100:]:
                try:
                    activations_to_save.append(self._serialize_promocode_activation(activation))
                except:
                    continue
            data['promocode_activations'] = activations_to_save

            temp_file = 'minerich_data_temp.json'
            final_file = 'minerich_data.json'
            
            if os.path.exists(final_file):
                backup_file = f'minerich_data_backup_{int(time.time())}.json'
                try:
                    import shutil
                    shutil.copy2(final_file, backup_file)
                    backups = sorted([f for f in os.listdir() if f.startswith('minerich_data_backup_') and f.endswith('.json')])
                    for old_backup in backups[:-5]:
                        try:
                            os.remove(old_backup)
                        except:
                            pass
                except:
                    pass

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                if os.path.exists(final_file):
                    os.remove(final_file)
                os.rename(temp_file, final_file)
            
            self.stats["saves"] += 1

        except Exception:
            self.stats["errors"] += 1

    def _serialize_player(self, player: Player) -> Dict:
        return {
            'user_id': player.user_id,
            'username': player.username,
            'first_name': player.first_name,
            'player_number': player.player_number,
            'player_id_str': player.player_id_str,
            'mineral_balance': {k: float(v) for k, v in player.mineral_balance.items() if v > 0},
            'gold_balance': player.gold_balance,
            'premium_coin_balance': player.premium_coin_balance,
            'miner_level': player.miner_level,
            'experience': player.experience,
            'total_experience': player.total_experience,
            'pickaxe_upgrade_level': player.pickaxe_upgrade_level,
            'mining_power_level': player.mining_power_level,
            'mining_time_level': player.mining_time_level,
            'mineral_multiplier_level': player.mineral_multiplier_level,
            'mineral_unlock_level': player.mineral_unlock_level,
            'premium_chance_level': player.premium_chance_level,
            'case_chance_level': player.case_chance_level,
            'collectible_chance_level': player.collectible_chance_level,
            'auto_mining_level': player.auto_mining_level,
            'inventory': player.inventory[:MAX_INVENTORY_DISPLAY],
            'equipped_items': player.equipped_items.copy(),
            'unlocked_minerals': player.unlocked_minerals[:30],
            'subscribed_channels': player.subscribed_channels[:10],
            'total_mined': float(player.total_mined),
            'total_gold_earned': player.total_gold_earned,
            'total_premium_earned': player.total_premium_earned,
            'stats': player.stats.copy(),
            'auto_mining_enabled': player.auto_mining_enabled,
            'auto_mining_minerals': player.auto_mining_minerals[:5],
            'collectibles': player.collectibles.copy(),
            'fuel': player.fuel,
            'custom_name': player.custom_name,
            'notifications_enabled': player.notifications_enabled,
            'market_notifications': player.market_notifications,
            'mining_notifications': player.mining_notifications,
            'daily_notifications': player.daily_notifications,
            'is_banned': player.is_banned,
            'reincarnation_level': player.reincarnation_level,
            'reincarnation_multiplier': float(player.reincarnation_multiplier),
            'current_pickaxe_material': player.current_pickaxe_material.value,
            'current_pickaxe_upgrade': player.current_pickaxe_upgrade,
            'created_at': player.created_at.isoformat() if player.created_at else None,
            'last_daily': player.last_daily.isoformat() if player.last_daily else None,
            'activated_promocodes': player.activated_promocodes.copy(),
            'active_discounts': player.active_discounts.copy() if hasattr(player, 'active_discounts') else {},
            'market_offers': player.market_offers.copy() if hasattr(player, 'market_offers') else [],
            'last_command_time': player.last_command_time.copy() if hasattr(player, 'last_command_time') else {},
            'notification_cooldown': getattr(player, 'notification_cooldown', 5.0)
        }

    def _deserialize_player(self, data: Dict) -> Optional[Player]:
        try:
            player = Player(
                user_id=data['user_id'],
                username=data.get('username', ''),
                first_name=data.get('first_name', 'Шахтёр'),
                player_number=data.get('player_number', 0),
                player_id_str=data.get('player_id_str', ''),
                mineral_balance=data.get('mineral_balance', {}),
                gold_balance=data.get('gold_balance', 0),
                premium_coin_balance=data.get('premium_coin_balance', 0),
                miner_level=data.get('miner_level', 1),
                experience=data.get('experience', 0),
                total_experience=data.get('total_experience', 0),
                pickaxe_upgrade_level=data.get('pickaxe_upgrade_level', 0),
                mining_power_level=data.get('mining_power_level', 0),
                mining_time_level=data.get('mining_time_level', 0),
                mineral_multiplier_level=data.get('mineral_multiplier_level', 0),
                mineral_unlock_level=data.get('mineral_unlock_level', 1),
                premium_chance_level=data.get('premium_chance_level', 0),
                case_chance_level=data.get('case_chance_level', 0),
                collectible_chance_level=data.get('collectible_chance_level', 0),
                auto_mining_level=data.get('auto_mining_level', 0),
                inventory=data.get('inventory', []),
                equipped_items=data.get('equipped_items', {}),
                unlocked_minerals=data.get('unlocked_minerals', []),
                subscribed_channels=data.get('subscribed_channels', []),
                total_mined=data.get('total_mined', 0.0),
                total_gold_earned=data.get('total_gold_earned', 0),
                total_premium_earned=data.get('total_premium_earned', 0),
                stats=data.get('stats', {}),
                auto_mining_enabled=data.get('auto_mining_enabled', False),
                auto_mining_minerals=data.get('auto_mining_minerals', []),
                collectibles=data.get('collectibles', {}),
                fuel=data.get('fuel', 0),
                is_banned=data.get('is_banned', False),
                reincarnation_level=data.get('reincarnation_level', 0),
                reincarnation_multiplier=data.get('reincarnation_multiplier', 1.0)
            )
            
            player.custom_name = data.get('custom_name', player.first_name)
            player.notifications_enabled = data.get('notifications_enabled', True)
            player.market_notifications = data.get('market_notifications', True)
            player.mining_notifications = data.get('mining_notifications', True)
            player.daily_notifications = data.get('daily_notifications', True)
            player.activated_promocodes = data.get('activated_promocodes', [])
            player.active_discounts = data.get('active_discounts', {})
            player.market_offers = data.get('market_offers', [])
            player.last_command_time = data.get('last_command_time', {})
            player.notification_cooldown = data.get('notification_cooldown', 5.0)
            
            material_str = data.get('current_pickaxe_material', 'Деревянная')
            found = False
            for material in PickaxeMaterial:
                if material.value == material_str or material.name == material_str:
                    player.current_pickaxe_material = material
                    found = True
                    break
            if not found:
                player.current_pickaxe_material = PickaxeMaterial.WOODEN
            
            player.current_pickaxe_upgrade = data.get('current_pickaxe_upgrade', 0)

            if data.get('created_at'):
                try:
                    player.created_at = datetime.fromisoformat(data['created_at'])
                except:
                    player.created_at = datetime.now()
            
            if data.get('last_daily'):
                try:
                    player.last_daily = datetime.fromisoformat(data['last_daily'])
                except:
                    player.last_daily = None
            
            player._update_unlocked_minerals_by_level()
            return player
        except Exception:
            return None

    def _serialize_promocode(self, promo: PromoCode) -> Dict:
        return {
            'code': promo.code,
            'reward_type': promo.reward_type,
            'reward_value': promo.reward_value,
            'max_uses': promo.max_uses,
            'used_count': promo.used_count,
            'created_at': promo.created_at.isoformat() if promo.created_at else None,
            'expires_at': promo.expires_at.isoformat() if promo.expires_at else None,
            'is_active': promo.is_active,
            'min_level': promo.min_level,
            'description': promo.description
        }

    def _deserialize_promocode(self, data: Dict) -> Optional[PromoCode]:
        try:
            created_at = datetime.now()
            if data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                except:
                    pass
            expires_at = None
            if data.get('expires_at'):
                try:
                    expires_at = datetime.fromisoformat(data['expires_at'])
                except:
                    pass
            return PromoCode(
                code=data['code'],
                reward_type=data['reward_type'],
                reward_value=data['reward_value'],
                max_uses=data['max_uses'],
                used_count=data.get('used_count', 0),
                created_at=created_at,
                expires_at=expires_at,
                is_active=data.get('is_active', True),
                min_level=data.get('min_level', 1),
                description=data.get('description', '')
            )
        except Exception:
            return None

    def _serialize_promocode_activation(self, activation: PromoCodeActivation) -> Dict:
        return {
            'user_id': activation.user_id,
            'code': activation.code,
            'activated_at': activation.activated_at.isoformat() if activation.activated_at else None
        }

    def _deserialize_promocode_activation(self, data: Dict) -> Optional[PromoCodeActivation]:
        try:
            activated_at = datetime.now()
            if data.get('activated_at'):
                try:
                    activated_at = datetime.fromisoformat(data['activated_at'])
                except:
                    pass
            return PromoCodeActivation(
                user_id=data['user_id'],
                code=data['code'],
                activated_at=activated_at
            )
        except Exception:
            return None

    def _serialize_item(self, item: Item) -> Dict:
        return {
            'item_id': item.item_id,
            'serial_number': item.serial_number,
            'name': item.name,
            'item_type': item.item_type.value if item.item_type else None,
            'rarity': item.rarity.value if item.rarity else None,
            'description': item.description,
            'mining_bonus': float(item.mining_bonus),
            'luck_bonus': float(item.luck_bonus),
            'buy_price': item.buy_price,
            'sell_price': item.sell_price,
            'is_tradable': item.is_tradable,
            'owner_id': item.owner_id,
            'is_collectible': item.is_collectible,
            'fuel_amount': item.fuel_amount,
            'created_at': item.created_at.isoformat() if item.created_at else None
        }

    def _deserialize_item(self, data: Dict) -> Optional[Item]:
        try:
            item_type = self._item_type_cache.get(data.get('item_type'))
            rarity = self._rarity_cache.get(data.get('rarity'))
            collectible_type = None
            if data.get('collectible_type'):
                collectible_type = self._collectible_cache.get(data['collectible_type'])
            created_at = datetime.now()
            if data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                except:
                    pass
            return Item(
                item_id=data['item_id'],
                serial_number=data.get('serial_number', '00000'),
                name=data['name'],
                item_type=item_type,
                rarity=rarity,
                description=data['description'],
                mining_bonus=data.get('mining_bonus', 1.0),
                luck_bonus=data.get('luck_bonus', 0.0),
                buy_price=data.get('buy_price', 0),
                sell_price=data.get('sell_price', 0),
                is_tradable=data.get('is_tradable', True),
                owner_id=data.get('owner_id'),
                created_at=created_at,
                collectible_type=collectible_type,
                is_collectible=data.get('is_collectible', False),
                fuel_amount=data.get('fuel_amount', 0)
            )
        except Exception:
            return None

    def _serialize_case(self, case: Case) -> Dict:
        drop_chances_serialized = {}
        for rarity, chance in case.drop_chances.items():
            drop_chances_serialized[rarity.value] = chance
        return {
            'case_id': case.case_id,
            'case_type': case.case_type.value if case.case_type else None,
            'name': case.name,
            'description': case.description,
            'price': case.price,
            'min_items': case.min_items,
            'max_items': case.max_items,
            'drop_chances': drop_chances_serialized,
            'collectible_chance': float(case.collectible_chance)
        }

    def _deserialize_case(self, data: Dict) -> Optional[Case]:
        try:
            case_type = None
            if data.get('case_type'):
                for ct in CaseType:
                    if ct.value == data['case_type']:
                        case_type = ct
                        break
            drop_chances = {}
            for rarity_str, chance in data.get('drop_chances', {}).items():
                rarity = self._rarity_cache.get(rarity_str)
                if rarity:
                    drop_chances[rarity] = chance
            return Case(
                case_id=data['case_id'],
                case_type=case_type,
                name=data['name'],
                description=data['description'],
                price=data['price'],
                min_items=data.get('min_items', 1),
                max_items=data.get('max_items', 3),
                drop_chances=drop_chances,
                collectible_chance=data.get('collectible_chance', 0.008)
            )
        except Exception:
            return None

    def _serialize_channel(self, channel: Channel) -> Dict:
        return {
            'id': channel.id,
            'name': channel.name,
            'url': channel.url,
            'required_level': channel.required_level,
            'reward': channel.reward,
            'is_active': channel.is_active,
            'bot_member': channel.bot_member,
            'last_check': channel.last_check.isoformat() if channel.last_check else None
        }

    def _deserialize_channel(self, data: Dict) -> Optional[Channel]:
        try:
            channel = Channel(
                id=data['id'],
                name=data['name'],
                url=data['url'],
                required_level=data['required_level'],
                reward=data['reward'],
                is_active=data.get('is_active', True),
                bot_member=data.get('bot_member', False)
            )
            if data.get('last_check'):
                try:
                    channel.last_check = datetime.fromisoformat(data['last_check'])
                except:
                    pass
            return channel
        except Exception:
            return None

    def _serialize_market_offer(self, offer: MarketOffer) -> Dict:
        return {
            'offer_id': offer.offer_id,
            'item_id': offer.item_id,
            'seller_id': offer.seller_id,
            'seller_name': offer.seller_name,
            'price': offer.price,
            'created_at': offer.created_at.isoformat() if offer.created_at else None,
            'is_active': offer.is_active
        }

    def _deserialize_market_offer(self, data: Dict) -> Optional[MarketOffer]:
        try:
            created_at = datetime.now()
            if data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                except:
                    pass
            return MarketOffer(
                offer_id=data['offer_id'],
                item_id=data['item_id'],
                seller_id=data['seller_id'],
                seller_name=data['seller_name'],
                price=data['price'],
                created_at=created_at,
                is_active=data.get('is_active', True)
            )
        except Exception:
            return None

    def _serialize_ban(self, ban: BanRecord) -> Dict:
        return {
            'user_id': ban.user_id,
            'admin_id': ban.admin_id,
            'reason': ban.reason,
            'ban_type': ban.ban_type.value if ban.ban_type else None,
            'created_at': ban.created_at.isoformat() if ban.created_at else None,
            'expires_at': ban.expires_at.isoformat() if ban.expires_at else None,
            'is_active': ban.is_active
        }

    def _deserialize_ban(self, data: Dict) -> Optional[BanRecord]:
        try:
            ban_type = BanType.PERMANENT
            if data.get('ban_type'):
                for bt in BanType:
                    if bt.value == data['ban_type']:
                        ban_type = bt
                        break
            created_at = datetime.now()
            if data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                except:
                    pass
            expires_at = None
            if data.get('expires_at'):
                try:
                    expires_at = datetime.fromisoformat(data['expires_at'])
                except:
                    pass
            return BanRecord(
                user_id=data['user_id'],
                admin_id=data['admin_id'],
                reason=data['reason'],
                ban_type=ban_type,
                created_at=created_at,
                expires_at=expires_at,
                is_active=data.get('is_active', True)
            )
        except Exception:
            return None

    def load_data(self):
        try:
            if not os.path.exists('minerich_data.json'):
                self.initialize_game_data()
                self.stats["loads"] += 1
                return

            with open('minerich_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

                self.player_counter = data.get('player_counter', 0)
                self.limited_item_counter = data.get('limited_item_counter', 0)
                self.ruby_price = data.get('ruby_price', 85)
                self.ruby_total = data.get('ruby_total', LIMITED_ITEM_TOTAL)

                for user_id_str, player_data in data.get('players', {}).items():
                    try:
                        player = self._deserialize_player(player_data)
                        if player:
                            self.players[player.user_id] = player
                    except:
                        continue

                for channel_id, channel_data in data.get('channels', {}).items():
                    try:
                        channel = self._deserialize_channel(channel_data)
                        if channel:
                            self.channels[channel_id] = channel
                    except:
                        continue

                for item_id, item_data in data.get('items', {}).items():
                    try:
                        item = self._deserialize_item(item_data)
                        if item:
                            self.items[item_id] = item
                    except:
                        continue

                for case_id, case_data in data.get('cases', {}).items():
                    try:
                        case = self._deserialize_case(case_data)
                        if case:
                            self.cases[case_id] = case
                    except:
                        continue

                for offer_id, offer_data in data.get('market_offers', {}).items():
                    try:
                        offer = self._deserialize_market_offer(offer_data)
                        if offer:
                            self.market_offers[offer_id] = offer
                    except:
                        continue

                for user_id_str, ban_data in data.get('bans', {}).items():
                    try:
                        user_id = int(user_id_str)
                        ban = self._deserialize_ban(ban_data)
                        if ban:
                            self.bans[user_id] = ban
                            if user_id in self.players:
                                self.players[user_id].is_banned = ban.is_active
                                self.players[user_id].ban_record = ban
                    except:
                        continue

                for code, promo_data in data.get('promocodes', {}).items():
                    try:
                        promo = self._deserialize_promocode(promo_data)
                        if promo:
                            self.promocodes[code] = promo
                    except:
                        continue

                for activation_data in data.get('promocode_activations', []):
                    try:
                        activation = self._deserialize_promocode_activation(activation_data)
                        if activation:
                            self.promocode_activations.append(activation)
                    except:
                        continue

            self.stats["loads"] += 1

        except Exception:
            self.initialize_game_data()

    def generate_serial_number(self) -> str:
        return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5))

    def generate_player_id(self) -> str:
        return ''.join(random.choices('0123456789', k=8))

    def initialize_game_data(self):
        if not self.channels:
            self.channels = {
                "main": Channel(
                    id="main",
                    name="📢 Гл. канал шахтёров",
                    url="https://t.me/minerich_official",
                    required_level=1,
                    reward=80
                )
            }

        if not self.cases:
            self.cases = {
                "common_case": Case(
                    case_id="common_case",
                    case_type=CaseType.COMMON,
                    name="📦 Обычный ящик",
                    description="Обычный ящик с шансом на обычные и редкие предметы",
                    price=400,
                    min_items=1,
                    max_items=2,
                    drop_chances={
                        ItemRarity.COMMON: 0.7,
                        ItemRarity.RARE: 0.25,
                        ItemRarity.EPIC: 0.05
                    },
                    collectible_chance=0.004
                ),
                "rare_case": Case(
                    case_id="rare_case",
                    case_type=CaseType.RARE,
                    name="🎁 Редкий ящик",
                    description="Редкий ящик с повышенным шансом на редкие предметы",
                    price=1500,
                    min_items=1,
                    max_items=3,
                    drop_chances={
                        ItemRarity.COMMON: 0.5,
                        ItemRarity.RARE: 0.35,
                        ItemRarity.EPIC: 0.12,
                        ItemRarity.LEGENDARY: 0.03
                    },
                    collectible_chance=0.008
                ),
                "epic_case": Case(
                    case_id="epic_case",
                    case_type=CaseType.EPIC,
                    name="💎 Эпический ящик",
                    description="Эпический ящик с высоким шансом на эпические предметы",
                    price=8000,
                    min_items=2,
                    max_items=4,
                    drop_chances={
                        ItemRarity.RARE: 0.4,
                        ItemRarity.EPIC: 0.4,
                        ItemRarity.LEGENDARY: 0.15,
                        ItemRarity.MYTHIC: 0.05
                    },
                    collectible_chance=0.015
                ),
                "legendary_case": Case(
                    case_id="legendary_case",
                    case_type=CaseType.LEGENDARY,
                    name="👑 Легендарный ящик",
                    description="Легендарный ящик с шансом на легендарные предметы",
                    price=40000,
                    min_items=3,
                    max_items=5,
                    drop_chances={
                        ItemRarity.EPIC: 0.3,
                        ItemRarity.LEGENDARY: 0.5,
                        ItemRarity.MYTHIC: 0.2
                    },
                    collectible_chance=0.04
                ),
                "mythic_case": Case(
                    case_id="mythic_case",
                    case_type=CaseType.MYTHIC,
                    name="✨ Мифический ящик",
                    description="Мифический ящик с максимальным шансом на мифические предметы",
                    price=80000,
                    min_items=3,
                    max_items=5,
                    drop_chances={
                        ItemRarity.LEGENDARY: 0.5,
                        ItemRarity.MYTHIC: 0.5
                    },
                    collectible_chance=0.08
                )
            }

        self.create_initial_items()
        self.initialize_promocodes()
        self.save_data()

    def create_initial_items(self):
        luck_charms = [
            ("🍀 Перо удачи", "Приносит удачу", 0.02, 1500, ItemRarity.COMMON),
            ("🐚 Раковина", "Старинный талисман", 0.04, 5000, ItemRarity.RARE),
            ("💫 Звезда", "Привлекает удачу", 0.08, 12000, ItemRarity.EPIC),
            ("🌙 Лунный камень", "Исполняет желания", 0.12, 35000, ItemRarity.LEGENDARY),
            ("✨ Кристалл судьбы", "Мифический талисман", 0.2, 80000, ItemRarity.MYTHIC),
        ]

        for name, desc, luck, price, rarity in luck_charms:
            item_id = str(uuid.uuid4())
            self.items[item_id] = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.LUCK_CHARM,
                rarity=rarity,
                description=desc,
                luck_bonus=luck,
                buy_price=price,
                sell_price=int(price * 0.6),
                is_tradable=True
            )

        fuels = [
            ("⛽ Угольные брикеты", "60 мин", 60, 800, ItemRarity.COMMON),
            ("🔥 Нефтяное топливо", "180 мин", 180, 2000, ItemRarity.RARE),
            ("⚡ Энергостержни", "300 мин", 300, 4000, ItemRarity.EPIC),
            ("🚀 Реактор", "600 мин", 600, 8000, ItemRarity.LEGENDARY),
            ("☢️ Ядерное топливо", "1200 мин", 1200, 20000, ItemRarity.MYTHIC),
        ]

        for name, desc, minutes, price, rarity in fuels:
            item_id = str(uuid.uuid4())
            self.items[item_id] = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.FUEL,
                rarity=rarity,
                description=desc,
                buy_price=price,
                sell_price=int(price * 0.5),
                is_tradable=True,
                fuel_amount=minutes
            )

        collectibles_data = {
            CollectibleType.NUGGET: [
                ("🥨 Золотой самородок", "Чистое золото", ItemRarity.RARE, 4000),
                ("🥨 Платиновый", "Редкая находка", ItemRarity.EPIC, 8000),
                ("🥨 Палладий", "Исключительно редкий", ItemRarity.LEGENDARY, 20000),
            ],
            CollectibleType.FOSSIL: [
                ("🦴 Аммонит", "Окаменелость моллюска", ItemRarity.COMMON, 2500),
                ("🦴 Трилобит", "Окаменелость", ItemRarity.RARE, 5000),
                ("🦴 Зубы мегалодона", "Зубы акулы", ItemRarity.EPIC, 10000),
            ],
            CollectibleType.GEODE: [
                ("🥚 Агатовая жеода", "Полый камень", ItemRarity.COMMON, 1500),
                ("🥚 Кварцевая жеода", "С кристаллами", ItemRarity.RARE, 3000),
                ("🥚 Аметистовая", "Драгоценная", ItemRarity.EPIC, 6000),
            ],
            CollectibleType.CRYSTAL: [
                ("🔮 Кварц", "Прозрачный кристалл", ItemRarity.COMMON, 1000),
                ("🔮 Аметист", "Фиолетовый", ItemRarity.RARE, 2500),
                ("🔮 Топаз", "Золотистый", ItemRarity.EPIC, 5000),
            ],
            CollectibleType.METEORITE: [
                ("🌠 Каменный", "Упал из космоса", ItemRarity.RARE, 6000),
                ("🌠 Железный", "Редкие металлы", ItemRarity.EPIC, 12000),
                ("🌠 Углистый", "Содержит органику", ItemRarity.LEGENDARY, 25000),
            ],
            CollectibleType.GEMSTONE: [
                ("💎 Рубин", "Красный", ItemRarity.RARE, 5000),
                ("💎 Сапфир", "Синий", ItemRarity.EPIC, 10000),
                ("💎 Изумруд", "Зелёный", ItemRarity.LEGENDARY, 20000),
            ],
            CollectibleType.ANCIENT_RELIC: [
                ("🏺 Древняя кирка", "Инструмент древних", ItemRarity.EPIC, 8000),
                ("🏺 Табличка", "С письменами", ItemRarity.LEGENDARY, 15000),
                ("🏺 Статуэтка", "Почиталась", ItemRarity.MYTHIC, 35000),
            ],
            CollectibleType.MINERAL_EGG: [
                ("🥚 Мин. яйцо", "Загадочное", ItemRarity.RARE, 3000),
                ("🥚 Яйцо дракона", "Легендарное", ItemRarity.LEGENDARY, 12000),
                ("🥚 Яйцо Феникса", "Редчайшее", ItemRarity.MYTHIC, 30000),
            ],
        }

        for collectible_type, items_list in collectibles_data.items():
            for name, desc, rarity, value in items_list:
                item_id = str(uuid.uuid4())
                self.items[item_id] = Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.COLLECTIBLE,
                    rarity=rarity,
                    description=desc,
                    buy_price=value,
                    sell_price=int(value * 0.3),
                    is_tradable=True,
                    is_collectible=True,
                    collectible_type=collectible_type
                )
        
        for reset_item in RESET_ITEMS:
            item_id = str(uuid.uuid4())
            self.items[item_id] = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=reset_item,
                item_type=ItemType.COLLECTIBLE,
                rarity=ItemRarity.LEGENDARY,
                description="Необходим для перерождения",
                buy_price=50000,
                sell_price=25000,
                is_tradable=False,
                is_collectible=True,
                collectible_type=CollectibleType.ANCIENT_RELIC
            )

        item_id = str(uuid.uuid4())
        self.items[item_id] = Item(
            item_id=item_id,
            serial_number=self.generate_serial_number(),
            name=LIMITED_ITEM_NAME,
            item_type=ItemType.LIMITED,
            rarity=ItemRarity.LIMITED,
            description="Особая награда за поддержку. Лимитированный выпуск (500 шт.)",
            mining_bonus=2.0,
            luck_bonus=0.5,
            buy_price=50000,
            sell_price=25000,
            is_tradable=True,
            is_collectible=True
        )

        for case_id, case in self.cases.items():
            item_id = str(uuid.uuid4())
            self.items[item_id] = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=case.name,
                item_type=ItemType.CASE,
                rarity=ItemRarity.EPIC if case.case_type == CaseType.EPIC else ItemRarity.RARE,
                description=case.description,
                buy_price=case.price,
                sell_price=int(case.price * 0.5),
                is_tradable=True
            )

    def get_or_create_player(self, user_id: int, username: str, first_name: str) -> Optional[Player]:
        try:
            self._player_last_access[user_id] = time.time()

            if user_id in self.bans:
                ban = self.bans[user_id]
                if ban.is_active:
                    if ban.expires_at and datetime.now() > ban.expires_at:
                        ban.is_active = False
                        if user_id in self.players:
                            self.players[user_id].is_banned = False
                    else:
                        return None

            if user_id not in self.players:
                self.player_counter += 1
                player = Player(
                    user_id=user_id,
                    username=username or "",
                    first_name=first_name or "Шахтёр",
                    player_number=self.player_counter,
                    player_id_str=self.generate_player_id()
                )
                self.players[user_id] = player
                asyncio.create_task(self.batch_save())
                return player
            else:
                player = self.players[user_id]
                player.update_activity()
                return player

        except Exception:
            return None

    def ban_player(self, admin_id: int, user_id: int, reason: str, ban_type: BanType, duration_hours: Optional[int] = None) -> Tuple[bool, str]:
        try:
            if user_id not in self.players:
                return False, "❌ Игрок не найден"
            expires_at = None
            if duration_hours and ban_type == BanType.TEMPORARY:
                expires_at = datetime.now() + timedelta(hours=duration_hours)
            ban = BanRecord(
                user_id=user_id,
                admin_id=admin_id,
                reason=reason,
                ban_type=ban_type,
                expires_at=expires_at,
                is_active=True
            )
            self.bans[user_id] = ban
            self.players[user_id].is_banned = True
            self.players[user_id].ban_record = ban
            self.active_mining_sessions.pop(user_id, None)
            self.auto_mining_sessions.pop(user_id, None)
            asyncio.create_task(self.batch_save())
            return True, f"✅ Игрок забанен. Тип: {ban_type.value}"
        except Exception:
            return False, f"❌ Ошибка бана"

    def unban_player(self, user_id: int) -> Tuple[bool, str]:
        try:
            if user_id not in self.bans:
                return False, "❌ Бан не найден"
            self.bans[user_id].is_active = False
            if user_id in self.players:
                self.players[user_id].is_banned = False
                self.players[user_id].ban_record = None
            asyncio.create_task(self.batch_save())
            return True, "✅ Игрок разбанен"
        except Exception:
            return False, f"❌ Ошибка разбана"

    def adjust_gold(self, user_id: int, amount: int) -> Tuple[bool, str, int]:
        try:
            player = self.players.get(user_id)
            if not player:
                return False, "❌ Игрок не найден", 0
            new_balance = player.gold_balance + amount
            if new_balance < 0:
                return False, f"❌ Нельзя уйти в минус. Баланс: {player.gold_balance}", 0
            player.gold_balance = new_balance
            asyncio.create_task(self.batch_save())
            return True, f"✅ Золото изменено на {amount:+}. Новый баланс: {new_balance}", new_balance
        except Exception:
            return False, f"❌ Ошибка", 0

    def start_mining(self, user_id: int, mineral_name: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player:
                return False, "Шахтёр не найден"
            if player.is_banned:
                return False, "❌ Вы забанены"
            mineral = self._mineral_cache.get(mineral_name)
            if not mineral:
                return False, "Ископаемое не найдено"
            if mineral_name not in player.unlocked_minerals:
                return False, f"Ископаемое {mineral.value} ещё не разблокировано (нужен {player.mineral_unlock_level} ур. улучшения)"
            if user_id in self.active_mining_sessions:
                session = self.active_mining_sessions[user_id]
                if session.active:
                    return False, "mining_status"

            time_multipliers = {
                "COAL": 0.5, "IRON": 0.6, "COPPER": 0.6, "ALUMINUM": 0.6, "ZINC": 0.7,
                "TIN": 0.6, "LEAD": 0.6, "NICKEL": 0.8, "SILVER": 1.0, "GOLD": 1.2,
                "PLATINUM": 1.3, "TITANIUM": 1.1, "URANIUM": 1.5, "DIAMOND": 1.6,
                "RUBY": 1.2, "SAPPHIRE": 1.2, "EMERALD": 1.3, "OBSIDIAN": 0.9,
                "COBALT": 1.0, "LITHIUM": 0.9, "CHROMIUM": 1.0, "MANGANESE": 0.8,
                "TUNGSTEN": 1.1, "PALLADIUM": 1.4, "RHODIUM": 1.5, "OSMIUM": 1.3,
                "IRIDIUM": 1.4, "PROMETHIUM": 2.0, "ACTINIUM": 2.2, "NOBELIUM": 2.4,
                "LAWRENCIUM": 2.6, "RUTHERFORDIUM": 2.8, "DUBNIUM": 3.0,
                "SEABORGIUM": 3.2, "BOHRIUM": 3.4, "HASSIUM": 3.6,
                "MEITNERIUM": 3.8, "DARMSTADTIUM": 4.0, "ROENTGENIUM": 4.2,
                "COPERNICIUM": 4.4, "NIHONIUM": 4.6, "FLEROVIUM": 4.8,
                "MOSCOVIUM": 5.0, "LIVERMORIUM": 5.2, "TENNESSINE": 5.4,
                "OGANESSON": 5.6, "QUANTIUM": 6.0, "INFINIUM": 7.0,
                "COSMIUM": 8.0, "GODLIUM": 10.0
            }

            base_time = MINING_BASE_TIME
            extra_time = player.mining_time_level * TIME_PER_UPGRADE
            total_hits = player.get_current_pickaxe_hits()
            hit_interval = player.get_hit_interval()
            total_mining_time = total_hits * hit_interval

            base_reward_per_hit = 5 * player.miner_level
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=total_mining_time)

            session = MiningSession(
                user_id=user_id,
                mineral=mineral,
                start_time=start_time,
                end_time=end_time,
                base_reward_per_hit=base_reward_per_hit,
                total_hits=total_hits,
                hits_done=0,
                mineral_multiplier=player.get_mineral_multiplier(),
                pickaxe_level=player.pickaxe_upgrade_level,
                pickaxe_material=player.current_pickaxe_material,
                last_hit_time=start_time,
                next_hit_time=start_time + timedelta(seconds=hit_interval),
                hit_interval=hit_interval,
                total_mining_time=total_mining_time,
                last_activity=start_time,
                last_notification_time=None
            )

            self.active_mining_sessions[user_id] = session
            player.mining_sessions.append(session)
            player.last_mining_time = start_time
            player.current_mining_session = mineral_name

            asyncio.create_task(self.batch_save())
            return True, "Добыча началась!"
        except Exception:
            return False, f"❌ Ошибка"

    def process_auto_hit(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        try:
            if user_id not in self.active_mining_sessions:
                return False, {"error": "Нет активной добычи"}
            session = self.active_mining_sessions[user_id]
            player = self.players.get(user_id)
            if not player or not session.active or player.is_banned:
                return False, {"error": "Сессия не активна"}
            
            session.last_activity = datetime.now()
            now = datetime.now()
            
            if session.next_hit_time and now < session.next_hit_time:
                return False, {"error": "Еще не время удара"}
            
            if session.hits_done >= session.total_hits:
                return self.complete_mining(user_id)
            
            if now >= session.end_time:
                return self.complete_mining(user_id)

            mineral_reward = player.get_mineral_per_hit(session.base_reward_per_hit)
            player.mineral_balance[session.mineral.name] = player.mineral_balance.get(session.mineral.name, 0) + mineral_reward
            player.total_mined += mineral_reward

            premium_earned = 0
            luck_chance = player.get_current_pickaxe_luck() + player.get_premium_coin_chance()
            if random.random() < luck_chance:
                player.premium_coin_balance += 1
                player.total_premium_earned += 1
                player.stats["premium_coins_found"] = player.stats.get("premium_coins_found", 0) + 1
                premium_earned = 1

            exp_gained = int(mineral_reward * 0.5)
            player.experience += exp_gained
            player.total_experience += exp_gained
            self._check_level_up(player)

            session.hits_done += 1
            session.last_hit_time = now
            session.next_hit_time = now + timedelta(seconds=session.hit_interval)
            player.stats["hits_done"] = player.stats.get("hits_done", 0) + 1

            asyncio.create_task(self.batch_save())
            
            return True, {
                "success": True,
                "hit_number": session.hits_done,
                "total_hits": session.total_hits,
                "mineral": session.mineral,
                "mineral_reward": mineral_reward,
                "gold_earned": 0,
                "premium_earned": premium_earned,
                "experience": exp_gained,
                "auto": True
            }
        except Exception:
            return False, {"error": "Ошибка"}

    def buy_fuel(self, user_id: int, fuel_type: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            fuel_item = None
            for item_id in player.inventory[:]:
                item = self.items.get(item_id)
                if item and item.item_type == ItemType.FUEL:
                    if fuel_type == "basic" and item.fuel_amount == 60:
                        fuel_item = item
                        break
                    elif fuel_type == "advanced" and item.fuel_amount == 180:
                        fuel_item = item
                        break
                    elif fuel_type == "premium" and item.fuel_amount == 300:
                        fuel_item = item
                        break
                    elif fuel_type == "ultra" and item.fuel_amount == 600:
                        fuel_item = item
                        break
                    elif fuel_type == "nuclear" and item.fuel_amount == 1200:
                        fuel_item = item
                        break
            if not fuel_item:
                return False, "У вас нет такого топлива"
            player.fuel += fuel_item.fuel_amount
            player.inventory.remove(fuel_item.item_id)
            if fuel_item.item_id in self.items:
                del self.items[fuel_item.item_id]
            asyncio.create_task(self.batch_save())
            return True, f"✅ Заправлено {fuel_item.fuel_amount} мин!"
        except Exception:
            return False, f"❌ Ошибка"

    def toggle_auto_mining(self, user_id: int) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            if not player.can_use_auto_mining():
                return False, "❌ Для автодобычи нужно прокачать улучшение 'Автодобыча' до 1 уровня."
            if player.fuel <= 0:
                return False, "❌ Нет топлива."
            player.auto_mining_enabled = not player.auto_mining_enabled
            if player.auto_mining_enabled:
                if not player.auto_mining_minerals:
                    player.auto_mining_minerals = [MineralType.COAL.name]
                minerals = [self._mineral_cache.get(m) for m in player.auto_mining_minerals if self._mineral_cache.get(m)]
                minerals = [m for m in minerals if m is not None]
                auto_session = AutoMiningSession(
                    user_id=user_id,
                    minerals=minerals,
                    is_active=True,
                    last_mine_time=datetime.now(),
                    interval_minutes=5,
                    next_mine_time=datetime.now(),
                    fuel_left=player.fuel,
                    last_activity=datetime.now(),
                    last_notification_time=None
                )
                self.auto_mining_sessions[user_id] = auto_session
                asyncio.create_task(self.batch_save())
                return True, "🤖 Автодобыча ВКЛЮЧЕНА!"
            else:
                if user_id in self.auto_mining_sessions:
                    auto_session = self.auto_mining_sessions[user_id]
                    player.fuel = auto_session.fuel_left
                    del self.auto_mining_sessions[user_id]
                asyncio.create_task(self.batch_save())
                return True, "🤖 Автодобыча ВЫКЛЮЧЕНА."
        except Exception:
            return False, f"❌ Ошибка"

    def process_auto_mining(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        try:
            player = self.players.get(user_id)
            if not player or not player.auto_mining_enabled or player.is_banned:
                return False, {"error": "Автодобыча не активна"}
            if user_id not in self.auto_mining_sessions:
                return False, {"error": "Сессия не найдена"}
            auto_session = self.auto_mining_sessions[user_id]
            auto_session.last_activity = datetime.now()
            
            if auto_session.fuel_left <= 0:
                player.auto_mining_enabled = False
                self.auto_mining_sessions.pop(user_id, None)
                asyncio.create_task(self.batch_save())
                return False, {"error": "⛽ Топливо кончилось."}
            
            results = []
            total_mineral = 0
            total_premium = 0
            auto_effect = player.get_auto_mining_effect()
            
            for mineral in auto_session.minerals:
                if not mineral:
                    continue
                base_reward = 2 * player.miner_level
                mineral_reward = base_reward * auto_effect * player.get_mineral_multiplier() / 5
                player.mineral_balance[mineral.name] = player.mineral_balance.get(mineral.name, 0) + mineral_reward
                player.total_mined += mineral_reward
                total_mineral += mineral_reward
                
                luck_chance = player.get_current_pickaxe_luck() + player.get_premium_coin_chance()
                if random.random() < luck_chance / 3:
                    player.premium_coin_balance += 1
                    player.total_premium_earned += 1
                    player.stats["premium_coins_found"] = player.stats.get("premium_coins_found", 0) + 1
                    total_premium += 1
                
                results.append({
                    "mineral": mineral,
                    "amount": mineral_reward,
                    "premium": 1 if total_premium > 0 else 0
                })
            
            exp_gained = int(total_mineral * 0.5)
            player.experience += exp_gained
            player.total_experience += exp_gained
            self._check_level_up(player)
            
            auto_session.fuel_left = max(0, auto_session.fuel_left - 5)
            player.fuel = auto_session.fuel_left
            
            if auto_session.fuel_left <= 0:
                player.auto_mining_enabled = False
                self.auto_mining_sessions.pop(user_id, None)
            
            auto_session.last_mine_time = datetime.now()
            auto_session.next_mine_time = datetime.now() + timedelta(minutes=auto_session.interval_minutes)
            player.stats["auto_mines"] = player.stats.get("auto_mines", 0) + 1
            
            asyncio.create_task(self.batch_save())
            
            return True, {
                "success": True,
                "results": results,
                "total_mineral": total_mineral,
                "total_premium": total_premium,
                "experience": exp_gained,
                "fuel_left": auto_session.fuel_left
            }
        except Exception:
            return False, {"error": "Ошибка"}

    def _check_level_up(self, player: Player):
        try:
            leveled_up = False
            while True:
                exp_needed = player.miner_level * 100
                if player.experience >= exp_needed and player.miner_level < MAX_LEVEL:
                    player.experience -= exp_needed
                    player.miner_level += 1
                    leveled_up = True
                    if player.miner_level == RESET_REWARD_LEVEL:
                        self._notify_reset_available(player.user_id)
                else:
                    break
            if leveled_up:
                asyncio.create_task(self.batch_save())
        except Exception:
            pass

    def _notify_reset_available(self, user_id: int):
        asyncio.create_task(self._send_reset_notification(user_id))

    async def _send_reset_notification(self, user_id: int):
        try:
            player = self.players.get(user_id)
            if player:
                bonus = player.calculate_reset_bonus()
                required_item = player.get_required_reset_item()
                await self.bot.send_message(
                    user_id,
                    f"🎉 Поздравляем! Вы достигли {RESET_REWARD_LEVEL} уровня!\n\n"
                    f"✨ Теперь вы можете переродиться и получить бонус!\n"
                    f"💰 Бонус: {bonus} 🪙\n"
                    f"📈 Множитель дохода станет: x{1.0 + (player.reincarnation_level + 1) * 0.5:.1f}\n\n"
                    f"⚠️ Требуется предмет: {required_item}\n"
                    f"💎 Все коллекционные и лимитированные предметы останутся, остальное сбросится!\n"
                    f"🔨 Кирка также останется!",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔄 Переродиться", callback_data="reset_level")]
                        ]
                    )
                )
        except Exception:
            pass

    def reset_player_level(self, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Игрок не найден или забанен", {}
            if not player.has_reset_item():
                required_item = player.get_required_reset_item()
                return False, f"❌ Требуется предмет: {required_item}", {}
            required_item_name = player.get_required_reset_item()
            has_item = player.consume_reset_item()
            if not has_item:
                return False, "❌ Не удалось использовать предмет", {}
            bonus = player.calculate_reset_bonus()
            collectibles = player.collectibles.copy()
            inventory = []
            for item_id in player.inventory:
                item = self.items.get(item_id)
                if item and (item.is_collectible or item.rarity == ItemRarity.LIMITED):
                    inventory.append(item_id)
            equipped = {}
            for slot, item_id in player.equipped_items.items():
                item = self.items.get(item_id)
                if item and (item.is_collectible or item.rarity == ItemRarity.LIMITED):
                    equipped[slot] = item_id
            unlocked = player.unlocked_minerals.copy()
            premium_coins = player.premium_coin_balance
            current_pickaxe_material = player.current_pickaxe_material
            current_pickaxe_upgrade = player.current_pickaxe_upgrade
            player.reincarnation_level += 1
            player.reincarnation_multiplier = 1.0 + (player.reincarnation_level * 0.5)
            player.miner_level = 1
            player.experience = 0
            player.gold_balance = bonus
            player.mining_power_level = 0
            player.mining_time_level = 0
            player.pickaxe_upgrade_level = 0
            player.mineral_multiplier_level = 0
            player.mineral_unlock_level = 1
            player.premium_chance_level = 0
            player.case_chance_level = 0
            player.collectible_chance_level = 0
            player.auto_mining_level = 0
            player.fuel = 0
            player.auto_mining_enabled = False
            player.premium_coin_balance = premium_coins
            player.collectibles = collectibles
            player.inventory = inventory
            player.equipped_items = equipped
            player.unlocked_minerals = unlocked
            player.current_pickaxe_material = current_pickaxe_material
            player.current_pickaxe_upgrade = current_pickaxe_upgrade
            player._update_unlocked_minerals_by_level()
            if user_id in self.active_mining_sessions:
                del self.active_mining_sessions[user_id]
            if user_id in self.auto_mining_sessions:
                del self.auto_mining_sessions[user_id]
            player.current_mining_session = None
            player.next_hit_time = None
            player.stats["times_reset"] = player.stats.get("times_reset", 0) + 1
            player.stats["total_reset_bonus"] = player.stats.get("total_reset_bonus", 0) + bonus
            asyncio.create_task(self.batch_save())
            return True, f"✅ Перерождение выполнено! Получен бонус {bonus} 🪙 и множитель x{player.reincarnation_multiplier:.1f}!", {
                "bonus": bonus,
                "new_level": 1,
                "times_reset": player.stats["times_reset"],
                "multiplier": player.reincarnation_multiplier
            }
        except Exception:
            return False, f"❌ Ошибка", {}

    def upgrade_pickaxe(self, user_id: int) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Игрок не найден или забанен"
            base_cost = 200
            material_index = list(PickaxeMaterial).index(player.current_pickaxe_material)
            upgrade_level = player.current_pickaxe_upgrade
            cost = int(base_cost * (1.2 ** (upgrade_level + material_index * 3)))
            if player.gold_balance < cost:
                return False, f"❌ Нужно: {cost} 🪙"
            old_material = player.current_pickaxe_material
            old_upgrade = player.current_pickaxe_upgrade
            if player.upgrade_current_pickaxe():
                player.gold_balance -= cost
                if player.current_pickaxe_material != old_material:
                    message = f"✅ Кирка улучшена до {player.current_pickaxe_material.value} материала! (ур. {player.current_pickaxe_upgrade})"
                else:
                    message = f"✅ Кирка прокачана до ур. {player.current_pickaxe_upgrade} (материал: {player.current_pickaxe_material.value})"
                asyncio.create_task(self.batch_save())
                return True, message
            else:
                return False, "❌ Достигнут максимальный уровень кирки!"
        except Exception:
            return False, f"❌ Ошибка"

    def complete_mining(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        try:
            if user_id not in self.active_mining_sessions:
                return False, {"error": "Нет активной добычи"}
            session = self.active_mining_sessions[user_id]
            player = self.players.get(user_id)
            if not player or not session.active or player.is_banned:
                return False, {"error": "Сессия не активна"}
            
            hits_done = session.hits_done
            remaining_hits = session.total_hits - hits_done
            mineral_per_hit = player.get_mineral_per_hit(session.base_reward_per_hit)
            total_mineral_reward = mineral_per_hit * session.total_hits
            
            if remaining_hits > 0:
                missed_reward = mineral_per_hit * remaining_hits
                total_mineral_reward += missed_reward
            
            player.mineral_balance[session.mineral.name] = player.mineral_balance.get(session.mineral.name, 0) + total_mineral_reward
            player.total_mined += total_mineral_reward
            player.stats["minerals_mined"] = player.stats.get("minerals_mined", 0) + 1

            premium_earned = 0
            luck_chance = player.get_current_pickaxe_luck() + player.get_premium_coin_chance()
            for _ in range(session.total_hits):
                if random.random() < luck_chance:
                    player.premium_coin_balance += 1
                    player.total_premium_earned += 1
                    player.stats["premium_coins_found"] = player.stats.get("premium_coins_found", 0) + 1
                    premium_earned += 1

            exp_gained = int(total_mineral_reward)
            player.experience += exp_gained
            player.total_experience += exp_gained
            self._check_level_up(player)

            drop_chance = 0.02
            
            dropped_items = []
            if random.random() < drop_chance:
                item = self._create_random_item(user_id)
                if item:
                    self.items[item.item_id] = item
                    player.inventory.append(item.item_id)
                    player.stats["items_found"] = player.stats.get("items_found", 0) + 1
                    dropped_items.append(item)

            collectible_chance = 0.0013
            collectible_chance += player.get_collectible_chance()
            if random.random() < collectible_chance:
                collectible_item = self.create_random_collectible(user_id)
                if collectible_item:
                    self.items[collectible_item.item_id] = collectible_item
                    player.inventory.append(collectible_item.item_id)
                    player.stats["collectibles_found"] = player.stats.get("collectibles_found", 0) + 1
                    if collectible_item.collectible_type:
                        ct_name = collectible_item.collectible_type.name
                        player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
                    dropped_items.append(collectible_item)

            case_chance = 0.0066
            case_chance += player.get_case_chance()
            dropped_cases = []
            if random.random() < case_chance:
                case = self._get_random_case_by_level(player.miner_level)
                if case:
                    case_item_id = str(uuid.uuid4())
                    case_item = Item(
                        item_id=case_item_id,
                        serial_number=self.generate_serial_number(),
                        name=case.name,
                        item_type=ItemType.CASE,
                        rarity=ItemRarity.EPIC if case.case_type == CaseType.EPIC else ItemRarity.RARE,
                        description=case.description,
                        buy_price=case.price,
                        sell_price=int(case.price * 0.5),
                        is_tradable=True,
                        owner_id=user_id
                    )
                    self.items[case_item_id] = case_item
                    player.inventory.append(case_item_id)
                    dropped_cases.append(case)

            session.hits_done = session.total_hits
            session.active = False
            self.active_mining_sessions.pop(user_id, None)
            player.stats["total_play_time"] = player.stats.get("total_play_time", 0) + int(session.total_mining_time)
            player.current_mining_session = None

            asyncio.create_task(self.batch_save())
            
            return True, {
                "success": True,
                "mineral": session.mineral,
                "mineral_reward": total_mineral_reward,
                "mineral_per_hit": mineral_per_hit,
                "total_hits": session.total_hits,
                "hits_done": hits_done,
                "gold_earned": 0,
                "premium_earned": premium_earned,
                "experience": exp_gained,
                "level_up": False,
                "items": dropped_items,
                "cases": dropped_cases
            }
        except Exception:
            return False, {"error": "Ошибка"}

    def _create_random_item(self, user_id: int) -> Optional[Item]:
        try:
            item_id = str(uuid.uuid4())
            item_types = [ItemType.LUCK_CHARM, ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE]
            weights = [50, 30, 20]
            item_type = random.choices(item_types, weights=weights)[0]
            rarity_weights = {
                ItemRarity.COMMON: 60,
                ItemRarity.RARE: 25,
                ItemRarity.EPIC: 10,
                ItemRarity.LEGENDARY: 4,
                ItemRarity.MYTHIC: 1
            }
            rarity = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()))[0]
            if item_type == ItemType.LUCK_CHARM:
                names = ["Камень удачи", "Талисман", "Амулет", "Оберег"]
                name = f"{random.choice(names)}"
                bonus = 0.02 * (list(ItemRarity).index(rarity) + 1)
                price = 1200 * (2 ** list(ItemRarity).index(rarity))
                return Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.LUCK_CHARM,
                    rarity=rarity,
                    description=f"{rarity.value} талисман",
                    luck_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
            elif item_type == ItemType.MINERAL_CHIP:
                names = ["Анализатор", "Сканер", "Детектор", "Датчик"]
                name = f"{random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.06)
                price = 1000 * (2 ** list(ItemRarity).index(rarity))
                return Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.MINERAL_CHIP,
                    rarity=rarity,
                    description=f"{rarity.value} чип",
                    mining_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
            else:
                names = ["Ядро", "Батарея", "Генератор"]
                name = f"{random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.05)
                price = 1000 * (2 ** list(ItemRarity).index(rarity))
                return Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.ENERGY_CORE,
                    rarity=rarity,
                    description=f"{rarity.value} ядро",
                    energy_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
        except Exception:
            return None

    def _get_random_case_by_level(self, level: int) -> Optional[Case]:
        try:
            available_cases = [self.cases["common_case"]]
            if level >= 5:
                available_cases.append(self.cases["rare_case"])
            if level >= 10:
                available_cases.append(self.cases["epic_case"])
            if level >= 15:
                available_cases.append(self.cases["legendary_case"])
            if level >= 20:
                available_cases.append(self.cases["mythic_case"])
            return random.choice(available_cases) if available_cases else None
        except Exception:
            return None

    def create_random_collectible(self, user_id: int) -> Optional[Item]:
        try:
            collectible_types = list(CollectibleType)
            collectible_type = random.choice(collectible_types)
            rarity_weights = {
                ItemRarity.COMMON: 50,
                ItemRarity.RARE: 30,
                ItemRarity.EPIC: 15,
                ItemRarity.LEGENDARY: 4,
                ItemRarity.MYTHIC: 1
            }
            rarity = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()))[0]
            names_map = {
                CollectibleType.NUGGET: ["🥨 Золотой", "🥨 Платиновый", "🥨 Палладий"],
                CollectibleType.FOSSIL: ["🦴 Аммонит", "🦴 Трилобит", "🦴 Зубы"],
                CollectibleType.GEODE: ["🥚 Агатовая", "🥚 Кварцевая", "🥚 Аметист"],
                CollectibleType.CRYSTAL: ["🔮 Кварц", "🔮 Аметист", "🔮 Топаз"],
                CollectibleType.METEORITE: ["🌠 Каменный", "🌠 Железный", "🌠 Углистый"],
                CollectibleType.GEMSTONE: ["💎 Рубин", "💎 Сапфир", "💎 Изумруд"],
                CollectibleType.ANCIENT_RELIC: ["🏺 Кирка", "🏺 Табличка", "🏺 Статуэтка"],
                CollectibleType.MINERAL_EGG: ["🥚 Мин. яйцо", "🥚 Дракона", "🥚 Феникса"]
            }
            name = random.choice(names_map[collectible_type])
            base_price = 8000
            price = base_price * (2 ** list(ItemRarity).index(rarity))
            return Item(
                item_id=str(uuid.uuid4()),
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.COLLECTIBLE,
                rarity=rarity,
                description="Коллекционный сувенир",
                buy_price=price,
                sell_price=int(price * 0.3),
                is_tradable=True,
                owner_id=user_id,
                is_collectible=True,
                collectible_type=collectible_type
            )
        except Exception:
            return None

    def convert_minerals_to_gold(self, user_id: int, mineral_name: str, amount: float) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            current_balance = player.mineral_balance.get(mineral_name, 0)
            if current_balance < amount:
                return False, f"❌ Недостаточно. Доступно: {current_balance:.2f}"
            base_rates = {
                "COAL": 0.2, "IRON": 0.5, "COPPER": 0.8, "ALUMINUM": 1.0, "ZINC": 1.2,
                "TIN": 1.5, "LEAD": 1.0, "NICKEL": 2.0, "SILVER": 5.0, "GOLD": 20.0,
                "PLATINUM": 30.0, "TITANIUM": 10.0, "URANIUM": 25.0, "DIAMOND": 50.0,
                "RUBY": 15.0, "SAPPHIRE": 12.0, "EMERALD": 18.0, "OBSIDIAN": 3.0,
                "COBALT": 4.0, "LITHIUM": 2.5, "CHROMIUM": 3.5, "MANGANESE": 2.0,
                "TUNGSTEN": 8.0, "PALLADIUM": 40.0, "RHODIUM": 60.0, "OSMIUM": 35.0,
                "IRIDIUM": 45.0, "PROMETHIUM": 100.0, "ACTINIUM": 150.0, "NOBELIUM": 200.0,
                "LAWRENCIUM": 250.0, "RUTHERFORDIUM": 300.0, "DUBNIUM": 350.0,
                "SEABORGIUM": 400.0, "BOHRIUM": 450.0, "HASSIUM": 500.0,
                "MEITNERIUM": 550.0, "DARMSTADTIUM": 600.0, "ROENTGENIUM": 650.0,
                "COPERNICIUM": 700.0, "NIHONIUM": 750.0, "FLEROVIUM": 800.0,
                "MOSCOVIUM": 850.0, "LIVERMORIUM": 900.0, "TENNESSINE": 950.0,
                "OGANESSON": 1000.0, "QUANTIUM": 1200.0, "INFINIUM": 1500.0,
                "COSMIUM": 2000.0, "GODLIUM": 5000.0
            }
            rate = base_rates.get(mineral_name, 0.5)
            gold = int(amount * rate)
            if gold < 1:
                return False, f"❌ Сумма слишком мала для конвертации"
            player.mineral_balance[mineral_name] -= amount
            player.gold_balance += gold
            asyncio.create_task(self.batch_save())
            mineral_value = next((m.value for m in MineralType if m.name == mineral_name), mineral_name)
            return True, f"✅ Продано {amount:.2f} {mineral_value}\n💰 Получено: {gold} 🪙"
        except Exception:
            return False, f"❌ Ошибка"

    def convert_all_minerals_to_gold(self, user_id: int) -> Tuple[bool, str, int]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен", 0
            base_rates = {
                "COAL": 0.2, "IRON": 0.5, "COPPER": 0.8, "ALUMINUM": 1.0, "ZINC": 1.2,
                "TIN": 1.5, "LEAD": 1.0, "NICKEL": 2.0, "SILVER": 5.0, "GOLD": 20.0,
                "PLATINUM": 30.0, "TITANIUM": 10.0, "URANIUM": 25.0, "DIAMOND": 50.0,
                "RUBY": 15.0, "SAPPHIRE": 12.0, "EMERALD": 18.0, "OBSIDIAN": 3.0,
                "COBALT": 4.0, "LITHIUM": 2.5, "CHROMIUM": 3.5, "MANGANESE": 2.0,
                "TUNGSTEN": 8.0, "PALLADIUM": 40.0, "RHODIUM": 60.0, "OSMIUM": 35.0,
                "IRIDIUM": 45.0, "PROMETHIUM": 100.0, "ACTINIUM": 150.0, "NOBELIUM": 200.0,
                "LAWRENCIUM": 250.0, "RUTHERFORDIUM": 300.0, "DUBNIUM": 350.0,
                "SEABORGIUM": 400.0, "BOHRIUM": 450.0, "HASSIUM": 500.0,
                "MEITNERIUM": 550.0, "DARMSTADTIUM": 600.0, "ROENTGENIUM": 650.0,
                "COPERNICIUM": 700.0, "NIHONIUM": 750.0, "FLEROVIUM": 800.0,
                "MOSCOVIUM": 850.0, "LIVERMORIUM": 900.0, "TENNESSINE": 950.0,
                "OGANESSON": 1000.0, "QUANTIUM": 1200.0, "INFINIUM": 1500.0,
                "COSMIUM": 2000.0, "GODLIUM": 5000.0
            }
            total_gold = 0
            converted = []
            minerals_to_convert = [(mineral_name, amount) for mineral_name, amount in player.mineral_balance.items() if amount > 0]
            if not minerals_to_convert:
                return False, "❌ Нет минералов для продажи", 0
            for mineral_name, amount in minerals_to_convert:
                rate = base_rates.get(mineral_name, 0.5)
                gold = int(amount * rate)
                if gold >= 1:
                    player.mineral_balance[mineral_name] = 0
                    total_gold += gold
                    mineral_value = next((m.value for m in MineralType if m.name == mineral_name), mineral_name)
                    converted.append(f"{mineral_value}: {gold}🪙")
            if total_gold > 0:
                player.gold_balance += total_gold
                asyncio.create_task(self.batch_save())
                result = "✅ Проданы ВСЕ минералы:\n\n"
                result += "\n".join(converted)
                result += f"\n\n💰 Всего: {total_gold} 🪙"
                return True, result, total_gold
            return False, "❌ Нет минералов для продажи", 0
        except Exception:
            return False, f"❌ Ошибка", 0

    def buy_upgrade(self, user_id: int, upgrade_type: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            upgrade_map = {
                "mining_power": ("mining_power_level", 100, 1.3, "💪 Количество ударов"),
                "mining_time": ("mining_time_level", 90, 1.3, "⏱️ Длительность (+10 мин)"),
                "mineral_multiplier": ("mineral_multiplier_level", 250, 1.3, "⛏️ Множитель минералов"),
                "mineral_unlock": ("mineral_unlock_level", 2000, 2.0, "🪨 Рудная жила"),
                "premium_chance": ("premium_chance_level", 150, 1.3, "💎 Шанс Premium Coin"),
                "case_chance": ("case_chance_level", 60, 1.3, "📦 Шанс ящиков"),
                "collectible_chance": ("collectible_chance_level", 150, 1.3, "🏆 Шанс коллекций"),
                "auto_mining": ("auto_mining_level", 10000, 1.5, "🤖 Автодобыча"),
            }
            if upgrade_type not in upgrade_map:
                return False, "❌ Неизвестное улучшение"
            attr_name, base_price, price_mult, display_name = upgrade_map[upgrade_type]
            current_level = getattr(player, attr_name, 0)
            if current_level >= MAX_LEVEL:
                return False, f"❌ Макс. уровень ({MAX_LEVEL})"
            cost = int(base_price * (price_mult ** current_level))
            if player.gold_balance < cost:
                return False, f"❌ Нужно: {cost} 🪙"
            player.gold_balance -= cost
            setattr(player, attr_name, current_level + 1)
            if upgrade_type == "mineral_unlock":
                player._update_unlocked_minerals_by_level()
            player.stats["upgrades_bought"] = player.stats.get("upgrades_bought", 0) + 1
            asyncio.create_task(self.batch_save())
            next_level = current_level + 2
            next_cost = int(base_price * (price_mult ** (next_level - 1))) if next_level <= MAX_LEVEL else 0
            next_cost_text = f" След: {next_cost} 🪙" if next_cost > 0 else " (MAX)"
            return True, f"✅ '{display_name}' до {current_level + 1} ур.!{next_cost_text}"
        except Exception:
            return False, f"❌ Ошибка"

    def buy_case(self, user_id: int, case_type_name: str) -> Tuple[bool, str, Optional[Item]]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Шахтёр не найден или забанен", None
            case = None
            case_name = ""
            case_price = 0
            if case_type_name == "COMMON":
                case = self.cases.get("common_case")
                case_name = "📦 Обычный ящик"
                case_price = 400
            elif case_type_name == "RARE":
                case = self.cases.get("rare_case")
                case_name = "🎁 Редкий ящик"
                case_price = 1500
            elif case_type_name == "EPIC":
                case = self.cases.get("epic_case")
                case_name = "💎 Эпический ящик"
                case_price = 8000
            elif case_type_name == "LEGENDARY":
                case = self.cases.get("legendary_case")
                case_name = "👑 Легендарный ящик"
                case_price = 40000
            elif case_type_name == "MYTHIC":
                case = self.cases.get("mythic_case")
                case_name = "✨ Мифический ящик"
                case_price = 80000
            else:
                return False, "❌ Неизвестный тип ящика", None
            if not case:
                return False, "❌ Ящик не найден", None
            if player.gold_balance < case_price:
                return False, f"❌ Нужно: {case_price} 🪙", None
            player.gold_balance -= case_price
            case_item_id = str(uuid.uuid4())
            case_item = Item(
                item_id=case_item_id,
                serial_number=self.generate_serial_number(),
                name=case_name,
                item_type=ItemType.CASE,
                rarity=ItemRarity.EPIC if case_type_name in ["EPIC", "LEGENDARY", "MYTHIC"] else ItemRarity.RARE,
                description=case.description,
                buy_price=case_price,
                sell_price=int(case_price * 0.5),
                is_tradable=True,
                owner_id=user_id
            )
            self.items[case_item_id] = case_item
            player.inventory.append(case_item_id)
            asyncio.create_task(self.batch_save())
            return True, f"✅ Куплен {case_name} за {case_price} 🪙", case_item
        except Exception:
            return False, f"❌ Ошибка", None

    def open_case(self, user_id: int, case_item_id: str) -> Tuple[bool, str, List[Item]]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Шахтёр не найден или забанен", []
            if case_item_id not in player.inventory:
                return False, "❌ Ящик не в инвентаре", []
            case_item = self.items.get(case_item_id)
            if not case_item or case_item.item_type != ItemType.CASE:
                return False, "❌ Это не ящик", []
            case = None
            for c in self.cases.values():
                if c.name == case_item.name:
                    case = c
                    break
            if not case:
                return False, "❌ Данные ящика не найдены", []
            num_items = random.randint(case.min_items, case.max_items)
            dropped_items = []
            for _ in range(num_items):
                collectible_chance = case.collectible_chance + player.get_collectible_chance()
                if random.random() < collectible_chance:
                    collectible_item = self.create_random_collectible(user_id)
                    if collectible_item:
                        self.items[collectible_item.item_id] = collectible_item
                        player.inventory.append(collectible_item.item_id)
                        player.stats["collectibles_found"] = player.stats.get("collectibles_found", 0) + 1
                        if collectible_item.collectible_type:
                            ct_name = collectible_item.collectible_type.name
                            player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
                        dropped_items.append(collectible_item)
                        continue
                rarities = list(case.drop_chances.keys())
                weights = list(case.drop_chances.values())
                selected_rarity = random.choices(rarities, weights=weights)[0]
                item_types = [ItemType.LUCK_CHARM, ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE]
                item_type = random.choice(item_types)
                item = self._create_item_by_type(user_id, item_type, selected_rarity)
                if item:
                    self.items[item.item_id] = item
                    player.inventory.append(item.item_id)
                    player.stats["items_found"] = player.stats.get("items_found", 0) + 1
                    dropped_items.append(item)
            player.inventory.remove(case_item_id)
            del self.items[case_item_id]
            player.stats["cases_opened"] = player.stats.get("cases_opened", 0) + 1
            asyncio.create_task(self.batch_save())
            return True, f"🎁 Открыт {case.name}!", dropped_items
        except Exception:
            return False, f"❌ Ошибка", []

    def _create_item_by_type(self, user_id: int, item_type: ItemType, rarity: ItemRarity) -> Optional[Item]:
        item_id = str(uuid.uuid4())
        if item_type == ItemType.LUCK_CHARM:
            names = ["Талисман", "Амулет", "Камень удачи", "Оберег"]
            name = f"{random.choice(names)}"
            bonus = 0.025 * (list(ItemRarity).index(rarity) + 1)
            price = 1500 * (2 ** list(ItemRarity).index(rarity))
            return Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.LUCK_CHARM,
                rarity=rarity,
                description=f"{rarity.value} талисман",
                luck_bonus=bonus,
                buy_price=price,
                sell_price=int(price * 0.6),
                is_tradable=True,
                owner_id=user_id
            )
        elif item_type == ItemType.MINERAL_CHIP:
            names = ["Чип", "Сканер", "Детектор"]
            name = f"{random.choice(names)}"
            bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.075)
            price = 1400 * (2 ** list(ItemRarity).index(rarity))
            return Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.MINERAL_CHIP,
                rarity=rarity,
                description=f"{rarity.value} чип",
                mining_bonus=bonus,
                buy_price=price,
                sell_price=int(price * 0.6),
                is_tradable=True,
                owner_id=user_id
            )
        else:
            names = ["Ядро", "Батарея", "Генератор"]
            name = f"{random.choice(names)}"
            bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.05)
            price = 1000 * (2 ** list(ItemRarity).index(rarity))
            return Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.ENERGY_CORE,
                rarity=rarity,
                description=f"{rarity.value} ядро",
                energy_bonus=bonus,
                buy_price=price,
                sell_price=int(price * 0.6),
                is_tradable=True,
                owner_id=user_id
            )

    def equip_item(self, user_id: int, item_id: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            if item_id not in player.inventory:
                return False, "❌ Предмет не в инвентаре"
            item = self.items.get(item_id)
            if not item:
                return False, "❌ Предмет не найден"
            slot_map = {
                ItemType.MINING_TOOL: "tool",
                ItemType.LUCK_CHARM: "charm",
                ItemType.MINERAL_CHIP: "chip",
                ItemType.ENERGY_CORE: "core",
                ItemType.LIMITED: "tool"
            }
            slot = slot_map.get(item.item_type)
            if not slot:
                return False, "❌ Этот предмет нельзя экипировать"
            old_item_id = player.equipped_items.get(slot)
            if old_item_id:
                player.equipped_items.pop(slot)
            player.equipped_items[slot] = item_id
            asyncio.create_task(self.batch_save())
            return True, f"✅ '{item.name}' надет!"
        except Exception:
            return False, f"❌ Ошибка"

    def unequip_item(self, user_id: int, slot: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            if slot not in player.equipped_items:
                return False, f"❌ В слоте '{slot}' нет предмета"
            item_id = player.equipped_items.pop(slot)
            item = self.items.get(item_id)
            asyncio.create_task(self.batch_save())
            item_name = item.name if item else "предмет"
            return True, f"✅ '{item_name}' снят!"
        except Exception:
            return False, f"❌ Ошибка"

    def sell_item(self, user_id: int, item_id: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            if item_id not in player.inventory:
                return False, "❌ Предмет не в инвентаре"
            item = self.items.get(item_id)
            if not item:
                return False, "❌ Предмет не найден"
            for slot, equipped_id in player.equipped_items.items():
                if equipped_id == item_id:
                    return False, "❌ Сначала снимите!"
            if player.is_item_on_market(item_id):
                return False, "❌ Предмет на рынке. Сначала снимите с продажи."
            sell_price = item.sell_price
            if sell_price <= 0:
                if item.is_collectible:
                    sell_price = 800
                elif item.item_type == ItemType.FUEL:
                    sell_price = item.buy_price // 2
                else:
                    sell_price = max(item.buy_price // 2, 80)
            player.gold_balance += sell_price
            player.inventory.remove(item_id)
            if item.is_collectible and item.collectible_type:
                ct_name = item.collectible_type.name
                if ct_name in player.collectibles and player.collectibles[ct_name] > 0:
                    player.collectibles[ct_name] -= 1
            del self.items[item_id]
            asyncio.create_task(self.batch_save())
            return True, f"✅ '{item.name}' продан за {sell_price} 🪙!"
        except Exception:
            return False, f"❌ Ошибка"

    def sell_items_by_rarity(self, user_id: int, rarity: ItemRarity) -> Tuple[bool, str, int, int]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен", 0, 0
            items_to_sell = []
            total_price = 0
            inventory_copy = player.inventory.copy()
            for item_id in inventory_copy:
                item = self.items.get(item_id)
                if item:
                    is_equipped = any(equipped_id == item_id for equipped_id in player.equipped_items.values())
                    is_on_market = player.is_item_on_market(item_id)
                    if not is_equipped and not is_on_market and item.rarity == rarity and item.is_tradable:
                        items_to_sell.append(item_id)
                        total_price += max(item.sell_price, 80)
            if not items_to_sell:
                return False, f"❌ Нет {rarity.value} предметов для продажи", 0, 0
            sold_count = 0
            for item_id in items_to_sell:
                success, _ = self.sell_item(user_id, item_id)
                if success:
                    sold_count += 1
            return True, f"✅ Продано {sold_count} {rarity.value} предметов", sold_count, total_price
        except Exception:
            return False, f"❌ Ошибка", 0, 0

    def create_market_offer(self, user_id: int, item_id: str, price: int) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен"
            if item_id not in player.inventory:
                return False, "❌ Предмет не в инвентаре"
            item = self.items.get(item_id)
            if not item:
                return False, "❌ Предмет не найден"
            if not item.is_collectible and item.rarity != ItemRarity.LIMITED:
                return False, "❌ Только коллекц. и лимитир. предметы!"
            if not item.is_tradable:
                return False, "❌ Этот предмет нельзя продавать"
            for slot, equipped_id in player.equipped_items.items():
                if equipped_id == item_id:
                    return False, "❌ Сначала снимите!"
            if price <= 0 or price > 800000:
                return False, "❌ Некорректная цена"
            if player.is_item_on_market(item_id):
                return False, "❌ Этот предмет уже выставлен на рынок"
            offer_id = str(uuid.uuid4())
            offer = MarketOffer(
                offer_id=offer_id,
                item_id=item_id,
                seller_id=user_id,
                seller_name=player.custom_name or player.username or player.first_name,
                price=price,
                is_active=True
            )
            self.market_offers[offer_id] = offer
            player.add_market_offer(item_id)
            asyncio.create_task(self.batch_save())
            return True, f"✅ '{item.name}' выставлен за {price} 🪙!"
        except Exception:
            return False, f"❌ Ошибка"

    def buy_market_offer(self, buyer_id: int, offer_id: str) -> Tuple[bool, str]:
        try:
            offer = self.market_offers.get(offer_id)
            if not offer:
                return False, "❌ Предложение не найдено"
            if not offer.is_active:
                return False, "❌ Предложение уже не активно"
            buyer = self.players.get(buyer_id)
            if not buyer or buyer.is_banned:
                return False, "❌ Покупатель не найден или забанен"
            if buyer_id == offer.seller_id:
                return False, "❌ Нельзя купить своё"
            item = self.items.get(offer.item_id)
            if not item:
                return False, "❌ Предмет не найден"
            seller = self.players.get(offer.seller_id)
            if not seller:
                return False, "❌ Продавец не найден"
            if buyer.gold_balance < offer.price:
                return False, f"❌ Нужно: {offer.price} 🪙"
            buyer.gold_balance -= offer.price
            seller.gold_balance += offer.price
            seller.remove_market_offer(offer.item_id)
            buyer.inventory.append(offer.item_id)
            if offer.item_id in seller.inventory:
                seller.inventory.remove(offer.item_id)
            item.owner_id = buyer_id
            buyer.stats["trades_completed"] = buyer.stats.get("trades_completed", 0) + 1
            buyer.stats["market_purchases"] = buyer.stats.get("market_purchases", 0) + 1
            seller.stats["trades_completed"] = seller.stats.get("trades_completed", 0) + 1
            seller.stats["market_sales"] = seller.stats.get("market_sales", 0) + 1
            del self.market_offers[offer_id]
            asyncio.create_task(self.batch_save())
            if buyer.notifications_enabled and buyer.market_notifications:
                asyncio.create_task(self._send_notification(
                    buyer_id,
                    f"✅ Покупка\n\n🎁 {item.name}\n💰 {offer.price} 🪙\n👤 Продавец: {seller.custom_name}"
                ))
            if seller.notifications_enabled and seller.market_notifications:
                asyncio.create_task(self._send_notification(
                    seller.user_id,
                    f"💰 Продажа\n\n🎁 {item.name}\n💰 {offer.price} 🪙\n👤 Покупатель: {buyer.custom_name}"
                ))
            return True, f"✅ Куплен '{item.name}' за {offer.price} 🪙!"
        except Exception:
            return False, f"❌ Ошибка"

    async def _send_notification(self, user_id: int, text: str):
        try:
            await self.bot.send_message(user_id, text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass

    def cancel_market_offer(self, user_id: int, offer_id: str) -> Tuple[bool, str]:
        try:
            offer = self.market_offers.get(offer_id)
            if not offer:
                return False, "❌ Предложение не найдено"
            if offer.seller_id != user_id:
                return False, "❌ Это не ваше предложение"
            player = self.players.get(user_id)
            if player:
                player.remove_market_offer(offer.item_id)
            del self.market_offers[offer_id]
            asyncio.create_task(self.batch_save())
            return True, "✅ Предложение снято"
        except Exception:
            return False, f"❌ Ошибка"

    def cancel_all_market_offers(self, user_id: int) -> Tuple[bool, str, int]:
        try:
            player = self.players.get(user_id)
            if not player:
                return False, "❌ Игрок не найден", 0
            offers_to_cancel = []
            for offer_id, offer in list(self.market_offers.items()):
                if offer.seller_id == user_id and offer.is_active:
                    offers_to_cancel.append(offer_id)
            for offer_id in offers_to_cancel:
                offer = self.market_offers[offer_id]
                player.remove_market_offer(offer.item_id)
                del self.market_offers[offer_id]
            asyncio.create_task(self.batch_save())
            return True, f"✅ Снято {len(offers_to_cancel)} предложений", len(offers_to_cancel)
        except Exception:
            return False, f"❌ Ошибка", 0

    def get_player_collectibles_stats(self, user_id: int) -> Dict[str, Any]:
        try:
            player = self.players.get(user_id)
            if not player:
                return {}
            total = sum(player.collectibles.values())
            unique = sum(1 for count in player.collectibles.values() if count > 0)
            percentage = (unique / len(CollectibleType)) * 100 if len(CollectibleType) > 0 else 0
            return {
                "total": total,
                "unique_types": unique,
                "by_type": player.collectibles.copy(),
                "completion_percentage": percentage
            }
        except Exception:
            return {}

    def get_top_players(self, top_type: str = "gold", limit: int = 10) -> List[Tuple]:
        try:
            players = list(self.players.values())
            if top_type == "gold":
                sorted_players = sorted(players, key=lambda p: p.gold_balance, reverse=True)[:limit]
                return [(p.custom_name, p.gold_balance, p.miner_level) for p in sorted_players]
            elif top_type == "level":
                sorted_players = sorted(players, key=lambda p: p.miner_level, reverse=True)[:limit]
                return [(p.custom_name, p.miner_level, p.gold_balance) for p in sorted_players]
            elif top_type == "collectibles":
                sorted_players = sorted(players, key=lambda p: sum(p.collectibles.values()), reverse=True)[:limit]
                return [(p.custom_name, sum(p.collectibles.values()), p.miner_level) for p in sorted_players]
            elif top_type == "reincarnation":
                sorted_players = sorted(players, key=lambda p: p.reincarnation_level, reverse=True)[:limit]
                return [(p.custom_name, p.reincarnation_level, p.miner_level) for p in sorted_players]
            elif top_type == "roulette":
                sorted_players = sorted(players, key=lambda p: p.stats.get("roulette_profit", 0), reverse=True)[:limit]
                return [(p.custom_name, p.stats.get("roulette_profit", 0), p.miner_level) for p in sorted_players]
            return []
        except Exception:
            return []

    def get_system_stats(self) -> Dict[str, Any]:
        try:
            total_players = len(self.players)
            active_today = sum(1 for p in self.players.values() if p.last_mining_time and (datetime.now() - p.last_mining_time).days < 1)
            active_now = len([p for p in self.players.values() if p.user_id in self.active_mining_sessions or p.auto_mining_enabled])
            total_gold = sum(p.gold_balance for p in self.players.values())
            total_premium = sum(p.premium_coin_balance for p in self.players.values())
            total_mined = sum(p.total_mined for p in self.players.values())
            banned = len(self.bans)
            online_auto = len(self.auto_mining_sessions)
            total_promocodes_activated = len(self.promocode_activations)
            total_roulette_bets = sum(p.stats.get("roulette_wins", 0) + p.stats.get("roulette_losses", 0) for p in self.players.values())
            return {
                "total_players": total_players,
                "active_today": active_today,
                "active_now": active_now,
                "total_gold": total_gold,
                "total_premium": total_premium,
                "total_mined": total_mined,
                "banned": banned,
                "online_auto": online_auto,
                "reincarnations": sum(p.stats.get("times_reset", 0) for p in self.players.values()),
                "promocodes_activated": total_promocodes_activated,
                "roulette_bets": total_roulette_bets
            }
        except Exception:
            return {}

    def get_donate_reward(self, stars: int) -> Dict[str, Any]:
        ruby_price = self.ruby_price
        ruby_total = self.ruby_total
        ruby_left = ruby_total - self.limited_item_counter
        rewards = {
            1: {"gold": 80, "bonus_percent": 0, "items": []},
            5: {"gold": 400, "bonus_percent": 10, "items": ["common_case"]},
            10: {"gold": 850, "bonus_percent": 20, "items": ["rare_case"]},
            20: {"gold": 1800, "bonus_percent": 30, "items": ["rare_case", "common_fuel"]},
            50: {"gold": 4500, "bonus_percent": 50, "items": ["epic_case", "advanced_fuel", "random_tool"]},
            ruby_price: {"gold": 6800, "bonus_percent": 85, "items": ["royal_ruby"]},
            100: {"gold": 9000, "bonus_percent": 100, "items": ["legendary_case", "premium_fuel", "epic_tool", "random_collectible"]}
        }
        if stars in rewards:
            return rewards[stars]
        gold = stars * 80
        bonus_percent = min(stars // 2, 80)
        items = []
        if stars >= 50:
            items.append("rare_case")
        if stars >= 100:
            items.append("epic_case")
        return {"gold": gold, "bonus_percent": bonus_percent, "items": items}

    def get_package_reward(self, package_type: str) -> Dict[str, Any]:
        packages = {
            "starter": {
                "gold": 5000,
                "items": ["epic_case", "advanced_fuel"],
                "description": "Стартовый пакет"
            },
            "business": {
                "gold": 12000,
                "items": ["legendary_case", "premium_fuel", "random_tool"],
                "description": "Промышленный пакет"
            },
            "premium": {
                "gold": 30000,
                "items": ["mythic_case", "ultra_fuel", "random_tool", "random_collectible"],
                "description": "Магнатский пакет"
            }
        }
        return packages.get(package_type, {"gold": 0, "items": [], "description": "Неизвестный пакет"})

    def process_donation(self, user_id: int, stars: int, payload: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "Шахтёр не найден или забанен", {}
            discount = player.get_discount("donate_bonus")
            ruby_discount = player.get_discount("ruby_discount")
            promo_code = None
            if payload and payload.startswith("promo_"):
                promo_code = payload[6:]
                if promo_code in self.promocodes:
                    promo = self.promocodes[promo_code]
                    if promo.is_active and promo.reward_type == "donate_bonus" and promo.used_count < promo.max_uses:
                        if player.miner_level >= promo.min_level:
                            if not player.has_activated_promocode(promo_code):
                                discount = promo.reward_value
                                player.add_discount("donate_bonus", discount, promo_code)
                                self.promocodes[promo_code].used_count += 1
                                player.add_activated_promocode(promo_code)
                                self.promocode_activations.append(PromoCodeActivation(
                                    user_id=user_id,
                                    code=promo_code
                                ))
            original_stars = stars
            stars_with_discount = stars
            discount_applied = 0
            if discount > 0:
                stars_with_discount = max(1, int(stars * (100 - discount) / 100))
                discount_applied = discount
            reward = self.get_donate_reward(original_stars)
            total_gold = reward["gold"]
            if reward["bonus_percent"] > 0:
                bonus = int(total_gold * reward["bonus_percent"] / 100)
                total_gold += bonus
            player.gold_balance += total_gold
            player.total_gold_earned += total_gold
            items_given = []
            for item_type in reward.get("items", []):
                if item_type == "common_case":
                    success, _, case_item = self.buy_case(user_id, "COMMON")
                    if success and case_item:
                        items_given.append(case_item)
                elif item_type == "rare_case":
                    success, _, case_item = self.buy_case(user_id, "RARE")
                    if success and case_item:
                        items_given.append(case_item)
                elif item_type == "epic_case":
                    success, _, case_item = self.buy_case(user_id, "EPIC")
                    if success and case_item:
                        items_given.append(case_item)
                elif item_type == "legendary_case":
                    success, _, case_item = self.buy_case(user_id, "LEGENDARY")
                    if success and case_item:
                        items_given.append(case_item)
                elif item_type == "mythic_case":
                    success, _, case_item = self.buy_case(user_id, "MYTHIC")
                    if success and case_item:
                        items_given.append(case_item)
                elif item_type == "common_fuel":
                    item_id = str(uuid.uuid4())
                    fuel_item = Item(
                        item_id=item_id,
                        serial_number=self.generate_serial_number(),
                        name="⛽ Угольные брикеты",
                        item_type=ItemType.FUEL,
                        rarity=ItemRarity.COMMON,
                        description="Топливо (60 мин)",
                        buy_price=800,
                        sell_price=400,
                        is_tradable=True,
                        owner_id=user_id,
                        fuel_amount=60
                    )
                    self.items[item_id] = fuel_item
                    player.inventory.append(item_id)
                    items_given.append(fuel_item)
                elif item_type == "advanced_fuel":
                    item_id = str(uuid.uuid4())
                    fuel_item = Item(
                        item_id=item_id,
                        serial_number=self.generate_serial_number(),
                        name="🔥 Нефтяное топливо",
                        item_type=ItemType.FUEL,
                        rarity=ItemRarity.RARE,
                        description="Топливо (180 мин)",
                        buy_price=2000,
                        sell_price=1000,
                        is_tradable=True,
                        owner_id=user_id,
                        fuel_amount=180
                    )
                    self.items[item_id] = fuel_item
                    player.inventory.append(item_id)
                    items_given.append(fuel_item)
                elif item_type == "premium_fuel":
                    item_id = str(uuid.uuid4())
                    fuel_item = Item(
                        item_id=item_id,
                        serial_number=self.generate_serial_number(),
                        name="⚡ Энергостержни",
                        item_type=ItemType.FUEL,
                        rarity=ItemRarity.EPIC,
                        description="Топливо (300 мин)",
                        buy_price=4000,
                        sell_price=2000,
                        is_tradable=True,
                        owner_id=user_id,
                        fuel_amount=300
                    )
                    self.items[item_id] = fuel_item
                    player.inventory.append(item_id)
                    items_given.append(fuel_item)
                elif item_type == "ultra_fuel":
                    item_id = str(uuid.uuid4())
                    fuel_item = Item(
                        item_id=item_id,
                        serial_number=self.generate_serial_number(),
                        name="🚀 Реактор",
                        item_type=ItemType.FUEL,
                        rarity=ItemRarity.LEGENDARY,
                        description="Топливо (600 мин)",
                        buy_price=8000,
                        sell_price=4000,
                        is_tradable=True,
                        owner_id=user_id,
                        fuel_amount=600
                    )
                    self.items[item_id] = fuel_item
                    player.inventory.append(item_id)
                    items_given.append(fuel_item)
                elif item_type == "nuclear_fuel":
                    item_id = str(uuid.uuid4())
                    fuel_item = Item(
                        item_id=item_id,
                        serial_number=self.generate_serial_number(),
                        name="☢️ Ядерное топливо",
                        item_type=ItemType.FUEL,
                        rarity=ItemRarity.MYTHIC,
                        description="Топливо (1200 мин)",
                        buy_price=20000,
                        sell_price=10000,
                        is_tradable=True,
                        owner_id=user_id,
                        fuel_amount=1200
                    )
                    self.items[item_id] = fuel_item
                    player.inventory.append(item_id)
                    items_given.append(fuel_item)
                elif item_type == "random_tool":
                    rarities = [ItemRarity.RARE, ItemRarity.EPIC, ItemRarity.LEGENDARY, ItemRarity.MYTHIC]
                    weights = [40, 35, 20, 5]
                    rarity = random.choices(rarities, weights=weights)[0]
                    item = self._create_item_by_type(user_id, random.choice([ItemType.LUCK_CHARM, ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE]), rarity)
                    if item:
                        self.items[item.item_id] = item
                        player.inventory.append(item.item_id)
                        items_given.append(item)
                elif item_type == "random_collectible":
                    collectible_item = self.create_random_collectible(user_id)
                    if collectible_item:
                        self.items[collectible_item.item_id] = collectible_item
                        player.inventory.append(collectible_item.item_id)
                        items_given.append(collectible_item)
                elif item_type == "royal_ruby":
                    if self.limited_item_counter < self.ruby_total:
                        ruby_item = self._get_ruby_item()
                        if ruby_item:
                            new_item_id = str(uuid.uuid4())
                            new_item = Item(
                                item_id=new_item_id,
                                serial_number=self.generate_serial_number(),
                                name=ruby_item.name,
                                item_type=ruby_item.item_type,
                                rarity=ruby_item.rarity,
                                description=ruby_item.description,
                                mining_bonus=ruby_item.mining_bonus,
                                luck_bonus=ruby_item.luck_bonus,
                                buy_price=ruby_item.buy_price,
                                sell_price=ruby_item.sell_price,
                                is_tradable=True,
                                owner_id=user_id,
                                is_collectible=True
                            )
                            self.items[new_item_id] = new_item
                            player.inventory.append(new_item_id)
                            items_given.append(new_item)
                            self.limited_item_counter += 1
                    else:
                        player.gold_balance += 20000
                        total_gold += 20000
                        items_given.append("Лимит исчерпан, выдано 20000 🪙")
            asyncio.create_task(self.batch_save())
            result = {
                "success": True,
                "stars": original_stars,
                "discounted_stars": stars_with_discount if discount_applied > 0 else original_stars,
                "gold": total_gold,
                "bonus_percent": reward["bonus_percent"],
                "discount_percent": discount_applied,
                "items": items_given,
                "player": player,
                "ruby_left": self.ruby_total - self.limited_item_counter
            }
            discount_text = f" (со скидкой {discount_applied}%, заплачено {stars_with_discount} ⭐)" if discount_applied > 0 else ""
            return True, f"✅ Спасибо! Получено {total_gold} 🪙{discount_text}", result
        except Exception:
            return False, f"❌ Ошибка", {}

    def _get_ruby_item(self) -> Optional[Item]:
        for item in self.items.values():
            if item.name == LIMITED_ITEM_NAME:
                return item
        return None

    async def add_channel(self, name: str, url: str, required_level: int, reward: int) -> Tuple[bool, str]:
        try:
            bot_in_channel = await self.check_bot_in_channel(url)
            channel_id = f"channel_{len(self.channels) + 1}"
            channel = Channel(
                id=channel_id,
                name=name,
                url=url,
                required_level=required_level,
                reward=reward,
                bot_member=bot_in_channel,
                last_check=datetime.now()
            )
            self.channels[channel_id] = channel
            asyncio.create_task(self.batch_save())
            if bot_in_channel:
                return True, f"✅ Канал '{name}' добавлен! ✅ Бот админ."
            else:
                return True, f"✅ Канал '{name}' добавлен! ⚠️ Бот НЕ админ. Добавьте бота."
        except Exception:
            return False, f"❌ Ошибка"

    def remove_channel(self, channel_id: str) -> Tuple[bool, str]:
        try:
            if channel_id not in self.channels:
                return False, "❌ Канал не найден"
            del self.channels[channel_id]
            asyncio.create_task(self.batch_save())
            return True, "✅ Канал удален"
        except Exception:
            return False, f"❌ Ошибка"

    def get_all_items_list(self) -> str:
        try:
            items_by_type = {}
            for item in self.items.values():
                if item.item_type not in items_by_type:
                    items_by_type[item.item_type] = []
                items_by_type[item.item_type].append(item.name)
            result = "📦 Все предметы в системе:\n\n"
            for item_type, names in items_by_type.items():
                result += f"{item_type.value}:\n"
                for name in sorted(set(names))[:10]:
                    result += f"  • {name}\n"
                result += "\n"
            return result
        except Exception:
            return "❌ Ошибка получения списка предметов"

    def get_all_minerals_list(self) -> str:
        try:
            result = "🪨 Все минералы:\n\n"
            for mineral in MineralType:
                result += f"• {mineral.value}\n"
            return result
        except Exception:
            return "❌ Ошибка получения списка минералов"

    def find_item_by_name(self, item_name: str) -> Optional[Item]:
        for item in self.items.values():
            if item.name.lower() == item_name.lower():
                return item
        for item in self.items.values():
            if item_name.lower() in item.name.lower():
                return item
        return None

    def give_item(self, user_id: int, item_name: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player:
                return False, "❌ Шахтёр не найден"
            found_item = self.find_item_by_name(item_name)
            if not found_item:
                if "Рубин" in item_name or "Королевский" in item_name:
                    found_item = self._get_ruby_item()
                if not found_item:
                    return False, f"❌ Предмет '{item_name}' не найден в системе"
            new_item_id = str(uuid.uuid4())
            new_item = Item(
                item_id=new_item_id,
                serial_number=self.generate_serial_number(),
                name=found_item.name,
                item_type=found_item.item_type,
                rarity=found_item.rarity,
                description=found_item.description,
                mining_bonus=found_item.mining_bonus,
                luck_bonus=found_item.luck_bonus,
                energy_bonus=found_item.energy_bonus,
                buy_price=found_item.buy_price,
                sell_price=found_item.sell_price,
                is_tradable=found_item.is_tradable,
                owner_id=user_id,
                is_collectible=found_item.is_collectible,
                collectible_type=found_item.collectible_type,
                fuel_amount=found_item.fuel_amount,
                pickaxe_level=found_item.pickaxe_level,
                pickaxe_material=found_item.pickaxe_material,
                base_hits=found_item.base_hits,
                pickaxe_upgrade_level=found_item.pickaxe_upgrade_level
            )
            self.items[new_item.item_id] = new_item
            player.inventory.append(new_item.item_id)
            if new_item.is_collectible and new_item.collectible_type:
                ct_name = new_item.collectible_type.name
                player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
            asyncio.create_task(self.batch_save())
            return True, f"✅ '{new_item.name}' выдан игроку {player.custom_name}"
        except Exception:
            return False, f"❌ Ошибка"

    def reset_player(self, user_id: int) -> Tuple[bool, str]:
        try:
            if user_id not in self.players:
                return False, "❌ Шахтёр не найден"
            old_player = self.players[user_id]
            new_player = Player(
                user_id=user_id,
                username=old_player.username,
                first_name=old_player.first_name,
                player_number=old_player.player_number,
                player_id_str=old_player.player_id_str
            )
            self.players[user_id] = new_player
            self.active_mining_sessions.pop(user_id, None)
            self.auto_mining_sessions.pop(user_id, None)
            asyncio.create_task(self.batch_save())
            return True, f"✅ Игрок {old_player.custom_name} сброшен"
        except Exception:
            return False, f"❌ Ошибка"

    def set_player_custom_name(self, user_id: int, new_name: str) -> Tuple[bool, str]:
        try:
            player = self.players.get(user_id)
            if not player:
                return False, "❌ Шахтёр не найден"
            if len(new_name) > 20 or len(new_name) < 3:
                return False, "❌ Имя должно быть от 3 до 20 символов"
            old_name = player.custom_name
            player.custom_name = new_name
            asyncio.create_task(self.batch_save())
            return True, f"✅ Имя изменено с '{old_name}' на '{new_name}'"
        except Exception:
            return False, f"❌ Ошибка"

    def toggle_notification(self, user_id: int, notification_type: str) -> Tuple[bool, str, bool]:
        try:
            player = self.players.get(user_id)
            if not player:
                return False, "❌ Шахтёр не найден", False
            if notification_type == "all":
                player.notifications_enabled = not player.notifications_enabled
                new_state = player.notifications_enabled
                return True, f"Уведомления {'вкл' if new_state else 'выкл'}", new_state
            elif notification_type == "market":
                player.market_notifications = not player.market_notifications
                new_state = player.market_notifications
                return True, f"Рынок {'вкл' if new_state else 'выкл'}", new_state
            elif notification_type == "mining":
                player.mining_notifications = not player.mining_notifications
                new_state = player.mining_notifications
                return True, f"Добыча {'вкл' if new_state else 'выкл'}", new_state
            elif notification_type == "daily":
                player.daily_notifications = not player.daily_notifications
                new_state = player.daily_notifications
                return True, f"Daily {'вкл' if new_state else 'выкл'}", new_state
            return False, "❌ Неизвестный тип", False
        except Exception:
            return False, f"❌ Ошибка", False

    def daily_bonus(self, user_id: int) -> Tuple[bool, str, int]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Шахтёр не найден или забанен", 0
            now = datetime.now()
            if player.last_daily:
                delta = now - player.last_daily
                if delta < timedelta(hours=20):
                    hours_left = 24 - delta.seconds // 3600
                    return False, f"⏳ Бонус уже получен. След. через {hours_left} ч.", 0
            gold_bonus = 500 + (player.miner_level * 20)
            if player.last_daily and (now - player.last_daily) < timedelta(hours=48):
                player.stats["daily_streak"] = player.stats.get("daily_streak", 0) + 1
            else:
                player.stats["daily_streak"] = 1
            streak = player.stats.get("daily_streak", 1)
            if streak > 1:
                gold_bonus = int(gold_bonus * (1 + (streak * 0.05)))
            player.gold_balance += gold_bonus
            player.last_daily = now
            asyncio.create_task(self.batch_save())
            if player.daily_notifications:
                asyncio.create_task(self._send_notification(
                    user_id,
                    f"🎁 Ежедневный бонус\n\n💰 {gold_bonus} 🪙\n🔥 Streak: {streak} дней"
                ))
            return True, "✅ Ежедневный бонус получен!", gold_bonus
        except Exception:
            return False, f"❌ Ошибка", 0

    def transfer_gold(self, from_id: int, to_username: str, amount: int, fee_percent: int = 5) -> Tuple[bool, str, int, int]:
        try:
            sender = self.players.get(from_id)
            if not sender or sender.is_banned:
                return False, "❌ Отправитель не найден или забанен", 0, 0
            receiver = None
            for p in self.players.values():
                if p.username and p.username.lower() == to_username.lower().replace('@', ''):
                    receiver = p
                    break
                if p.custom_name.lower() == to_username.lower():
                    receiver = p
                    break
            if not receiver:
                return False, "❌ Получатель не найден", 0, 0
            if sender.user_id == receiver.user_id:
                return False, "❌ Нельзя перевести самому себе", 0, 0
            if amount <= 0:
                return False, "❌ Сумма должна быть > 0", 0, 0
            total = amount
            fee = int(total * fee_percent / 100)
            send_amount = total - fee
            if sender.gold_balance < total:
                return False, f"❌ Нужно: {total} 🪙 (с комиссией {fee_percent}%)", 0, 0
            sender.gold_balance -= total
            receiver.gold_balance += send_amount
            asyncio.create_task(self.batch_save())
            if receiver.notifications_enabled and receiver.market_notifications:
                asyncio.create_task(self._send_notification(
                    receiver.user_id,
                    f"💰 Получен перевод\n\n👤 От: {sender.custom_name}\n💵 Сумма: {send_amount} 🪙"
                ))
            return True, f"✅ Переведено {send_amount} 🪙 пользователю {receiver.custom_name}", send_amount, fee
        except Exception:
            return False, f"❌ Ошибка", 0, 0

    def set_ruby_price(self, stars: int) -> Tuple[bool, str]:
        try:
            if stars < 1:
                return False, "❌ Цена должна быть > 0"
            self.ruby_price = stars
            asyncio.create_task(self.batch_save())
            return True, f"✅ Цена рубина изменена на {stars} ⭐"
        except Exception:
            return False, f"❌ Ошибка"

    def set_ruby_limit(self, limit: int) -> Tuple[bool, str]:
        try:
            if limit < 0:
                return False, "❌ Лимит не может быть < 0"
            self.ruby_total = limit
            asyncio.create_task(self.batch_save())
            return True, f"✅ Лимит рубина изменён на {limit}"
        except Exception:
            return False, f"❌ Ошибка"

    def set_ruby_count(self, count: int) -> Tuple[bool, str]:
        try:
            if count < 0 or count > self.ruby_total:
                return False, f"❌ Некорректное кол-во (0-{self.ruby_total})"
            self.limited_item_counter = count
            asyncio.create_task(self.batch_save())
            return True, f"✅ Выданных рубинов: {count}"
        except Exception:
            return False, f"❌ Ошибка"

    def get_ruby_info(self) -> str:
        return f"""
👑 Информация о Королевском рубине

📊 Статистика:
• Цена: {self.ruby_price} ⭐
• Всего выпущено: {self.ruby_total}
• Выдано: {self.limited_item_counter}
• Осталось: {self.ruby_total - self.limited_item_counter}

💎 Характеристики:
• Бонус добычи: +100%
• Бонус удачи: +50%
• Редкость: Лимитированный

⚠️ Предмет можно продавать на рынке
"""

    def broadcast_donate_message(self, stars: int, user_name: str) -> str:
        return f"🎉 Игрок {user_name} поддержал проект на {stars} ⭐! Спасибо!"

    def broadcast_limited_message(self, user_name: str) -> str:
        return f"👑 Игрок {user_name} получил лимитированный Королевский рубин! Осталось {self.ruby_total - self.limited_item_counter} шт."

    def search_player(self, query: str) -> Optional[Player]:
        try:
            if query.isdigit():
                user_id = int(query)
                return self.players.get(user_id)
            for player in self.players.values():
                if player.username and player.username.lower() == query.lower().replace('@', ''):
                    return player
                if player.custom_name.lower() == query.lower():
                    return player
            return None
        except Exception:
            return None

    def cleanup_old_data(self):
        try:
            now = datetime.now()
            for user_id, session in list(self.active_mining_sessions.items()):
                if now - session.last_activity > timedelta(hours=24):
                    del self.active_mining_sessions[user_id]
            for offer_id, offer in list(self.market_offers.items()):
                if now - offer.created_at > timedelta(days=14):
                    seller = self.players.get(offer.seller_id)
                    if seller:
                        seller.remove_market_offer(offer.item_id)
                    del self.market_offers[offer_id]
            for user_id in list(self._player_last_access.keys()):
                if now.timestamp() - self._player_last_access[user_id] > SESSION_TIMEOUT:
                    del self._player_last_access[user_id]
            gc.collect()
        except Exception:
            pass

    def create_promocode(self, code: str, reward_type: str, reward_value: Any, max_uses: int, 
                         min_level: int = 1, expires_at: Optional[datetime] = None, description: str = "") -> Tuple[bool, str]:
        try:
            if code in self.promocodes:
                return False, "❌ Промокод с таким названием уже существует"
            promo = PromoCode(
                code=code,
                reward_type=reward_type,
                reward_value=reward_value,
                max_uses=max_uses,
                min_level=min_level,
                expires_at=expires_at,
                description=description
            )
            self.promocodes[code] = promo
            asyncio.create_task(self.batch_save())
            return True, f"✅ Промокод {code} создан!"
        except Exception:
            return False, f"❌ Ошибка"

    def delete_promocode(self, code: str) -> Tuple[bool, str]:
        try:
            if code not in self.promocodes:
                return False, "❌ Промокод не найден"
            del self.promocodes[code]
            asyncio.create_task(self.batch_save())
            return True, f"✅ Промокод {code} удален!"
        except Exception:
            return False, f"❌ Ошибка"

    def activate_promocode(self, user_id: int, code: str) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Игрок не найден или забанен", {}
            code = code.upper().strip()
            if code not in self.promocodes:
                return False, "❌ Промокод не найден", {}
            promo = self.promocodes[code]
            if not promo.is_active:
                return False, "❌ Промокод неактивен", {}
            if promo.used_count >= promo.max_uses:
                return False, "❌ Промокод больше недействителен (лимит использований)", {}
            if promo.expires_at and datetime.now() > promo.expires_at:
                promo.is_active = False
                asyncio.create_task(self.batch_save())
                return False, "❌ Промокод истек", {}
            if player.miner_level < promo.min_level:
                return False, f"❌ Требуется уровень {promo.min_level}+", {}
            if player.has_activated_promocode(code):
                return False, "❌ Вы уже активировали этот промокод", {}
            reward_text = ""
            reward_items = []
            
            if promo.reward_type == "gold":
                gold = int(promo.reward_value)
                player.gold_balance += gold
                player.total_gold_earned += gold
                reward_text = f"+{gold} 🪙"
                
            elif promo.reward_type == "ruby_discount":
                player.add_discount("ruby_discount", int(promo.reward_value), code)
                reward_text = f"скидка {promo.reward_value}% на Королевский рубин"
                
            elif promo.reward_type == "donate_bonus":
                player.add_discount("donate_bonus", int(promo.reward_value), code)
                reward_text = f"скидка {promo.reward_value}% на любой донат"
                
            elif promo.reward_type == "item":
                success, msg = self.give_item(user_id, promo.reward_value)
                if success:
                    reward_text = f"предмет {promo.reward_value}"
                else:
                    return False, msg, {}
                    
            elif promo.reward_type == "case":
                case_type = promo.reward_value
                success, msg, case_item = self.buy_case(user_id, case_type)
                if success and case_item:
                    reward_items.append(case_item)
                    reward_text = f"ящик {case_type}"
                else:
                    return False, msg, {}
                    
            elif promo.reward_type == "premium_coin":
                amount = int(promo.reward_value)
                player.premium_coin_balance += amount
                player.total_premium_earned += amount
                reward_text = f"+{amount} 💎"
                
            elif promo.reward_type == "fuel":
                amount = int(promo.reward_value)
                player.fuel += amount
                reward_text = f"+{amount} мин топлива"
                
            elif promo.reward_type == "package":
                package = self.get_package_reward(promo.reward_value)
                if package["gold"] > 0:
                    player.gold_balance += package["gold"]
                    player.total_gold_earned += package["gold"]
                    reward_text = f"{package['description']}: +{package['gold']}🪙"
                for item_type in package["items"]:
                    if item_type == "epic_case":
                        success, _, case_item = self.buy_case(user_id, "EPIC")
                        if success and case_item:
                            reward_items.append(case_item)
                    elif item_type == "legendary_case":
                        success, _, case_item = self.buy_case(user_id, "LEGENDARY")
                        if success and case_item:
                            reward_items.append(case_item)
                    elif item_type == "mythic_case":
                        success, _, case_item = self.buy_case(user_id, "MYTHIC")
                        if success and case_item:
                            reward_items.append(case_item)
                    elif item_type == "advanced_fuel":
                        item_id = str(uuid.uuid4())
                        fuel_item = Item(
                            item_id=item_id,
                            serial_number=self.generate_serial_number(),
                            name="🔥 Нефтяное топливо",
                            item_type=ItemType.FUEL,
                            rarity=ItemRarity.RARE,
                            description="Топливо (180 мин)",
                            buy_price=2000,
                            sell_price=1000,
                            is_tradable=True,
                            owner_id=user_id,
                            fuel_amount=180
                        )
                        self.items[item_id] = fuel_item
                        player.inventory.append(item_id)
                        reward_items.append(fuel_item)
                    elif item_type == "premium_fuel":
                        item_id = str(uuid.uuid4())
                        fuel_item = Item(
                            item_id=item_id,
                            serial_number=self.generate_serial_number(),
                            name="⚡ Энергостержни",
                            item_type=ItemType.FUEL,
                            rarity=ItemRarity.EPIC,
                            description="Топливо (300 мин)",
                            buy_price=4000,
                            sell_price=2000,
                            is_tradable=True,
                            owner_id=user_id,
                            fuel_amount=300
                        )
                        self.items[item_id] = fuel_item
                        player.inventory.append(item_id)
                        reward_items.append(fuel_item)
                    elif item_type == "ultra_fuel":
                        item_id = str(uuid.uuid4())
                        fuel_item = Item(
                            item_id=item_id,
                            serial_number=self.generate_serial_number(),
                            name="🚀 Реактор",
                            item_type=ItemType.FUEL,
                            rarity=ItemRarity.LEGENDARY,
                            description="Топливо (600 мин)",
                            buy_price=8000,
                            sell_price=4000,
                            is_tradable=True,
                            owner_id=user_id,
                            fuel_amount=600
                        )
                        self.items[item_id] = fuel_item
                        player.inventory.append(item_id)
                        reward_items.append(fuel_item)
                    elif item_type == "random_tool":
                        rarities = [ItemRarity.RARE, ItemRarity.EPIC, ItemRarity.LEGENDARY, ItemRarity.MYTHIC]
                        weights = [40, 35, 20, 5]
                        rarity = random.choices(rarities, weights=weights)[0]
                        item = self._create_item_by_type(user_id, random.choice([ItemType.LUCK_CHARM, ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE]), rarity)
                        if item:
                            self.items[item.item_id] = item
                            player.inventory.append(item.item_id)
                            reward_items.append(item)
                    elif item_type == "random_collectible":
                        collectible_item = self.create_random_collectible(user_id)
                        if collectible_item:
                            self.items[collectible_item.item_id] = collectible_item
                            player.inventory.append(collectible_item.item_id)
                            reward_items.append(collectible_item)
                reward_text = f"{package['description']}: +{package['gold']}🪙 + {len(reward_items)} предметов"
            
            promo.used_count += 1
            player.add_activated_promocode(code)
            self.promocode_activations.append(PromoCodeActivation(
                user_id=user_id,
                code=code
            ))
            asyncio.create_task(self.batch_save())
            result = {
                "code": code,
                "reward_type": promo.reward_type,
                "reward_value": promo.reward_value,
                "reward_text": reward_text,
                "items": reward_items
            }
            return True, f"✅ Промокод активирован! Получено: {reward_text}", result
        except Exception:
            return False, f"❌ Ошибка", {}

    def get_promocode_info(self, code: str) -> Optional[PromoCode]:
        return self.promocodes.get(code.upper())

    def list_promocodes(self) -> List[PromoCode]:
        return list(self.promocodes.values())

    def play_roulette(self, user_id: int, bet_type: str, amount: int) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            player = self.players.get(user_id)
            if not player or player.is_banned:
                return False, "❌ Игрок не найден или забанен", {}
            if amount < 10:
                return False, "❌ Минимальная ставка: 10 🪙", {}
            if player.gold_balance < amount:
                return False, f"❌ Недостаточно золота. Баланс: {player.gold_balance} 🪙", {}
            if bet_type.lower() in ["red", "красное", "кра", "красный"]:
                bet_type_enum = RouletteBetType.RED
            elif bet_type.lower() in ["black", "черное", "чер", "черный"]:
                bet_type_enum = RouletteBetType.BLACK
            else:
                return False, "❌ Неверный тип ставки. Используйте: красное или черное", {}
            player.gold_balance -= amount
            result = random.randint(1, 6)
            if result in [1, 3, 5]:
                result_color = "red"
                color_name = RouletteBetType.RED.value
            else:
                result_color = "black"
                color_name = RouletteBetType.BLACK.value
            win = (result_color == "red" and bet_type_enum == RouletteBetType.RED) or \
                  (result_color == "black" and bet_type_enum == RouletteBetType.BLACK)
            if win:
                winnings = amount * 2
                player.gold_balance += winnings
                player.stats["roulette_wins"] = player.stats.get("roulette_wins", 0) + 1
                player.stats["roulette_profit"] = player.stats.get("roulette_profit", 0) + amount
                result_text = f"✅ ВЫ ВЫИГРАЛИ! {winnings} 🪙 (чистая прибыль: {amount} 🪙)"
            else:
                player.stats["roulette_losses"] = player.stats.get("roulette_losses", 0) + 1
                player.stats["roulette_profit"] = player.stats.get("roulette_profit", 0) - amount
                result_text = f"❌ ВЫ ПРОИГРАЛИ {amount} 🪙"
            asyncio.create_task(self.batch_save())
            result_data = {
                "success": True,
                "bet": amount,
                "bet_type": bet_type_enum.value,
                "result": result,
                "color": color_name,
                "win": win,
                "winnings": winnings if win else 0,
                "new_balance": player.gold_balance
            }
            message = f"""
🎰 РУЛЕТКА

🎲 Выпало число: {result} ({color_name})
💰 Ваша ставка: {amount} 🪙 на {bet_type_enum.value}

{result_text}

💰 Текущий баланс: {player.gold_balance} 🪙
"""
            return True, message, result_data
        except Exception:
            return False, f"❌ Ошибка", {}

class KeyboardManager:
    _cache = Cache(ttl=300, max_size=1000)
    _menu_cache = {}
    
    @staticmethod
    def get_rarity_emoji(rarity: ItemRarity) -> str:
        emoji_map = {
            ItemRarity.COMMON: "⚪",
            ItemRarity.RARE: "🔵",
            ItemRarity.EPIC: "🟣",
            ItemRarity.LEGENDARY: "🟡",
            ItemRarity.MYTHIC: "🔴",
            ItemRarity.LIMITED: "👑"
        }
        return emoji_map.get(rarity, "⚪")

    @staticmethod
    async def main_menu() -> InlineKeyboardMarkup:
        cache_key = "main_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="⛏️ Добыча", callback_data="mining_menu")
        builder.button(text="👤 Профиль", callback_data="profile_menu")
        builder.button(text="⚡ Улучшения", callback_data="upgrades")
        builder.button(text="🎒 Инвентарь", callback_data="inventory")
        builder.button(text="🪙 Золото", callback_data="gold")
        builder.button(text="📦 Ящики", callback_data="cases")
        builder.button(text="🤖 Авто", callback_data="auto_mining")
        builder.button(text="🏆 Коллекции", callback_data="collections")
        builder.button(text="🏪 Рынок", callback_data="market")
        builder.button(text="🛒 Магазин", callback_data="shop")
        builder.button(text="🏆 Топ", callback_data="top_players")
        builder.button(text="⭐ Донаты", callback_data="donate")
        builder.button(text="❓ Помощь", callback_data="help")
        builder.adjust(2)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def profile_menu(player: Player) -> InlineKeyboardMarkup:
        cache_key = f"profile_menu_{player.user_id}"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="👤 Инфо", callback_data="profile_info")
        builder.button(text="📊 Статистика", callback_data="profile_stats")
        builder.button(text="✏️ Изм. имя", callback_data="change_name")
        builder.button(text="🔔 Уведомл.", callback_data="notification_settings")
        builder.button(text="🔄 Перерождение", callback_data="reset_level_menu")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def notification_settings(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        all_status = "✅" if player.notifications_enabled else "❌"
        market_status = "✅" if player.market_notifications else "❌"
        mining_status = "✅" if player.mining_notifications else "❌"
        daily_status = "✅" if player.daily_notifications else "❌"
        builder.button(text=f"🔔 Все: {all_status}", callback_data="toggle_notif_all")
        builder.button(text=f"🏪 Рынок: {market_status}", callback_data="toggle_notif_market")
        builder.button(text=f"⛏️ Добыча: {mining_status}", callback_data="toggle_notif_mining")
        builder.button(text=f"🎁 Daily: {daily_status}", callback_data="toggle_notif_daily")
        builder.button(text="⬅️ Назад", callback_data="profile_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def reset_level_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Подтвердить перерождение", callback_data="reset_level")
        builder.button(text="❌ Отмена", callback_data="profile_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def mining_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        hits = player.get_current_pickaxe_hits()
        material = player.current_pickaxe_material.value
        upgrade = player.current_pickaxe_upgrade
        builder.button(text=f"🔨 {material} +{upgrade} ({hits}уд)", callback_data="pickaxe_info")
        visible_minerals = player.get_visible_minerals_for_mining()
        minerals_shown = 0
        for mineral_name in visible_minerals:
            if minerals_shown >= 8:
                break
            for mineral in MineralType:
                if mineral.name == mineral_name:
                    builder.button(text=mineral.value[:10], callback_data=f"start_mine_{mineral_name}")
                    minerals_shown += 1
                    break
        builder.button(text="📊 Статус", callback_data="mining_status")
        builder.button(text="🤖 Статус авто", callback_data="auto_mining_status")
        builder.button(text="💰 Мои минералы", callback_data="my_minerals")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    async def pickaxe_info(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        hits = player.get_current_pickaxe_hits()
        bonus = player.get_current_pickaxe_bonus()
        luck = player.get_current_pickaxe_luck()
        material = player.current_pickaxe_material.value
        upgrade = player.current_pickaxe_upgrade
        base_cost = 200
        material_index = list(PickaxeMaterial).index(player.current_pickaxe_material)
        cost = int(base_cost * (1.2 ** (upgrade + material_index * 3)))
        if player.current_pickaxe_upgrade < 4:
            builder.button(text=f"🔨 Прокачать кирку ({cost} 🪙)", callback_data="upgrade_pickaxe")
        else:
            next_material = list(PickaxeMaterial)[list(PickaxeMaterial).index(player.current_pickaxe_material) + 1] if list(PickaxeMaterial).index(player.current_pickaxe_material) < len(PickaxeMaterial)-1 else None
            if next_material:
                builder.button(text=f"🔨 Улучшить до {next_material.value} ({cost} 🪙)", callback_data="upgrade_pickaxe")
        builder.button(text="⬅️ Назад", callback_data="mining_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def auto_mining_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        status = "✅ ВКЛ" if player.auto_mining_enabled else "❌ ВЫКЛ"
        can_use = player.can_use_auto_mining()
        status_text = f"🤖 Вкл/Выкл ({status})"
        if not can_use:
            status_text = "🤖 Требуется улучшение"
        builder.button(text=status_text, callback_data="toggle_auto_mining")
        if not player.auto_mining_enabled:
            builder.button(text="⛽ Топливо", callback_data="buy_fuel_menu")
        else:
            builder.button(text="⛽ Статус топлива", callback_data="fuel_status")
        builder.button(text="📊 Инфо", callback_data="auto_mining_info")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def buy_fuel_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        has_fuel = False
        for item_id in player.inventory[:10]:
            if data_manager:
                item = data_manager.get_item(item_id)
                if item and item.item_type == ItemType.FUEL:
                    has_fuel = True
                    fuel_type = "basic" if item.fuel_amount == 60 else "advanced" if item.fuel_amount == 180 else "premium" if item.fuel_amount == 300 else "ultra" if item.fuel_amount == 600 else "nuclear"
                    builder.button(text=f"{item.name} ({item.fuel_amount} мин)", callback_data=f"use_fuel_{fuel_type}")
        if not has_fuel:
            builder.button(text="🛒 Купить в магазине", callback_data="shop_fuel")
        builder.button(text="⬅️ Назад", callback_data="auto_mining")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def shop_menu() -> InlineKeyboardMarkup:
        cache_key = "shop_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="⛽ Топливо", callback_data="shop_fuel")
        builder.button(text="📦 Ящики", callback_data="cases")
        builder.button(text="⚡ Улучшения", callback_data="upgrades")
        builder.button(text="⭐ Донаты", callback_data="donate")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def shop_fuel_menu() -> InlineKeyboardMarkup:
        cache_key = "shop_fuel_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        fuels = [
            ("⛽ Угольные 60мин", 800, "shop_buy_fuel_basic"),
            ("🔥 Нефтяное 180мин", 2000, "shop_buy_fuel_advanced"),
            ("⚡ Энерго 300мин", 4000, "shop_buy_fuel_premium"),
            ("🚀 Реактор 600мин", 8000, "shop_buy_fuel_ultra"),
            ("☢️ Ядерное 1200мин", 20000, "shop_buy_fuel_nuclear")
        ]
        for name, price, callback in fuels:
            builder.button(text=f"{name} - {price}🪙", callback_data=callback)
        builder.button(text="⬅️ Назад", callback_data="shop")
        builder.adjust(1)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def collections_menu(collectibles_stats: Dict[str, Any]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        total = collectibles_stats.get("total", 0)
        unique = collectibles_stats.get("unique_types", 0)
        percentage = collectibles_stats.get("completion_percentage", 0)
        builder.button(text=f"📊 {total} шт. / {unique}/24", callback_data="collections_stats")
        builder.button(text=f"📈 {percentage:.1f}%", callback_data="collections_progress")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def gold_menu(player_gold: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=f"💰 Баланс: {player_gold}🪙", callback_data="gold_balance")
        builder.button(text="💱 Продать ВСЕ", callback_data="convert_all_minerals")
        builder.button(text="⚡ Улучшения", callback_data="upgrades")
        builder.button(text="⭐ Купить золото", callback_data="donate")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def upgrades_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        upgrades = [
            ("mining_power", "💪 Кол-во ударов", player.mining_power_level, 100, 1.3),
            ("mining_time", "⏱️ Длительность (+10 мин)", player.mining_time_level, 90, 1.3),
            ("mineral_multiplier", "⛏️ Множитель минералов", player.mineral_multiplier_level, 250, 1.3),
            ("mineral_unlock", "🪨 Рудная жила", player.mineral_unlock_level, 2000, 2.0),
            ("premium_chance", "💎 Шанс Premium Coin", player.premium_chance_level, 150, 1.3),
            ("case_chance", "📦 Шанс ящиков", player.case_chance_level, 60, 1.3),
            ("collectible_chance", "🏆 Шанс коллекций", player.collectible_chance_level, 150, 1.3),
            ("auto_mining", "🤖 Автодобыча", player.auto_mining_level, 10000, 1.5),
        ]
        for upgrade_id, name, level, base_price, mult in upgrades:
            if level < MAX_LEVEL:
                cost = int(base_price * (mult ** level))
                if upgrade_id == "mineral_unlock":
                    unlocked = MINERAL_UNLOCK_LEVELS.get(level + 1, [])
                    if unlocked:
                        mineral_names = []
                        for m in unlocked:
                            if m in MineralType.__members__:
                                mineral_names.append(MineralType[m].value)
                        extra_info = f" ({', '.join(mineral_names[:1])})"
                    else:
                        extra_info = ""
                    builder.button(text=f"{name} {level}ур - {cost}🪙{extra_info}", callback_data=f"buy_upgrade_{upgrade_id}")
                else:
                    builder.button(text=f"{name} {level}ур - {cost}🪙", callback_data=f"buy_upgrade_{upgrade_id}")
            else:
                builder.button(text=f"{name} {level}ур (MAX)", callback_data="none")
        builder.button(text=f"💰 {player.gold_balance}🪙", callback_data="gold_balance")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def cases_menu(cases: Dict[str, Case], player_gold: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📦 Обычный ящик - 400🪙", callback_data="buy_case_COMMON")
        builder.button(text="🎁 Редкий ящик - 1500🪙", callback_data="buy_case_RARE")
        builder.button(text="💎 Эпический ящик - 8000🪙", callback_data="buy_case_EPIC")
        builder.button(text="👑 Легендарный ящик - 40000🪙", callback_data="buy_case_LEGENDARY")
        builder.button(text="✨ Мифический ящик - 80000🪙", callback_data="buy_case_MYTHIC")
        builder.button(text="🎁 Открыть ящики из инвентаря", callback_data="open_cases")
        builder.button(text=f"💰 {player_gold}🪙", callback_data="gold_balance")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def inventory_menu(player: Player, items: Dict[str, Item], page: int = 0) -> InlineKeyboardMarkup:
        items_per_page = 8
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        builder = InlineKeyboardBuilder()
        page_items = player.inventory[start_idx:end_idx]
        for item_id in page_items:
            item = items.get(item_id)
            if item:
                emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                market_indicator = " 📌" if player.is_item_on_market(item_id) else ""
                case_indicator = " 📦" if item.item_type == ItemType.CASE else ""
                builder.button(text=f"{emoji} {item.name[:15]}{market_indicator}{case_indicator}", callback_data=f"item_{item_id}")
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"inv_page_{page-1}"))
        if end_idx < len(player.inventory):
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"inv_page_{page+1}"))
        if nav_buttons:
            builder.row(*nav_buttons)
        builder.row(
            InlineKeyboardButton(text="🛡️ Экипировка", callback_data="equipment"),
            InlineKeyboardButton(text="💰 Продать", callback_data="sell_menu")
        )
        builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def sell_menu() -> InlineKeyboardMarkup:
        cache_key = "sell_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="⚪ Обычные", callback_data="sell_rarity_COMMON")
        builder.button(text="🔵 Редкие", callback_data="sell_rarity_RARE")
        builder.button(text="🟣 Эпические", callback_data="sell_rarity_EPIC")
        builder.button(text="🟡 Легендарные", callback_data="sell_rarity_LEGENDARY")
        builder.button(text="🔴 Мифические", callback_data="sell_rarity_MYTHIC")
        builder.button(text="👑 Лимитированные", callback_data="sell_rarity_LIMITED")
        builder.button(text="⬅️ Назад", callback_data="inventory")
        builder.adjust(1)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def item_menu(item: Item, is_equipped: bool = False, is_on_market: bool = False) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if item.item_type == ItemType.CASE:
            builder.button(text="🎁 Открыть", callback_data=f"open_{item.item_id}")
        elif item.item_type == ItemType.FUEL:
            builder.button(text="⛽ Использовать", callback_data=f"use_fuel_item_{item.item_id}")
        elif not is_equipped and item.item_type in [ItemType.MINING_TOOL, ItemType.LUCK_CHARM,
                                                   ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE, ItemType.LIMITED]:
            builder.button(text="🛡️ Надеть", callback_data=f"equip_{item.item_id}")
        elif is_equipped:
            builder.button(text="📦 Снять", callback_data=f"unequip_{item.item_id}")
        builder.button(text="💰 Продать", callback_data=f"sell_{item.item_id}")
        if item.is_tradable and (item.is_collectible or item.rarity == ItemRarity.LIMITED) and not is_on_market:
            builder.button(text="🏪 На рынок", callback_data=f"market_sell_{item.item_id}")
        elif is_on_market:
            builder.button(text="📌 На рынке", callback_data="none")
        builder.button(text="⬅️ Назад", callback_data="inventory")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    async def equipment_menu(equipped_items: Dict[str, str], items: Dict[str, Item]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        slot_names = {"tool": "⛏️ Инструм.", "charm": "🍀 Талисман", "chip": "💿 Чип", "core": "🔋 Ядро"}
        for slot, slot_name in slot_names.items():
            item_id = equipped_items.get(slot)
            if item_id:
                item = items.get(item_id)
                if item:
                    emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                    builder.button(text=f"{slot_name}: {emoji} {item.name[:8]}", callback_data=f"unequip_{slot}")
            else:
                builder.button(text=f"{slot_name}: Пусто", callback_data="none")
        builder.button(text="📊 Бонусы", callback_data="equipment_bonuses")
        builder.button(text="⬅️ Назад", callback_data="inventory")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def market_menu(market_offers: Dict[str, MarketOffer], items: Dict[str, Item], page: int = 0) -> InlineKeyboardMarkup:
        offers_list = list(market_offers.values())[:MAX_MARKET_OFFERS_DISPLAY]
        items_per_page = 5
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        builder = InlineKeyboardBuilder()
        for i in range(start_idx, min(end_idx, len(offers_list))):
            offer = offers_list[i]
            item = items.get(offer.item_id)
            if item:
                emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                builder.button(text=f"{emoji} {item.name[:10]} - {offer.price}🪙", callback_data=f"buy_offer_{offer.offer_id}")
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"market_page_{page-1}"))
        if end_idx < len(offers_list):
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"market_page_{page+1}"))
        if nav_buttons:
            builder.row(*nav_buttons)
        builder.row(
            InlineKeyboardButton(text="📤 Мои предл.", callback_data="my_offers"),
            InlineKeyboardButton(text="➕ Выставить", callback_data="create_offer")
        )
        builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def top_menu() -> InlineKeyboardMarkup:
        cache_key = "top_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="💰 По золоту", callback_data="top_gold")
        builder.button(text="🏆 По уровню", callback_data="top_level")
        builder.button(text="🏺 По коллекциям", callback_data="top_collectibles")
        builder.button(text="🔄 По перерождению", callback_data="top_reincarnation")
        builder.button(text="🎰 По рулетке", callback_data="top_roulette")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def channels_menu(channels: Dict[str, Channel]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for channel_id, channel in channels.items():
            bot_status = "✅" if channel.bot_member else "⚠️"
            builder.button(text=f"{bot_status} {channel.name[:10]}", callback_data=f"channel_{channel_id}")
        builder.button(text="✅ Проверить", callback_data="check_subscriptions")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def admin_menu() -> InlineKeyboardMarkup:
        cache_key = "admin_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Статистика", callback_data="admin_stats")
        builder.button(text="👤 Упр. игроками", callback_data="admin_players")
        builder.button(text="🔍 Найти игрока", callback_data="admin_find_player")
        builder.button(text="📋 Все предметы", callback_data="admin_all_items")
        builder.button(text="🪨 Все минералы", callback_data="admin_all_minerals")
        builder.button(text="➕ Добавить канал", callback_data="admin_add_channel")
        builder.button(text="➖ Удалить канал", callback_data="admin_remove_channel")
        builder.button(text="🔧 Проверить каналы", callback_data="admin_check_channels")
        builder.button(text="🎁 Выдать золото (±)", callback_data="admin_adjust_gold")
        builder.button(text="🎁 Выдать предмет", callback_data="admin_give_item")
        builder.button(text="📈 Уст. уровень", callback_data="admin_set_level")
        builder.button(text="💰 Уст. золото", callback_data="admin_set_gold")
        builder.button(text="💱 Уст. минералы", callback_data="admin_set_balance")
        builder.button(text="🔄 Сброс игрока", callback_data="admin_reset_player")
        builder.button(text="🚫 Бан игрока", callback_data="admin_ban_player")
        builder.button(text="✅ Разбан", callback_data="admin_unban_player")
        builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
        builder.button(text="💾 Создать бекап", callback_data="admin_backup")
        builder.button(text="⭐ Стат. донатов", callback_data="admin_donate_stats")
        builder.button(text="👑 Настр. рубина", callback_data="admin_ruby_settings")
        builder.button(text="🎁 Управление промокодами", callback_data="admin_promocodes")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def admin_ruby_settings() -> InlineKeyboardMarkup:
        cache_key = "admin_ruby_settings"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="👑 Уст. цену", callback_data="admin_set_ruby_price")
        builder.button(text="👑 Уст. лимит", callback_data="admin_set_ruby_limit")
        builder.button(text="👑 Уст. кол-во", callback_data="admin_set_ruby_count")
        builder.button(text="👑 Инфо", callback_data="admin_ruby_info")
        builder.button(text="⬅️ Назад", callback_data="admin")
        builder.adjust(1)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def admin_promocodes_menu() -> InlineKeyboardMarkup:
        cache_key = "admin_promocodes_menu"
        if cache_key in KeyboardManager._menu_cache:
            return KeyboardManager._menu_cache[cache_key]
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            KeyboardManager._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Список промокодов", callback_data="admin_list_promocodes")
        builder.button(text="➕ Создать промокод", callback_data="admin_create_promocode")
        builder.button(text="❌ Удалить промокод", callback_data="admin_delete_promocode")
        builder.button(text="📊 Статистика", callback_data="admin_promocode_stats")
        builder.button(text="⬅️ Назад", callback_data="admin")
        builder.adjust(1)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        KeyboardManager._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def back_button(target: str) -> InlineKeyboardMarkup:
        cache_key = f"back_button_{target}"
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=target)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        return result

    @staticmethod
    async def cancel_button(target: str) -> InlineKeyboardMarkup:
        cache_key = f"cancel_button_{target}"
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Отмена", callback_data=target)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        return result

    @staticmethod
    async def admin_back_button() -> InlineKeyboardMarkup:
        cache_key = "admin_back_button"
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад в админку", callback_data="admin")
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        return result

    @staticmethod
    async def transfer_menu() -> InlineKeyboardMarkup:
        cache_key = "transfer_menu"
        cached = await KeyboardManager._cache.get(cache_key)
        if cached:
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="💰 Перевести", callback_data="transfer_gold")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        result = builder.as_markup()
        await KeyboardManager._cache.set(cache_key, result)
        return result

class DonateKeyboards:
    _cache = Cache(ttl=300, max_size=500)
    _menu_cache = {}

    @staticmethod
    async def donate_menu(ruby_price: int, ruby_left: int) -> InlineKeyboardMarkup:
        cache_key = f"donate_menu_{ruby_price}_{ruby_left}"
        if cache_key in DonateKeyboards._menu_cache:
            return DonateKeyboards._menu_cache[cache_key]
        cached = await DonateKeyboards._cache.get(cache_key)
        if cached:
            DonateKeyboards._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="1 ⭐ - 80 🪙", callback_data="donate_1")
        builder.button(text="5 ⭐ - 400 🪙", callback_data="donate_5")
        builder.button(text="10 ⭐ - 850 🪙", callback_data="donate_10")
        builder.button(text="20 ⭐ - 1800 🪙", callback_data="donate_20")
        builder.button(text="50 ⭐ - 4500 🪙", callback_data="donate_50")
        ruby_text = f"{ruby_price} ⭐ - 6800 🪙 (осталось {ruby_left})"
        builder.button(text=ruby_text, callback_data=f"donate_{ruby_price}")
        builder.button(text="100 ⭐ - 9000 🪙", callback_data="donate_100")
        builder.button(text="🎁 Спецнаборы", callback_data="donate_special")
        builder.button(text="🎁 Промокоды", callback_data="promocode_info")
        builder.button(text="ℹ️ Поддержка", callback_data="donate_help")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        result = builder.as_markup()
        await DonateKeyboards._cache.set(cache_key, result)
        DonateKeyboards._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def special_donates() -> InlineKeyboardMarkup:
        cache_key = "special_donates"
        if cache_key in DonateKeyboards._menu_cache:
            return DonateKeyboards._menu_cache[cache_key]
        cached = await DonateKeyboards._cache.get(cache_key)
        if cached:
            DonateKeyboards._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="🪨 Стартовый (50 ⭐)", callback_data="donate_starter")
        builder.button(text="⚡ Промышленный (100 ⭐)", callback_data="donate_business")
        builder.button(text="👑 Магнатский (200 ⭐)", callback_data="donate_premium")
        builder.button(text="🤖 Автодобыча (50 ⭐)", callback_data="donate_auto")
        builder.button(text="🏺 Коллекционный (100 ⭐)", callback_data="donate_collection")
        builder.button(text="⬅️ Назад", callback_data="donate")
        builder.adjust(1)
        result = builder.as_markup()
        await DonateKeyboards._cache.set(cache_key, result)
        DonateKeyboards._menu_cache[cache_key] = result
        return result

    @staticmethod
    async def confirm_donation(stars: int, gold: int, player: Optional[Player] = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        discount_text = ""
        if player:
            discount = player.get_discount("donate_bonus")
            if discount > 0:
                discounted_stars = max(1, int(stars * (100 - discount) / 100))
                discount_text = f" (скидка {discount}%: {discounted_stars} ⭐)"
        builder.button(text=f"⭐ Оплатить {stars} звёзд{discount_text}", callback_data=f"confirm_donate_{stars}")
        builder.button(text="❌ Отмена", callback_data="donate")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def payment_keyboard(stars: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=f"⭐ Оплатить {stars} ⭐", pay=True)
        builder.button(text="❌ Отмена", callback_data="donate")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def donate_thank_you() -> InlineKeyboardMarkup:
        cache_key = "donate_thank_you"
        if cache_key in DonateKeyboards._menu_cache:
            return DonateKeyboards._menu_cache[cache_key]
        cached = await DonateKeyboards._cache.get(cache_key)
        if cached:
            DonateKeyboards._menu_cache[cache_key] = cached
            return cached
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Главное меню", callback_data="back_to_main")
        builder.button(text="🎁 Промокоды", callback_data="promocode_info")
        builder.adjust(1)
        result = builder.as_markup()
        await DonateKeyboards._cache.set(cache_key, result)
        DonateKeyboards._menu_cache[cache_key] = result
        return result

class TextTemplates:
    @staticmethod
    def welcome(first_name: str) -> str:
        return f"""
⛏️ Добро пожаловать в {GAME_NAME}, {first_name}!

🪨 Вы - старатель, добывающий редкие минералы.
💰 Добывайте 50+ видов ископаемых, продавайте за золото.
⚡ Покупайте улучшения.
🔨 Базовая кирка есть всегда. Прокачивайте её!
💎 Есть шанс получить {PREMIUM_COIN_NAME} при каждом ударе!
🤖 Для автодобычи нужно прокачать улучшение "Автодобыча" до 1 уровня!
🔄 На 500 уровне можно переродиться для множителя дохода.
🎰 Новая игра: /rul красное 100 - ставка на красное
🎁 Используйте промокоды: /promocode

🚀 Начните с /mine или используйте кнопки ниже!
"""

    @staticmethod
    def profile(player: Player) -> str:
        total_mineral = player.get_total_mineral_value()
        mining_status = "🟢 Готов"
        if player.auto_mining_enabled:
            mining_status = "🤖 Авто"
        elif player.user_id in data_manager.active_mining_sessions if data_manager else False:
            mining_status = "⛏️ В процессе"
        collectibles_stats = {
            "total": sum(player.collectibles.values()),
            "unique_types": sum(1 for count in player.collectibles.values() if count > 0),
        }
        hits = player.get_current_pickaxe_hits()
        material = player.current_pickaxe_material.value
        upgrade = player.current_pickaxe_upgrade
        required_item = player.get_required_reset_item()
        unlocked_minerals_count = len(player.unlocked_minerals)
        total_minerals = len(MineralType)
        minerals_progress = f"{unlocked_minerals_count}/{total_minerals}"
        roulette_stats = f"🎰 Выигрышей: {player.stats.get('roulette_wins', 0)} | Проигрышей: {player.stats.get('roulette_losses', 0)} | Прибыль: {player.stats.get('roulette_profit', 0)} 🪙"
        discounts_text = ""
        ruby_discount = player.get_discount("ruby_discount")
        donate_discount = player.get_discount("donate_bonus")
        if ruby_discount > 0:
            discounts_text += f"🎁 Скидка на рубин: {ruby_discount}%\n"
        if donate_discount > 0:
            discounts_text += f"🎁 Скидка на донат: {donate_discount}%\n"
        market_items = len(player.market_offers) if hasattr(player, 'market_offers') else 0
        return f"""
👤 Профиль: {player.custom_name}
🆔 ID: {player.player_id_str} | #{player.player_number}

🏆 Ур. {player.miner_level}/{MAX_LEVEL} | ⭐ Опыт: {player.experience}/{player.miner_level*100}
💰 Золота: {player.gold_balance} 🪙
💎 {PREMIUM_COIN_NAME}: {player.premium_coin_balance}
🔄 Перерождений: {player.reincarnation_level} (x{player.reincarnation_multiplier:.1f} доход)
🎒 Предметов: {len(player.inventory)} | 🏆 Коллекц.: {collectibles_stats['total']}
🏪 На рынке: {market_items}
⛽ Топливо: {player.fuel} мин.
⛏️ Статус: {mining_status}

🔨 Кирка: {material} +{upgrade} ({hits} ударов)
💪 Кол-во ударов: +{player.mining_power_level}%
⛏️ Множитель минералов: +{player.mineral_multiplier_level * 2}%
🪨 Рудная жила: Ур.{player.mineral_unlock_level} (мин.{minerals_progress})
💎 Шанс Premium Coin: +{player.premium_chance_level * 0.1:.1f}%
🤖 Автодобыча: Ур.{player.auto_mining_level} (+{player.get_auto_mining_effect()*100-100:.0f}%)

{roulette_stats}

{discounts_text}
📅 С: {player.created_at.strftime('%d.%m.%Y')}
🔄 Требуется для перерождения: {required_item}
"""

    @staticmethod
    def profile_stats(player: Player) -> str:
        total_mined_value = player.get_total_mineral_value()
        return f"""
📊 Статистика {player.custom_name}

⛏️ Добыча:
• Всего: {player.total_mined:.2f} кг
• Стоимость: {total_mined_value:.2f} 🪙
• Добыч: {player.stats.get('minerals_mined', 0)}
• Автодобыч: {player.stats.get('auto_mines', 0)}
• Ударов: {player.stats.get('hits_done', 0)}

💰 Золото:
• Заработано: {player.total_gold_earned} 🪙
• Баланс: {player.gold_balance} 🪙

💎 Premium Coin:
• Всего: {player.total_premium_earned}
• В наличии: {player.premium_coin_balance}
• Найдено: {player.stats.get('premium_coins_found', 0)}

📦 Ящики:
• Открыто: {player.stats.get('cases_opened', 0)}
• Предметов найдено: {player.stats.get('items_found', 0)}
• Коллекц.: {player.stats.get('collectibles_found', 0)}
• Улучшений куплено: {player.stats.get('upgrades_bought', 0)}

🏪 Рынок:
• Сделок: {player.stats.get('trades_completed', 0)}
🔥 Streak: {player.stats.get('daily_streak', 0)} дней
🔄 Перерождений: {player.stats.get('times_reset', 0)}
🎰 Рулетка:
  • Выигрышей: {player.stats.get('roulette_wins', 0)}
  • Проигрышей: {player.stats.get('roulette_losses', 0)}
  • Прибыль: {player.stats.get('roulette_profit', 0)} 🪙
⏱️ В игре: {player.stats.get('total_play_time', 0) // 60} мин
"""

    @staticmethod
    def mining_status(session: MiningSession) -> str:
        time_left = max(0, (session.end_time - datetime.now()).seconds)
        total_time = (session.end_time - session.start_time).seconds
        progress = 100 - (time_left / total_time * 100) if total_time > 0 else 100
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        minutes = time_left // 60
        seconds = time_left % 60
        next_hit = ""
        if session.next_hit_time:
            hit_time_left = max(0, (session.next_hit_time - datetime.now()).seconds)
            if hit_time_left > 0:
                next_hit = f"⏳ След. удар через: {hit_time_left}с"
            else:
                next_hit = "⚡ Удар сейчас!"
        mineral_per_hit = session.base_reward_per_hit * session.mineral_multiplier
        return f"""
⛏️ Добыча {session.mineral.value}

🔨 Кирка: {session.pickaxe_material.value}
{progress_bar} {progress:.0f}%
⏳ Осталось: {minutes}м {seconds}с
🔄 Ударов: {session.hits_done}/{session.total_hits}
⛏️ За удар: {mineral_per_hit:.2f} кг
{next_hit}
💡 Золото начисляется только при продаже минералов!
"""

    @staticmethod
    def auto_mining_status(player: Player, auto_session: Optional[AutoMiningSession] = None) -> str:
        if not player.auto_mining_enabled:
            return f"""
🤖 Автодобыча ВЫКЛ
⛽ Топливо: {player.fuel} мин.
💡 Требуется улучшение автодобычи до 1 уровня (10000 🪙).
Уровень автодобычи: {player.auto_mining_level}
Эффективность: +{player.get_auto_mining_effect()*100-100:.0f}%
"""
        if not auto_session:
            return "🤖 Нет данных о сессии"
        time_until_next = "Сейчас"
        if auto_session.next_mine_time and datetime.now() < auto_session.next_mine_time:
            time_left = (auto_session.next_mine_time - datetime.now()).seconds
            minutes = time_left // 60
            seconds = time_left % 60
            time_until_next = f"{minutes}м {seconds}с"
        return f"""
🤖 Автодобыча ВКЛ
⏱️ След. запуск: {time_until_next}
⛽ Топлива: {auto_session.fuel_left} мин.
💰 Добыч авто: {player.stats.get('auto_mines', 0)}
⚡ Эффективность: +{player.get_auto_mining_effect()*100-100:.0f}%
💡 Золото начисляется только при продаже минералов!
"""

    @staticmethod
    def auto_mining_info() -> str:
        return f"""
🤖 Информация об автодобыче

📋 Как работает:
• Требуется улучшение "Автодобыча" >=1 уровня (10000 🪙).
• Работает постоянно (каждые 5 мин), пока есть топливо.
• Эффективность зависит от уровня улучшения.
• Приносит в 5 раз меньше, чем ручная добыча.
• Топливо тратится по 5 минут за цикл.

⛽ Типы топлива:
• Угольные брикеты: 60 мин (800 🪙)
• Нефтяное топливо: 180 мин (2000 🪙)
• Энергостержни: 300 мин (4000 🪙)
• Реактор: 600 мин (8000 🪙)
• Ядерное: 1200 мин (20000 🪙)
"""

    @staticmethod
    def auto_mining_result(result: Dict[str, Any]) -> str:
        text = "🤖 Автодобыча:\n\n"
        for res in result.get('results', []):
            premium_text = f" + {res.get('premium', 0)}💎" if res.get('premium', 0) > 0 else ""
            text += f"• {res['mineral'].value}: {res['amount']:.2f} кг{premium_text}\n"
        if result.get('total_premium', 0) > 0:
            text += f"\n💎 Premium Coin: +{result['total_premium']}\n"
        text += f"\n💰 Всего минералов: {result.get('total_mineral', 0):.2f} кг"
        text += f"\n⛽ Осталось: {result.get('fuel_left', 0)} мин."
        text += f"\n💡 Продайте минералы в меню Золото!"
        return text

    @staticmethod
    def mining_result(result: Dict[str, Any]) -> str:
        text = f"""
🎉 Добыча завершена!

💰 Добыто: {result['mineral_reward']:.2f} кг {result['mineral'].value}
💎 Premium Coin: +{result.get('premium_earned', 0)}
⭐ Опыта: {result['experience']}
💡 Продайте минералы в меню Золото!
"""
        if result.get('items'):
            text += "\n🎁 Предметы:\n"
            for item in result['items']:
                emoji = "🏆" if item.is_collectible else KeyboardManager.get_rarity_emoji(item.rarity)
                text += f"  {emoji} {item.name}\n"
        if result.get('cases'):
            text += "\n📦 Ящики:\n"
            for case in result['cases']:
                text += f"  • {case.name}\n"
        return text

    @staticmethod
    def gold_balance(player: Player) -> str:
        total_mineral = player.get_total_mineral_value()
        return f"""
🪙 Золотые слитки

💰 Баланс: {player.gold_balance} 🪙
💎 Premium Coin: {player.premium_coin_balance}
📊 Всего заработано: {player.total_gold_earned} 🪙
💱 Стоимость минералов: {total_mineral:.2f} 🪙 экв.

💡 Золото можно получить:
• Продавая минералы
• Продавая предметы
• За подписку на каналы
• Ежедневный бонус
• Выигрыш в рулетке /rul
"""

    @staticmethod
    def case_info(case: Case) -> str:
        drop_info = ""
        for rarity, chance in case.drop_chances.items():
            drop_info += f"  {rarity.value}: {chance*100:.1f}%\n"
        return f"""
{case.name}

📝 {case.description}
💰 {case.price} 🪙
🎁 Предметов: {case.min_items}-{case.max_items}
{drop_info}
🏆 Шанс коллекц.: {case.collectible_chance*100:.2f}%
"""

    @staticmethod
    def item_info(item: Item) -> str:
        text = f"""
{KeyboardManager.get_rarity_emoji(item.rarity)} {item.name}
🌟 {item.rarity.value}
🔢 Сер.№ {item.serial_number}
📝 {item.description}
"""
        if item.is_collectible and item.collectible_type:
            text += f"🏆 Тип: {item.collectible_type.value}\n"
        elif item.item_type == ItemType.FUEL:
            text += f"⛽ {item.fuel_amount} мин\n"
        elif item.item_type == ItemType.MINING_TOOL:
            text += f"🔨 Уровень: {item.pickaxe_level}\n"
            text += f"🔄 Ударов: {item.base_hits}\n"
            text += f"⚡ Добыча: +{(item.mining_bonus-1)*100:.1f}%\n"
            if item.luck_bonus > 0:
                text += f"🍀 Шанс {PREMIUM_COIN_NAME}: +{item.luck_bonus*100:.1f}%\n"
        else:
            if item.mining_bonus > 1.0:
                text += f"⚡ Добыча: +{(item.mining_bonus-1)*100:.1f}%\n"
            if item.luck_bonus > 0:
                text += f"🍀 Шанс {PREMIUM_COIN_NAME}: +{item.luck_bonus*100:.1f}%\n"
        if item.buy_price > 0:
            text += f"💰 Цена: {item.buy_price} 🪙\n💵 Продажа: {item.sell_price} 🪙\n"
        return text

    @staticmethod
    def collections_stats(collectibles_stats: Dict[str, Any]) -> str:
        total = collectibles_stats.get("total", 0)
        unique = collectibles_stats.get("unique_types", 0)
        percentage = collectibles_stats.get("completion_percentage", 0)
        by_type = collectibles_stats.get("by_type", {})
        text = f"""
🏆 Коллекции

📊 Всего: {total} шт. | Уникальных: {unique}/24
📈 Завершено: {percentage:.1f}%

📈 По типам:
"""
        for collectible_type in CollectibleType:
            count = by_type.get(collectible_type.name, 0)
            progress = "✅" if count >= 3 else "🟡" if count > 0 else "❌"
            text += f"  {progress} {collectible_type.value}: {count}/3\n"
        return text

    @staticmethod
    def market_info() -> str:
        return """
🏪 Рынок

📋 Продавать можно только:
• 🏆 Коллекционные сувениры
• 👑 Лимитированные предметы

💡 Покупайте редкие предметы у других!
"""

    @staticmethod
    def top_players(top_type: str, top_list: List[Tuple]) -> str:
        if top_type == "gold":
            title = "💰 Топ по золоту"
            items = [f"{i+1}. {name} - {value} 🪙 (Ур.{level})" for i, (name, value, level) in enumerate(top_list)]
        elif top_type == "level":
            title = "🏆 Топ по уровню"
            items = [f"{i+1}. {name} - Ур.{level} ({value} 🪙)" for i, (name, level, value) in enumerate(top_list)]
        elif top_type == "collectibles":
            title = "🏺 Топ по коллекциям"
            items = [f"{i+1}. {name} - {value} шт. (Ур.{level})" for i, (name, value, level) in enumerate(top_list)]
        elif top_type == "reincarnation":
            title = "🔄 Топ по перерождениям"
            items = [f"{i+1}. {name} - {value} ур. (Ур.{level})" for i, (name, value, level) in enumerate(top_list)]
        elif top_type == "roulette":
            title = "🎰 Топ по рулетке"
            items = [f"{i+1}. {name} - {value} 🪙 прибыли (Ур.{level})" for i, (name, value, level) in enumerate(top_list)]
        else:
            return "❌ Неизвестный тип"
        return f"{title}\n\n" + "\n".join(items)

    @staticmethod
    def system_stats(stats: Dict[str, Any]) -> str:
        return f"""
📊 Активность игры v{VERSION}

👥 Всего игроков: {stats['total_players']}
🎮 Активных сегодня: {stats['active_today']}
⚡ Онлайн сейчас: {stats['active_now']}
🤖 Автодобыча: {stats['online_auto']}
🚫 Забанено: {stats['banned']}

💰 Золота в системе: {stats['total_gold']} 🪙
💎 Premium Coin: {stats['total_premium']}
⛏️ Всего добыто: {stats['total_mined']:.2f} кг
🔄 Перерождений: {stats['reincarnations']}
🎁 Промокодов активировано: {stats.get('promocodes_activated', 0)}
🎰 Ставок в рулетке: {stats.get('roulette_bets', 0)}
"""

    @staticmethod
    def donate_menu(ruby_price: int, ruby_left: int) -> str:
        return f"""
⭐ Поддержать проект

Ваша поддержка помогает развивать игру!

🪙 За донаты вы получаете золото:
• 1 ⭐ = 80 🪙
• 5 ⭐ = 400 🪙
• 10 ⭐ = 850 🪙
• 20 ⭐ = 1800 🪙
• 50 ⭐ = 4500 🪙
• {ruby_price} ⭐ = 6800 🪙 + Королевский рубин (осталось {ruby_left})
• 100 ⭐ = 9000 🪙

🎁 Также есть спецнаборы!
🎁 Используйте промокоды для скидок! /promocode
"""

    @staticmethod
    def special_donates() -> str:
        return """
🎁 Спецнаборы:

🪨 Стартовый (50 ⭐):
5000🪙 + эпик ящ + топливо 180мин

⚡ Промышленный (100 ⭐):
12000🪙 + легенд ящ + топливо 300мин + эпик инструмент

👑 Магнатский (200 ⭐):
30000🪙 + миф ящ + топливо 600мин + легенд инструмент

🤖 Автодобыча (50 ⭐):
4400🪙 + топливо 180/300мин

🏺 Коллекционный (100 ⭐):
10000🪙 + эпик/легенд ящ + случ. коллекция
"""

    @staticmethod
    def donate_info(stars: int) -> str:
        reward = data_manager.get_donate_reward(stars) if data_manager else {"gold": 0, "bonus_percent": 0, "items": []}
        total_gold = reward['gold'] + int(reward['gold'] * reward['bonus_percent'] / 100)
        text = f"""
⭐ Донат на {stars} звёзд

🪙 Золота: {reward['gold']}
🎁 Бонус: +{reward['bonus_percent']}%
📊 Итого: {total_gold} 🪙

🎁 Предметы:
"""
        if reward.get('items'):
            for item in reward['items']:
                if item == "common_case": text += "• 📦 Обычный ящик\n"
                elif item == "rare_case": text += "• 🎁 Редкий ящик\n"
                elif item == "epic_case": text += "• 💎 Эпический ящик\n"
                elif item == "legendary_case": text += "• 👑 Легендарный ящик\n"
                elif item == "mythic_case": text += "• ✨ Мифический ящик\n"
                elif item == "common_fuel": text += "• ⛽ Топливо 60 мин\n"
                elif item == "advanced_fuel": text += "• 🔥 Топливо 180 мин\n"
                elif item == "premium_fuel": text += "• ⚡ Топливо 300 мин\n"
                elif item == "ultra_fuel": text += "• 🚀 Топливо 600 мин\n"
                elif item == "nuclear_fuel": text += "• ☢️ Топливо 1200 мин\n"
                elif item == "random_tool": text += "• ⛏️ Случ. инструмент\n"
                elif item == "random_collectible": text += "• 🏆 Случ. коллекция\n"
                elif item == "royal_ruby": text += "• 👑 Королевский рубин\n"
        else:
            text += "• Без предметов\n"
        return text

    @staticmethod
    def donate_thank_you(result: Dict[str, Any]) -> str:
        text = f"""
🎉 Спасибо за поддержку!

⭐ Получено звёзд: {result['stars']}
{'🎫 Со скидкой: ' + str(result.get('discounted_stars', result['stars'])) + ' ⭐' if result.get('discounted_stars', result['stars']) != result['stars'] else ''}
🪙 Начислено золота: {result['gold']}
🎁 Бонус: +{result.get('bonus_percent', 0)}%
{'💰 Скидка: ' + str(result.get('discount_percent', 0)) + '%' if result.get('discount_percent', 0) > 0 else ''}

🎊 Ваш вклад помогает!
"""
        if result.get('items'):
            text += "\n🎁 Предметы:\n"
            for item in result['items']:
                if isinstance(item, Item):
                    emoji = "🏆" if getattr(item, 'is_collectible', False) else KeyboardManager.get_rarity_emoji(getattr(item, 'rarity', ItemRarity.COMMON))
                    text += f"{emoji} {item.name}\n"
                else:
                    text += f"  {item}\n"
        if result.get('ruby_left') is not None:
            text += f"\n👑 Рубинов осталось: {result['ruby_left']}"
        return text

    @staticmethod
    def pay_support_info() -> str:
        return f"""
ℹ️ Информация о возврате средств

⭐ Донаты - добровольная поддержка.
🔙 Возврат в исключительных случаях.
📞 Обращаться к {ADMIN_USERNAME}
"""

    @staticmethod
    def help_text() -> str:
        return f"""
❓ Помощь

Основные команды:
/start - Начало
/mine - Добыча
/profile - Профиль
/daily - Ежедневный бонус
/transfer - Перевод золота
/donate - Поддержать
/automine - Автодобыча
/collections - Коллекции
/rul [красное/черное] [сумма] - Рулетка
/promocode [код] - Активация промокода
/help - Справка

🎰 Рулетка:
• /rul красное 100 - ставка на красное
• /rul черное 50 - ставка на черное
• Шанс выигрыша 50%
• Минимальная ставка: 10 🪙
• Выигрыш: x2 от ставки

🎁 Промокоды:
• /promocode [код] - ввести промокод
• Активируйте промокоды для получения бонусов

📞 По вопросам: {ADMIN_USERNAME}
"""

    @staticmethod
    def shop_fuel_info() -> str:
        return """
🛒 Топливо:

1. ⛽ Угольные брикеты - 800🪙 (60 мин)
2. 🔥 Нефтяное топливо - 2000🪙 (180 мин)
3. ⚡ Энергостержни - 4000🪙 (300 мин)
4. 🚀 Реактор - 8000🪙 (600 мин)
5. ☢️ Ядерное топливо - 20000🪙 (1200 мин)

💡 Автодобыча каждые 5 мин.
"""

    @staticmethod
    def daily_bonus(gold: int, streak: int) -> str:
        return f"""
🎁 Ежедневный бонус

✅ Бонус получен!
💰 Золото: +{gold} 🪙
🔥 Streak: {streak} дней
"""

    @staticmethod
    def transfer_success(amount: int, to: str, fee: int) -> str:
        return f"""
✅ Перевод выполнен!

💰 Отправлено: {amount} 🪙
👤 Получатель: {to}
💸 Комиссия: {fee} 🪙
📊 Списано: {amount + fee} 🪙
"""

    @staticmethod
    def reset_level_success(bonus: int, times: int, multiplier: float) -> str:
        return f"""
🔄 Перерождение выполнено!

✨ Получен бонус: {bonus} 🪙
📊 Всего перерождений: {times}
📈 Новый множитель дохода: x{multiplier:.1f}

💡 Все коллекционные и лимитированные предметы сохранены!
🔨 Кирка также сохранена!
"""

    @staticmethod
    def reset_level_menu(player: Player) -> str:
        has_item = player.has_reset_item()
        required_item = player.get_required_reset_item()
        item_status = "✅ Есть" if has_item else "❌ Нет"
        bonus = player.calculate_reset_bonus()
        return f"""
🔄 Перерождение

🏆 Текущий уровень: {player.miner_level}/{MAX_LEVEL}
💰 Бонус за перерождение: {bonus} 🪙
📈 Текущий множитель: x{player.reincarnation_multiplier:.1f}
📊 Требуется предмет: {required_item} ({item_status})

⚠️ При перерождении:
• Уровень и улучшения сбросятся
• Все коллекционные и лимитированные предметы останутся
• Обычные предметы (кроме коллекционных) исчезнут
• Кирка останется с текущей прокачкой
"""

    @staticmethod
    def pickaxe_info(player: Player) -> str:
        hits = player.get_current_pickaxe_hits()
        bonus = player.get_current_pickaxe_bonus()
        luck = player.get_current_pickaxe_luck()
        material = player.current_pickaxe_material.value
        upgrade = player.current_pickaxe_upgrade
        base_cost = 200
        material_index = list(PickaxeMaterial).index(player.current_pickaxe_material)
        cost = int(base_cost * (1.2 ** (upgrade + material_index * 3)))
        text = f"""
🔨 Информация о кирке

📛 Материал: {material}
📊 Уровень прокачки: {upgrade}/4
🔄 Ударов за сессию: {hits}
⚡ Бонус минералов: +{(bonus-1)*100:.1f}%
🍀 Шанс {PREMIUM_COIN_NAME}: +{luck*100:.1f}%

💰 Стоимость прокачки: {cost} 🪙
"""
        if upgrade >= 4:
            materials = list(PickaxeMaterial)
            current_index = materials.index(player.current_pickaxe_material)
            if current_index < len(materials) - 1:
                next_material = materials[current_index + 1].value
                text += f"\n🔜 Следующий материал: {next_material}"
            else:
                text += "\n🏆 Достигнут максимум!"
        return text

    @staticmethod
    def all_minerals() -> str:
        return data_manager.get_all_minerals_list() if data_manager else ""

    @staticmethod
    def all_items() -> str:
        return data_manager.get_all_items_list() if data_manager else ""

    @staticmethod
    def roulette_info() -> str:
        return """
🎰 Рулетка The Gold Rush

Правила игры:
• Делайте ставки на красное или черное
• Выпадает число от 1 до 6
• Красные: 1, 3, 5
• Черные: 2, 4, 6
• Шанс выигрыша: 50%
• Минимальная ставка: 10 🪙
• Выигрыш: x2 от ставки

Команда:
/rul красное 100 - ставка на красное
/rul черное 50 - ставка на черное

💡 Игра доступна в группах и личных сообщениях!
"""

    @staticmethod
    def roulette_stats(player: Player) -> str:
        wins = player.stats.get('roulette_wins', 0)
        losses = player.stats.get('roulette_losses', 0)
        profit = player.stats.get('roulette_profit', 0)
        total_bets = wins + losses
        win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0
        return f"""
🎰 Ваша статистика в рулетке

📊 Всего игр: {total_bets}
✅ Выигрышей: {wins} ({win_rate:.1f}%)
❌ Проигрышей: {losses}
💰 Прибыль: {profit} 🪙
"""

    @staticmethod
    def promocode_info() -> str:
        return """
🎁 Промокоды The Gold Rush

Вводите промокоды и получайте бонусы:
• 🪙 Золото
• 💎 Premium Coin
• 📦 Ящики
• 🏆 Предметы
• ⭐ Скидки на донат
• 🎁 Готовые пакеты с предметами

Чтобы ввести промокод, используйте:
/promocode [код]

Пример: /promocode GOLD100

🎁 Доступные промокоды можно узнать в нашем канале!
"""

    @staticmethod
    def promocode_activate_success(result: Dict[str, Any]) -> str:
        text = f"""
✅ Промокод {result['code']} активирован!

🎁 Получено: {result['reward_text']}
"""
        if result.get('items'):
            text += "\n📦 Предметы:\n"
            for item in result['items']:
                if isinstance(item, Item):
                    text += f"  • {item.name}\n"
                else:
                    text += f"  • {item}\n"
        return text

    @staticmethod
    def promocode_list(promocodes: List[PromoCode], for_player: bool = False) -> str:
        if not promocodes:
            return "📋 Нет доступных промокодов"
        text = "📋 Доступные промокоды:\n\n"
        now = datetime.now()
        for promo in promocodes[:10]:
            if for_player:
                if not promo.is_active or promo.used_count >= promo.max_uses:
                    continue
                if promo.expires_at and now > promo.expires_at:
                    continue
            status = "✅ Активен" if promo.is_active else "❌ Неактивен"
            uses = f"{promo.used_count}/{promo.max_uses}"
            expiry = f" до {promo.expires_at.strftime('%d.%m.%Y')}" if promo.expires_at else ""
            text += f"🎁 {promo.code}\n"
            text += f"  • {promo.description}\n"
            text += f"  • Статус: {status}{expiry}\n"
            text += f"  • Использовано: {uses}\n\n"
        return text

data_manager: Optional[DataManager] = None
bot_instance = None

class MinerichBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.keyboard_manager = KeyboardManager()
        self.donate_keyboards = DonateKeyboards()
        self.text_templates = TextTemplates()
        self.user_states = {}
        self._last_error_report = time.time()
        self._error_count = 0
        self.user_cooldowns: Dict[int, Dict[str, float]] = {}
        self.global_cooldown = 0.5
        self.user_rate_limits: Dict[int, List[float]] = {}
        self._rate_limit_lock = asyncio.Lock()
        self.notification_queue = asyncio.Queue()
        self._callback_lock = asyncio.Lock()

        global data_manager, bot_instance
        data_manager = DataManager(self.bot)
        bot_instance = self

        self.register_handlers()
        asyncio.create_task(self.process_notification_queue())

    async def process_notification_queue(self):
        while True:
            try:
                user_id, text = await self.notification_queue.get()
                player = None
                if data_manager:
                    player = data_manager.players.get(user_id)
                
                if player and player.can_send_notification():
                    await self.safe_send_message(user_id, text, parse_mode=ParseMode.MARKDOWN)
                
                await asyncio.sleep(BATCH_SEND_DELAY)
            except Exception:
                pass

    async def queue_notification(self, user_id: int, text: str):
        try:
            await self.notification_queue.put((user_id, text))
        except asyncio.QueueFull:
            pass

    async def check_rate_limit(self, user_id: int) -> bool:
        async with self._rate_limit_lock:
            now = time.time()
            if user_id not in self.user_rate_limits:
                self.user_rate_limits[user_id] = []
            timestamps = self.user_rate_limits[user_id]
            timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
            if len(timestamps) >= MAX_ACTIONS_PER_WINDOW:
                return False
            timestamps.append(now)
            self.user_rate_limits[user_id] = timestamps
            return True

    async def safe_send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode=None, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                return await self.bot.send_message(
                    chat_id, 
                    text, 
                    reply_markup=reply_markup, 
                    parse_mode=parse_mode
                )
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except TelegramBadRequest as e:
                if "message is too long" in str(e):
                    parts = [text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
                    for part in parts:
                        await self.bot.send_message(chat_id, part, reply_markup=reply_markup, parse_mode=parse_mode)
                    return
                elif "can't parse entities" in str(e):
                    return await self.bot.send_message(chat_id, text, reply_markup=reply_markup)
                else:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)
            except TelegramForbiddenError:
                return
            except Exception:
                if attempt == max_retries - 1:
                    return
                await asyncio.sleep(1)

    async def safe_edit_message(self, message: Message, text: str, reply_markup=None, parse_mode=None, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                return await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    return
                elif "can't parse entities" in str(e):
                    return await message.edit_text(text, reply_markup=reply_markup)
                elif "message can't be edited" in str(e):
                    return await self.safe_send_message(message.chat.id, text, reply_markup, parse_mode)
                else:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)
            except Exception:
                if attempt == max_retries - 1:
                    return
                await asyncio.sleep(1)

    def check_cooldown(self, user_id: int, action: str) -> Tuple[bool, float]:
        now = time.time()
        last_global = self.user_cooldowns.get(user_id, {}).get('global', 0)
        if now - last_global < self.global_cooldown:
            return False, self.global_cooldown - (now - last_global)
        last_action = self.user_cooldowns.get(user_id, {}).get(action, 0)
        cooldown_time = COOLDOWN_COMMANDS.get(action, 1)
        if now - last_action < cooldown_time:
            return False, cooldown_time - (now - last_action)
        if user_id not in self.user_cooldowns:
            self.user_cooldowns[user_id] = {}
        self.user_cooldowns[user_id]['global'] = now
        self.user_cooldowns[user_id][action] = now
        return True, 0

    def register_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "start")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены и не можете играть.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.welcome(player.first_name),
                    reply_markup=await self.keyboard_manager.main_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("donate"))
        async def cmd_donate(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "donate")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.donate_menu(data_manager.ruby_price, data_manager.ruby_total - data_manager.limited_item_counter),
                    reply_markup=await self.donate_keyboards.donate_menu(data_manager.ruby_price, data_manager.ruby_total - data_manager.limited_item_counter),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("paysupport"))
        async def cmd_paysupport(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "help")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player and message.from_user.id != ADMIN_ID:
                    return
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.pay_support_info(),
                    reply_markup=await self.keyboard_manager.main_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("mine"))
        async def cmd_mine(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "mine")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    "⛏️ Выберите минерал:",
                    reply_markup=await self.keyboard_manager.mining_menu(player),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("profile"))
        async def cmd_profile(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "profile")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.profile(player),
                    reply_markup=await self.keyboard_manager.profile_menu(player),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("daily"))
        async def cmd_daily(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "daily")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                success, msg, gold = data_manager.daily_bonus(message.from_user.id)
                if success:
                    streak = player.stats.get("daily_streak", 1)
                    await self.safe_send_message(
                        message.chat.id,
                        self.text_templates.daily_bonus(gold, streak),
                        reply_markup=await self.keyboard_manager.main_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await message.answer(f"❌ {msg}", reply_markup=await self.keyboard_manager.main_menu())
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("gold"))
        async def cmd_gold(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "gold")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.gold_balance(player),
                    reply_markup=await self.keyboard_manager.gold_menu(player.gold_balance),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("automine"))
        async def cmd_automine(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "auto")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                auto_session = data_manager.auto_mining_sessions.get(message.from_user.id) if data_manager else None
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.auto_mining_status(player, auto_session),
                    reply_markup=await self.keyboard_manager.auto_mining_menu(player),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("collections"))
        async def cmd_collections(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "collections")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                collectibles_stats = data_manager.get_player_collectibles_stats(message.from_user.id)
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.collections_stats(collectibles_stats),
                    reply_markup=await self.keyboard_manager.collections_menu(collectibles_stats),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "help")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.help_text(),
                    reply_markup=await self.keyboard_manager.main_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("shop"))
        async def cmd_shop(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "shop")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    "🛒 Магазин",
                    reply_markup=await self.keyboard_manager.shop_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("top"))
        async def cmd_top(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "top")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    "🏆 Топ игроков",
                    reply_markup=await self.keyboard_manager.top_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("transfer"))
        async def cmd_transfer(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "transfer")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    "💰 Переводы (комиссия 5%)",
                    reply_markup=await self.keyboard_manager.transfer_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("admin"))
        async def cmd_admin(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "admin")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if message.from_user.id != ADMIN_ID:
                    await message.answer("⛔ Нет прав!")
                    return
                await self.safe_send_message(
                    message.chat.id,
                    "👑 Админ панель",
                    reply_markup=await self.keyboard_manager.admin_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("arun"))
        async def cmd_arun(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                text = """
👑 Быстрые админ-команды:

📊 Статистика:
/astats - статистика

💰 Золото:
/ag @user сумма - выдать/забрать золото

📈 Уровень:
/as @user уровень - установить уровень

🎁 Предметы:
/ai @user название - выдать предмет (только существующие в системе)

🚫 Баны:
/aban @user причина - забанить
/aunban @user - разбанить

🎁 Промокоды:
/apromo создать gold 1000 10 "Описание" - создать промокод на золото
/apromo создать package starter 5 "Описание" - создать промокод на пакет
/apromo удалить КОД - удалить промокод

💾 Бекап:
/abackup - создать бекап
"""
                await message.answer(text)
            except Exception:
                await message.answer("❌ Ошибка")

        @self.dp.message(Command("ag"))
        async def admin_quick_gold(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                parts = message.text.split()
                if len(parts) != 3:
                    await message.answer("❌ Использование: /ag @user 1000")
                    return
                username = parts[1].replace('@', '')
                amount = int(parts[2])
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.search_player(username)
                if not player:
                    await message.answer("❌ Игрок не найден")
                    return
                success, msg, _ = data_manager.adjust_gold(player.user_id, amount)
                await message.answer(msg)
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("as"))
        async def admin_quick_set_level(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                parts = message.text.split()
                if len(parts) != 3:
                    await message.answer("❌ Использование: /as @user 50")
                    return
                username = parts[1].replace('@', '')
                level = int(parts[2])
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.search_player(username)
                if not player:
                    await message.answer("❌ Игрок не найден")
                    return
                player.miner_level = min(level, MAX_LEVEL)
                player.experience = 0
                player.total_experience = level * 100
                player._update_unlocked_minerals_by_level()
                await data_manager.batch_save()
                await message.answer(f"✅ Уровень {player.custom_name} установлен на {level}")
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("ai"))
        async def admin_quick_give_item(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                parts = message.text.split(maxsplit=2)
                if len(parts) < 3:
                    await message.answer("❌ Использование: /ai @user Рубин")
                    return
                username = parts[1].replace('@', '')
                item_name = parts[2]
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.search_player(username)
                if not player:
                    await message.answer("❌ Игрок не найден")
                    return
                success, msg = data_manager.give_item(player.user_id, item_name)
                await message.answer(msg)
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("aban"))
        async def admin_quick_ban(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                parts = message.text.split(maxsplit=2)
                if len(parts) < 3:
                    await message.answer("❌ Использование: /aban @user Причина")
                    return
                username = parts[1].replace('@', '')
                reason = parts[2]
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.search_player(username)
                if not player:
                    await message.answer("❌ Игрок не найден")
                    return
                success, msg = data_manager.ban_player(ADMIN_ID, player.user_id, reason, BanType.PERMANENT)
                await message.answer(msg)
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("aunban"))
        async def admin_quick_unban(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                parts = message.text.split()
                if len(parts) != 2:
                    await message.answer("❌ Использование: /aunban @user")
                    return
                username = parts[1].replace('@', '')
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.search_player(username)
                if not player:
                    await message.answer("❌ Игрок не найден")
                    return
                success, msg = data_manager.unban_player(player.user_id)
                await message.answer(msg)
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("astats"))
        async def admin_quick_stats(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                stats = data_manager.get_system_stats()
                await self.safe_send_message(
                    message.chat.id,
                    self.text_templates.system_stats(stats),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("abackup"))
        async def admin_quick_backup(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                if data_manager:
                    data_manager.save_data()
                await message.answer("✅ Бекап создан!")
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("apromo"))
        async def admin_quick_promo(message: Message):
            if message.from_user.id != ADMIN_ID:
                return
            try:
                parts = message.text.split()
                if len(parts) < 2:
                    await message.answer("❌ Использование: /apromo создать gold 1000 10 Описание\n/apromo создать package starter 5 Описание\n/apromo удалить КОД")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                action = parts[1].lower()
                if action == "создать" and len(parts) >= 6:
                    reward_type = parts[2].lower()
                    reward_value = parts[3]
                    max_uses = int(parts[4])
                    description = " ".join(parts[5:])
                    code = "PROMO" + str(random.randint(1000, 9999))
                    if reward_type == "gold":
                        success, msg = data_manager.create_promocode(
                            code=code,
                            reward_type="gold",
                            reward_value=int(reward_value),
                            max_uses=max_uses,
                            description=description
                        )
                    elif reward_type == "ruby":
                        success, msg = data_manager.create_promocode(
                            code=code,
                            reward_type="ruby_discount",
                            reward_value=int(reward_value),
                            max_uses=max_uses,
                            description=description
                        )
                    elif reward_type == "donate":
                        success, msg = data_manager.create_promocode(
                            code=code,
                            reward_type="donate_bonus",
                            reward_value=int(reward_value),
                            max_uses=max_uses,
                            description=description
                        )
                    elif reward_type == "premium":
                        success, msg = data_manager.create_promocode(
                            code=code,
                            reward_type="premium_coin",
                            reward_value=int(reward_value),
                            max_uses=max_uses,
                            description=description
                        )
                    elif reward_type == "package":
                        if reward_value in ["starter", "business", "premium"]:
                            success, msg = data_manager.create_promocode(
                                code=code,
                                reward_type="package",
                                reward_value=reward_value,
                                max_uses=max_uses,
                                description=description
                            )
                        else:
                            await message.answer("❌ Доступные пакеты: starter, business, premium")
                            return
                    else:
                        await message.answer("❌ Неизвестный тип награды")
                        return
                    if success:
                        await message.answer(f"✅ {msg}\nКод: {code}")
                    else:
                        await message.answer(f"❌ {msg}")
                elif action == "удалить" and len(parts) >= 3:
                    code = parts[2].upper()
                    success, msg = data_manager.delete_promocode(code)
                    await message.answer(msg)
                elif action == "список":
                    promos = data_manager.list_promocodes()
                    await message.answer(self.text_templates.promocode_list(promos))
                else:
                    await message.answer("❌ Неверная команда")
            except Exception:
                await message.answer(f"❌ Ошибка")

        @self.dp.message(Command("rul"))
        async def cmd_rul(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "rul")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                parts = message.text.split()
                if len(parts) == 1:
                    await self.safe_send_message(
                        message.chat.id,
                        self.text_templates.roulette_info(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                if len(parts) < 3:
                    await message.answer("❌ Использование: /rul красное 100 или /rul черное 50")
                    return
                bet_type = parts[1].lower()
                try:
                    amount = int(parts[2])
                except ValueError:
                    await message.answer("❌ Сумма должна быть числом")
                    return
                success, msg, result = data_manager.play_roulette(message.from_user.id, bet_type, amount)
                if success:
                    await self.safe_send_message(
                        message.chat.id,
                        msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await message.answer(msg)
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.message(Command("promocode"))
        async def cmd_promocode(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "promocode")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                parts = message.text.split()
                if len(parts) == 1:
                    await self.safe_send_message(
                        message.chat.id,
                        self.text_templates.promocode_info(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                code = parts[1].upper()
                player = data_manager.get_or_create_player(
                    message.from_user.id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                success, msg, result = data_manager.activate_promocode(message.from_user.id, code)
                if success:
                    await self.safe_send_message(
                        message.chat.id,
                        self.text_templates.promocode_activate_success(result),
                        reply_markup=await self.keyboard_manager.main_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await message.answer(f"❌ {msg}")
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

        @self.dp.pre_checkout_query()
        async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
            try:
                await pre_checkout_query.answer(ok=True)
            except Exception:
                await pre_checkout_query.answer(ok=False, error_message="Ошибка")

        @self.dp.message(F.successful_payment)
        async def success_payment_handler(message: Message):
            try:
                payment = message.successful_payment
                user_id = message.from_user.id
                payload = message.invoice_payload
                if not data_manager:
                    await message.answer("❌ Ошибка сервера")
                    return
                player = data_manager.get_or_create_player(
                    user_id,
                    message.from_user.username or "",
                    message.from_user.first_name or "Шахтёр"
                )
                if not player:
                    await message.answer("❌ Вы забанены.")
                    return
                if payload.startswith("donate_"):
                    try:
                        stars_str = payload.split("_")[1]
                        stars = int(stars_str)
                        success, result_message, result = data_manager.process_donation(user_id, stars, payload)
                        if success:
                            await self.safe_send_message(
                                message.chat.id,
                                self.text_templates.donate_thank_you(result),
                                reply_markup=await self.donate_keyboards.donate_thank_you(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            if ADMIN_ID:
                                broadcast_msg = data_manager.broadcast_donate_message(stars, player.custom_name or player.username or player.first_name)
                                await self.safe_send_message(
                                    ADMIN_ID,
                                    f"🎁 Новый донат!\n\n"
                                    f"👤 Игрок: {player.custom_name} (@{player.username})\n"
                                    f"⭐ Звёзд: {stars}\n"
                                    f"{'🎫 Со скидкой: ' + str(result.get('discounted_stars', stars)) + ' ⭐' if result.get('discounted_stars', stars) != stars else ''}\n"
                                    f"🪙 Золота: {result['gold']}\n"
                                    f"💰 Сумма: {payment.total_amount / 100} {payment.currency}\n"
                                    f"{broadcast_msg}",
                                    parse_mode=ParseMode.MARKDOWN
                                )
                                if "royal_ruby" in str(result.get('items', [])):
                                    ruby_msg = data_manager.broadcast_limited_message(player.custom_name or player.username or player.first_name)
                                    await self.safe_send_message(ADMIN_ID, ruby_msg, parse_mode=ParseMode.MARKDOWN)
                        else:
                            await message.answer(f"❌ Ошибка: {result_message}", reply_markup=await self.keyboard_manager.main_menu())
                    except Exception:
                        await message.answer("❌ Ошибка обработки", reply_markup=await self.keyboard_manager.main_menu())
            except Exception:
                await message.answer("❌ Ошибка", reply_markup=await self.keyboard_manager.main_menu())

        @self.dp.message()
        async def handle_message(message: Message):
            try:
                if not await self.check_rate_limit(message.from_user.id):
                    await message.answer("⏳ Слишком много запросов. Подождите немного.")
                    return
                if message.from_user.id not in self.user_states:
                    return
                can_use, wait = self.check_cooldown(message.from_user.id, "message_input")
                if not can_use:
                    await message.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.")
                    return
                state = self.user_states[message.from_user.id]
                if "timestamp" in state and time.time() - state["timestamp"] > 1800:
                    del self.user_states[message.from_user.id]
                    await message.answer("⏱️ Время ожидания истекло. Начните заново.")
                    return
                if state["action"] == "change_name" and state["step"] == "enter_name":
                    new_name = message.text.strip()
                    if not data_manager:
                        await message.answer("❌ Ошибка сервера")
                        del self.user_states[message.from_user.id]
                        return
                    player = data_manager.players.get(message.from_user.id)
                    if not player:
                        del self.user_states[message.from_user.id]
                        return
                    success, msg = data_manager.set_player_custom_name(message.from_user.id, new_name)
                    if success:
                        await self.safe_send_message(
                            message.chat.id,
                            f"✅ {msg}",
                            reply_markup=await self.keyboard_manager.profile_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await message.answer(f"❌ {msg}")
                    del self.user_states[message.from_user.id]
                elif state["action"] == "create_offer" and state["step"] == "select_item":
                    try:
                        item_index = int(message.text.strip()) - 1
                        if "tradable_items" not in state or item_index < 0 or item_index >= len(state["tradable_items"]):
                            await message.answer("❌ Неверный номер. Попробуйте снова.")
                            return
                        selected_item_id = state["tradable_items"][item_index]
                        state["selected_item"] = selected_item_id
                        state["step"] = "enter_price"
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        item = data_manager.get_item(selected_item_id)
                        item_name = item.name if item else "предмет"
                        await message.answer(f"Введите цену для {item_name} в золоте (макс 800000):")
                    except ValueError:
                        await message.answer("❌ Введите номер предмета цифрой")
                elif state["action"] == "create_offer" and state["step"] == "enter_price":
                    try:
                        price = int(message.text.strip())
                        selected_item_id = state.get("selected_item")
                        if not selected_item_id:
                            await message.answer("❌ Ошибка выбора предмета")
                            del self.user_states[message.from_user.id]
                            return
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        success, msg = data_manager.create_market_offer(message.from_user.id, selected_item_id, price)
                        player = data_manager.players.get(message.from_user.id)
                        if success:
                            await self.safe_send_message(
                                message.chat.id,
                                f"✅ {msg}",
                                reply_markup=await self.keyboard_manager.market_menu(data_manager.market_offers, data_manager.items),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await message.answer(f"❌ {msg}")
                        del self.user_states[message.from_user.id]
                    except ValueError:
                        await message.answer("❌ Введите цену цифрой")
                elif state["action"] == "transfer_gold":
                    if state["step"] == "enter_username":
                        state["to_username"] = message.text.strip()
                        state["step"] = "enter_amount"
                        await message.answer("Введите сумму для перевода:")
                    elif state["step"] == "enter_amount":
                        try:
                            amount = int(message.text.strip())
                            to_username = state.get("to_username")
                            if not to_username:
                                await message.answer("❌ Ошибка")
                                del self.user_states[message.from_user.id]
                                return
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            success, msg, sent_amount, fee = data_manager.transfer_gold(
                                message.from_user.id, to_username, amount
                            )
                            if success:
                                await self.safe_send_message(
                                    message.chat.id,
                                    self.text_templates.transfer_success(sent_amount, to_username, fee),
                                    reply_markup=await self.keyboard_manager.main_menu(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await message.answer(f"❌ {msg}")
                            del self.user_states[message.from_user.id]
                        except ValueError:
                            await message.answer("❌ Введите сумму цифрой")
                elif message.from_user.id == ADMIN_ID:
                    if state["action"] == "find_player" and state["step"] == "enter_query":
                        query = message.text.strip()
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        player = data_manager.search_player(query)
                        if player:
                            await self.safe_send_message(
                                message.chat.id,
                                f"👤 Найден игрок:\n\n"
                                f"ID: {player.user_id}\n"
                                f"Username: @{player.username}\n"
                                f"Имя: {player.custom_name}\n"
                                f"Уровень: {player.miner_level}\n"
                                f"Золото: {player.gold_balance} 🪙\n"
                                f"Предметов: {len(player.inventory)}\n"
                                f"🚫 Бан: {'Да' if player.is_banned else 'Нет'}",
                                reply_markup=await self.keyboard_manager.admin_back_button()
                            )
                        else:
                            await message.answer("❌ Игрок не найден")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "add_channel":
                        if state["step"] == "enter_name":
                            state["channel_name"] = message.text.strip()
                            state["step"] = "enter_url"
                            await message.answer("Введите ссылку на канал (например, https://t.me/channel):")
                        elif state["step"] == "enter_url":
                            state["channel_url"] = message.text.strip()
                            state["step"] = "enter_level"
                            await message.answer("Введите требуемый уровень:")
                        elif state["step"] == "enter_level":
                            try:
                                level = int(message.text.strip())
                                state["channel_level"] = level
                                state["step"] = "enter_reward"
                                await message.answer("Введите награду в золоте:")
                            except ValueError:
                                await message.answer("❌ Введите число")
                        elif state["step"] == "enter_reward":
                            try:
                                reward = int(message.text.strip())
                                if not data_manager:
                                    await message.answer("❌ Ошибка сервера")
                                    del self.user_states[message.from_user.id]
                                    return
                                success, msg = await data_manager.add_channel(
                                    state["channel_name"],
                                    state["channel_url"],
                                    state["channel_level"],
                                    reward
                                )
                                await message.answer(msg)
                                del self.user_states[message.from_user.id]
                            except ValueError:
                                await message.answer("❌ Введите число")
                    elif state["action"] == "remove_channel" and state["step"] == "select_channel":
                        try:
                            channel_index = int(message.text.strip()) - 1
                            if "channels_list" not in state or channel_index < 0 or channel_index >= len(state["channels_list"]):
                                await message.answer("❌ Неверный номер")
                                return
                            channel_id = state["channels_list"][channel_index]
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            success, msg = data_manager.remove_channel(channel_id)
                            await message.answer(msg)
                            del self.user_states[message.from_user.id]
                        except ValueError:
                            await message.answer("❌ Введите номер")
                    elif state["action"] == "adjust_gold":
                        if state["step"] == "enter_username":
                            state["target_username"] = message.text.strip()
                            state["step"] = "enter_amount"
                            await message.answer("Введите сумму (±):")
                        elif state["step"] == "enter_amount":
                            try:
                                amount = int(message.text.strip())
                                if not data_manager:
                                    await message.answer("❌ Ошибка сервера")
                                    del self.user_states[message.from_user.id]
                                    return
                                player = data_manager.search_player(state["target_username"])
                                if player:
                                    success, msg, _ = data_manager.adjust_gold(player.user_id, amount)
                                    await message.answer(msg)
                                else:
                                    await message.answer("❌ Игрок не найден")
                                del self.user_states[message.from_user.id]
                            except ValueError:
                                await message.answer("❌ Введите число")
                    elif state["action"] == "give_item":
                        if state["step"] == "enter_username":
                            state["target_username"] = message.text.strip()
                            state["step"] = "enter_item"
                            await message.answer("Введите название предмета:")
                        elif state["step"] == "enter_item":
                            item_name = message.text.strip()
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            player = data_manager.search_player(state["target_username"])
                            if player:
                                success, msg = data_manager.give_item(player.user_id, item_name)
                                await message.answer(msg)
                            else:
                                await message.answer("❌ Игрок не найден")
                            del self.user_states[message.from_user.id]
                    elif state["action"] == "set_level":
                        if state["step"] == "enter_username":
                            state["target_username"] = message.text.strip()
                            state["step"] = "enter_level"
                            await message.answer("Введите уровень:")
                        elif state["step"] == "enter_level":
                            try:
                                level = int(message.text.strip())
                                if not data_manager:
                                    await message.answer("❌ Ошибка сервера")
                                    del self.user_states[message.from_user.id]
                                    return
                                player = data_manager.search_player(state["target_username"])
                                if player:
                                    player.miner_level = min(level, MAX_LEVEL)
                                    player.experience = 0
                                    player.total_experience = level * 100
                                    player._update_unlocked_minerals_by_level()
                                    await data_manager.batch_save()
                                    await message.answer(f"✅ Уровень {player.custom_name} установлен на {level}")
                                else:
                                    await message.answer("❌ Игрок не найден")
                                del self.user_states[message.from_user.id]
                            except ValueError:
                                await message.answer("❌ Введите число")
                    elif state["action"] == "set_gold":
                        if state["step"] == "enter_username":
                            state["target_username"] = message.text.strip()
                            state["step"] = "enter_amount"
                            await message.answer("Введите количество золота:")
                        elif state["step"] == "enter_amount":
                            try:
                                amount = int(message.text.strip())
                                if not data_manager:
                                    await message.answer("❌ Ошибка сервера")
                                    del self.user_states[message.from_user.id]
                                    return
                                player = data_manager.search_player(state["target_username"])
                                if player:
                                    player.gold_balance = amount
                                    await data_manager.batch_save()
                                    await message.answer(f"✅ Золото {player.custom_name} установлено на {amount} 🪙")
                                else:
                                    await message.answer("❌ Игрок не найден")
                                del self.user_states[message.from_user.id]
                            except ValueError:
                                await message.answer("❌ Введите число")
                    elif state["action"] == "set_balance":
                        if state["step"] == "enter_username":
                            state["target_username"] = message.text.strip()
                            state["step"] = "enter_mineral"
                            await message.answer("Введите название минерала:")
                        elif state["step"] == "enter_mineral":
                            state["mineral_name"] = message.text.strip().upper()
                            state["step"] = "enter_amount"
                            await message.answer("Введите количество:")
                        elif state["step"] == "enter_amount":
                            try:
                                amount = float(message.text.strip())
                                if not data_manager:
                                    await message.answer("❌ Ошибка сервера")
                                    del self.user_states[message.from_user.id]
                                    return
                                player = data_manager.search_player(state["target_username"])
                                if player:
                                    mineral_name = state["mineral_name"]
                                    if mineral_name in player.mineral_balance:
                                        player.mineral_balance[mineral_name] = amount
                                        await data_manager.batch_save()
                                        mineral_value = next((m.value for m in MineralType if m.name == mineral_name), mineral_name)
                                        await message.answer(f"✅ {mineral_value} {player.custom_name} установлен на {amount}")
                                    else:
                                        await message.answer(f"❌ Минерал {mineral_name} не найден")
                                else:
                                    await message.answer("❌ Игрок не найден")
                                del self.user_states[message.from_user.id]
                            except ValueError:
                                await message.answer("❌ Введите число")
                    elif state["action"] == "reset_player" and state["step"] == "enter_username":
                        username = message.text.strip()
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        player = data_manager.search_player(username)
                        if player:
                            success, msg = data_manager.reset_player(player.user_id)
                            await message.answer(msg)
                        else:
                            await message.answer("❌ Игрок не найден")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "ban_player" and state["step"] == "enter_username":
                        state["target_username"] = message.text.strip()
                        state["step"] = "enter_reason"
                        await message.answer("Введите причину бана:")
                    elif state["action"] == "ban_player" and state["step"] == "enter_reason":
                        reason = message.text.strip()
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        player = data_manager.search_player(state["target_username"])
                        if player:
                            success, msg = data_manager.ban_player(ADMIN_ID, player.user_id, reason, BanType.PERMANENT)
                            await message.answer(msg)
                        else:
                            await message.answer("❌ Игрок не найден")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "unban_player" and state["step"] == "enter_username":
                        username = message.text.strip()
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        player = data_manager.search_player(username)
                        if player:
                            success, msg = data_manager.unban_player(player.user_id)
                            await message.answer(msg)
                        else:
                            await message.answer("❌ Игрок не найден")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "broadcast" and state["step"] == "enter_message":
                        broadcast_text = message.text.strip()
                        count = 0
                        if data_manager:
                            for user_id in list(data_manager.players.keys())[:100]:
                                try:
                                    await self.safe_send_message(user_id, f"📢 Рассылка:\n\n{broadcast_text}")
                                    count += 1
                                    await asyncio.sleep(BATCH_SEND_DELAY)
                                except:
                                    continue
                        await message.answer(f"✅ Отправлено {count} пользователям")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "set_ruby_price" and state["step"] == "enter_price":
                        try:
                            price = int(message.text.strip())
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            success, msg = data_manager.set_ruby_price(price)
                            await message.answer(msg)
                        except ValueError:
                            await message.answer("❌ Введите число")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "set_ruby_limit" and state["step"] == "enter_limit":
                        try:
                            limit = int(message.text.strip())
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            success, msg = data_manager.set_ruby_limit(limit)
                            await message.answer(msg)
                        except ValueError:
                            await message.answer("❌ Введите число")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "set_ruby_count" and state["step"] == "enter_count":
                        try:
                            count = int(message.text.strip())
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            success, msg = data_manager.set_ruby_count(count)
                            await message.answer(msg)
                        except ValueError:
                            await message.answer("❌ Введите число")
                        del self.user_states[message.from_user.id]
                    elif state["action"] == "create_promocode":
                        if state["step"] == "enter_code":
                            state["promo_code"] = message.text.strip().upper()
                            state["step"] = "enter_type"
                            await message.answer("Введите тип награды (gold, ruby_discount, donate_bonus, item, case, premium_coin, fuel, package):")
                        elif state["step"] == "enter_type":
                            reward_type = message.text.strip().lower()
                            if reward_type not in ["gold", "ruby_discount", "donate_bonus", "item", "case", "premium_coin", "fuel", "package"]:
                                await message.answer("❌ Неверный тип. Доступные: gold, ruby_discount, donate_bonus, item, case, premium_coin, fuel, package")
                                return
                            state["promo_type"] = reward_type
                            state["step"] = "enter_value"
                            await message.answer("Введите значение награды:")
                        elif state["step"] == "enter_value":
                            value = message.text.strip()
                            if state["promo_type"] in ["gold", "ruby_discount", "donate_bonus", "premium_coin", "fuel"]:
                                try:
                                    state["promo_value"] = int(value)
                                except ValueError:
                                    await message.answer("❌ Введите число")
                                    return
                            else:
                                state["promo_value"] = value
                            state["step"] = "enter_max_uses"
                            await message.answer("Введите максимальное количество использований:")
                        elif state["step"] == "enter_max_uses":
                            try:
                                max_uses = int(message.text.strip())
                                state["promo_max_uses"] = max_uses
                                state["step"] = "enter_description"
                                await message.answer("Введите описание промокода:")
                            except ValueError:
                                await message.answer("❌ Введите число")
                        elif state["step"] == "enter_description":
                            description = message.text.strip()
                            if not data_manager:
                                await message.answer("❌ Ошибка сервера")
                                del self.user_states[message.from_user.id]
                                return
                            success, msg = data_manager.create_promocode(
                                code=state["promo_code"],
                                reward_type=state["promo_type"],
                                reward_value=state["promo_value"],
                                max_uses=state["promo_max_uses"],
                                description=description
                            )
                            await message.answer(msg)
                            del self.user_states[message.from_user.id]
                    elif state["action"] == "delete_promocode" and state["step"] == "enter_code":
                        code = message.text.strip().upper()
                        if not data_manager:
                            await message.answer("❌ Ошибка сервера")
                            del self.user_states[message.from_user.id]
                            return
                        success, msg = data_manager.delete_promocode(code)
                        await message.answer(msg)
                        del self.user_states[message.from_user.id]
            except Exception:
                await message.answer("❌ Произошла ошибка. Попробуйте снова.")
                if message.from_user.id in self.user_states:
                    del self.user_states[message.from_user.id]

        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery):
            async with self._callback_lock:
                try:
                    if not await self.check_rate_limit(callback.from_user.id):
                        await callback.answer("⏳ Слишком много запросов. Подождите немного.", show_alert=True)
                        return
                    can_use, wait = self.check_cooldown(callback.from_user.id, "callback")
                    if not can_use:
                        await callback.answer(f"⏳ Слишком быстро! Подождите {wait:.1f} сек.", show_alert=True)
                        return
                    
                    await callback.answer()
                    
                    data = callback.data
                    
                    if data == "back_to_main":
                        await self.safe_edit_message(
                            callback.message,
                            f"⛏️ {GAME_NAME}\n\nГлавное меню",
                            reply_markup=await self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "profile_menu":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "👤 Профиль",
                            reply_markup=await self.keyboard_manager.profile_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "profile_info":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.profile(player),
                            reply_markup=await self.keyboard_manager.profile_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "profile_stats":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.profile_stats(player),
                            reply_markup=await self.keyboard_manager.profile_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "change_name":
                        self.user_states[callback.from_user.id] = {"action": "change_name", "step": "enter_name", "timestamp": time.time()}
                        await self.safe_edit_message(
                            callback.message,
                            "✏️ Новое имя (3-20 символов):",
                            reply_markup=await self.keyboard_manager.cancel_button("profile_menu"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "notification_settings":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "🔔 Настройки уведомлений",
                            reply_markup=await self.keyboard_manager.notification_settings(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("toggle_notif_"):
                        notif_type = data[13:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if player and not player.is_banned:
                            success, msg, new_state = data_manager.toggle_notification(callback.from_user.id, notif_type)
                            if success:
                                await self.safe_edit_message(
                                    callback.message,
                                    f"✅ {msg}",
                                    reply_markup=await self.keyboard_manager.notification_settings(player),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        return
                    
                    if data == "reset_level_menu":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Нет доступа")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.reset_level_menu(player),
                            reply_markup=await self.keyboard_manager.reset_level_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "reset_level":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Нет доступа")
                            return
                        success, msg, result = data_manager.reset_player_level(callback.from_user.id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.reset_level_success(result['bonus'], result['times_reset'], result['multiplier']),
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {msg}")
                        return
                    
                    if data == "top_players":
                        await self.safe_edit_message(
                            callback.message,
                            "🏆 Выберите тип топа:",
                            reply_markup=await self.keyboard_manager.top_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "top_gold":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        top = data_manager.get_top_players("gold")
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.top_players("gold", top),
                            reply_markup=await self.keyboard_manager.back_button("top_players"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "top_level":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        top = data_manager.get_top_players("level")
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.top_players("level", top),
                            reply_markup=await self.keyboard_manager.back_button("top_players"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "top_collectibles":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        top = data_manager.get_top_players("collectibles")
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.top_players("collectibles", top),
                            reply_markup=await self.keyboard_manager.back_button("top_players"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "top_reincarnation":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        top = data_manager.get_top_players("reincarnation")
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.top_players("reincarnation", top),
                            reply_markup=await self.keyboard_manager.back_button("top_players"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "top_roulette":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        top = data_manager.get_top_players("roulette")
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.top_players("roulette", top),
                            reply_markup=await self.keyboard_manager.back_button("top_players"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "donate":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.donate_menu(data_manager.ruby_price, data_manager.ruby_total - data_manager.limited_item_counter),
                            reply_markup=await self.donate_keyboards.donate_menu(data_manager.ruby_price, data_manager.ruby_total - data_manager.limited_item_counter),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "promocode_info":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.promocode_info(),
                            reply_markup=await self.keyboard_manager.back_button("donate"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("donate_"):
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        donate_type = data[7:]
                        if donate_type == "help":
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.pay_support_info(),
                                reply_markup=await self.donate_keyboards.back_button("donate"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        elif donate_type == "special":
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.special_donates(),
                                reply_markup=await self.donate_keyboards.special_donates(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        elif donate_type in ["starter", "business", "premium", "auto", "collection"]:
                            special_rewards = {
                                "starter": {"stars": 50, "title": "Стартовый набор"},
                                "business": {"stars": 100, "title": "Промышленный набор"},
                                "premium": {"stars": 200, "title": "Магнатский набор"},
                                "auto": {"stars": 50, "title": "Автодобыча"},
                                "collection": {"stars": 100, "title": "Коллекционный набор"}
                            }
                            reward = special_rewards[donate_type]
                            stars = reward["stars"]
                            await self.safe_edit_message(
                                callback.message,
                                f"⭐ {reward['title']} - {stars} звёзд\n\n" +
                                self.text_templates.donate_info(stars),
                                reply_markup=await self.donate_keyboards.confirm_donation(stars, data_manager.get_donate_reward(stars)["gold"], player),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            try:
                                stars = int(donate_type)
                                if stars > 0:
                                    await self.safe_edit_message(
                                        callback.message,
                                        self.text_templates.donate_info(stars),
                                        reply_markup=await self.donate_keyboards.confirm_donation(stars, data_manager.get_donate_reward(stars)["gold"], player),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                            except:
                                await callback.answer("❌ Неизвестный тип")
                        return
                    
                    if data.startswith("confirm_donate_"):
                        try:
                            stars_str = data[15:]
                            stars = int(stars_str)
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            player = data_manager.get_or_create_player(
                                callback.from_user.id,
                                callback.from_user.username or "",
                                callback.from_user.first_name or "Шахтёр"
                            )
                            if not player:
                                await callback.message.edit_text("❌ Вы забанены.")
                                return
                            reward = data_manager.get_donate_reward(stars)
                            total_gold = reward["gold"] + int(reward["gold"] * reward["bonus_percent"] / 100)
                            discount = player.get_discount("donate_bonus")
                            final_stars = stars
                            if discount > 0:
                                final_stars = max(1, int(stars * (100 - discount) / 100))
                                if final_stars != stars:
                                    await callback.answer(f"✅ Применена скидка {discount}%! Итоговая сумма: {final_stars} ⭐")
                            prices = [LabeledPrice(label="XTR", amount=final_stars)]
                            title = f"Донат {final_stars} ⭐ - {total_gold} 🪙"
                            if discount > 0:
                                title = f"Донат {final_stars} ⭐ (было {stars}⭐, скидка {discount}%) - {total_gold} 🪙"
                            description = f"Поддержка {GAME_NAME}. Вы получите {total_gold} золота!"
                            payload = f"donate_{stars}"
                            await callback.message.delete()
                            await callback.message.answer_invoice(
                                title=title,
                                description=description,
                                payload=payload,
                                provider_token="",
                                currency="XTR",
                                prices=prices,
                                reply_markup=await self.donate_keyboards.payment_keyboard(final_stars)
                            )
                        except Exception:
                            await callback.answer("❌ Ошибка создания счета")
                        return
                    
                    if data == "shop":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "🛒 Магазин",
                            reply_markup=await self.keyboard_manager.shop_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "shop_fuel":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.shop_fuel_info(),
                            reply_markup=await self.keyboard_manager.shop_fuel_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("shop_buy_fuel_"):
                        fuel_type = data[14:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        fuel_prices = {"basic": 800, "advanced": 2000, "premium": 4000, "ultra": 8000, "nuclear": 20000}
                        fuel_minutes = {"basic": 60, "advanced": 180, "premium": 300, "ultra": 600, "nuclear": 1200}
                        fuel_names = {"basic": "⛽ Угольные брикеты", "advanced": "🔥 Нефтяное топливо", "premium": "⚡ Энергостержни", "ultra": "🚀 Реактор", "nuclear": "☢️ Ядерное топливо"}
                        price = fuel_prices.get(fuel_type)
                        minutes = fuel_minutes.get(fuel_type)
                        name = fuel_names.get(fuel_type)
                        if price is None:
                            await callback.answer("❌ Неизвестный тип")
                            return
                        if player.gold_balance < price:
                            await callback.answer(f"❌ Нужно: {price} 🪙")
                            return
                        player.gold_balance -= price
                        item_id = str(uuid.uuid4())
                        rarity = ItemRarity.COMMON if fuel_type == "basic" else ItemRarity.RARE if fuel_type == "advanced" else ItemRarity.EPIC if fuel_type == "premium" else ItemRarity.LEGENDARY if fuel_type == "ultra" else ItemRarity.MYTHIC
                        fuel_item = Item(
                            item_id=item_id,
                            serial_number=data_manager.generate_serial_number(),
                            name=name,
                            item_type=ItemType.FUEL,
                            rarity=rarity,
                            description=f"Топливо ({minutes} мин)",
                            buy_price=price,
                            sell_price=int(price * 0.5),
                            is_tradable=True,
                            owner_id=callback.from_user.id,
                            fuel_amount=minutes
                        )
                        data_manager.items[item_id] = fuel_item
                        player.inventory.append(item_id)
                        await data_manager.batch_save()
                        await self.safe_edit_message(
                            callback.message,
                            f"✅ Куплено {name} за {price} 🪙",
                            reply_markup=await self.keyboard_manager.shop_fuel_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "mining_menu":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "⛏️ Выберите минерал:",
                            reply_markup=await self.keyboard_manager.mining_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "pickaxe_info":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.pickaxe_info(player),
                            reply_markup=await self.keyboard_manager.pickaxe_info(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "upgrade_pickaxe":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message = data_manager.upgrade_pickaxe(callback.from_user.id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}\n\n" + self.text_templates.pickaxe_info(player),
                                reply_markup=await self.keyboard_manager.pickaxe_info(player),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data.startswith("start_mine_"):
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        mineral_name = data[11:]
                        success, message = data_manager.start_mining(callback.from_user.id, mineral_name)
                        if success:
                            session = data_manager.active_mining_sessions[callback.from_user.id]
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.mining_status(session),
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="📊 Статус", callback_data="mining_status")],
                                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                    ]
                                ),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        elif message == "mining_status":
                            session = data_manager.active_mining_sessions[callback.from_user.id]
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.mining_status(session),
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="📊 Статус", callback_data="mining_status")],
                                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                    ]
                                ),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "mining_status":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        if callback.from_user.id in data_manager.active_mining_sessions:
                            session = data_manager.active_mining_sessions[callback.from_user.id]
                            if datetime.now() >= session.end_time:
                                success, result = data_manager.complete_mining(callback.from_user.id)
                                if success:
                                    await self.safe_edit_message(
                                        callback.message,
                                        self.text_templates.mining_result(result),
                                        reply_markup=await self.keyboard_manager.main_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                else:
                                    await callback.answer(result.get("error", "Ошибка"))
                            else:
                                await self.safe_edit_message(
                                    callback.message,
                                    self.text_templates.mining_status(session),
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="📊 Обновить", callback_data="mining_status")],
                                            [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                        ]
                                    ),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        else:
                            await callback.answer("❌ Нет активной добычи")
                        return
                    
                    if data == "my_minerals":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        minerals_text = "💰 Ваши минералы:\n\n"
                        for mineral_name, amount in player.mineral_balance.items():
                            if amount > 0:
                                mineral_value = next((m.value for m in MineralType if m.name == mineral_name), mineral_name)
                                minerals_text += f"{mineral_value}: {amount:.2f} кг\n"
                        if not any(amount > 0 for amount in player.mineral_balance.values()):
                            minerals_text += "Минералы отсутствуют\n"
                        total_value = player.get_total_mineral_value()
                        minerals_text += f"\n💰 Общая стоимость при продаже: {total_value:.2f} 🪙"
                        await self.safe_edit_message(
                            callback.message,
                            minerals_text,
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="💱 Продать ВСЕ", callback_data="convert_all_minerals")],
                                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "auto_mining":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.auto_mining_status(player, auto_session),
                            reply_markup=await self.keyboard_manager.auto_mining_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "toggle_auto_mining":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message = data_manager.toggle_auto_mining(callback.from_user.id)
                        if success:
                            auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}\n\n" + self.text_templates.auto_mining_status(player, auto_session),
                                reply_markup=await self.keyboard_manager.auto_mining_menu(player),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "buy_fuel_menu":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "⛽ Использовать топливо из инвентаря:",
                            reply_markup=await self.keyboard_manager.buy_fuel_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("use_fuel_"):
                        fuel_type = data[9:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        success, message = data_manager.buy_fuel(callback.from_user.id, fuel_type)
                        if success:
                            await callback.answer(f"✅ {message}")
                            player = data_manager.players[callback.from_user.id]
                            auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.auto_mining_status(player, auto_session),
                                reply_markup=await self.keyboard_manager.auto_mining_menu(player),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data.startswith("use_fuel_item_"):
                        item_id = data[14:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        item = data_manager.get_item(item_id)
                        if item and item.item_type == ItemType.FUEL:
                            player = data_manager.players.get(callback.from_user.id)
                            if player and not player.is_banned and item_id in player.inventory:
                                player.fuel += item.fuel_amount
                                player.inventory.remove(item_id)
                                del data_manager.items[item_id]
                                await data_manager.batch_save()
                                await self.safe_edit_message(
                                    callback.message,
                                    f"✅ Заправлено {item.fuel_amount} мин!",
                                    reply_markup=await self.keyboard_manager.auto_mining_menu(player),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await callback.answer("❌ Предмет не найден")
                        else:
                            await callback.answer("❌ Это не топливо")
                        return
                    
                    if data == "auto_mining_status":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.auto_mining_status(player, auto_session),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="auto_mining")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "fuel_status":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            f"⛽ Топливо: {player.fuel} мин",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="auto_mining")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "auto_mining_info":
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.auto_mining_info(),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="auto_mining")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "collections":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.collections_stats(collectibles_stats),
                            reply_markup=await self.keyboard_manager.collections_menu(collectibles_stats),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "collections_stats":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                        if not collectibles_stats:
                            await callback.answer("❌ Нет данных")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.collections_stats(collectibles_stats),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "collections_progress":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                        if not collectibles_stats:
                            await callback.answer("❌ Нет данных")
                            return
                        percentage = collectibles_stats.get("completion_percentage", 0)
                        progress_bar_length = 20
                        filled = int(percentage / 100 * progress_bar_length)
                        progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
                        text = f"""
📊 Прогресс

{progress_bar} {percentage:.1f}%

🎯 Уникальных: {collectibles_stats.get('unique_types', 0)}/24
📈 Всего: {collectibles_stats.get('total', 0)}

🏆 Награды за 100%: 40,000🪙 + Мифический ящик
"""
                        await self.safe_edit_message(
                            callback.message,
                            text,
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "gold":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.gold_balance(player),
                            reply_markup=await self.keyboard_manager.gold_menu(player.gold_balance),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "gold_balance":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.gold_balance(player),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="gold")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "convert_all_minerals":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message, gold = data_manager.convert_all_minerals_to_gold(callback.from_user.id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}",
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "upgrades":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "⚡ Улучшения",
                            reply_markup=await self.keyboard_manager.upgrades_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("buy_upgrade_"):
                        upgrade_id = data[12:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message = data_manager.buy_upgrade(callback.from_user.id, upgrade_id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}\n\nВыберите следующее:",
                                reply_markup=await self.keyboard_manager.upgrades_menu(player),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "cases":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "📦 Ящики",
                            reply_markup=await self.keyboard_manager.cases_menu(data_manager.cases, player.gold_balance),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("buy_case_"):
                        case_type_name = data[9:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message, case_item = data_manager.buy_case(callback.from_user.id, case_type_name)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}\n\nЯщик в инвентаре!",
                                reply_markup=await self.keyboard_manager.cases_menu(data_manager.cases, player.gold_balance),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "open_cases":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        cases = []
                        for item_id in player.inventory[:20]:
                            item = data_manager.get_item(item_id)
                            if item and item.item_type == ItemType.CASE:
                                cases.append(item)
                        if not cases:
                            await callback.answer("❌ У вас нет ящиков")
                            return
                        builder = InlineKeyboardBuilder()
                        for case_item in cases[:10]:
                            builder.button(text=f"{case_item.name}", callback_data=f"open_{case_item.item_id}")
                        builder.button(text="⬅️ Назад", callback_data="cases")
                        builder.adjust(1)
                        await self.safe_edit_message(
                            callback.message,
                            "🎁 Выберите ящик для открытия:",
                            reply_markup=builder.as_markup(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("open_"):
                        case_item_id = data[5:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        if case_item_id not in player.inventory:
                            await callback.answer("❌ Ящик не найден в инвентаре")
                            return
                        success, message, items = data_manager.open_case(callback.from_user.id, case_item_id)
                        if success:
                            text = f"✅ {message}\n\n🎁 Получены предметы:\n"
                            for item in items:
                                emoji = "🏆" if item.is_collectible else KeyboardManager.get_rarity_emoji(item.rarity)
                                text += f"{emoji} {item.name}\n"
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "inventory":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        if not player.inventory:
                            await self.safe_edit_message(
                                callback.message,
                                "🎒 Инвентарь пуст!",
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await self.safe_edit_message(
                                callback.message,
                                f"🎒 Инвентарь ({len(player.inventory)})",
                                reply_markup=await self.keyboard_manager.inventory_menu(player, data_manager.items),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        return
                    
                    if data.startswith("inv_page_"):
                        page = int(data[9:])
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            f"🎒 Инвентарь (стр. {page+1})",
                            reply_markup=await self.keyboard_manager.inventory_menu(player, data_manager.items, page),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "sell_menu":
                        await self.safe_edit_message(
                            callback.message,
                            "💰 Продать предметы по редкости:",
                            reply_markup=await self.keyboard_manager.sell_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("sell_rarity_"):
                        rarity_str = data[12:]
                        try:
                            rarity = ItemRarity[rarity_str]
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            player = data_manager.players.get(callback.from_user.id)
                            if not player or player.is_banned:
                                await callback.answer("❌ Шахтёр не найден или забанен")
                                return
                            success, message, sold, total = data_manager.sell_items_by_rarity(callback.from_user.id, rarity)
                            if success:
                                await self.safe_edit_message(
                                    callback.message,
                                    f"✅ {message}\n💰 Получено: {total} 🪙",
                                    reply_markup=await self.keyboard_manager.main_menu(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await callback.answer(f"❌ {message}")
                        except Exception:
                            await callback.answer("❌ Ошибка")
                        return
                    
                    if data.startswith("item_"):
                        item_id = data[5:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        item = data_manager.get_item(item_id)
                        if item:
                            player = data_manager.players.get(callback.from_user.id)
                            if not player or player.is_banned:
                                await callback.answer("❌ Шахтёр не найден или забанен")
                                return
                            is_equipped = item_id in player.equipped_items.values()
                            is_on_market = player.is_item_on_market(item_id)
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.item_info(item),
                                reply_markup=await self.keyboard_manager.item_menu(item, is_equipped, is_on_market),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer("❌ Предмет не найден")
                        return
                    
                    if data.startswith("equip_"):
                        item_id = data[6:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message = data_manager.equip_item(callback.from_user.id, item_id)
                        if success:
                            await callback.answer(f"✅ {message}")
                            item = data_manager.get_item(item_id)
                            if item:
                                await self.safe_edit_message(
                                    callback.message,
                                    self.text_templates.item_info(item),
                                    reply_markup=await self.keyboard_manager.item_menu(item, True, player.is_item_on_market(item_id)),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data.startswith("unequip_"):
                        slot_or_item_id = data[8:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        if slot_or_item_id in ["tool", "charm", "chip", "core"]:
                            success, message = data_manager.unequip_item(callback.from_user.id, slot_or_item_id)
                        else:
                            slot = None
                            for s, iid in player.equipped_items.items():
                                if iid == slot_or_item_id:
                                    slot = s
                                    break
                            if slot:
                                success, message = data_manager.unequip_item(callback.from_user.id, slot)
                            else:
                                await callback.answer("❌ Предмет не экипирован")
                                return
                        if success:
                            await callback.answer(f"✅ {message}")
                            await self.safe_edit_message(
                                callback.message,
                                "🛡️ Экипировка",
                                reply_markup=await self.keyboard_manager.equipment_menu(player.equipped_items, data_manager.items),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "equipment":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "🛡️ Экипировка",
                            reply_markup=await self.keyboard_manager.equipment_menu(player.equipped_items, data_manager.items),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "equipment_bonuses":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        bonuses_text = "📊 Бонусы от экипировки:\n\n"
                        total_mining_bonus = 1.0
                        total_luck_bonus = 0.0
                        for slot, item_id in player.equipped_items.items():
                            item = data_manager.get_item(item_id)
                            if item:
                                if item.mining_bonus > 1.0:
                                    total_mining_bonus *= item.mining_bonus
                                if item.luck_bonus > 0:
                                    total_luck_bonus += item.luck_bonus
                        bonuses_text += f"⚡ Добыча: +{(total_mining_bonus-1)*100:.1f}%\n"
                        bonuses_text += f"🍀 Шанс {PREMIUM_COIN_NAME}: +{total_luck_bonus*100:.1f}%\n"
                        await self.safe_edit_message(
                            callback.message,
                            bonuses_text,
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="equipment")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("sell_"):
                        item_id = data[5:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message = data_manager.sell_item(callback.from_user.id, item_id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}",
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data.startswith("market_sell_"):
                        item_id = data[12:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        if item_id not in player.inventory:
                            await callback.answer("❌ Предмет не найден")
                            return
                        item = data_manager.get_item(item_id)
                        if not item or not item.is_tradable or (not item.is_collectible and item.rarity != ItemRarity.LIMITED):
                            await callback.answer("❌ Только коллекц. и лимит.")
                            return
                        if player.is_item_on_market(item_id):
                            await callback.answer("❌ Предмет уже на рынке")
                            return
                        self.user_states[callback.from_user.id] = {
                            "action": "create_offer",
                            "step": "select_item",
                            "tradable_items": [item_id],
                            "selected_item": item_id,
                            "timestamp": time.time()
                        }
                        await self.safe_edit_message(
                            callback.message,
                            f"Введите цену для {item.name} в золоте (макс 800000):",
                            reply_markup=await self.keyboard_manager.cancel_button(f"item_{item_id}")
                        )
                        return
                    
                    if data == "market":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.market_info(),
                            reply_markup=await self.keyboard_manager.market_menu(data_manager.market_offers, data_manager.items),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("market_page_"):
                        page = int(data[12:])
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.market_info(),
                            reply_markup=await self.keyboard_manager.market_menu(data_manager.market_offers, data_manager.items, page),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("buy_offer_"):
                        offer_id = data[10:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, message = data_manager.buy_market_offer(callback.from_user.id, offer_id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {message}",
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {message}")
                        return
                    
                    if data == "my_offers":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        my_offers = [offer for offer in data_manager.market_offers.values() if offer.seller_id == callback.from_user.id and offer.is_active]
                        if not my_offers:
                            await self.safe_edit_message(
                                callback.message,
                                "📤 Нет активных предложений",
                                reply_markup=await self.keyboard_manager.back_button("market"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        text = "📤 Ваши предложения:\n\n"
                        for i, offer in enumerate(my_offers, 1):
                            item = data_manager.get_item(offer.item_id)
                            if item:
                                text += f"{i}. {item.name} - {offer.price} 🪙\n"
                        await self.safe_edit_message(
                            callback.message,
                            text,
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Снять все", callback_data="cancel_all_offers")],
                                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="market")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "create_offer":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        if not player.inventory:
                            await callback.answer("❌ В инвентаре нет предметов")
                            return
                        tradable_items = []
                        for item_id in player.inventory[:20]:
                            if player.is_item_on_market(item_id):
                                continue
                            item = data_manager.get_item(item_id)
                            if item and item.is_tradable and (item.is_collectible or item.rarity == ItemRarity.LIMITED):
                                tradable_items.append((item_id, item))
                        if not tradable_items:
                            await callback.answer("❌ Нет подходящих предметов")
                            return
                        text = "Выберите предмет для продажи (введите номер):\n\n"
                        for i, (item_id, item) in enumerate(tradable_items, 1):
                            text += f"{i}. {item.name}\n"
                        self.user_states[callback.from_user.id] = {
                            "action": "create_offer",
                            "step": "select_item",
                            "tradable_items": [item_id for item_id, _ in tradable_items],
                            "timestamp": time.time()
                        }
                        await self.safe_edit_message(
                            callback.message,
                            text,
                            reply_markup=await self.keyboard_manager.cancel_button("market"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "cancel_all_offers":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.players.get(callback.from_user.id)
                        if not player or player.is_banned:
                            await callback.answer("❌ Шахтёр не найден или забанен")
                            return
                        success, msg, count = data_manager.cancel_all_market_offers(callback.from_user.id)
                        if success:
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ {msg}",
                                reply_markup=await self.keyboard_manager.back_button("market"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {msg}")
                        return
                    
                    if data == "channels":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        await self.safe_edit_message(
                            callback.message,
                            "📢 Каналы для подписки\n\nПодпишитесь и получайте награды!",
                            reply_markup=await self.keyboard_manager.channels_menu(data_manager.channels),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data.startswith("channel_"):
                        channel_id = data[8:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        channel = data_manager.channels.get(channel_id)
                        if channel:
                            player = data_manager.get_or_create_player(
                                callback.from_user.id,
                                callback.from_user.username or "",
                                callback.from_user.first_name or "Шахтёр"
                            )
                            if not player:
                                await callback.message.edit_text("❌ Вы забанены.")
                                return
                            is_subscribed = channel_id in player.subscribed_channels
                            status = "✅ Подписан" if is_subscribed else "❌ Не подписан"
                            bot_status = "✅ Бот в канале" if channel.bot_member else "⚠️ Бота нет"
                            text = f"""
📢 {channel.name}
🔗 {channel.url}
🏆 Треб. ур.: {channel.required_level}
💰 Награда: {channel.reward} 🪙
📊 Статус: {status}
🤖 {bot_status}
"""
                            buttons = [
                                [InlineKeyboardButton(text="🔗 Перейти", url=channel.url),
                                 InlineKeyboardButton(text="✅ Проверить", callback_data=f"check_{channel_id}")],
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="channels")]
                            ]
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        return
                    
                    if data.startswith("check_"):
                        channel_id = data[6:]
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        channel = data_manager.channels.get(channel_id)
                        if channel:
                            player = data_manager.get_or_create_player(
                                callback.from_user.id,
                                callback.from_user.username or "",
                                callback.from_user.first_name or "Шахтёр"
                            )
                            if not player or player.is_banned:
                                await callback.message.edit_text("❌ Вы забанены.")
                                return
                            if channel_id not in player.subscribed_channels:
                                if not channel.bot_member:
                                    bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                                    if bot_in_channel:
                                        channel.bot_member = True
                                        await data_manager.batch_save()
                                    else:
                                        await self.safe_edit_message(
                                            callback.message,
                                            f"⚠️ Бот не админ в канале! Добавьте бота.",
                                            reply_markup=await self.keyboard_manager.back_button("channels"),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                        return
                                player.subscribed_channels.append(channel_id)
                                player.gold_balance += channel.reward
                                await data_manager.batch_save()
                                await self.safe_edit_message(
                                    callback.message,
                                    f"✅ Подписка подтверждена! +{channel.reward} 🪙",
                                    reply_markup=await self.keyboard_manager.back_button("channels"),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await callback.answer("✅ Уже подписаны")
                        return
                    
                    if data == "check_subscriptions":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player or player.is_banned:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        new_subs = 0
                        total_reward = 0
                        for channel_id, channel in data_manager.channels.items():
                            if channel_id not in player.subscribed_channels:
                                if not channel.bot_member:
                                    bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                                    if bot_in_channel:
                                        channel.bot_member = True
                                        await data_manager.batch_save()
                                    else:
                                        continue
                                player.subscribed_channels.append(channel_id)
                                player.gold_balance += channel.reward
                                new_subs += 1
                                total_reward += channel.reward
                        if new_subs > 0:
                            await data_manager.batch_save()
                            await self.safe_edit_message(
                                callback.message,
                                f"✅ Проверено! Новых: {new_subs}, награда: {total_reward} 🪙",
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer("ℹ️ Вы уже подписаны на всё")
                        return
                    
                    if data == "help":
                        await self.safe_edit_message(
                            callback.message,
                            self.text_templates.help_text(),
                            reply_markup=await self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "transfer_menu":
                        await self.safe_edit_message(
                            callback.message,
                            "💰 Переводы (комиссия 5%)",
                            reply_markup=await self.keyboard_manager.transfer_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "transfer_gold":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        self.user_states[callback.from_user.id] = {"action": "transfer_gold", "step": "enter_username", "timestamp": time.time()}
                        await self.safe_edit_message(
                            callback.message,
                            "Введите username получателя (без @):",
                            reply_markup=await self.keyboard_manager.cancel_button("transfer_menu"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    if data == "daily_bonus":
                        if not data_manager:
                            await callback.message.edit_text("❌ Ошибка сервера.")
                            return
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        if not player:
                            await callback.message.edit_text("❌ Вы забанены.")
                            return
                        success, msg, gold = data_manager.daily_bonus(callback.from_user.id)
                        if success:
                            streak = player.stats.get("daily_streak", 1)
                            await self.safe_edit_message(
                                callback.message,
                                self.text_templates.daily_bonus(gold, streak),
                                reply_markup=await self.keyboard_manager.main_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer(f"❌ {msg}")
                        return
                    
                    if callback.from_user.id == ADMIN_ID:
                        if data == "admin":
                            await self.safe_edit_message(
                                callback.message,
                                "👑 Админ панель",
                                reply_markup=await self.keyboard_manager.admin_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_stats":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            stats = data_manager.get_system_stats()
                            stats_text = f"""
📊 Статистика v{VERSION}

👥 Игроков: {stats['total_players']}
🚫 Забанено: {stats['banned']}
🎮 Активных сегодня: {stats['active_today']}
⚡ Онлайн сейчас: {stats['active_now']}
🤖 Авто: {stats['online_auto']}
⛏️ Добыто: {stats['total_mined']:.2f} кг
🪙 Золота в системе: {stats['total_gold']}
💎 Premium Coin: {stats['total_premium']}
🔄 Перерождений: {stats['reincarnations']}
🎁 Промокодов активировано: {stats.get('promocodes_activated', 0)}
🎰 Ставок в рулетке: {stats.get('roulette_bets', 0)}

👑 Рубин: {data_manager.limited_item_counter}/{data_manager.ruby_total}
📈 Топ 5 по уровню:
"""
                            sorted_players = sorted(data_manager.players.values(), key=lambda p: p.miner_level, reverse=True)[:5]
                            for i, player in enumerate(sorted_players, 1):
                                stats_text += f"{i}. {player.custom_name} - Ур.{player.miner_level}\n"
                            await self.safe_edit_message(
                                callback.message,
                                stats_text,
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_donate_stats":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            await self.safe_edit_message(
                                callback.message,
                                f"""
⭐ Донаты

👑 Рубин:
• Цена: {data_manager.ruby_price} ⭐
• Выдано: {data_manager.limited_item_counter}/{data_manager.ruby_total}
• Осталось: {data_manager.ruby_total - data_manager.limited_item_counter}
""",
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_ruby_settings":
                            await self.safe_edit_message(
                                callback.message,
                                "👑 Настройки рубина",
                                reply_markup=await self.keyboard_manager.admin_ruby_settings(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_set_ruby_price":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            self.user_states[callback.from_user.id] = {"action": "set_ruby_price", "step": "enter_price", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                f"👑 Цена рубина сейчас: {data_manager.ruby_price} ⭐\nВведите новую цену:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin_ruby_settings"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_set_ruby_limit":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            self.user_states[callback.from_user.id] = {"action": "set_ruby_limit", "step": "enter_limit", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                f"👑 Лимит рубина сейчас: {data_manager.ruby_total}\nВведите новый лимит:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin_ruby_settings"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_set_ruby_count":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            self.user_states[callback.from_user.id] = {"action": "set_ruby_count", "step": "enter_count", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                f"👑 Выдано сейчас: {data_manager.limited_item_counter}\nВведите новое кол-во:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin_ruby_settings"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_ruby_info":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            await self.safe_edit_message(
                                callback.message,
                                data_manager.get_ruby_info(),
                                reply_markup=await self.keyboard_manager.admin_ruby_settings(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_players":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            text = "👤 Список игроков (первые 20):\n\n"
                            for i, player in enumerate(list(data_manager.players.values())[:20], 1):
                                banned = "🚫" if player.is_banned else ""
                                text += f"{i}. {banned} @{player.username} ({player.custom_name}) - Ур.{player.miner_level} (Пер.{player.reincarnation_level})\n"
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_find_player":
                            self.user_states[callback.from_user.id] = {"action": "find_player", "step": "enter_query", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "🔍 Введите username или ID:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_all_items":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            await self.safe_edit_message(
                                callback.message,
                                data_manager.get_all_items_list(),
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_all_minerals":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            await self.safe_edit_message(
                                callback.message,
                                data_manager.get_all_minerals_list(),
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_add_channel":
                            self.user_states[callback.from_user.id] = {"action": "add_channel", "step": "enter_name", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "➕ Введите название канала:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_remove_channel":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            text = "➖ Выберите канал для удаления (введите номер):\n\n"
                            channels_list = list(data_manager.channels.items())
                            for i, (channel_id, channel) in enumerate(channels_list, 1):
                                bot_status = "✅" if channel.bot_member else "⚠️"
                                text += f"{i}. {bot_status} {channel.name}\n"
                            if not data_manager.channels:
                                text += "Каналов нет"
                            self.user_states[callback.from_user.id] = {"action": "remove_channel", "step": "select_channel", "channels_list": [cid for cid, _ in channels_list], "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_check_channels":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            text = "🔧 Проверка каналов:\n\n"
                            updated = 0
                            for channel_id, channel in data_manager.channels.items():
                                bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                                if bot_in_channel != channel.bot_member:
                                    channel.bot_member = bot_in_channel
                                    channel.last_check = datetime.now()
                                    updated += 1
                                status = "✅ Бот есть" if channel.bot_member else "⚠️ Бота нет"
                                text += f"• {channel.name}: {status}\n"
                            if updated > 0:
                                await data_manager.batch_save()
                                text += f"\n✅ Обновлено {updated} каналов"
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_adjust_gold":
                            self.user_states[callback.from_user.id] = {"action": "adjust_gold", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "🎁 Введите username для изменения золота (±):",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_give_item":
                            self.user_states[callback.from_user.id] = {"action": "give_item", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "🎁 Введите username для выдачи предмета:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_set_level":
                            self.user_states[callback.from_user.id] = {"action": "set_level", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "📈 Введите username для установки уровня:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_set_gold":
                            self.user_states[callback.from_user.id] = {"action": "set_gold", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "💰 Введите username для установки золота:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_set_balance":
                            self.user_states[callback.from_user.id] = {"action": "set_balance", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "💱 Введите username для установки баланса минералов:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_reset_player":
                            self.user_states[callback.from_user.id] = {"action": "reset_player", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "🔄 Введите username для сброса игрока:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_ban_player":
                            self.user_states[callback.from_user.id] = {"action": "ban_player", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "🚫 Введите username для бана:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_unban_player":
                            self.user_states[callback.from_user.id] = {"action": "unban_player", "step": "enter_username", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "✅ Введите username для разбана:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_broadcast":
                            self.user_states[callback.from_user.id] = {"action": "broadcast", "step": "enter_message", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "📢 Введите сообщение для рассылки:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_backup":
                            try:
                                if data_manager:
                                    data_manager.save_data()
                                await self.safe_edit_message(
                                    callback.message,
                                    "✅ Бекап создан!",
                                    reply_markup=await self.keyboard_manager.admin_back_button(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            except Exception:
                                await callback.answer("❌ Ошибка")
                            return
                        
                        if data == "admin_promocodes":
                            await self.safe_edit_message(
                                callback.message,
                                "🎁 Управление промокодами",
                                reply_markup=await self.keyboard_manager.admin_promocodes_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_list_promocodes":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            promos = data_manager.list_promocodes()
                            text = self.text_templates.promocode_list(promos)
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_create_promocode":
                            self.user_states[callback.from_user.id] = {"action": "create_promocode", "step": "enter_code", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "🎁 Введите код промокода (англ. буквы и цифры):",
                                reply_markup=await self.keyboard_manager.cancel_button("admin_promocodes"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_delete_promocode":
                            self.user_states[callback.from_user.id] = {"action": "delete_promocode", "step": "enter_code", "timestamp": time.time()}
                            await self.safe_edit_message(
                                callback.message,
                                "❌ Введите код промокода для удаления:",
                                reply_markup=await self.keyboard_manager.cancel_button("admin_promocodes"),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                        
                        if data == "admin_promocode_stats":
                            if not data_manager:
                                await callback.message.edit_text("❌ Ошибка сервера.")
                                return
                            promos = data_manager.list_promocodes()
                            total_activations = len(data_manager.promocode_activations)
                            text = f"📊 Статистика промокодов\n\n"
                            text += f"🎁 Всего промокодов: {len(promos)}\n"
                            text += f"✅ Активных: {sum(1 for p in promos if p.is_active)}\n"
                            text += f"📈 Всего активаций: {total_activations}\n\n"
                            text += "Топ-5 промокодов:\n"
                            promo_usage = {}
                            for activation in data_manager.promocode_activations[-100:]:
                                promo_usage[activation.code] = promo_usage.get(activation.code, 0) + 1
                            sorted_promos = sorted(promo_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                            for i, (code, count) in enumerate(sorted_promos, 1):
                                text += f"{i}. {code}: {count} раз\n"
                            await self.safe_edit_message(
                                callback.message,
                                text,
                                reply_markup=await self.keyboard_manager.admin_back_button(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
                    else:
                        await callback.answer("ℹ️ Функция не реализована")
                except TelegramBadRequest as e:
                    if "query is too old" in str(e) or "message is not modified" in str(e):
                        pass
                    else:
                        await callback.answer("❌ Ошибка")
                except Exception:
                    await callback.answer("❌ Ошибка!")

    async def run(self):
        asyncio.create_task(self.check_mining_sessions())
        asyncio.create_task(self.check_auto_mining())
        asyncio.create_task(self.cleanup_states())
        asyncio.create_task(self.auto_save())
        asyncio.create_task(self.memory_cleanup())
        asyncio.create_task(self.cleanup_cooldowns())
        if data_manager:
            await data_manager.start_save_worker()
        
        asyncio.create_task(self.cleanup_rate_limits())
        asyncio.create_task(self.periodic_cache_cleanup())
        
        await self.dp.start_polling(self.bot)

    async def auto_save(self):
        while True:
            try:
                await asyncio.sleep(BATCH_SAVE_INTERVAL)
                if data_manager and time.time() - data_manager._last_auto_save > BATCH_SAVE_INTERVAL - 60:
                    await data_manager.batch_save()
                    
                    current_time = time.time()
                    for user_id in list(self.user_states.keys()):
                        if user_id in self.user_states and "timestamp" in self.user_states[user_id]:
                            if current_time - self.user_states[user_id]["timestamp"] > 3600:
                                del self.user_states[user_id]
            except Exception:
                await asyncio.sleep(60)

    async def check_mining_sessions(self):
        while True:
            try:
                if not data_manager:
                    await asyncio.sleep(1)
                    continue
                current_time = datetime.now()
                
                for user_id, session in list(data_manager.active_mining_sessions.items()):
                    if session.active and session.next_hit_time and current_time >= session.next_hit_time:
                        try:
                            player = data_manager.players.get(user_id)
                            if player and not player.is_banned:
                                success, result = data_manager.process_auto_hit(user_id)
                                if success and result.get('success'):
                                    if result.get('hit_number', 0) % 5 == 0 and player.mining_notifications:
                                        await self.queue_notification(
                                            user_id,
                                            f"⛏️ Удар {result['hit_number']}/{result['total_hits']}\n"
                                            f"💰 Добыто: {result['mineral_reward']:.2f} кг {result['mineral'].value}"
                                        )
                        except Exception:
                            pass
                    
                    await asyncio.sleep(0.01)
                
                completed_users = []
                for user_id, session in data_manager.active_mining_sessions.items():
                    if session.active and current_time >= session.end_time:
                        completed_users.append(user_id)
                
                for user_id in completed_users:
                    try:
                        success, result = data_manager.complete_mining(user_id)
                        if success:
                            player = data_manager.players.get(user_id)
                            if player and player.mining_notifications:
                                await self.queue_notification(
                                    user_id,
                                    self.text_templates.mining_result(result)
                                )
                        await asyncio.sleep(BATCH_SEND_DELAY)
                    except Exception:
                        pass
                
                await asyncio.sleep(0.5)
                
            except Exception:
                await asyncio.sleep(5)

    async def check_auto_mining(self):
        while True:
            try:
                if not data_manager:
                    await asyncio.sleep(1)
                    continue
                current_time = datetime.now()
                
                for user_id, auto_session in list(data_manager.auto_mining_sessions.items()):
                    if auto_session.is_active and auto_session.next_mine_time and current_time >= auto_session.next_mine_time:
                        try:
                            player = data_manager.players.get(user_id)
                            if player and not player.is_banned:
                                success, result = data_manager.process_auto_mining(user_id)
                                if success and result.get('total_mineral', 0) > 0:
                                    if player.mining_notifications:
                                        await self.queue_notification(
                                            user_id,
                                            self.text_templates.auto_mining_result(result)
                                        )
                                await asyncio.sleep(BATCH_SEND_DELAY)
                        except Exception:
                            pass
                
                await asyncio.sleep(10)
                
            except Exception:
                await asyncio.sleep(30)

    async def cleanup_states(self):
        while True:
            try:
                current_time = time.time()
                to_delete = []
                
                for user_id, state in self.user_states.items():
                    if "timestamp" in state and current_time - state["timestamp"] > 1800:
                        to_delete.append(user_id)
                
                for user_id in to_delete:
                    del self.user_states[user_id]
                
                await asyncio.sleep(300)
                
            except Exception:
                await asyncio.sleep(60)

    async def cleanup_cooldowns(self):
        while True:
            try:
                await asyncio.sleep(1800)
                current_time = time.time()
                
                for user_id in list(self.user_cooldowns.keys()):
                    to_remove = []
                    for action, timestamp in self.user_cooldowns[user_id].items():
                        if current_time - timestamp > 3600:
                            to_remove.append(action)
                    
                    for action in to_remove:
                        del self.user_cooldowns[user_id][action]
                    
                    if not self.user_cooldowns[user_id]:
                        del self.user_cooldowns[user_id]
                        
            except Exception:
                pass

    async def cleanup_rate_limits(self):
        while True:
            try:
                await asyncio.sleep(300)
                current_time = time.time()
                
                async with self._rate_limit_lock:
                    for user_id in list(self.user_rate_limits.keys()):
                        timestamps = self.user_rate_limits[user_id]
                        timestamps = [t for t in timestamps if current_time - t < RATE_LIMIT_WINDOW]
                        
                        if timestamps:
                            self.user_rate_limits[user_id] = timestamps
                        else:
                            del self.user_rate_limits[user_id]
                            
            except Exception:
                pass

    async def memory_cleanup(self):
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL)
                
                if data_manager:
                    data_manager.cleanup_old_data()
                
                await self.keyboard_manager._cache.clear()
                await self.donate_keyboards._cache.clear()
                self.keyboard_manager._menu_cache.clear()
                self.donate_keyboards._menu_cache.clear()
                
                gc.collect()
                
            except Exception:
                pass

    async def periodic_cache_cleanup(self):
        while True:
            try:
                await asyncio.sleep(600)
                
                await self.keyboard_manager._cache.clear()
                await self.donate_keyboards._cache.clear()
                self.keyboard_manager._menu_cache.clear()
                self.donate_keyboards._menu_cache.clear()
                
                if data_manager:
                    current_time = time.time()
                    for user_id in list(data_manager._player_last_access.keys()):
                        if current_time - data_manager._player_last_access[user_id] > 86400:
                            del data_manager._player_last_access[user_id]
                        
            except Exception:
                pass

async def main():
    try:
        bot = MinerichBot(BOT_TOKEN)
        await bot.run()
    except KeyboardInterrupt:
        if data_manager:
            data_manager.save_data()
    except Exception:
        if data_manager:
            data_manager.save_data()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if data_manager:
            data_manager.save_data()
