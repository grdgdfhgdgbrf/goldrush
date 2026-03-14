import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, LabeledPrice, PreCheckoutQuery,
    SuccessfulPayment
)
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import os

# ========== НАСТРОЙКИ ==========
ADMIN_ID = 5356400377
ADMIN_USERNAME = "@hjklgf1"
BOT_TOKEN = "8269087933:AAE-lRMxUUdZJ3R085BUlbji6G0Rjoq7Hhg"
GAME_NAME = "⛏️ The Gold Rush"
MINING_BASE_TIME = 240  # Уменьшено для быстрой игры
GAME_CURRENCY = "🪙 Золотые слитки"
VERSION = "1.0.0"

# ========== МОДЕЛИ ДАННЫХ ==========

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

class UpgradeType(Enum):
    MINER_LEVEL = "👷 Уровень шахтёра"
    MINING_POWER = "💪 Сила удара"
    MINING_SPEED = "⚡ Скорость копания"
    MINING_TIME = "⏱️ Длительность смены"
    LUCK = "🍀 Удача старателя"
    ENERGY_EFF = "🔋 Энергоэффективность"
    MULTI_MINING = "🔄 Мультишахта"
    AUTO_MINING = "🤖 Автодобыча"
    CASE_CHANCE = "🎁 Шанс ящиков"

class ItemRarity(Enum):
    COMMON = "Обычный"
    RARE = "Редкий"
    EPIC = "Эпический"
    LEGENDARY = "Легендарный"
    MYTHIC = "Мифический"

class ItemType(Enum):
    MINING_TOOL = "⛏️ Кирка"
    LUCK_CHARM = "🍀 Талисман"
    MINERAL_CHIP = "💿 Чип анализатора"
    ENERGY_CORE = "🔋 Ядро реактора"
    FUEL = "⛽ Топливо"
    CASE = "📦 Ящик"
    BOOSTER = "🚀 Бустер"
    COLLECTIBLE = "🏆 Сувенир"

class CaseType(Enum):
    COMMON = "📦 Обычный ящик"
    RARE = "🎁 Редкий ящик"
    EPIC = "💎 Эпический ящик"
    LEGENDARY = "👑 Легендарный ящик"
    MYTHIC = "✨ Мифический ящик"

class CollectibleType(Enum):
    NUGGET = "🥨 Самородок"
    FOSSIL = "🦴 Окаменелость"
    GEODE = "🥚 Жеода"
    CRYSTAL = "🔮 Кристалл"
    METEORITE = "🌠 Метеорит"
    GEMSTONE = "💎 Драгоценный камень"
    ANCIENT_RELIC = "🏺 Древний артефакт"
    MINERAL_EGG = "🥚 Минеральное яйцо"

@dataclass
class Channel:
    id: str
    name: str
    url: str
    required_level: int
    reward: int
    is_active: bool = True
    bot_member: bool = False

@dataclass
class MiningSession:
    user_id: int
    mineral: MineralType
    start_time: datetime
    end_time: datetime
    active: bool = True
    base_reward: float = 0
    bonus_multiplier: float = 1.0

@dataclass
class AutoMiningSession:
    user_id: int
    minerals: List[MineralType]
    is_active: bool = True
    last_mine_time: Optional[datetime] = None
    interval_minutes: int = 180  # Каждые 3 часа
    next_mine_time: Optional[datetime] = None
    fuel_left: int = 0

@dataclass
class Upgrade:
    upgrade_type: UpgradeType
    level: int = 0
    base_price: int = 80  # Уменьшена базовая цена
    price_multiplier: float = 1.4
    effect_per_level: float = 0.08
    max_level: int = 80
    description: str = ""
    
    @property
    def current_price(self) -> int:
        return int(self.base_price * (self.price_multiplier ** self.level))
    
    @property
    def current_effect(self) -> float:
        return self.effect_per_level * self.level

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

@dataclass
class Case:
    case_id: str
    case_type: CaseType
    name: str
    description: str
    price: int
    min_items: int = 1
    max_items: int = 3
    drop_chances: Dict[str, float] = field(default_factory=dict)
    collectible_chance: float = 0.008

@dataclass
class MarketOffer:
    offer_id: str
    item_id: str
    seller_id: int
    seller_name: str
    price: int
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Player:
    user_id: int
    username: str
    first_name: str
    mineral_balance: Dict[str, float] = field(default_factory=dict)
    gold_balance: int = 0  # Золотые слитки (внутренняя валюта)
    miner_level: int = 1
    experience: int = 0
    total_experience: int = 0
    upgrades: Dict[str, Upgrade] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    equipped_items: Dict[str, str] = field(default_factory=dict)
    mining_sessions: List[MiningSession] = field(default_factory=list)
    unlocked_minerals: List[str] = field(default_factory=list)
    subscribed_channels: List[str] = field(default_factory=list)
    last_mining_time: Optional[datetime] = None
    total_mined: float = 0
    total_gold_earned: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    stats: Dict[str, Any] = field(default_factory=lambda: {
        "cases_opened": 0,
        "items_found": 0,
        "trades_completed": 0,
        "total_play_time": 0,
        "upgrades_bought": 0,
        "minerals_mined": 0,
        "collectibles_found": 0,
        "auto_mines": 0
    })
    auto_mining_enabled: bool = False
    auto_mining_minerals: List[str] = field(default_factory=list)
    collectibles: Dict[str, int] = field(default_factory=dict)
    fuel: int = 0
    
    def __post_init__(self):
        for mineral in MineralType:
            if mineral.name not in self.mineral_balance:
                self.mineral_balance[mineral.name] = 0.0

        upgrade_configs = {
            UpgradeType.MINER_LEVEL: Upgrade(
                upgrade_type=UpgradeType.MINER_LEVEL,
                base_price=400,
                effect_per_level=0.15,
                description="Базовый уровень шахтёра. Увеличивает все характеристики"
                ),
            UpgradeType.MINING_POWER: Upgrade(
                upgrade_type=UpgradeType.MINING_POWER,
                description="Увеличивает количество добываемой руды"
                ),
            UpgradeType.MINING_SPEED: Upgrade(
                upgrade_type=UpgradeType.MINING_SPEED,
                description="Уменьшает время добычи"
                ),
            UpgradeType.MINING_TIME: Upgrade(
                upgrade_type=UpgradeType.MINING_TIME,
                base_price=180,
                effect_per_level=3,
                description="Увеличивает длительность смены (+3 минуты за уровень)"
                ),
            UpgradeType.LUCK: Upgrade(
                upgrade_type=UpgradeType.LUCK,
                description="Увеличивает шанс найти сувениры и ящики"
                ),
            UpgradeType.ENERGY_EFF: Upgrade(
                upgrade_type=UpgradeType.ENERGY_EFF,
                description="Увеличивает эффективность переработки"
                ),
            UpgradeType.MULTI_MINING: Upgrade(
                upgrade_type=UpgradeType.MULTI_MINING,
                base_price=180,
                description="Позволяет добывать несколько ископаемых"
                ),
            UpgradeType.AUTO_MINING: Upgrade(
                upgrade_type=UpgradeType.AUTO_MINING,
                base_price=4000,
                effect_per_level=0.04,
                description="Позволяет использовать автодобычу"
                ),
            UpgradeType.CASE_CHANCE: Upgrade(
                upgrade_type=UpgradeType.CASE_CHANCE,
                base_price=120,
                effect_per_level=0.015,
                description="Увеличивает шанс выпадения ящиков"
            )
        }

        for upgrade_type in UpgradeType:
            if upgrade_type.name not in self.upgrades:
                if upgrade_type in upgrade_configs:
                    self.upgrades[upgrade_type.name] = upgrade_configs[upgrade_type]
                else:
                    self.upgrades[upgrade_type.name] = Upgrade(upgrade_type=upgrade_type)

        self.upgrades[UpgradeType.MINER_LEVEL.name].level = self.miner_level

        if not self.unlocked_minerals:
            self.unlocked_minerals.append(MineralType.COAL.name)
            self.unlocked_minerals.append(MineralType.IRON.name)
            self.unlocked_minerals.append(MineralType.COPPER.name)

        for collectible_type in CollectibleType:
            if collectible_type.name not in self.collectibles:
                self.collectibles[collectible_type.name] = 0
    
    def get_total_mineral_value(self) -> float:
        # Базовая стоимость в золотых слитках (приблизительная)
        base_values = {
            "COAL": 0.2,
            "IRON": 0.5,
            "COPPER": 0.8,
            "ALUMINUM": 1.0,
            "ZINC": 1.2,
            "TIN": 1.5,
            "LEAD": 1.0,
            "NICKEL": 2.0,
            "SILVER": 5.0,
            "GOLD": 20.0,
            "PLATINUM": 30.0,
            "TITANIUM": 10.0,
            "URANIUM": 25.0,
            "DIAMOND": 50.0,
            "RUBY": 15.0,
            "SAPPHIRE": 12.0,
            "EMERALD": 18.0,
            "OBSIDIAN": 3.0,
            "COBALT": 4.0,
            "LITHIUM": 2.5,
            "CHROMIUM": 3.5,
            "MANGANESE": 2.0,
            "TUNGSTEN": 8.0,
            "PALLADIUM": 40.0,
            "RHODIUM": 60.0,
            "OSMIUM": 35.0,
            "IRIDIUM": 45.0,
            "PROMETHIUM": 100.0
        }
        
        total = 0.0
        for mineral_name, amount in self.mineral_balance.items():
            total += amount * base_values.get(mineral_name, 0.0)
        return total
    
    def get_mining_power(self) -> float:
        base_power = 1.0
        miner_upgrade = self.upgrades.get(UpgradeType.MINER_LEVEL.name)
        if miner_upgrade:
            base_power *= (1 + miner_upgrade.current_effect)
        power_upgrade = self.upgrades.get(UpgradeType.MINING_POWER.name)
        if power_upgrade:
            base_power *= (1 + power_upgrade.current_effect)
        return base_power

# ========== КЛАВИАТУРЫ ДЛЯ ДОНАТОВ ==========

class DonateKeyboards:
    @staticmethod
    def donate_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="⭐ 1 Звезда (80 🪙)", callback_data="donate_1")
        builder.button(text="⭐ 5 Звезд (400 🪙)", callback_data="donate_5")
        builder.button(text="⭐ 10 Звезд (850 🪙)", callback_data="donate_10")
        builder.button(text="⭐ 20 Звезд (1800 🪙)", callback_data="donate_20")
        builder.button(text="⭐ 50 Звезд (4500 🪙)", callback_data="donate_50")
        builder.button(text="⭐ 100 Звезд (9000 🪙)", callback_data="donate_100")
        builder.button(text="🎁 Спецпредложения", callback_data="donate_special")
        builder.button(text="❓ Помощь", callback_data="donate_help")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def special_donates() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🪨 Стартовый набор: 50 ⭐ (5000 🪙)", callback_data="donate_starter")
        builder.button(text="⚡ Промышленный набор: 100 ⭐ (12000 🪙)", callback_data="donate_business")
        builder.button(text="👑 Магнатский набор: 200 ⭐ (30000 🪙)", callback_data="donate_premium")
        builder.button(text="🤖 Автодобыча: 50 ⭐ + топливо", callback_data="donate_auto")
        builder.button(text="🏺 Коллекционный набор: 100 ⭐", callback_data="donate_collection")
        builder.button(text="⬅️ Назад", callback_data="donate")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def confirm_donation(stars: int, gold: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=f"✅ Оплатить {stars} ⭐", callback_data=f"confirm_donate_{stars}")
        builder.button(text="❌ Отмена", callback_data="donate")
        return builder.as_markup()
    
    @staticmethod
    def payment_keyboard(stars: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=f"💳 Оплатить {stars} ⭐", pay=True)
        builder.button(text="❌ Отмена", callback_data="donate")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def donate_thank_you() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Магазин", callback_data="shop")
        builder.button(text="🤖 Автодобыча", callback_data="auto_mining")
        builder.button(text="📦 Ящики", callback_data="cases")
        builder.button(text="⬅️ Главное меню", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

# ========== МЕНЕДЖЕРЫ ДАННЫХ ==========

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
        self.load_data()
        self.initialize_game_data()
    
    async def check_bot_in_channel(self, channel_url: str) -> bool:
        try:
            if "t.me/" in channel_url:
                username = channel_url.split("t.me/")[-1].replace("@", "")
                if username:
                    try:
                        chat = await self.bot.get_chat(f"@{username}")
                        member = await self.bot.get_chat_member(chat.id, self.bot.id)
                        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                            return True
                    except:
                        return False
            return False
        except:
            return False
    
    def save_data(self):
        try:
            data = {
                'players': {},
                'channels': {},
                'items': {},
                'cases': {},
                'market_offers': {},
                'active_mining_sessions': {},
                'auto_mining_sessions': {},
                'version': VERSION,
                'last_save': datetime.now().isoformat()
            }
            
            for user_id, player in self.players.items():
                data['players'][str(user_id)] = self._serialize_player(player)
            
            for channel_id, channel in self.channels.items():
                data['channels'][channel_id] = self._serialize_channel(channel)
            
            for item_id, item in self.items.items():
                data['items'][item_id] = self._serialize_item(item)
            
            for case_id, case in self.cases.items():
                data['cases'][case_id] = self._serialize_case(case)
            
            for offer_id, offer in self.market_offers.items():
                data['market_offers'][offer_id] = self._serialize_market_offer(offer)
            
            for user_id, session in self.active_mining_sessions.items():
                data['active_mining_sessions'][str(user_id)] = {
                    'user_id': session.user_id,
                    'mineral': session.mineral.name,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat(),
                    'active': session.active,
                    'base_reward': float(session.base_reward),
                    'bonus_multiplier': float(session.bonus_multiplier)
                }
            
            for user_id, auto_session in self.auto_mining_sessions.items():
                data['auto_mining_sessions'][str(user_id)] = {
                    'user_id': auto_session.user_id,
                    'minerals': [m.name for m in auto_session.minerals],
                    'is_active': auto_session.is_active,
                    'interval_minutes': auto_session.interval_minutes,
                    'fuel_left': auto_session.fuel_left
                }
                if auto_session.last_mine_time:
                    data['auto_mining_sessions'][str(user_id)]['last_mine_time'] = auto_session.last_mine_time.isoformat()
                if auto_session.next_mine_time:
                    data['auto_mining_sessions'][str(user_id)]['next_mine_time'] = auto_session.next_mine_time.isoformat()
            
            with open('minerich_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        except:
            pass
    
    def _serialize_player(self, player: Player) -> Dict:
        player_dict = {
            'user_id': player.user_id,
            'username': player.username,
            'first_name': player.first_name,
            'mineral_balance': {k: float(v) for k, v in player.mineral_balance.items()},
            'gold_balance': player.gold_balance,
            'miner_level': player.miner_level,
            'experience': player.experience,
            'total_experience': player.total_experience,
            'upgrades': {},
            'inventory': player.inventory.copy(),
            'equipped_items': player.equipped_items.copy(),
            'unlocked_minerals': player.unlocked_minerals.copy(),
            'subscribed_channels': player.subscribed_channels.copy(),
            'total_mined': float(player.total_mined),
            'total_gold_earned': player.total_gold_earned,
            'stats': player.stats.copy(),
            'auto_mining_enabled': player.auto_mining_enabled,
            'auto_mining_minerals': player.auto_mining_minerals.copy(),
            'collectibles': player.collectibles.copy(),
            'fuel': player.fuel
        }
        
        for upgrade_name, upgrade in player.upgrades.items():
            player_dict['upgrades'][upgrade_name] = {
                'upgrade_type': upgrade.upgrade_type.value,
                'level': upgrade.level,
                'base_price': upgrade.base_price,
                'price_multiplier': upgrade.price_multiplier,
                'effect_per_level': upgrade.effect_per_level,
                'max_level': upgrade.max_level,
                'description': upgrade.description
            }
        
        if player.created_at:
            player_dict['created_at'] = player.created_at.isoformat()
        if player.last_mining_time:
            player_dict['last_mining_time'] = player.last_mining_time.isoformat()
        
        return player_dict
    
    def _deserialize_player(self, player_data: Dict) -> Player:
        user_id = player_data['user_id']
        username = player_data.get('username', '')
        first_name = player_data.get('first_name', 'Шахтёр')
        
        upgrades_dict = {}
        for upgrade_name, upgrade_data in player_data.get('upgrades', {}).items():
            try:
                upgrade_type = None
                for ut in UpgradeType:
                    if ut.value == upgrade_data.get('upgrade_type'):
                        upgrade_type = ut
                        break
                
                if upgrade_type:
                    upgrade = Upgrade(
                        upgrade_type=upgrade_type,
                        level=upgrade_data.get('level', 0),
                        base_price=upgrade_data.get('base_price', 80),
                        price_multiplier=upgrade_data.get('price_multiplier', 1.4),
                        effect_per_level=upgrade_data.get('effect_per_level', 0.08),
                        max_level=upgrade_data.get('max_level', 80),
                        description=upgrade_data.get('description', '')
                    )
                    upgrades_dict[upgrade_type.name] = upgrade
            except:
                continue
        
        player = Player(
            user_id=user_id,
            username=username,
            first_name=first_name,
            mineral_balance=player_data.get('mineral_balance', {}),
            gold_balance=player_data.get('gold_balance', 0),
            miner_level=player_data.get('miner_level', 1),
            experience=player_data.get('experience', 0),
            total_experience=player_data.get('total_experience', 0),
            upgrades=upgrades_dict,
            inventory=player_data.get('inventory', []),
            equipped_items=player_data.get('equipped_items', {}),
            unlocked_minerals=player_data.get('unlocked_minerals', []),
            subscribed_channels=player_data.get('subscribed_channels', []),
            total_mined=player_data.get('total_mined', 0.0),
            total_gold_earned=player_data.get('total_gold_earned', 0),
            stats=player_data.get('stats', {}),
            auto_mining_enabled=player_data.get('auto_mining_enabled', False),
            auto_mining_minerals=player_data.get('auto_mining_minerals', []),
            collectibles=player_data.get('collectibles', {}),
            fuel=player_data.get('fuel', 0)
        )
        
        if player_data.get('created_at'):
            try:
                player.created_at = datetime.fromisoformat(player_data['created_at'])
            except:
                player.created_at = datetime.now()
        
        if player_data.get('last_mining_time'):
            try:
                player.last_mining_time = datetime.fromisoformat(player_data['last_mining_time'])
            except:
                player.last_mining_time = None
        
        return player
    
    def _serialize_item(self, item: Item) -> Dict:
        item_dict = {
            'item_id': item.item_id,
            'serial_number': item.serial_number,
            'name': item.name,
            'item_type': item.item_type.value,
            'rarity': item.rarity.value,
            'description': item.description,
            'mining_bonus': float(item.mining_bonus),
            'luck_bonus': float(item.luck_bonus),
            'energy_bonus': float(item.energy_bonus),
            'buy_price': item.buy_price,
            'sell_price': item.sell_price,
            'is_tradable': item.is_tradable,
            'owner_id': item.owner_id,
            'is_collectible': item.is_collectible,
            'fuel_amount': item.fuel_amount
        }
        
        if item.collectible_type:
            item_dict['collectible_type'] = item.collectible_type.value
        
        item_dict['created_at'] = item.created_at.isoformat()
        return item_dict
    
    def _deserialize_item(self, item_data: Dict) -> Item:
        item_type = None
        for it in ItemType:
            if it.value == item_data.get('item_type'):
                item_type = it
                break
        
        rarity = None
        for r in ItemRarity:
            if r.value == item_data.get('rarity'):
                rarity = r
                break
        
        collectible_type = None
        if item_data.get('collectible_type'):
            for ct in CollectibleType:
                if ct.value == item_data['collectible_type']:
                    collectible_type = ct
                    break
        
        created_at = datetime.now()
        if item_data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(item_data['created_at'])
            except:
                pass
        
        item = Item(
            item_id=item_data['item_id'],
            serial_number=item_data.get('serial_number', '00000'),
            name=item_data['name'],
            item_type=item_type,
            rarity=rarity,
            description=item_data['description'],
            mining_bonus=item_data.get('mining_bonus', 1.0),
            luck_bonus=item_data.get('luck_bonus', 0.0),
            energy_bonus=item_data.get('energy_bonus', 0.0),
            buy_price=item_data.get('buy_price', 0),
            sell_price=item_data.get('sell_price', 0),
            is_tradable=item_data.get('is_tradable', True),
            owner_id=item_data.get('owner_id'),
            created_at=created_at,
            collectible_type=collectible_type,
            is_collectible=item_data.get('is_collectible', False),
            fuel_amount=item_data.get('fuel_amount', 0)
        )
        
        return item
    
    def _serialize_case(self, case: Case) -> Dict:
        case_dict = {
            'case_id': case.case_id,
            'case_type': case.case_type.value,
            'name': case.name,
            'description': case.description,
            'price': case.price,
            'min_items': case.min_items,
            'max_items': case.max_items,
            'drop_chances': case.drop_chances.copy(),
            'collectible_chance': float(case.collectible_chance)
        }
        return case_dict
    
    def _deserialize_case(self, case_data: Dict) -> Case:
        case_type = None
        for ct in CaseType:
            if ct.value == case_data.get('case_type'):
                case_type = ct
                break
        
        case = Case(
            case_id=case_data['case_id'],
            case_type=case_type,
            name=case_data['name'],
            description=case_data['description'],
            price=case_data['price'],
            min_items=case_data.get('min_items', 1),
            max_items=case_data.get('max_items', 3),
            drop_chances=case_data.get('drop_chances', {}),
            collectible_chance=case_data.get('collectible_chance', 0.008)
        )
        
        return case
    
    def _serialize_channel(self, channel: Channel) -> Dict:
        return {
            'id': channel.id,
            'name': channel.name,
            'url': channel.url,
            'required_level': channel.required_level,
            'reward': channel.reward,
            'is_active': channel.is_active,
            'bot_member': channel.bot_member
        }
    
    def _deserialize_channel(self, channel_data: Dict) -> Channel:
        channel = Channel(
            id=channel_data['id'],
            name=channel_data['name'],
            url=channel_data['url'],
            required_level=channel_data['required_level'],
            reward=channel_data['reward'],
            is_active=channel_data.get('is_active', True),
            bot_member=channel_data.get('bot_member', False)
        )
        
        return channel
    
    def _serialize_market_offer(self, offer: MarketOffer) -> Dict:
        return {
            'offer_id': offer.offer_id,
            'item_id': offer.item_id,
            'seller_id': offer.seller_id,
            'seller_name': offer.seller_name,
            'price': offer.price,
            'created_at': offer.created_at.isoformat()
        }
    
    def _deserialize_market_offer(self, offer_data: Dict) -> MarketOffer:
        created_at = datetime.now()
        if offer_data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(offer_data['created_at'])
            except:
                pass
        
        offer = MarketOffer(
            offer_id=offer_data['offer_id'],
            item_id=offer_data['item_id'],
            seller_id=offer_data['seller_id'],
            seller_name=offer_data['seller_name'],
            price=offer_data['price'],
            created_at=created_at
        )
        
        return offer
    
    def _deserialize_mining_session(self, session_data: Dict) -> MiningSession:
        mineral = None
        for m in MineralType:
            if m.name == session_data['mineral']:
                mineral = m
                break
        
        start_time = datetime.fromisoformat(session_data['start_time'])
        end_time = datetime.fromisoformat(session_data['end_time'])
        
        session = MiningSession(
            user_id=session_data['user_id'],
            mineral=mineral,
            start_time=start_time,
            end_time=end_time,
            active=session_data.get('active', True),
            base_reward=session_data.get('base_reward', 0),
            bonus_multiplier=session_data.get('bonus_multiplier', 1.0)
        )
        
        return session
    
    def _deserialize_auto_mining_session(self, auto_data: Dict) -> AutoMiningSession:
        minerals = []
        for mineral_name in auto_data.get('minerals', []):
            for m in MineralType:
                if m.name == mineral_name:
                    minerals.append(m)
                    break
        
        auto_session = AutoMiningSession(
            user_id=auto_data['user_id'],
            minerals=minerals,
            is_active=auto_data.get('is_active', True),
            interval_minutes=auto_data.get('interval_minutes', 180),
            fuel_left=auto_data.get('fuel_left', 0)
        )
        
        if auto_data.get('last_mine_time'):
            try:
                auto_session.last_mine_time = datetime.fromisoformat(auto_data['last_mine_time'])
            except:
                pass
        
        if auto_data.get('next_mine_time'):
            try:
                auto_session.next_mine_time = datetime.fromisoformat(auto_data['next_mine_time'])
            except:
                auto_session.next_mine_time = datetime.now() + timedelta(minutes=auto_session.interval_minutes)
        else:
            auto_session.next_mine_time = datetime.now() + timedelta(minutes=auto_session.interval_minutes)
        
        return auto_session
    
    def load_data(self):
        try:
            if not os.path.exists('minerich_data.json'):
                self.initialize_game_data()
                return
            
            with open('minerich_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for user_id_str, player_data in data.get('players', {}).items():
                    try:
                        player = self._deserialize_player(player_data)
                        self.players[player.user_id] = player
                    except:
                        continue
                
                for channel_id, channel_data in data.get('channels', {}).items():
                    try:
                        channel = self._deserialize_channel(channel_data)
                        self.channels[channel_id] = channel
                    except:
                        continue
                
                for item_id, item_data in data.get('items', {}).items():
                    try:
                        item = self._deserialize_item(item_data)
                        self.items[item_id] = item
                    except:
                        continue
                
                for case_id, case_data in data.get('cases', {}).items():
                    try:
                        case = self._deserialize_case(case_data)
                        self.cases[case_id] = case
                    except:
                        continue
                
                for offer_id, offer_data in data.get('market_offers', {}).items():
                    try:
                        offer = self._deserialize_market_offer(offer_data)
                        self.market_offers[offer_id] = offer
                    except:
                        continue
                
                for user_id_str, session_data in data.get('active_mining_sessions', {}).items():
                    try:
                        user_id = int(user_id_str)
                        session = self._deserialize_mining_session(session_data)
                        
                        if datetime.now() < session.end_time:
                            self.active_mining_sessions[user_id] = session
                        else:
                            if user_id in self.players:
                                self.complete_mining(user_id)
                    except:
                        continue
                
                for user_id_str, auto_data in data.get('auto_mining_sessions', {}).items():
                    try:
                        user_id = int(user_id_str)
                        auto_session = self._deserialize_auto_mining_session(auto_data)
                        
                        if user_id in self.players:
                            self.auto_mining_sessions[user_id] = auto_session
                            self.players[user_id].auto_mining_enabled = auto_session.is_active
                    except:
                        continue
                
        except:
            self.initialize_game_data()
    
    def generate_serial_number(self) -> str:
        return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5))
    
    def initialize_game_data(self):
        if not self.channels:
            self.channels = {
                "main": Channel(
                    id="main",
                    name="📢 Главный канал шахтёров",
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
                    description="Шанс получить обычные инструменты",
                    price=400,
                    min_items=1,
                    max_items=2,
                    drop_chances={
                        "Обычный": 0.7,
                        "Редкий": 0.25,
                        "Эпический": 0.05
                    },
                    collectible_chance=0.004
                ),
                "rare_case": Case(
                    case_id="rare_case",
                    case_type=CaseType.RARE,
                    name="🎁 Редкий ящик",
                    description="Шанс получить редкие инструменты",
                    price=1500,
                    min_items=1,
                    max_items=3,
                    drop_chances={
                        "Обычный": 0.5,
                        "Редкий": 0.35,
                        "Эпический": 0.12,
                        "Легендарный": 0.03
                    },
                    collectible_chance=0.008
                ),
                "epic_case": Case(
                    case_id="epic_case",
                    case_type=CaseType.EPIC,
                    name="💎 Эпический ящик",
                    description="Шанс получить эпические инструменты",
                    price=8000,
                    min_items=2,
                    max_items=4,
                    drop_chances={
                        "Редкий": 0.4,
                        "Эпический": 0.4,
                        "Легендарный": 0.15,
                        "Мифический": 0.05
                    },
                    collectible_chance=0.015
                ),
                "legendary_case": Case(
                    case_id="legendary_case",
                    case_type=CaseType.LEGENDARY,
                    name="👑 Легендарный ящик",
                    description="Шанс получить легендарные инструменты",
                    price=40000,
                    min_items=3,
                    max_items=5,
                    drop_chances={
                        "Эпический": 0.3,
                        "Легендарный": 0.5,
                        "Мифический": 0.2
                    },
                    collectible_chance=0.04
                ),
                "mythic_case": Case(
                    case_id="mythic_case",
                    case_type=CaseType.MYTHIC,
                    name="✨ Мифический ящик",
                    description="Шанс получить мифические инструменты",
                    price=80000,
                    min_items=3,
                    max_items=5,
                    drop_chances={
                        "Легендарный": 0.5,
                        "Мифический": 0.5
                    },
                    collectible_chance=0.08
                )
            }
        
        self.create_initial_items()
        self.save_data()
    
    def create_initial_items(self):
        mining_tools = [
            ("⛏️ Кайло новичка", "Базовый инструмент", 1.05, 800, ItemRarity.COMMON),
            ("⚒️ Отбойник старателя", "Прочный инструмент", 1.15, 2500, ItemRarity.RARE),
            ("🔨 Молот горняка", "Мощный инструмент", 1.3, 6000, ItemRarity.EPIC),
            ("💎 Алмазный бур", "Элитный инструмент", 1.5, 15000, ItemRarity.LEGENDARY),
            ("🔥 Плазменный резак", "Высокотехнологичный", 1.8, 40000, ItemRarity.MYTHIC),
        ]
        
        for name, desc, bonus, price, rarity in mining_tools:
            item_id = str(uuid.uuid4())
            self.items[item_id] = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=name,
                item_type=ItemType.MINING_TOOL,
                rarity=rarity,
                description=desc,
                mining_bonus=bonus,
                buy_price=price,
                sell_price=int(price * 0.6),
                is_tradable=True
            )
        
        luck_charms = [
            ("🍀 Перо удачи", "Приносит удачу", 0.04, 1500, ItemRarity.COMMON),
            ("🐚 Раковина счастья", "Старинный талисман", 0.08, 5000, ItemRarity.RARE),
            ("💫 Звезда старателя", "Привлекает удачу", 0.15, 12000, ItemRarity.EPIC),
            ("🌙 Лунный камень", "Исполняет желания", 0.25, 35000, ItemRarity.LEGENDARY),
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
            ("⛽ Угольные брикеты", "60 минут автодобычи", 60, 800, ItemRarity.COMMON),
            ("🔥 Нефтяное топливо", "180 минут автодобычи", 180, 2000, ItemRarity.RARE),
            ("⚡ Энергетические стержни", "300 минут автодобычи", 300, 4000, ItemRarity.EPIC),
            ("🚀 Плутониевый реактор", "600 минут автодобычи", 600, 8000, ItemRarity.LEGENDARY),
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
                ("🥨 Золотой самородок", "Чистое золото, найденное в ручье", ItemRarity.RARE, 4000),
                ("🥨 Платиновый самородок", "Редкая находка для коллекции", ItemRarity.EPIC, 8000),
                ("🥨 Самородок палладия", "Исключительно редкий минерал", ItemRarity.LEGENDARY, 20000),
            ],
            CollectibleType.FOSSIL: [
                ("🦴 Аммонит", "Окаменелая раковина древнего моллюска", ItemRarity.COMMON, 2500),
                ("🦴 Трилобит", "Окаменелость членистоногого", ItemRarity.RARE, 5000),
                ("🦴 Зубы мегалодона", "Зубы древней акулы", ItemRarity.EPIC, 10000),
            ],
            CollectibleType.GEODE: [
                ("🥚 Агатовая жеода", "Полый камень с кристаллами внутри", ItemRarity.COMMON, 1500),
                ("🥚 Кварцевая жеода", "Красивый минеральный агрегат", ItemRarity.RARE, 3000),
                ("🥚 Аметистовая жеода", "Драгоценная жеода с фиолетовыми кристаллами", ItemRarity.EPIC, 6000),
            ],
            CollectibleType.CRYSTAL: [
                ("🔮 Кварц", "Прозрачный кристалл", ItemRarity.COMMON, 1000),
                ("🔮 Аметист", "Фиолетовый кристалл", ItemRarity.RARE, 2500),
                ("🔮 Топаз", "Золотистый драгоценный камень", ItemRarity.EPIC, 5000),
            ],
            CollectibleType.METEORITE: [
                ("🌠 Каменный метеорит", "Упал из космоса", ItemRarity.RARE, 6000),
                ("🌠 Железный метеорит", "Содержит редкие металлы", ItemRarity.EPIC, 12000),
                ("🌠 Углистый метеорит", "Содержит органику", ItemRarity.LEGENDARY, 25000),
            ],
            CollectibleType.GEMSTONE: [
                ("💎 Рубин", "Красный драгоценный камень", ItemRarity.RARE, 5000),
                ("💎 Сапфир", "Синий драгоценный камень", ItemRarity.EPIC, 10000),
                ("💎 Изумруд", "Зелёный драгоценный камень", ItemRarity.LEGENDARY, 20000),
            ],
            CollectibleType.ANCIENT_RELIC: [
                ("🏺 Древняя кирка", "Инструмент древних шахтёров", ItemRarity.EPIC, 8000),
                ("🏺 Каменная табличка", "С письменами", ItemRarity.LEGENDARY, 15000),
                ("🏺 Статуэтка божества", "Почиталось шахтёрами", ItemRarity.MYTHIC, 35000),
            ],
            CollectibleType.MINERAL_EGG: [
                ("🥚 Минеральное яйцо", "Загадочное образование", ItemRarity.RARE, 3000),
                ("🥚 Яйцо дракона (миф)", "Легендарный артефакт", ItemRarity.LEGENDARY, 12000),
                ("🥚 Яйцо Феникса", "Редчайшая находка", ItemRarity.MYTHIC, 30000),
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
    
    def get_or_create_player(self, user_id: int, username: str, first_name: str) -> Player:
        if user_id not in self.players:
            player = Player(
                user_id=user_id,
                username=username or "",
                first_name=first_name or "Шахтёр"
            )
            self.players[user_id] = player
            self.save_data()
        
        return self.players[user_id]
    
    def start_mining(self, user_id: int, mineral_name: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        try:
            mineral = None
            for m in MineralType:
                if m.name == mineral_name:
                    mineral = m
                    break
            
            if not mineral:
                return False, "Ископаемое не найдено"
        except:
            return False, "Ископаемое не найдено"
        
        if mineral_name not in player.unlocked_minerals:
            return False, f"Ископаемое {mineral.value} ещё не разблокировано"
        
        if user_id in self.active_mining_sessions:
            session = self.active_mining_sessions[user_id]
            if session.active:
                return False, "mining_status"
        
        # Базовое время зависит от ценности ископаемого
        time_multipliers = {
            "COAL": 0.5, "IRON": 0.6, "COPPER": 0.6, "ALUMINUM": 0.6, "ZINC": 0.7,
            "TIN": 0.6, "LEAD": 0.6, "NICKEL": 0.8, "SILVER": 1.0, "GOLD": 1.2,
            "PLATINUM": 1.3, "TITANIUM": 1.1, "URANIUM": 1.5, "DIAMOND": 1.6,
            "RUBY": 1.2, "SAPPHIRE": 1.2, "EMERALD": 1.3, "OBSIDIAN": 0.9,
            "COBALT": 1.0, "LITHIUM": 0.9, "CHROMIUM": 1.0, "MANGANESE": 0.8,
            "TUNGSTEN": 1.1, "PALLADIUM": 1.4, "RHODIUM": 1.5, "OSMIUM": 1.3,
            "IRIDIUM": 1.4, "PROMETHIUM": 2.0
        }
        
        base_time = MINING_BASE_TIME
        time_multiplier = time_multipliers.get(mineral_name, 1.0)
        
        time_upgrade = player.upgrades.get(UpgradeType.MINING_TIME.name)
        mining_time = (base_time * time_multiplier) + (time_upgrade.current_effect * 60 if time_upgrade else 0)
        mining_time = max(mining_time, 45)  # Минимум 45 секунд
        
        # Количество добычи (базовое)
        reward_multipliers = {
            "COAL": 15, "IRON": 12, "COPPER": 10, "ALUMINUM": 8, "ZINC": 7,
            "TIN": 8, "LEAD": 9, "NICKEL": 6, "SILVER": 4, "GOLD": 2,
            "PLATINUM": 1.5, "TITANIUM": 3, "URANIUM": 1.2, "DIAMOND": 0.8,
            "RUBY": 2, "SAPPHIRE": 2.5, "EMERALD": 2, "OBSIDIAN": 5,
            "COBALT": 4, "LITHIUM": 6, "CHROMIUM": 5, "MANGANESE": 7,
            "TUNGSTEN": 3, "PALLADIUM": 1, "RHODIUM": 0.8, "OSMIUM": 1.2,
            "IRIDIUM": 0.9, "PROMETHIUM": 0.3
        }
        
        base_reward = reward_multipliers.get(mineral_name, 5) * player.miner_level
        power_upgrade = player.upgrades.get(UpgradeType.MINING_POWER.name)
        bonus_multiplier = 1 + (power_upgrade.current_effect if power_upgrade else 0)
        
        miner_upgrade = player.upgrades.get(UpgradeType.MINER_LEVEL.name)
        if miner_upgrade:
            bonus_multiplier *= (1 + miner_upgrade.current_effect)
        
        for slot, item_id in player.equipped_items.items():
            item = self.items.get(item_id)
            if item and item.mining_bonus > 1.0:
                bonus_multiplier *= item.mining_bonus
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=mining_time)
        
        session = MiningSession(
            user_id=user_id,
            mineral=mineral,
            start_time=start_time,
            end_time=end_time,
            base_reward=base_reward,
            bonus_multiplier=bonus_multiplier
        )
        
        self.active_mining_sessions[user_id] = session
        player.mining_sessions.append(session)
        player.last_mining_time = start_time
        
        self.save_data()
        return True, "Добыча началась!"
    
    def buy_fuel(self, user_id: int, fuel_type: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        fuel_item = None
        for item_id in player.inventory:
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
        
        if not fuel_item:
            return False, "У вас нет такого топлива"
        
        player.fuel += fuel_item.fuel_amount
        player.inventory.remove(fuel_item.item_id)
        
        if fuel_item.item_id in self.items:
            del self.items[fuel_item.item_id]
        
        self.save_data()
        return True, f"Заправлено {fuel_item.fuel_amount} минут автодобычи!"
    
    def toggle_auto_mining(self, user_id: int) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        auto_upgrade = player.upgrades.get(UpgradeType.AUTO_MINING.name)
        if not auto_upgrade or auto_upgrade.level < 1:
            return False, "Сначала купите улучшение 'Автодобыча' (4000 🪙)"
        
        if player.fuel <= 0:
            return False, "Нет топлива для автодобычи. Купите топливо в магазине!"
        
        player.auto_mining_enabled = not player.auto_mining_enabled
        
        if player.auto_mining_enabled:
            if not player.auto_mining_minerals:
                player.auto_mining_minerals = [MineralType.COAL.name]
            
            minerals = []
            for m_name in player.auto_mining_minerals:
                for m in MineralType:
                    if m.name == m_name:
                        minerals.append(m)
                        break
            
            auto_session = AutoMiningSession(
                user_id=user_id,
                minerals=minerals,
                is_active=True,
                last_mine_time=datetime.now(),
                interval_minutes=180,
                next_mine_time=datetime.now() + timedelta(minutes=180),
                fuel_left=player.fuel
            )
            self.auto_mining_sessions[user_id] = auto_session
            
            self.save_data()
            return True, "🤖 Автодобыча включена! Добыча будет запускаться автоматически пока есть топливо."
        else:
            if user_id in self.auto_mining_sessions:
                auto_session = self.auto_mining_sessions[user_id]
                player.fuel = auto_session.fuel_left
                del self.auto_mining_sessions[user_id]
            
            self.save_data()
            return True, "🤖 Автодобыча выключена."
    
    def process_auto_mining(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        player = self.players.get(user_id)
        if not player or not player.auto_mining_enabled:
            return False, {"error": "Автодобыча не активна"}
        
        if user_id not in self.auto_mining_sessions:
            return False, {"error": "Сессия автодобычи не найдена"}
        
        auto_session = self.auto_mining_sessions[user_id]
        
        if auto_session.fuel_left <= 0:
            player.auto_mining_enabled = False
            if user_id in self.auto_mining_sessions:
                del self.auto_mining_sessions[user_id]
            self.save_data()
            return False, {"error": "Закончилось топливо. Автодобыча остановлена."}
        
        if auto_session.next_mine_time and datetime.now() < auto_session.next_mine_time:
            return False, {"error": "Ещё не время для автодобычи"}
        
        results = []
        total_mineral = 0
        total_gold = 0
        dropped_items = []
        
        for mineral in auto_session.minerals:
            base_reward = 3 * player.miner_level
            power_upgrade = player.upgrades.get(UpgradeType.MINING_POWER.name)
            bonus_multiplier = 1 + (power_upgrade.current_effect if power_upgrade else 0)
            
            miner_upgrade = player.upgrades.get(UpgradeType.MINER_LEVEL.name)
            if miner_upgrade:
                bonus_multiplier *= (1 + miner_upgrade.current_effect)
            
            for slot, item_id in player.equipped_items.items():
                item = self.items.get(item_id)
                if item and item.mining_bonus > 1.0:
                    bonus_multiplier *= item.mining_bonus
            
            mineral_reward = base_reward * bonus_multiplier
            
            player.mineral_balance[mineral.name] = player.mineral_balance.get(mineral.name, 0) + mineral_reward
            player.total_mined += mineral_reward
            total_mineral += mineral_reward
            
            gold_earned = int(mineral_reward * 4)
            player.gold_balance += gold_earned
            player.total_gold_earned += gold_earned
            total_gold += gold_earned
            
            results.append({
                "mineral": mineral,
                "amount": mineral_reward,
                "gold": gold_earned
            })
        
        exp_gained = int(total_mineral)
        player.experience += exp_gained
        player.total_experience += exp_gained
        
        auto_session.fuel_left = max(0, auto_session.fuel_left - 180)
        player.fuel = auto_session.fuel_left
        
        if auto_session.fuel_left <= 0:
            player.auto_mining_enabled = False
            if user_id in self.auto_mining_sessions:
                del self.auto_mining_sessions[user_id]
        
        auto_session.last_mine_time = datetime.now()
        auto_session.next_mine_time = datetime.now() + timedelta(minutes=180)
        
        player.stats["auto_mines"] += 1
        
        self.save_data()
        
        return True, {
            "success": True,
            "results": results,
            "total_mineral": total_mineral,
            "total_gold": total_gold,
            "experience": exp_gained,
            "items": dropped_items,
            "fuel_left": auto_session.fuel_left
        }
    
    def complete_mining(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        if user_id not in self.active_mining_sessions:
            return False, {"error": "Нет активной добычи"}
        
        session = self.active_mining_sessions[user_id]
        player = self.players.get(user_id)
        
        if not player or not session.active:
            return False, {"error": "Сессия не активна"}
        
        if datetime.now() < session.end_time:
            time_left = (session.end_time - datetime.now()).seconds
            minutes = time_left // 60
            seconds = time_left % 60
            return False, {"error": f"Добыча ещё идёт. Осталось: {minutes}м {seconds}с"}
        
        mineral_reward = session.base_reward * session.bonus_multiplier
        
        energy_upgrade = player.upgrades.get(UpgradeType.ENERGY_EFF.name)
        if energy_upgrade and energy_upgrade.level > 0:
            mineral_reward *= (1 + energy_upgrade.current_effect)
        
        player.mineral_balance[session.mineral.name] = player.mineral_balance.get(session.mineral.name, 0) + mineral_reward
        player.total_mined += mineral_reward
        player.stats["minerals_mined"] += 1
        
        gold_earned = int(mineral_reward * 8)
        player.gold_balance += gold_earned
        player.total_gold_earned += gold_earned
        
        exp_gained = int(mineral_reward * 1.5)
        player.experience += exp_gained
        player.total_experience += exp_gained
        
        level_up = False
        exp_needed = player.miner_level * 80  # Меньше опыта для уровня
        
        while player.experience >= exp_needed:
            player.experience -= exp_needed
            player.miner_level += 1
            player.upgrades[UpgradeType.MINER_LEVEL.name].level = player.miner_level
            level_up = True
            exp_needed = player.miner_level * 80
            
            if player.miner_level >= 2:
                new_minerals = [
                    MineralType.COPPER.name, MineralType.ALUMINUM.name, MineralType.ZINC.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
            
            if player.miner_level >= 3:
                new_minerals = [
                    MineralType.TIN.name, MineralType.LEAD.name, MineralType.NICKEL.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
            
            if player.miner_level >= 5:
                new_minerals = [
                    MineralType.SILVER.name, MineralType.OBSIDIAN.name, MineralType.COBALT.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
            
            if player.miner_level >= 8:
                new_minerals = [
                    MineralType.GOLD.name, MineralType.TITANIUM.name, MineralType.LITHIUM.name,
                    MineralType.CHROMIUM.name, MineralType.MANGANESE.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
            
            if player.miner_level >= 12:
                new_minerals = [
                    MineralType.PLATINUM.name, MineralType.URANIUM.name, MineralType.TUNGSTEN.name,
                    MineralType.RUBY.name, MineralType.SAPPHIRE.name, MineralType.EMERALD.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
            
            if player.miner_level >= 15:
                new_minerals = [
                    MineralType.DIAMOND.name, MineralType.PALLADIUM.name, MineralType.RHODIUM.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
            
            if player.miner_level >= 20:
                new_minerals = [
                    MineralType.OSMIUM.name, MineralType.IRIDIUM.name, MineralType.PROMETHIUM.name
                ]
                for m in new_minerals:
                    if m not in player.unlocked_minerals:
                        player.unlocked_minerals.append(m)
        
        drop_chance = 0.12
        luck_upgrade = player.upgrades.get(UpgradeType.LUCK.name)
        if luck_upgrade:
            drop_chance += luck_upgrade.current_effect
        
        luck_bonus = 0.0
        for slot, item_id in player.equipped_items.items():
            item = self.items.get(item_id)
            if item and item.luck_bonus > 0:
                luck_bonus += item.luck_bonus
        
        total_drop_chance = drop_chance + luck_bonus
        
        dropped_items = []
        if random.random() < total_drop_chance:
            item_id = str(uuid.uuid4())
            
            item_types = [ItemType.MINING_TOOL, ItemType.LUCK_CHARM, ItemType.MINERAL_CHIP]
            weights = [50, 30, 20]
            item_type = random.choices(item_types, weights=weights)[0]
            
            rarity_weights = {
                ItemRarity.COMMON: 60,
                ItemRarity.RARE: 25,
                ItemRarity.EPIC: 10,
                ItemRarity.LEGENDARY: 4,
                ItemRarity.MYTHIC: 1
            }
            rarity = random.choices(list(rarity_weights.keys()), 
                                  weights=list(rarity_weights.values()))[0]
            
            if item_type == ItemType.MINING_TOOL:
                names = ["Кайло", "Отбойник", "Молот", "Бур", "Лопата"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.15)
                price = 800 * (2 ** list(ItemRarity).index(rarity))
                
                item = Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.MINING_TOOL,
                    rarity=rarity,
                    description=f"{rarity.value} инструмент для добычи",
                    mining_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
                
            elif item_type == ItemType.LUCK_CHARM:
                names = ["Камень удачи", "Талисман", "Амулет", "Оберег"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 0.04 * (list(ItemRarity).index(rarity) + 1)
                price = 1200 * (2 ** list(ItemRarity).index(rarity))
                
                item = Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.LUCK_CHARM,
                    rarity=rarity,
                    description=f"{rarity.value} талисман удачи",
                    luck_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
                
            else:
                names = ["Анализатор", "Сканер", "Детектор", "Датчик"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.12)
                price = 1000 * (2 ** list(ItemRarity).index(rarity))
                
                item = Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.MINERAL_CHIP,
                    rarity=rarity,
                    description=f"{rarity.value} чип анализатора",
                    mining_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
            
            self.items[item_id] = item
            player.inventory.append(item_id)
            player.stats["items_found"] += 1
            dropped_items.append(item)
        
        collectible_chance = 0.008
        if random.random() < collectible_chance:
            collectible_item = self.create_random_collectible(user_id)
            if collectible_item:
                self.items[collectible_item.item_id] = collectible_item
                player.inventory.append(collectible_item.item_id)
                player.stats["collectibles_found"] += 1
                
                if collectible_item.collectible_type:
                    ct_name = collectible_item.collectible_type.name
                    player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
                
                dropped_items.append(collectible_item)
        
        case_chance = 0.04
        case_upgrade = player.upgrades.get(UpgradeType.CASE_CHANCE.name)
        if case_upgrade:
            case_chance += case_upgrade.current_effect
        
        dropped_cases = []
        if random.random() < case_chance:
            available_cases = []
            if player.miner_level >= 15:
                available_cases.append(self.cases["legendary_case"])
            if player.miner_level >= 10:
                available_cases.append(self.cases["epic_case"])
            if player.miner_level >= 5:
                available_cases.append(self.cases["rare_case"])
            available_cases.append(self.cases["common_case"])
            
            if available_cases:
                case = random.choice(available_cases)
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
        
        session.active = False
        if user_id in self.active_mining_sessions:
            del self.active_mining_sessions[user_id]
        
        player.stats["total_play_time"] += MINING_BASE_TIME
        
        self.save_data()
        
        result = {
            "success": True,
            "mineral": session.mineral,
            "mineral_reward": mineral_reward,
            "gold_earned": gold_earned,
            "experience": exp_gained,
            "level_up": level_up,
            "new_level": player.miner_level if level_up else None,
            "items": dropped_items,
            "cases": dropped_cases
        }
        
        return True, result
    
    def create_random_collectible(self, user_id: int) -> Optional[Item]:
        collectible_types = list(CollectibleType)
        collectible_type = random.choice(collectible_types)
        
        rarity_weights = {
            ItemRarity.COMMON: 50,
            ItemRarity.RARE: 30,
            ItemRarity.EPIC: 15,
            ItemRarity.LEGENDARY: 4,
            ItemRarity.MYTHIC: 1
        }
        rarity = random.choices(list(rarity_weights.keys()), 
                              weights=list(rarity_weights.values()))[0]
        
        names_map = {
            CollectibleType.NUGGET: ["Золотой самородок", "Платиновый самородок", "Самородок палладия"],
            CollectibleType.FOSSIL: ["Аммонит", "Трилобит", "Зубы мегалодона"],
            CollectibleType.GEODE: ["Агатовая жеода", "Кварцевая жеода", "Аметистовая жеода"],
            CollectibleType.CRYSTAL: ["Кварц", "Аметист", "Топаз"],
            CollectibleType.METEORITE: ["Каменный метеорит", "Железный метеорит", "Углистый метеорит"],
            CollectibleType.GEMSTONE: ["Рубин", "Сапфир", "Изумруд"],
            CollectibleType.ANCIENT_RELIC: ["Древняя кирка", "Каменная табличка", "Статуэтка божества"],
            CollectibleType.MINERAL_EGG: ["Минеральное яйцо", "Яйцо дракона (миф)", "Яйцо Феникса"]
        }
        
        descriptions_map = {
            CollectibleType.NUGGET: "Драгоценный самородок, найденный в недрах",
            CollectibleType.FOSSIL: "Окаменелость древнего существа",
            CollectibleType.GEODE: "Камень с кристаллами внутри",
            CollectibleType.CRYSTAL: "Природный кристалл",
            CollectibleType.METEORITE: "Кусок космической породы",
            CollectibleType.GEMSTONE: "Драгоценный камень",
            CollectibleType.ANCIENT_RELIC: "Древний артефакт шахтёров",
            CollectibleType.MINERAL_EGG: "Загадочное минеральное образование"
        }
        
        name = random.choice(names_map[collectible_type])
        description = descriptions_map[collectible_type]
        
        base_price = 8000
        price = base_price * (2 ** list(ItemRarity).index(rarity))
        
        item_id = str(uuid.uuid4())
        item = Item(
            item_id=item_id,
            serial_number=self.generate_serial_number(),
            name=name,
            item_type=ItemType.COLLECTIBLE,
            rarity=rarity,
            description=description,
            buy_price=price,
            sell_price=int(price * 0.3),
            is_tradable=True,
            owner_id=user_id,
            is_collectible=True,
            collectible_type=collectible_type
        )
        
        return item
    
    def convert_minerals_to_gold(self, user_id: int, mineral_name: str, amount: float) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        current_balance = player.mineral_balance.get(mineral_name, 0)
        if current_balance < amount:
            return False, f"Недостаточно минералов. Доступно: {current_balance:.2f}"
        
        base_rates = {
            "COAL": 0.2, "IRON": 0.5, "COPPER": 0.8, "ALUMINUM": 1.0, "ZINC": 1.2,
            "TIN": 1.5, "LEAD": 1.0, "NICKEL": 2.0, "SILVER": 5.0, "GOLD": 20.0,
            "PLATINUM": 30.0, "TITANIUM": 10.0, "URANIUM": 25.0, "DIAMOND": 50.0,
            "RUBY": 15.0, "SAPPHIRE": 12.0, "EMERALD": 18.0, "OBSIDIAN": 3.0,
            "COBALT": 4.0, "LITHIUM": 2.5, "CHROMIUM": 3.5, "MANGANESE": 2.0,
            "TUNGSTEN": 8.0, "PALLADIUM": 40.0, "RHODIUM": 60.0, "OSMIUM": 35.0,
            "IRIDIUM": 45.0, "PROMETHIUM": 100.0
        }
        
        default_rate = 0.5
        rate = base_rates.get(mineral_name, default_rate)
        level_multiplier = 1 + (player.miner_level * 0.01)
        gold = int(amount * rate * level_multiplier)
        
        if gold < 1:
            return False, f"Сумма слишком мала для конвертации"
        
        player.mineral_balance[mineral_name] -= amount
        player.gold_balance += gold
        self.save_data()
        
        mineral_value = mineral_name
        for m in MineralType:
            if m.name == mineral_name:
                mineral_value = m.value
                break
        
        bonus_percent = int((level_multiplier - 1) * 100)
        
        return True, f"✅ Продано {amount:.2f} {mineral_value}\n💰 Получено: {gold} 🪙\n🎁 Бонус за уровень: +{bonus_percent}%"
    
    def convert_all_minerals_to_gold(self, user_id: int) -> Tuple[bool, str, int]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден", 0
        
        base_rates = {
            "COAL": 0.2, "IRON": 0.5, "COPPER": 0.8, "ALUMINUM": 1.0, "ZINC": 1.2,
            "TIN": 1.5, "LEAD": 1.0, "NICKEL": 2.0, "SILVER": 5.0, "GOLD": 20.0,
            "PLATINUM": 30.0, "TITANIUM": 10.0, "URANIUM": 25.0, "DIAMOND": 50.0,
            "RUBY": 15.0, "SAPPHIRE": 12.0, "EMERALD": 18.0, "OBSIDIAN": 3.0,
            "COBALT": 4.0, "LITHIUM": 2.5, "CHROMIUM": 3.5, "MANGANESE": 2.0,
            "TUNGSTEN": 8.0, "PALLADIUM": 40.0, "RHODIUM": 60.0, "OSMIUM": 35.0,
            "IRIDIUM": 45.0, "PROMETHIUM": 100.0
        }
        
        level_multiplier = 1 + (player.miner_level * 0.01)
        total_gold = 0
        converted = []
        minerals_to_convert = []
        
        for mineral_name, amount in player.mineral_balance.items():
            if amount > 0:
                minerals_to_convert.append((mineral_name, amount))
        
        if not minerals_to_convert:
            return False, "Нет минералов для продажи", 0
        
        for mineral_name, amount in minerals_to_convert:
            rate = base_rates.get(mineral_name, 0.5)
            gold = int(amount * rate * level_multiplier)
            
            if gold >= 1:
                player.mineral_balance[mineral_name] = 0
                total_gold += gold
                
                mineral_value = mineral_name
                for m in MineralType:
                    if m.name == mineral_name:
                        mineral_value = m.value
                        break
                
                converted.append(f"{mineral_value}: {gold}🪙")
        
        if total_gold > 0:
            player.gold_balance += total_gold
            bonus_percent = int((level_multiplier - 1) * 100)
            
            self.save_data()
            
            result = "✅ Проданы ВСЕ минералы:\n\n"
            result += "\n".join(converted)
            result += f"\n\n💰 Всего получено: {total_gold} 🪙"
            result += f"\n🎁 Бонус за уровень {player.miner_level}: +{bonus_percent}%"
            
            return True, result, total_gold
        
        return False, "Нет минералов для продажи", 0
    
    def buy_upgrade(self, user_id: int, upgrade_type_name: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        upgrade = player.upgrades.get(upgrade_type_name)
        if not upgrade:
            return False, "Улучшение не найдено"
        
        if upgrade.level >= upgrade.max_level:
            return False, f"Достигнут максимальный уровень ({upgrade.max_level})"
        
        cost = upgrade.current_price
        
        if player.gold_balance < cost:
            return False, f"Недостаточно золотых слитков. Нужно: {cost} 🪙"
        
        player.gold_balance -= cost
        upgrade.level += 1
        player.stats["upgrades_bought"] += 1
        
        if upgrade_type_name == UpgradeType.MINER_LEVEL.name:
            player.miner_level = upgrade.level
        
        self.save_data()
        
        return True, f"Улучшение '{upgrade.upgrade_type.value}' повышено до уровня {upgrade.level}!"
    
    def buy_case(self, user_id: int, case_type_name: str) -> Tuple[bool, str, Optional[Item]]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден", None
        
        case = None
        for c in self.cases.values():
            if c.case_type.name == case_type_name:
                case = c
                break
        
        if not case:
            return False, "Ящик не найден", None
        
        if player.gold_balance < case.price:
            return False, f"Недостаточно золотых слитков. Нужно: {case.price} 🪙", None
        
        player.gold_balance -= case.price
        
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
        
        self.save_data()
        
        return True, f"Купили {case.name} за {case.price} 🪙", case_item
    
    def open_case(self, user_id: int, case_item_id: str) -> Tuple[bool, str, List[Item]]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден", []
        
        if case_item_id not in player.inventory:
            return False, "Ящик не в вашем инвентаре", []
        
        case_item = self.items.get(case_item_id)
        if not case_item or case_item.item_type != ItemType.CASE:
            return False, "Это не ящик", []
        
        case = None
        for c in self.cases.values():
            if c.name == case_item.name:
                case = c
                break
        
        if not case:
            return False, "Ящик не найден", []
        
        num_items = random.randint(case.min_items, case.max_items)
        dropped_items = []
        
        for _ in range(num_items):
            if random.random() < case.collectible_chance:
                collectible_item = self.create_random_collectible(user_id)
                if collectible_item:
                    self.items[collectible_item.item_id] = collectible_item
                    player.inventory.append(collectible_item.item_id)
                    player.stats["collectibles_found"] += 1
                    
                    if collectible_item.collectible_type:
                        ct_name = collectible_item.collectible_type.name
                        player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
                    
                    dropped_items.append(collectible_item)
                    continue
            
            rarity_str = random.choices(
                list(case.drop_chances.keys()),
                weights=list(case.drop_chances.values())
            )[0]
            
            rarity = None
            for r in ItemRarity:
                if r.value == rarity_str:
                    rarity = r
                    break
            
            if not rarity:
                rarity = ItemRarity.COMMON
            
            item_types = [ItemType.MINING_TOOL, ItemType.LUCK_CHARM, ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE]
            item_type = random.choice(item_types)
            
            new_item_id = str(uuid.uuid4())
            
            if item_type == ItemType.MINING_TOOL:
                names = ["Кайло", "Лопата", "Отбойник", "Молот"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.2)
                price = 1200 * (2 ** list(ItemRarity).index(rarity))
                
                new_item = Item(
                    item_id=new_item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.MINING_TOOL,
                    rarity=rarity,
                    description=f"{rarity.value} инструмент из ящика",
                    mining_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
                
            elif item_type == ItemType.LUCK_CHARM:
                names = ["Талисман", "Амулет", "Камень удачи", "Оберег"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 0.05 * (list(ItemRarity).index(rarity) + 1)
                price = 1500 * (2 ** list(ItemRarity).index(rarity))
                
                new_item = Item(
                    item_id=new_item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.LUCK_CHARM,
                    rarity=rarity,
                    description=f"{rarity.value} талисман из ящика",
                    luck_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
                
            elif item_type == ItemType.MINERAL_CHIP:
                names = ["Чип анализатора", "Сканер пород", "Детектор"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.15)
                price = 1400 * (2 ** list(ItemRarity).index(rarity))
                
                new_item = Item(
                    item_id=new_item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.MINERAL_CHIP,
                    rarity=rarity,
                    description=f"{rarity.value} чип из ящика",
                    mining_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
                
            else:
                names = ["Ядро реактора", "Батарея", "Генератор"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.1)
                price = 1000 * (2 ** list(ItemRarity).index(rarity))
                
                new_item = Item(
                    item_id=new_item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.ENERGY_CORE,
                    rarity=rarity,
                    description=f"{rarity.value} ядро из ящика",
                    energy_bonus=bonus,
                    buy_price=price,
                    sell_price=int(price * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
            
            self.items[new_item_id] = new_item
            player.inventory.append(new_item_id)
            dropped_items.append(new_item)
        
        player.inventory.remove(case_item_id)
        del self.items[case_item_id]
        
        player.stats["cases_opened"] += 1
        
        self.save_data()
        
        return True, f"Открыт {case.name}!", dropped_items
    
    def equip_item(self, user_id: int, item_id: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if item_id not in player.inventory:
            return False, "Предмет не в вашем инвентаре"
        
        item = self.items.get(item_id)
        if not item:
            return False, "Предмет не найден"
        
        slot_map = {
            ItemType.MINING_TOOL: "tool",
            ItemType.LUCK_CHARM: "charm",
            ItemType.MINERAL_CHIP: "chip",
            ItemType.ENERGY_CORE: "core"
        }
        
        slot = slot_map.get(item.item_type)
        if not slot:
            return False, "Этот предмет нельзя экипировать"
        
        old_item_id = player.equipped_items.get(slot)
        if old_item_id:
            player.equipped_items.pop(slot)
        
        player.equipped_items[slot] = item_id
        
        self.save_data()
        
        return True, f"Предмет '{item.name}' экипирован!"
    
    def unequip_item(self, user_id: int, slot: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if slot not in player.equipped_items:
            return False, f"В слоте '{slot}' нет предмета"
        
        item_id = player.equipped_items.pop(slot)
        item = self.items.get(item_id)
        
        self.save_data()
        
        item_name = item.name if item else "предмет"
        return True, f"Предмет '{item_name}' снят!"
    
    def sell_item(self, user_id: int, item_id: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if item_id not in player.inventory:
            return False, "Предмет не в вашем инвентаре"
        
        item = self.items.get(item_id)
        if not item:
            return False, "Предмет не найден"
        
        for slot, equipped_id in player.equipped_items.items():
            if equipped_id == item_id:
                return False, "Сначала снимите предмет!"
        
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
        
        if item_id in self.items:
            del self.items[item_id]
        
        self.save_data()
        
        return True, f"Предмет '{item.name}' продан за {sell_price} 🪙!"
    
    def sell_all_common_items(self, user_id: int) -> Tuple[bool, str, int, int]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден", 0, 0
        
        items_to_sell = []
        total_price = 0
        inventory_copy = player.inventory.copy()
        
        for item_id in inventory_copy:
            item = self.items.get(item_id)
            if item:
                is_equipped = any(equipped_id == item_id for equipped_id in player.equipped_items.values())
                if (not is_equipped and 
                    item.rarity == ItemRarity.COMMON and 
                    not item.is_collectible and 
                    item.item_type != ItemType.CASE and 
                    item.item_type != ItemType.FUEL and
                    item.is_tradable):
                    
                    items_to_sell.append(item_id)
                    total_price += max(item.sell_price, 80)
        
        if not items_to_sell:
            return False, "У вас нет обычных предметов для продажи", 0, 0
        
        sold_count = 0
        for item_id in items_to_sell:
            success, _ = self.sell_item(user_id, item_id)
            if success:
                sold_count += 1
        
        self.save_data()
        
        return True, f"Продано {sold_count} обычных предметов", sold_count, total_price
    
    def create_market_offer(self, user_id: int, item_id: str, price: int) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if item_id not in player.inventory:
            return False, "Предмет не в вашем инвентаре"
        
        item = self.items.get(item_id)
        if not item:
            return False, "Предмет не найден"
        
        if not item.is_tradable:
            return False, "Этот предмет нельзя продавать"
        
        for slot, equipped_id in player.equipped_items.items():
            if equipped_id == item_id:
                return False, "Сначала снимите предмет!"
        
        if price <= 0:
            return False, "Цена должна быть больше 0"
        
        if price > 800000:
            return False, "Цена слишком высока"
        
        offer_id = str(uuid.uuid4())
        offer = MarketOffer(
            offer_id=offer_id,
            item_id=item_id,
            seller_id=user_id,
            seller_name=player.username or player.first_name,
            price=price
        )
        
        self.market_offers[offer_id] = offer
        self.save_data()
        
        return True, f"Предмет '{item.name}' выставлен на рынок за {price} 🪙!"
    
    def buy_market_offer(self, buyer_id: int, offer_id: str) -> Tuple[bool, str]:
        offer = self.market_offers.get(offer_id)
        if not offer:
            return False, "Предложение не найдено"
        
        buyer = self.players.get(buyer_id)
        if not buyer:
            return False, "Покупатель не найден"
        
        if buyer_id == offer.seller_id:
            return False, "Нельзя купить свой же предмет"
        
        item = self.items.get(offer.item_id)
        if not item:
            return False, "Предмет не найден"
        
        seller = self.players.get(offer.seller_id)
        if not seller:
            return False, "Продавец не найден"
        
        if buyer.gold_balance < offer.price:
            return False, f"Недостаточно золотых слитков. Нужно: {offer.price} 🪙"
        
        buyer.gold_balance -= offer.price
        seller.gold_balance += offer.price
        
        buyer.inventory.append(offer.item_id)
        if offer.item_id in seller.inventory:
            seller.inventory.remove(offer.item_id)
        
        item.owner_id = buyer_id
        
        buyer.stats["trades_completed"] += 1
        seller.stats["trades_completed"] += 1
        
        del self.market_offers[offer_id]
        self.save_data()
        
        return True, f"Куплен предмет '{item.name}' за {offer.price} 🪙!"
    
    def cancel_market_offer(self, user_id: int, offer_id: str) -> Tuple[bool, str]:
        offer = self.market_offers.get(offer_id)
        if not offer:
            return False, "Предложение не найдено"
        
        if offer.seller_id != user_id:
            return False, "Это не ваше предложение"
        
        del self.market_offers[offer_id]
        self.save_data()
        
        return True, "Предложение снято с рынка"
    
    def get_player_collectibles_stats(self, user_id: int) -> Dict[str, Any]:
        player = self.players.get(user_id)
        if not player:
            return {}
        
        total_collectibles = sum(player.collectibles.values())
        unique_types = sum(1 for count in player.collectibles.values() if count > 0)
        
        return {
            "total": total_collectibles,
            "unique_types": unique_types,
            "by_type": player.collectibles.copy(),
            "completion_percentage": (unique_types / len(CollectibleType)) * 100 if len(CollectibleType) > 0 else 0
        }
    
    def get_donate_reward(self, stars: int) -> Dict[str, Any]:
        rewards = {
            1: {"gold": 80, "bonus_percent": 0, "items": []},
            5: {"gold": 400, "bonus_percent": 10, "items": ["common_case"]},
            10: {"gold": 850, "bonus_percent": 20, "items": ["rare_case"]},
            20: {"gold": 1800, "bonus_percent": 30, "items": ["rare_case", "common_fuel"]},
            50: {"gold": 4500, "bonus_percent": 50, "items": ["epic_case", "advanced_fuel", "random_tool"]},
            100: {"gold": 9000, "bonus_percent": 100, "items": ["legendary_case", "premium_fuel", "epic_tool", "random_collectible"]}
        }
        
        special_rewards = {
            "starter": {"stars": 50, "gold": 5000, "items": ["epic_case", "advanced_fuel", "mining_tool_rare"]},
            "business": {"stars": 100, "gold": 12000, "items": ["legendary_case", "premium_fuel", "mining_tool_epic", "luck_charm_rare"]},
            "premium": {"stars": 200, "gold": 30000, "items": ["mythic_case", "ultra_fuel", "mining_tool_legendary", "luck_charm_epic", "random_collectible"]},
            "auto": {"stars": 50, "gold": 4400, "items": ["advanced_fuel", "premium_fuel", "auto_mining_upgrade"]},
            "collection": {"stars": 100, "gold": 10000, "items": ["epic_case", "legendary_case", "random_collectible", "collectible_badge"]}
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
        
        return {
            "gold": gold,
            "bonus_percent": bonus_percent,
            "items": items
        }
    
    def process_donation(self, user_id: int, stars: int, payload: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден", {}
        
        reward = self.get_donate_reward(stars)
        
        total_gold = reward["gold"]
        if reward["bonus_percent"] > 0:
            bonus = int(total_gold * reward["bonus_percent"] / 100)
            total_gold += bonus
        
        player.gold_balance += total_gold
        player.total_gold_earned += total_gold
        
        items_given = []
        for item_type in reward.get("items", []):
            if item_type == "common_case":
                success, message, case_item = self.buy_case(user_id, "COMMON")
                if success:
                    items_given.append(case_item)
            elif item_type == "rare_case":
                success, message, case_item = self.buy_case(user_id, "RARE")
                if success:
                    items_given.append(case_item)
            elif item_type == "epic_case":
                success, message, case_item = self.buy_case(user_id, "EPIC")
                if success:
                    items_given.append(case_item)
            elif item_type == "legendary_case":
                success, message, case_item = self.buy_case(user_id, "LEGENDARY")
                if success:
                    items_given.append(case_item)
            elif item_type == "mythic_case":
                success, message, case_item = self.buy_case(user_id, "MYTHIC")
                if success:
                    items_given.append(case_item)
            elif item_type == "common_fuel":
                item_id = str(uuid.uuid4())
                fuel_item = Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name="⛽ Угольные брикеты",
                    item_type=ItemType.FUEL,
                    rarity=ItemRarity.COMMON,
                    description="Топливо для автодобычи (60 минут)",
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
                    description="Топливо для автодобычи (180 минут)",
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
                    name="⚡ Энергетические стержни",
                    item_type=ItemType.FUEL,
                    rarity=ItemRarity.EPIC,
                    description="Топливо для автодобычи (300 минут)",
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
                    name="🚀 Плутониевый реактор",
                    item_type=ItemType.FUEL,
                    rarity=ItemRarity.LEGENDARY,
                    description="Топливо для автодобычи (600 минут)",
                    buy_price=8000,
                    sell_price=4000,
                    is_tradable=True,
                    owner_id=user_id,
                    fuel_amount=600
                )
                self.items[item_id] = fuel_item
                player.inventory.append(item_id)
                items_given.append(fuel_item)
            elif item_type == "random_tool":
                item_id = str(uuid.uuid4())
                rarity = random.choices(
                    [ItemRarity.COMMON, ItemRarity.RARE, ItemRarity.EPIC],
                    weights=[60, 30, 10]
                )[0]
                
                names = ["Кайло", "Отбойник", "Молот", "Лопата"]
                name = f"{rarity.value} {random.choice(names)}"
                bonus = 1.0 + (list(ItemRarity).index(rarity) * 0.15)
                
                tool_item = Item(
                    item_id=item_id,
                    serial_number=self.generate_serial_number(),
                    name=name,
                    item_type=ItemType.MINING_TOOL,
                    rarity=rarity,
                    description=f"{rarity.value} инструмент из доната",
                    mining_bonus=bonus,
                    buy_price=800 * (2 ** list(ItemRarity).index(rarity)),
                    sell_price=int(800 * (2 ** list(ItemRarity).index(rarity)) * 0.6),
                    is_tradable=True,
                    owner_id=user_id
                )
                self.items[item_id] = tool_item
                player.inventory.append(item_id)
                items_given.append(tool_item)
            elif item_type == "random_collectible":
                collectible_item = self.create_random_collectible(user_id)
                if collectible_item:
                    self.items[collectible_item.item_id] = collectible_item
                    player.inventory.append(collectible_item.item_id)
                    items_given.append(collectible_item)
                    
                    if collectible_item.collectible_type:
                        ct_name = collectible_item.collectible_type.name
                        player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
            elif item_type == "auto_mining_upgrade":
                if UpgradeType.AUTO_MINING.name in player.upgrades:
                    player.upgrades[UpgradeType.AUTO_MINING.name].level += 1
        
        self.save_data()
        
        result = {
            "success": True,
            "stars": stars,
            "gold": total_gold,
            "bonus_percent": reward["bonus_percent"],
            "items": items_given,
            "player": player
        }
        
        return True, f"✅ Спасибо за поддержку! Вы получили {total_gold} 🪙", result
    
    async def add_channel(self, name: str, url: str, required_level: int, reward: int) -> Tuple[bool, str]:
        bot_in_channel = await self.check_bot_in_channel(url)
        channel_id = f"channel_{len(self.channels) + 1}"
        
        channel = Channel(
            id=channel_id,
            name=name,
            url=url,
            required_level=required_level,
            reward=reward,
            bot_member=bot_in_channel
        )
        
        self.channels[channel_id] = channel
        self.save_data()
        
        if bot_in_channel:
            return True, f"Канал '{name}' добавлен! ✅ Бот является администратором."
        else:
            return True, f"Канал '{name}' добавлен! ⚠️ Бот НЕ добавлен в канал или не является администратором. Добавьте бота: @CRIPTO_MAINER_GAMEBOT"
    
    def remove_channel(self, channel_id: str) -> Tuple[bool, str]:
        if channel_id not in self.channels:
            return False, "Канал не найден"
        
        del self.channels[channel_id]
        self.save_data()
        return True, "Канал удален"
    
    def give_gold(self, user_id: int, amount: int) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        player.gold_balance += amount
        self.save_data()
        
        return True, f"Выдано {amount} 🪙 игроку {player.first_name}"
    
    def give_item(self, user_id: int, item_name: str) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        item_id = str(uuid.uuid4())
        
        rarity = ItemRarity.RARE
        if "Эпический" in item_name or "эпический" in item_name:
            rarity = ItemRarity.EPIC
        elif "Легендарный" in item_name or "легендарный" in item_name:
            rarity = ItemRarity.LEGENDARY
        elif "Мифический" in item_name or "мифический" in item_name:
            rarity = ItemRarity.MYTHIC
        
        is_collectible = False
        for collectible_type in CollectibleType:
            if collectible_type.value in item_name:
                is_collectible = True
                break
        
        if is_collectible:
            collectible_type = random.choice(list(CollectibleType))
            
            item = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=item_name,
                item_type=ItemType.COLLECTIBLE,
                rarity=rarity,
                description="Подарок от администратора",
                buy_price=8000,
                sell_price=2400,
                is_tradable=True,
                owner_id=user_id,
                is_collectible=True,
                collectible_type=collectible_type
            )
        else:
            item = Item(
                item_id=item_id,
                serial_number=self.generate_serial_number(),
                name=item_name,
                item_type=ItemType.MINING_TOOL,
                rarity=rarity,
                description="Подарок от администратора",
                mining_bonus=1.4,
                buy_price=8000,
                sell_price=4000,
                is_tradable=True,
                owner_id=user_id
            )
        
        self.items[item_id] = item
        player.inventory.append(item_id)
        
        if is_collectible and item.collectible_type:
            ct_name = item.collectible_type.name
            player.collectibles[ct_name] = player.collectibles.get(ct_name, 0) + 1
        
        self.save_data()
        
        return True, f"Предмет '{item_name}' выдан игроку {player.first_name}"
    
    def reset_player(self, user_id: int) -> Tuple[bool, str]:
        if user_id not in self.players:
            return False, "Шахтёр не найден"
        
        old_player = self.players[user_id]
        new_player = Player(
            user_id=user_id,
            username=old_player.username,
            first_name=old_player.first_name
        )
        
        self.players[user_id] = new_player
        self.save_data()
        
        return True, f"Игрок {old_player.first_name} сброшен"
    
    def broadcast_message(self, message: str) -> List[Tuple[int, bool]]:
        results = []
        for user_id in self.players.keys():
            results.append((user_id, True))
        return results
    
    def get_all_players(self) -> List[Player]:
        return list(self.players.values())
    
    def search_player(self, query: str) -> Optional[Player]:
        try:
            user_id = int(query)
            if user_id in self.players:
                return self.players[user_id]
        except ValueError:
            pass
        
        query_lower = query.lower().replace('@', '')
        for player in self.players.values():
            if player.username and player.username.lower() == query_lower:
                return player
        
        return None
    
    def set_player_level(self, user_id: int, level: int) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if level < 1 or level > 80:
            return False, "Уровень должен быть от 1 до 80"
        
        player.miner_level = level
        if UpgradeType.MINER_LEVEL.name in player.upgrades:
            player.upgrades[UpgradeType.MINER_LEVEL.name].level = level
        
        player.experience = 0
        player.total_experience = level * 80
        
        self.save_data()
        
        return True, f"Уровень игрока {player.first_name} установлен на {level}"
    
    def set_player_gold(self, user_id: int, gold: int) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if gold < 0:
            return False, "Количество золота не может быть отрицательным"
        
        player.gold_balance = gold
        self.save_data()
        
        return True, f"Золото игрока {player.first_name} установлено на {gold}"
    
    def set_player_balance(self, user_id: int, mineral_name: str, amount: float) -> Tuple[bool, str]:
        player = self.players.get(user_id)
        if not player:
            return False, "Шахтёр не найден"
        
        if amount < 0:
            return False, "Баланс не может быть отрицательным"
        
        player.mineral_balance[mineral_name] = amount
        self.save_data()
        
        mineral_value = mineral_name
        for m in MineralType:
            if m.name == mineral_name:
                mineral_value = m.value
                break
        
        return True, f"Баланс {mineral_value} игрока {player.first_name} установлен на {amount:.2f}"

# ========== КЛАВИАТУРЫ ==========

class KeyboardManager:
    @staticmethod
    def get_rarity_emoji(rarity: ItemRarity) -> str:
        emoji_map = {
            ItemRarity.COMMON: "⚪",
            ItemRarity.RARE: "🔵",
            ItemRarity.EPIC: "🟣",
            ItemRarity.LEGENDARY: "🟡",
            ItemRarity.MYTHIC: "🔴"
        }
        return emoji_map.get(rarity, "⚪")
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⛏️ Добыча", callback_data="mining_menu"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        )
        builder.row(
            InlineKeyboardButton(text="⚡ Улучшения", callback_data="upgrades"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")
        )
        builder.row(
            InlineKeyboardButton(text="🪙 Золото", callback_data="gold"),
            InlineKeyboardButton(text="📦 Ящики", callback_data="cases")
        )
        builder.row(
            InlineKeyboardButton(text="🤖 Автодобыча", callback_data="auto_mining"),
            InlineKeyboardButton(text="🏆 Коллекции", callback_data="collections")
        )
        builder.row(
            InlineKeyboardButton(text="⭐ Донаты", callback_data="donate"),
            InlineKeyboardButton(text="📢 Каналы", callback_data="channels")
        )
        builder.row(
            InlineKeyboardButton(text="🏪 Рынок", callback_data="market"),
            InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")
        )
        builder.row(
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        )
        return builder.as_markup()
    
    @staticmethod
    def mining_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        for mineral_name in player.unlocked_minerals[:9]:
            for mineral in MineralType:
                if mineral.name == mineral_name:
                    builder.button(
                        text=mineral.value,
                        callback_data=f"start_mine_{mineral_name}"
                    )
                    break
        
        builder.button(text="📊 Статус добычи", callback_data="mining_status")
        builder.button(text="🤖 Статус автодобычи", callback_data="auto_mining_status")
        builder.button(text="💰 Мои минералы", callback_data="my_minerals")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(3)
        return builder.as_markup()
    
    @staticmethod
    def auto_mining_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        status = "✅ ВКЛ" if player.auto_mining_enabled else "❌ ВЫКЛ"
        auto_upgrade = player.upgrades.get(UpgradeType.AUTO_MINING.name)
        
        builder.button(text=f"🤖 Автодобыча: {status}", callback_data="toggle_auto_mining")
        
        if auto_upgrade and auto_upgrade.level > 0:
            if not player.auto_mining_enabled:
                builder.button(text="⛽ Купить топливо", callback_data="buy_fuel_menu")
            else:
                builder.button(text="📊 Статус топлива", callback_data="fuel_status")
        
        builder.button(text="📊 Информация", callback_data="auto_mining_info")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def buy_fuel_menu(player: Player) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        has_fuel = False
        for item_id in player.inventory:
            item = data_manager.items.get(item_id)
            if item and item.item_type == ItemType.FUEL:
                has_fuel = True
                builder.button(
                    text=f"{item.name} ({item.fuel_amount} мин)",
                    callback_data=f"use_fuel_{'basic' if item.fuel_amount == 60 else 'advanced' if item.fuel_amount == 180 else 'premium' if item.fuel_amount == 300 else 'ultra'}"
                )
        
        if not has_fuel:
            builder.button(text="🛒 Купить топливо в магазине", callback_data="shop_fuel")
        
        builder.button(text="⬅️ Назад", callback_data="auto_mining")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def shop_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="⛽ Топливо", callback_data="shop_fuel")
        builder.button(text="📦 Ящики", callback_data="cases")
        builder.button(text="⚡ Улучшения", callback_data="upgrades")
        builder.button(text="🪙 Золото", callback_data="gold")
        builder.button(text="⭐ Донаты", callback_data="donate")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def shop_fuel_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        fuels = [
            ("⛽ Угольные брикеты", "60 минут", 800, "shop_buy_fuel_basic"),
            ("🔥 Нефтяное топливо", "180 минут", 2000, "shop_buy_fuel_advanced"),
            ("⚡ Энергетические стержни", "300 минут", 4000, "shop_buy_fuel_premium"),
            ("🚀 Плутониевый реактор", "600 минут", 8000, "shop_buy_fuel_ultra")
        ]
        
        for name, desc, price, callback in fuels:
            builder.button(text=f"{name} - {price} 🪙", callback_data=callback)
        
        builder.button(text="⬅️ Назад", callback_data="shop")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def collections_menu(collectibles_stats: Dict[str, Any]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        total = collectibles_stats.get("total", 0)
        unique = collectibles_stats.get("unique_types", 0)
        percentage = collectibles_stats.get("completion_percentage", 0)
        
        builder.button(text=f"🏆 Коллекция: {total} шт.", callback_data="collections_stats")
        builder.button(text=f"🎯 Уникальных: {unique}/24", callback_data="collections_types")
        builder.button(text=f"📊 Завершено: {percentage:.1f}%", callback_data="collections_progress")
        
        for collectible_type in CollectibleType:
            builder.button(
                text=f"{collectible_type.value}",
                callback_data=f"collectible_type_{collectible_type.name}"
            )
        
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def gold_menu(player_gold: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=f"💰 Баланс: {player_gold} 🪙", callback_data="gold_balance")
        builder.button(text="💱 Продать ВСЕ минералы", callback_data="convert_all_minerals")
        builder.button(text="🛒 Магазин улучшений", callback_data="upgrades")
        builder.button(text="⭐ Купить золото", callback_data="donate")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def upgrades_menu(upgrades: Dict[str, Upgrade], player_gold: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        for upgrade_name, upgrade in upgrades.items():
            try:
                upgrade_type = None
                for ut in UpgradeType:
                    if ut.name == upgrade_name:
                        upgrade_type = ut
                        break
                
                if upgrade_type:
                    cost = upgrade.current_price
                    builder.button(
                        text=f"{upgrade_type.value} (Ур. {upgrade.level}) - {cost} 🪙",
                        callback_data=f"buy_upgrade_{upgrade_name}"
                    )
            except:
                continue
        
        builder.button(text=f"💰 Золота: {player_gold} 🪙", callback_data="gold_balance")
        builder.button(text="📊 Эффекты улучшений", callback_data="upgrade_effects")
        builder.button(text="⭐ Купить золото", callback_data="donate")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def cases_menu(cases: Dict[str, Case], player_gold: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        for case_id, case in cases.items():
            builder.button(
                text=f"{case.name} - {case.price} 🪙",
                callback_data=f"buy_case_{case.case_type.name}"
            )
        
        builder.button(text="🎁 Открыть ящики", callback_data="open_cases")
        builder.button(text=f"💰 Баланс: {player_gold} 🪙", callback_data="gold_balance")
        builder.button(text="⭐ Купить золото", callback_data="donate")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def inventory_menu(player: Player, items: Dict[str, Item], page: int = 0) -> InlineKeyboardMarkup:
        items_per_page = 8
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        
        builder = InlineKeyboardBuilder()
        
        page_items = player.inventory[start_idx:end_idx]
        for item_id in page_items:
            item = items.get(item_id)
            if item:
                emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                display_name = f"{emoji} {item.name[:12]}"
                if len(item.name) > 12:
                    display_name += "..."
                builder.button(
                    text=display_name,
                    callback_data=f"item_{item_id}"
                )
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"inv_page_{page-1}"))
        
        if end_idx < len(player.inventory):
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"inv_page_{page+1}"))
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.row(
            InlineKeyboardButton(text="🛡️ Экипировка", callback_data="equipment"),
            InlineKeyboardButton(text="💰 Продать все обычные", callback_data="sell_all_common_items")
        )
        builder.row(
            InlineKeyboardButton(text="🏪 На рынок", callback_data="create_offer"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="inventory")
        )
        builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
        
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def item_menu(item: Item, is_equipped: bool = False) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        if item.item_type == ItemType.CASE:
            builder.button(text="🎁 Открыть ящик", callback_data=f"open_{item.item_id}")
        elif item.item_type == ItemType.FUEL:
            builder.button(text="⛽ Использовать", callback_data=f"use_fuel_item_{item.item_id}")
        elif not is_equipped and item.item_type in [ItemType.MINING_TOOL, ItemType.LUCK_CHARM, 
                                                   ItemType.MINERAL_CHIP, ItemType.ENERGY_CORE]:
            builder.button(text="🛡️ Надеть", callback_data=f"equip_{item.item_id}")
        elif is_equipped:
            builder.button(text="📦 Снять", callback_data=f"unequip_{item.item_id}")
        
        builder.button(text="💰 Продать", callback_data=f"sell_{item.item_id}")
        
        if item.is_tradable:
            builder.button(text="🏪 На рынок", callback_data=f"market_sell_{item.item_id}")
        
        builder.button(text="⬅️ Назад", callback_data="inventory")
        
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def equipment_menu(equipped_items: Dict[str, str], items: Dict[str, Item]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        slot_names = {
            "tool": "⛏️ Инструмент",
            "charm": "🍀 Талисман",
            "chip": "💿 Чип",
            "core": "🔋 Ядро"
        }
        
        for slot, slot_name in slot_names.items():
            item_id = equipped_items.get(slot)
            if item_id:
                item = items.get(item_id)
                if item:
                    emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                    builder.button(
                        text=f"{slot_name}: {emoji} {item.name[:10]}",
                        callback_data=f"unequip_{slot}"
                    )
            else:
                builder.button(text=f"{slot_name}: Пусто", callback_data="inventory")
        
        builder.button(text="📊 Бонусы", callback_data="equipment_bonuses")
        builder.button(text="⬅️ Назад", callback_data="inventory")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def market_menu(market_offers: Dict[str, MarketOffer], items: Dict[str, Item], page: int = 0) -> InlineKeyboardMarkup:
        offers_list = list(market_offers.values())
        items_per_page = 5
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        
        builder = InlineKeyboardBuilder()
        
        for i in range(start_idx, min(end_idx, len(offers_list))):
            offer = offers_list[i]
            item = items.get(offer.item_id)
            if item:
                emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                builder.button(
                    text=f"{emoji} {item.name[:10]} - {offer.price} 🪙",
                    callback_data=f"buy_offer_{offer.offer_id}"
                )
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"market_page_{page-1}"))
        
        if end_idx < len(offers_list):
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"market_page_{page+1}"))
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.row(
            InlineKeyboardButton(text="📤 Мои предложения", callback_data="my_offers"),
            InlineKeyboardButton(text="➕ Выставить предмет", callback_data="create_offer")
        )
        builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def channels_menu(channels: Dict[str, Channel]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        for channel_id, channel in channels.items():
            bot_status = "✅" if channel.bot_member else "⚠️"
            builder.button(
                text=f"{bot_status} {channel.name} (Ур. {channel.required_level}+)",
                callback_data=f"channel_{channel_id}"
            )
        
        builder.button(text="✅ Проверить подписки", callback_data="check_subscriptions")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Статистика", callback_data="admin_stats")
        builder.button(text="👤 Управление игроками", callback_data="admin_players")
        builder.button(text="🔍 Найти игрока", callback_data="admin_find_player")
        builder.button(text="➕ Добавить канал", callback_data="admin_add_channel")
        builder.button(text="➖ Удалить канал", callback_data="admin_remove_channel")
        builder.button(text="🔧 Проверить каналы", callback_data="admin_check_channels")
        builder.button(text="🤖 Добавить бота в канал", callback_data="admin_add_bot")
        builder.button(text="🎁 Выдать золото", callback_data="admin_give_gold")
        builder.button(text="🎁 Выдать предмет", callback_data="admin_give_item")
        builder.button(text="📈 Установить уровень", callback_data="admin_set_level")
        builder.button(text="💰 Установить золото", callback_data="admin_set_gold")
        builder.button(text="💱 Установить минералы", callback_data="admin_set_balance")
        builder.button(text="🔄 Сброс игрока", callback_data="admin_reset_player")
        builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
        builder.button(text="📋 Список предметов", callback_data="admin_items_list")
        builder.button(text="📋 Список минералов", callback_data="admin_minerals_list")
        builder.button(text="📋 Коллекции игроков", callback_data="admin_collections")
        builder.button(text="💾 Создать бекап", callback_data="admin_backup")
        builder.button(text="⭐ Статистика донатов", callback_data="admin_donate_stats")
        builder.button(text="⬅️ Назад", callback_data="back_to_main")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def back_button(target: str = "back_to_main") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=target)
        return builder.as_markup()

# ========== ТЕКСТОВЫЕ ШАБЛОНЫ ==========

class TextTemplates:
    @staticmethod
    def welcome(first_name: str) -> str:
        return f"""
⛏️ Добро пожаловать в {GAME_NAME}, {first_name}!

🪨 Вы - старатель, добывающий редкие минералы. Ваша цель:
💰 Добывать 28+ видов ископаемых
🪙 Продавать их за золотые слитки
⭐ Поддерживать проект донатами
⚡ Покупать улучшения за золото
🎒 Коллекционировать редкие предметы
📦 Открывать ящики с наградами
🤖 Использовать автодобычу (требует топливо)
🏆 Собирать коллекционные сувениры (24 типа по 3 шт.)

🚀 Начните с команды /mine или используйте кнопки ниже!
"""
    
    @staticmethod
    def profile(player: Player) -> str:
        total_mineral = player.get_total_mineral_value()
        miner_level = player.miner_level
        
        mining_status = "🟢 Готов к работе"
        if player.auto_mining_enabled:
            mining_status = "🤖 Автодобыча активна"
        elif any(session.active for session in data_manager.active_mining_sessions.values() if session.user_id == player.user_id):
            mining_status = "⛏️ Добыча в процессе"
        
        collectibles_stats = {
            "total": sum(player.collectibles.values()),
            "unique_types": sum(1 for count in player.collectibles.values() if count > 0),
            "completion_percentage": (sum(1 for count in player.collectibles.values() if count > 0) / 24) * 100
        }
        
        upgrades_text = ""
        key_upgrades = [UpgradeType.MINER_LEVEL, UpgradeType.MINING_POWER, 
                       UpgradeType.MINING_SPEED, UpgradeType.MINING_TIME, UpgradeType.LUCK]
        for upgrade_type in key_upgrades:
            upgrade = player.upgrades.get(upgrade_type.name)
            if upgrade:
                effect = upgrade.current_effect
                if upgrade_type == UpgradeType.MINING_TIME:
                    upgrades_text += f"{upgrade_type.value}: Ур. {upgrade.level} (+{effect:.0f} мин)\n"
                else:
                    upgrades_text += f"{upgrade_type.value}: Ур. {upgrade.level} (+{effect:.1%})\n"
        
        return f"""
👤 Профиль: {player.first_name} (@{player.username})

🏆 Уровень шахтёра: {miner_level}
⭐ Опыт: {player.experience}/{miner_level*80}
💰 Золотых слитков: {player.gold_balance} 🪙
🎒 Предметов: {len(player.inventory)}
🏆 Коллекционных: {collectibles_stats['total']} шт.
⛽ Топливо: {player.fuel} мин.

⛏️ Добыча:
  Всего добыто: {player.total_mined:.2f} кг экв.
  Статус: {mining_status}

{upgrades_text}
📅 Играет с: {player.created_at.strftime('%d.%m.%Y')}
"""
    
    @staticmethod
    def mining_status(session: MiningSession) -> str:
        time_left = (session.end_time - datetime.now()).seconds
        total_time = (session.end_time - session.start_time).seconds
        progress = 100 - (time_left / total_time * 100)
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        
        minutes = time_left // 60
        seconds = time_left % 60
        
        return f"""
⛏️ Добыча в процессе

💰 Минерал: {session.mineral.value}
⏱️ Прогресс: {progress:.0f}%
{progress_bar}
⏳ Осталось: {minutes}м {seconds}с
🕐 Завершится: {session.end_time.strftime('%H:%M:%S')}
"""
    
    @staticmethod
    def auto_mining_status(player: Player, auto_session: Optional[AutoMiningSession] = None) -> str:
        auto_upgrade = player.upgrades.get(UpgradeType.AUTO_MINING.name)
        
        if not auto_upgrade or auto_upgrade.level < 1:
            return """
🤖 Автодобыча

❌ Автодобыча недоступна
💰 Для разблокировки купите улучшение "Автодобыча"
🪙 Стоимость: 4000 🪙 (уровень 1)
⛽ Требуется топливо для работы
"""
        
        if not player.auto_mining_enabled:
            return f"""
🤖 Автодобыча

❌ Автодобыча выключена
⛽ Топливо: {player.fuel} мин.
💰 Для включения нужно топливо
🎯 Купите топливо в магазине или найдите в ящиках
"""
        
        if not auto_session:
            return "🤖 Автодобыча активна, но нет данных о сессии"
        
        time_until_next = "Готово"
        if auto_session.next_mine_time:
            time_left = (auto_session.next_mine_time - datetime.now()).seconds
            if time_left > 0:
                hours = time_left // 3600
                minutes = (time_left % 3600) // 60
                time_until_next = f"{hours}ч {minutes}м"
        
        return f"""
🤖 Автодобыча

✅ Статус: Активна
⏱️ Следующий запуск: {time_until_next}
⛽ Топлива осталось: {auto_session.fuel_left} мин.
💰 Минералов для добычи: {len(player.auto_mining_minerals)}

📊 Статистика:
  • Автодобыч: {player.stats.get('auto_mines', 0)}
  • Последний запуск: {auto_session.last_mine_time.strftime('%H:%M:%S') if auto_session.last_mine_time else 'Никогда'}
"""
    
    @staticmethod
    def auto_mining_info() -> str:
        return """
🤖 Информация об автодобыче

📋 Как работает:
1. Купите улучшение "Автодобыча" (4000 🪙)
2. Приобретите топливо (в магазине или ящиках)
3. Включите автодобычу
4. Система автоматически добывает каждые 3 часа

⛽ Типы топлива:
• Угольные брикеты: 60 мин (800 🪙)
• Нефтяное топливо: 180 мин (2000 🪙)
• Энергетические стержни: 300 мин (4000 🪙)
• Плутониевый реактор: 600 мин (8000 🪙)

💰 Доход:
• 50% от обычной добычи
• Автоматическая продажа в золото
• Шанс найти предметы

💡 Автодобыча работает только пока есть топливо!
"""
    
    @staticmethod
    def auto_mining_result(result: Dict[str, Any]) -> str:
        text = """
🤖 Автодобыча завершена!

💰 Результаты:
"""
        
        for res in result.get('results', []):
            text += f"  • {res['mineral'].value}: {res['amount']:.2f} кг (+{res['gold']}🪙)\n"
        
        text += f"\n📊 Всего:\n"
        text += f"  • Минералов: {result.get('total_mineral', 0):.2f} кг\n"
        text += f"  • Золота: {result.get('total_gold', 0)} 🪙\n"
        text += f"  • Опыта: {result.get('experience', 0)}\n"
        text += f"  • Топлива осталось: {result.get('fuel_left', 0)} мин.\n"
        
        if result.get('items'):
            text += "\n🎁 Найдены предметы:\n"
            for item in result['items']:
                emoji = KeyboardManager.get_rarity_emoji(item.rarity)
                text += f"  {emoji} {item.name}\n"
        
        return text
    
    @staticmethod
    def mining_result(result: Dict[str, Any]) -> str:
        text = f"""
🎉 Добыча завершена!

💰 Добыто: {result['mineral_reward']:.2f} кг {result['mineral'].value}
🪙 Получено золота: {result['gold_earned']}
⭐ Опыта: {result['experience']}
"""
        
        if result.get('level_up'):
            text += f"🏆 Новый уровень шахтёра: {result['new_level']}!\n"
        
        if result.get('items'):
            text += "\n🎁 Найдены предметы:\n"
            for item in result['items']:
                emoji = "🏆" if item.is_collectible else KeyboardManager.get_rarity_emoji(item.rarity)
                text += f"  {emoji} {item.name} ({item.rarity.value})\n"
        
        if result.get('cases'):
            text += "\n📦 Найдены ящики:\n"
            for case in result['cases']:
                text += f"  • {case.name}\n"
        
        return text
    
    @staticmethod
    def gold_balance(player: Player) -> str:
        total_mineral = player.get_total_mineral_value()
        
        text = f"""
🪙 Золотые слитки

💰 Баланс: {player.gold_balance} 🪙
📊 Всего заработано: {player.total_gold_earned} 🪙
💱 Стоимость минералов: {total_mineral:.2f} 🪙 экв.

💡 Золото можно получить:
• Продавая минералы (чем ценнее минерал и выше уровень, тем больше)
• Продавая предметы
• За подписку на каналы
• Через автодобычу
• Покупая донаты ⭐

⚡ Золото можно потратить на:
• Улучшения оборудования
• Покупку ящиков
• Покупку предметов на рынке
• Покупку топлива для автодобычи
"""
        return text
    
    @staticmethod
    def upgrade_info(upgrade: Upgrade) -> str:
        effect = upgrade.current_effect
        next_effect = effect + upgrade.effect_per_level if upgrade.level < upgrade.max_level else effect
        
        if upgrade.upgrade_type == UpgradeType.MINING_TIME:
            return f"""
{upgrade.upgrade_type.value}

📝 {upgrade.description}
🏆 Уровень: {upgrade.level}/{upgrade.max_level}
💰 Стоимость улучшения: {upgrade.current_price} 🪙
📈 Текущий эффект: +{effect:.0f} минут
📈 Следующий уровень: +{next_effect:.0f} минут
"""
        else:
            return f"""
{upgrade.upgrade_type.value}

📝 {upgrade.description}
🏆 Уровень: {upgrade.level}/{upgrade.max_level}
💰 Стоимость улучшения: {upgrade.current_price} 🪙
📈 Текущий эффект: +{effect:.1%}
📈 Следующий уровень: +{next_effect:.1%}
"""
    
    @staticmethod
    def upgrade_effects() -> str:
        return """
📊 Эффекты улучшений:

👷 Уровень шахтёра: +15% всех характеристик за уровень
💪 Сила удара: +8% дохода от добычи за уровень
⚡ Скорость копания: -5% времени добычи за уровень
⏱️ Длительность смены: +3 минуты времени добычи за уровень
🍀 Удача старателя: +8% шанса предметов за уровень
🔋 Энергоэффективность: +4% эффективности за уровень
🔄 Мультишахта: Открывает новые минералы
🤖 Автодобыча: Разблокирует автодобычу (4000 🪙)
🎁 Шанс ящиков: +1.5% шанса ящиков за уровень
"""
    
    @staticmethod
    def case_info(case: Case) -> str:
        drop_info = "\n🎁 Шансы выпадения:\n"
        for rarity_str, chance in case.drop_chances.items():
            drop_info += f"  {rarity_str}: {chance*100:.1f}%\n"
        
        drop_info += f"\n🏆 Шанс коллекционного: {case.collectible_chance*100:.2f}%"
        
        return f"""
{case.name}

📝 {case.description}
💰 Цена: {case.price} 🪙
🎁 Предметов: {case.min_items}-{case.max_items}
{drop_info}
"""
    
    @staticmethod
    def item_info(item: Item) -> str:
        text = f"""
{KeyboardManager.get_rarity_emoji(item.rarity)} {item.name}

📝 {item.description}
🌟 Редкость: {item.rarity.value}
🔢 Серийный номер: {item.serial_number}
"""
        
        if item.is_collectible and item.collectible_type:
            text += f"🏆 Тип: {item.collectible_type.value}\n"
            text += f"🏆 Коллекционный сувенир\n"
        elif item.item_type == ItemType.FUEL:
            text += f"⛽ Топливо: {item.fuel_amount} минут\n"
            text += f"🪙 Цена продажи: {item.sell_price} 🪙\n"
        else:
            if item.mining_bonus > 1.0:
                text += f"⚡ Бонус добычи: +{(item.mining_bonus-1)*100:.1f}%\n"
            
            if item.luck_bonus > 0:
                text += f"🍀 Бонус удачи: +{item.luck_bonus*100:.1f}%\n"
            
            if item.energy_bonus > 0:
                text += f"🔋 Бонус энергии: +{item.energy_bonus*100:.1f}%\n"
        
        if item.buy_price > 0:
            text += f"💰 Цена покупки: {item.buy_price} 🪙\n"
            text += f"💵 Цена продажи: {item.sell_price} 🪙\n"
        
        return text
    
    @staticmethod
    def collections_stats(collectibles_stats: Dict[str, Any]) -> str:
        total = collectibles_stats.get("total", 0)
        unique = collectibles_stats.get("unique_types", 0)
        percentage = collectibles_stats.get("completion_percentage", 0)
        by_type = collectibles_stats.get("by_type", {})
        
        text = f"""
🏆 Коллекционные сувениры

📊 Статистика:
• Всего предметов: {total}
• Уникальных типов: {unique}/24
• Завершено: {percentage:.1f}%

📈 По типам:
"""
        
        for collectible_type in CollectibleType:
            count = by_type.get(collectible_type.name, 0)
            progress = "✅" if count >= 3 else "🟡" if count > 0 else "❌"
            text += f"  {progress} {collectible_type.value}: {count}/3 шт.\n"
        
        text += f"""
💡 Коллекционные сувениры можно получить:
• При обычной добыче (0.8% шанс)
• Из ящиков (0.4-8% шанс)
• В подарок от администратора
• Из специальных донатных наборов ⭐

🎯 Цель: собрать по 3 сувенира каждого типа (всего 24 типа)!
"""
        
        return text
    
    @staticmethod
    def market_info() -> str:
        return """
🏪 Рынок предметов

Здесь игроки продают предметы за золото 🪙
Вы можете:
• Купить предметы у других игроков
• Выставить свои предметы на продажу
• Отслеживать свои предложения

💡 Совет: Редкие и коллекционные предметы стоят дороже!
"""
    
    @staticmethod
    def donate_menu() -> str:
        return """
⭐ Поддержать проект

Спасибо, что хотите поддержать проект!
Ваша поддержка помогает развивать игру и добавлять новые функции.

🪙 За донаты вы получаете золото с бонусами:
• 1 ⭐ = 80 🪙
• 5 ⭐ = 400 🪙 + 10% бонус + ящик
• 10 ⭐ = 850 🪙 + 20% бонус + редкий ящик
• 20 ⭐ = 1800 🪙 + 30% бонус + ящик + топливо
• 50 ⭐ = 4500 🪙 + 50% бонус + эпический ящик + продвинутое топливо
• 100 ⭐ = 9000 🪙 + 100% бонус + легендарный ящик + премиум топливо

🎁 Также есть специальные наборы с уникальными предметами!
"""
    
    @staticmethod
    def special_donates() -> str:
        return """
🎁 Специальные донатные наборы

🪨 Стартовый набор (50 ⭐):
• 5000 🪙 (вместо 4000)
• Эпический ящик
• Продвинутое топливо (180 минут)
• Редкий инструмент

⚡ Промышленный набор (100 ⭐):
• 12000 🪙 (вместо 8000)
• Легендарный ящик
• Премиум топливо (300 минут)
• Эпический инструмент
• Редкий талисман удачи

👑 Магнатский набор (200 ⭐):
• 30000 🪙 (вместо 16000)
• Мифический ящик
• Ультра топливо (600 минут)
• Легендарный инструмент
• Эпический талисман удачи
• Случайный коллекционный предмет

🤖 Автодобыча (50 ⭐):
• 4400 🪙
• Продвинутое топливо (180 минут)
• Премиум топливо (300 минут)
• Улучшение автодобычи (+1 уровень)

🏺 Коллекционный набор (100 ⭐):
• 10000 🪙
• Эпический ящик
• Легендарный ящик
• Случайный коллекционный предмет
• Коллекционный значок
"""
    
    @staticmethod
    def donate_info(stars: int) -> str:
        reward = data_manager.get_donate_reward(stars)
        
        text = f"""
⭐ Донат на {stars} звёзд

🪙 Золота: {reward['gold']}
🎁 Бонус: +{reward['bonus_percent']}%
📊 Итого: {reward['gold'] + int(reward['gold'] * reward['bonus_percent'] / 100)} 🪙

🎁 Предметы в наборе:
"""
        
        if reward.get('items'):
            for item in reward['items']:
                if item == "common_case":
                    text += "• 📦 Обычный ящик\n"
                elif item == "rare_case":
                    text += "• 🎁 Редкий ящик\n"
                elif item == "epic_case":
                    text += "• 💎 Эпический ящик\n"
                elif item == "legendary_case":
                    text += "• 👑 Легендарный ящик\n"
                elif item == "mythic_case":
                    text += "• ✨ Мифический ящик\n"
                elif item == "common_fuel":
                    text += "• ⛽ Угольные брикеты (60 минут)\n"
                elif item == "advanced_fuel":
                    text += "• 🔥 Нефтяное топливо (180 минут)\n"
                elif item == "premium_fuel":
                    text += "• ⚡ Энергетические стержни (300 минут)\n"
                elif item == "ultra_fuel":
                    text += "• 🚀 Плутониевый реактор (600 минут)\n"
                elif item == "random_tool":
                    text += "• ⛏️ Случайный инструмент\n"
                elif item == "random_collectible":
                    text += "• 🏆 Случайный коллекционный предмет\n"
                elif item == "auto_mining_upgrade":
                    text += "• 🤖 Улучшение автодобычи\n"
        else:
            text += "• Без дополнительных предметов\n"
        
        return text
    
    @staticmethod
    def donate_thank_you(result: Dict[str, Any]) -> str:
        text = f"""
🎉 Спасибо за поддержку проекта!

⭐ Получено звёзд: {result['stars']}
🪙 Начислено золота: {result['gold']}
🎁 Бонус: +{result.get('bonus_percent', 0)}%

🎊 Ваш вклад помогает развивать игру!
"""
        
        if result.get('items'):
            text += "\n🎁 Полученные предметы:\n"
            for item in result['items']:
                if hasattr(item, 'name'):
                    emoji = "🏆" if getattr(item, 'is_collectible', False) else KeyboardManager.get_rarity_emoji(getattr(item, 'rarity', ItemRarity.COMMON))
                    text += f"{emoji} {item.name}\n"
        
        text += f"\n💰 Теперь у вас: {result['player'].gold_balance} 🪙"
        
        return text
    
    @staticmethod
    def pay_support_info() -> str:
        return f"""
ℹ️ Информация о возврате средств

⭐ Донаты в Telegram Stars:
• Являются добровольной поддержкой проекта
• Не подразумевают возврат средств по умолчанию
• Дают виртуальные внутриигровые бонусы (золото, предметы)

🔙 Возврат средств возможен в исключительных случаях:
• Ошибка платежной системы
• Двойное списание
• Технические проблемы с получением награды

📞 Для запроса возврата:
1. Сохраните информацию о платеже
2. Обратитесь к администратору {ADMIN_USERNAME}
3. Укажите ID платежа и причину возврата

⏱️ Срок рассмотрения заявки: до 7 рабочих дней
"""
    
    @staticmethod
    def help_text() -> str:
        return f"""
❓ Помощь по игре

Основные команды:
/start - Начало игры
/mine - Добыча минералов
/profile - Мой профиль
/donate - Поддержать проект
/automine - Автодобыча
/collections - Коллекционные сувениры
/paysupport - Информация о возврате средств
/help - Эта справка

Новые функции:
• 🤖 Автодобыча - требует улучшение и топливо
• ⏱️ Длительность смены - +3 минуты за уровень
• 🏆 Коллекционные сувениры - 24 типа по 3 предмета
• 🔢 Серийные номера - у каждого предмета уникальный номер
• ⭐ Донаты - поддержка проекта с бонусами

Экономика:
1. Добывайте минералы (чем ценнее, тем дольше)
2. Продавайте их за золото (чем выше уровень, тем лучше курс)
3. Покупайте улучшения и ящики за золото
4. Собирайте коллекционные сувениры
5. Используйте автодобычу с топливом
6. Поддерживайте проект донатами ⭐

📞 По всем вопросам: {ADMIN_USERNAME}
"""
    
    @staticmethod
    def shop_fuel_info() -> str:
        return """
🛒 Магазин топлива

⛽ Выберите тип топлива:

1. ⛽ Угольные брикеты - 800 🪙
   • 60 минут автодобычи
   • Для начального уровня

2. 🔥 Нефтяное топливо - 2000 🪙
   • 180 минут автодобычи
   • Лучшее соотношение цены

3. ⚡ Энергетические стержни - 4000 🪙
   • 300 минут автодобычи
   • Для активных игроков

4. 🚀 Плутониевый реактор - 8000 🪙
   • 600 минут автодобычи
   • Максимальная эффективность

💡 Автодобыча работает каждые 3 часа, пока есть топливо!
"""

# ========== ГЛОБАЛЬНЫЙ МЕНЕДЖЕР ДАННЫХ ==========

data_manager = None
bot_instance = None

# ========== ОСНОВНОЙ БОТ ==========

class MinerichBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.keyboard_manager = KeyboardManager()
        self.text_templates = TextTemplates()
        self.donate_keyboards = DonateKeyboards()
        
        self.user_states = {}
        
        global data_manager, bot_instance
        data_manager = DataManager(self.bot)
        bot_instance = self
        
        self.register_handlers()
    
    def register_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Привет! Я {GAME_NAME}\n\nДля игры со мной напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            player = data_manager.get_or_create_player(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "Шахтёр"
            )
            
            await message.answer(
                self.text_templates.welcome(player.first_name),
                reply_markup=self.keyboard_manager.main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("donate"))
        async def cmd_donate(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для донатов напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            await message.answer(
                self.text_templates.donate_menu(),
                reply_markup=self.donate_keyboards.donate_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("paysupport"))
        async def cmd_paysupport(message: Message):
            await message.answer(
                self.text_templates.pay_support_info(),
                reply_markup=self.keyboard_manager.main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("mine"))
        async def cmd_mine(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для добычи напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            player = data_manager.get_or_create_player(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "Шахтёр"
            )
            
            await message.answer(
                "⛏️ Выберите минерал для добычи:\n\n*Начинайте с самых простых и постепенно открывайте более ценные!*",
                reply_markup=self.keyboard_manager.mining_menu(player),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("profile"))
        async def cmd_profile(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для просмотра профиля напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            player = data_manager.get_or_create_player(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "Шахтёр"
            )
            
            await message.answer(
                self.text_templates.profile(player),
                reply_markup=self.keyboard_manager.main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("gold"))
        async def cmd_gold(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для работы с золотом напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            player = data_manager.get_or_create_player(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "Шахтёр"
            )
            
            await message.answer(
                self.text_templates.gold_balance(player),
                reply_markup=self.keyboard_manager.gold_menu(player.gold_balance),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("automine"))
        async def cmd_automine(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для автодобычи напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            player = data_manager.get_or_create_player(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "Шахтёр"
            )
            
            auto_session = data_manager.auto_mining_sessions.get(message.from_user.id)
            
            await message.answer(
                self.text_templates.auto_mining_status(player, auto_session),
                reply_markup=self.keyboard_manager.auto_mining_menu(player),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("collections"))
        async def cmd_collections(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для просмотра коллекций напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            player = data_manager.get_or_create_player(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "Шахтёр"
            )
            
            collectibles_stats = data_manager.get_player_collectibles_stats(message.from_user.id)
            
            await message.answer(
                self.text_templates.collections_stats(collectibles_stats),
                reply_markup=self.keyboard_manager.collections_menu(collectibles_stats),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            await message.answer(
                self.text_templates.help_text(),
                reply_markup=self.keyboard_manager.main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("shop"))
        async def cmd_shop(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Для доступа к магазину напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            await message.answer(
                "🛒 Магазин\n\nЗдесь вы можете купить всё необходимое для игры!",
                reply_markup=self.keyboard_manager.shop_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(F.text.contains("donate"))
        async def handle_donate_text(message: Message):
            if message.chat.type != "private":
                return
            
            await cmd_donate(message)
        
        @self.dp.pre_checkout_query()
        async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
            try:
                await pre_checkout_query.answer(ok=True)
            except:
                await pre_checkout_query.answer(ok=False, error_message="Произошла ошибка обработки платежа")
        
        @self.dp.message(F.successful_payment)
        async def success_payment_handler(message: Message):
            try:
                payment = message.successful_payment
                user_id = message.from_user.id
                
                payload = payment.invoice_payload
                if payload.startswith("donate_"):
                    try:
                        stars_str = payload.split("_")[1]
                        stars = int(stars_str)
                        
                        success, result_message, result = data_manager.process_donation(
                            user_id, stars, payload
                        )
                        
                        if success:
                            await message.answer(
                                self.text_templates.donate_thank_you(result),
                                reply_markup=self.donate_keyboards.donate_thank_you(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            
                            try:
                                player = data_manager.players.get(user_id)
                                if player and ADMIN_ID:
                                    await self.bot.send_message(
                                        ADMIN_ID,
                                        f"🎁 Новый донат!\n\n"
                                        f"👤 Игрок: {player.first_name} (@{player.username})\n"
                                        f"⭐ Звёзд: {stars}\n"
                                        f"🪙 Золота: {result['gold']}\n"
                                        f"💰 Сумма: {payment.total_amount / 100} {payment.currency}",
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                            except:
                                pass
                        else:
                            await message.answer(
                                f"❌ Ошибка обработки платежа: {result_message}",
                                reply_markup=self.keyboard_manager.main_menu()
                            )
                    except:
                        await message.answer(
                            "❌ Ошибка обработки платежа. Обратитесь к администратору.",
                            reply_markup=self.keyboard_manager.main_menu()
                        )
                else:
                    await message.answer(
                        "❌ Неизвестный тип платежа",
                        reply_markup=self.keyboard_manager.main_menu()
                    )
                    
            except:
                await message.answer(
                    "❌ Произошла ошибка при обработке платежа. Обратитесь к администратору.",
                    reply_markup=self.keyboard_manager.main_menu()
                )
        
        @self.dp.message(Command("admin"))
        async def cmd_admin(message: Message):
            if message.chat.type != "private":
                await message.answer("⛔ Админ панель доступна только в личных сообщениях!")
                return
            
            if message.from_user.id != ADMIN_ID:
                await message.answer("⛔ У вас нет прав администратора!")
                return
            
            await message.answer(
                "👑 Админ панель",
                reply_markup=self.keyboard_manager.admin_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("addbot"))
        async def cmd_addbot(message: Message):
            if message.chat.type != "private":
                await message.answer("⛔ Эта команда доступна только в личных сообщениях!")
                return
            
            if message.from_user.id != ADMIN_ID:
                await message.answer("⛔ У вас нет прав администратора!")
                return
            
            instructions = f"""
🤖 Как добавить бота в канал:

1. Создайте канал в Telegram
2. Добавьте бота @CRIPTO_MAINER_GAMEBOT как администратора
3. Дайте боту права:
   • Отправка сообщений
   • Просмотр участников
   • Добавление участников
4. После добавления используйте команду /admin и выберите "🔧 Проверить каналы"

⚠️ Важно: Бот должен быть администратором для проверки подписок игроков!
"""
            
            await message.answer(
                instructions,
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(Command("stats"))
        async def cmd_stats(message: Message):
            if message.chat.type != "private":
                await message.answer("⛔ Статистика доступна только в личных сообщениях!")
                return
            
            if message.from_user.id != ADMIN_ID:
                await message.answer("⛔ У вас нет прав администратора!")
                return
            
            total_players = len(data_manager.players)
            active_today = sum(
                1 for player in data_manager.players.values()
                if player.last_mining_time and (datetime.now() - player.last_mining_time).days < 1
            )
            total_mined = sum(player.total_mined for player in data_manager.players.values())
            total_gold = sum(player.gold_balance for player in data_manager.players.values())
            
            total_collectibles = 0
            for player in data_manager.players.values():
                total_collectibles += sum(player.collectibles.values())
            
            stats_text = f"""
📊 Статистика бота v{VERSION}

👥 Игроков всего: {total_players}
🎮 Активных сегодня: {active_today}
⛏️ Всего добыто: {total_mined:.2f} кг
🪙 Золота в системе: {total_gold}
🏆 Коллекционных предметов: {total_collectibles}

🤖 Автодобыча:
  Активных: {sum(1 for p in data_manager.players.values() if p.auto_mining_enabled)}
  Всего автодобыч: {sum(p.stats.get('auto_mines', 0) for p in data_manager.players.values())}

📦 Ящики:
  Всего ящиков в системе: {len(data_manager.cases)}
  Всего предметов в системе: {len(data_manager.items)}

📢 Каналы:
  Всего каналов: {len(data_manager.channels)}
  Каналов с ботом: {sum(1 for c in data_manager.channels.values() if c.bot_member)}

📈 Топ 5 игроков по уровню:
"""
            
            sorted_players = sorted(
                data_manager.players.values(),
                key=lambda p: p.miner_level,
                reverse=True
            )[:5]
            
            for i, player in enumerate(sorted_players, 1):
                collectibles_count = sum(player.collectibles.values())
                stats_text += f"{i}. {player.first_name} (@{player.username}) - Ур. {player.miner_level} | 🪙{player.gold_balance} | 🏆{collectibles_count}\n"
            
            await message.answer(stats_text, parse_mode=ParseMode.MARKDOWN)
        
        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery):
            data = callback.data
            
            try:
                await callback.answer()
                
                if data == "back_to_main":
                    await callback.message.edit_text(
                        f"⛏️ {GAME_NAME}\n\nГлавное меню",
                        reply_markup=self.keyboard_manager.main_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "profile":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    await callback.message.edit_text(
                        self.text_templates.profile(player),
                        reply_markup=self.keyboard_manager.main_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "donate":
                    await callback.message.edit_text(
                        self.text_templates.donate_menu(),
                        reply_markup=self.donate_keyboards.donate_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("donate_"):
                    donate_type = data[7:]
                    
                    if donate_type == "help":
                        await callback.message.edit_text(
                            self.text_templates.pay_support_info(),
                            reply_markup=self.donate_keyboards.back_button("donate"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif donate_type == "special":
                        await callback.message.edit_text(
                            self.text_templates.special_donates(),
                            reply_markup=self.donate_keyboards.special_donates(),
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
                        
                        await callback.message.edit_text(
                            f"⭐ {reward['title']} - {stars} звёзд\n\n" +
                            self.text_templates.donate_info(stars),
                            reply_markup=self.donate_keyboards.confirm_donation(
                                stars, data_manager.get_donate_reward(stars)["gold"]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    else:
                        try:
                            stars = int(donate_type)
                            if stars > 0:
                                await callback.message.edit_text(
                                    self.text_templates.donate_info(stars),
                                    reply_markup=self.donate_keyboards.confirm_donation(
                                        stars, data_manager.get_donate_reward(stars)["gold"]
                                    ),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        except:
                            await callback.answer("❌ Неизвестный тип доната")
                
                elif data.startswith("confirm_donate_"):
                    try:
                        stars_str = data[15:]
                        stars = int(stars_str)
                        
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        
                        reward = data_manager.get_donate_reward(stars)
                        total_gold = reward["gold"] + int(reward["gold"] * reward["bonus_percent"] / 100)
                        
                        prices = [LabeledPrice(label="XTR", amount=stars)]
                        
                        title = f"Донат {stars} ⭐ - {total_gold} 🪙"
                        description = f"Поддержка проекта {GAME_NAME}. Вы получите {total_gold} золота с бонусами!"
                        payload = f"donate_{stars}"
                        
                        await callback.message.delete()
                        
                        await callback.message.answer_invoice(
                            title=title,
                            description=description,
                            payload=payload,
                            provider_token="",
                            currency="XTR",
                            prices=prices,
                            reply_markup=self.donate_keyboards.payment_keyboard(stars)
                        )
                        
                    except:
                        await callback.answer("❌ Ошибка создания счета для оплаты")
                
                elif data == "shop":
                    await callback.message.edit_text(
                        "🛒 Магазин\n\nЗдесь вы можете купить всё необходимое для игры!",
                        reply_markup=self.keyboard_manager.shop_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "shop_fuel":
                    await callback.message.edit_text(
                        self.text_templates.shop_fuel_info(),
                        reply_markup=self.keyboard_manager.shop_fuel_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("shop_buy_fuel_"):
                    fuel_type = data[14:]
                    player = data_manager.players.get(callback.from_user.id)
                    
                    if not player:
                        await callback.answer("❌ Шахтёр не найден")
                        return
                    
                    fuel_prices = {
                        "basic": 800,
                        "advanced": 2000,
                        "premium": 4000,
                        "ultra": 8000
                    }
                    
                    fuel_minutes = {
                        "basic": 60,
                        "advanced": 180,
                        "premium": 300,
                        "ultra": 600
                    }
                    
                    fuel_names = {
                        "basic": "⛽ Угольные брикеты",
                        "advanced": "🔥 Нефтяное топливо",
                        "premium": "⚡ Энергетические стержни",
                        "ultra": "🚀 Плутониевый реактор"
                    }
                    
                    price = fuel_prices.get(fuel_type)
                    minutes = fuel_minutes.get(fuel_type)
                    name = fuel_names.get(fuel_type)
                    
                    if price is None:
                        await callback.answer("❌ Неизвестный тип топлива")
                        return
                    
                    if player.gold_balance < price:
                        await callback.answer(f"❌ Недостаточно золота. Нужно: {price} 🪙")
                        return
                    
                    player.gold_balance -= price
                    
                    item_id = str(uuid.uuid4())
                    fuel_item = Item(
                        item_id=item_id,
                        serial_number=data_manager.generate_serial_number(),
                        name=name,
                        item_type=ItemType.FUEL,
                        rarity=ItemRarity.COMMON if fuel_type == "basic" else ItemRarity.RARE if fuel_type == "advanced" else ItemRarity.EPIC if fuel_type == "premium" else ItemRarity.LEGENDARY,
                        description=f"Топливо для автодобычи ({minutes} минут)",
                        buy_price=price,
                        sell_price=int(price * 0.5),
                        is_tradable=True,
                        owner_id=callback.from_user.id,
                        fuel_amount=minutes
                    )
                    
                    data_manager.items[item_id] = fuel_item
                    player.inventory.append(item_id)
                    data_manager.save_data()
                    
                    await callback.message.edit_text(
                        f"✅ Куплено {name} за {price} 🪙\n\nТопливо добавлено в ваш инвентарь!",
                        reply_markup=self.keyboard_manager.shop_fuel_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "mining_menu":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    await callback.message.edit_text(
                        "⛏️ Выберите минерал для добычи:\n\n*Начинайте с самых простых и постепенно открывайте более ценные!*",
                        reply_markup=self.keyboard_manager.mining_menu(player),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("start_mine_"):
                    mineral_name = data[11:]
                    success, message = data_manager.start_mining(
                        callback.from_user.id,
                        mineral_name
                    )
                    
                    if success:
                        session = data_manager.active_mining_sessions[callback.from_user.id]
                        await callback.message.edit_text(
                            self.text_templates.mining_status(session),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="📊 Статус добычи", callback_data="mining_status")],
                                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif message == "mining_status":
                        session = data_manager.active_mining_sessions[callback.from_user.id]
                        await callback.message.edit_text(
                            self.text_templates.mining_status(session),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="📊 Статус добычи", callback_data="mining_status")],
                                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "mining_status":
                    if callback.from_user.id in data_manager.active_mining_sessions:
                        session = data_manager.active_mining_sessions[callback.from_user.id]
                        
                        if datetime.now() >= session.end_time:
                            success, result = data_manager.complete_mining(callback.from_user.id)
                            if success:
                                await callback.message.edit_text(
                                    self.text_templates.mining_result(result),
                                    reply_markup=self.keyboard_manager.main_menu(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await callback.answer(result.get("error", "Ошибка"))
                        else:
                            await callback.message.edit_text(
                                self.text_templates.mining_status(session),
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="📊 Обновить статус", callback_data="mining_status")],
                                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                                    ]
                                ),
                                parse_mode=ParseMode.MARKDOWN
                            )
                    else:
                        await callback.answer("❌ Нет активной добычи")
                
                elif data == "my_minerals":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    minerals_text = "💰 Ваши минералы:\n\n"
                    for mineral_name, amount in player.mineral_balance.items():
                        if amount > 0:
                            mineral_value = mineral_name
                            for m in MineralType:
                                if m.name == mineral_name:
                                    mineral_value = m.value
                                    break
                            minerals_text += f"{mineral_value}: {amount:.2f} кг\n"
                    
                    if not any(amount > 0 for amount in player.mineral_balance.values()):
                        minerals_text += "Минералы отсутствуют\n"
                    
                    total_value = player.get_total_mineral_value()
                    minerals_text += f"\n💰 Общая стоимость: {total_value:.2f} 🪙"
                    
                    await callback.message.edit_text(
                        minerals_text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="💱 Продать ВСЕ минералы", callback_data="convert_all_minerals")],
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="mining_menu")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "auto_mining":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                    
                    await callback.message.edit_text(
                        self.text_templates.auto_mining_status(player, auto_session),
                        reply_markup=self.keyboard_manager.auto_mining_menu(player),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "toggle_auto_mining":
                    success, message = data_manager.toggle_auto_mining(callback.from_user.id)
                    
                    if success:
                        player = data_manager.players[callback.from_user.id]
                        auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                        
                        await callback.message.edit_text(
                            f"✅ {message}\n\n" + self.text_templates.auto_mining_status(player, auto_session),
                            reply_markup=self.keyboard_manager.auto_mining_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "buy_fuel_menu":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    await callback.message.edit_text(
                        "⛽ Выберите топливо для использования из инвентаря:",
                        reply_markup=self.keyboard_manager.buy_fuel_menu(player),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("use_fuel_"):
                    fuel_type = data[9:]
                    success, message = data_manager.buy_fuel(callback.from_user.id, fuel_type)
                    
                    if success:
                        await callback.answer(f"✅ {message}")
                        player = data_manager.players[callback.from_user.id]
                        await callback.message.edit_text(
                            self.text_templates.auto_mining_status(player, None),
                            reply_markup=self.keyboard_manager.auto_mining_menu(player),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data.startswith("use_fuel_item_"):
                    item_id = data[14:]
                    item = data_manager.items.get(item_id)
                    
                    if item and item.item_type == ItemType.FUEL:
                        player = data_manager.players.get(callback.from_user.id)
                        if player and item_id in player.inventory:
                            player.fuel += item.fuel_amount
                            player.inventory.remove(item_id)
                            del data_manager.items[item_id]
                            data_manager.save_data()
                            
                            await callback.message.edit_text(
                                f"✅ Заправлено {item.fuel_amount} минут автодобычи!",
                                reply_markup=self.keyboard_manager.auto_mining_menu(player),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer("❌ Предмет не найден")
                    else:
                        await callback.answer("❌ Это не топливо")
                
                elif data == "auto_mining_status":
                    player = data_manager.players.get(callback.from_user.id)
                    auto_session = data_manager.auto_mining_sessions.get(callback.from_user.id)
                    
                    if player:
                        await callback.message.edit_text(
                            self.text_templates.auto_mining_status(player, auto_session),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="auto_mining")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                
                elif data == "fuel_status":
                    player = data_manager.players.get(callback.from_user.id)
                    if player:
                        await callback.message.edit_text(
                            f"⛽ Статус топлива: {player.fuel} минут",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="auto_mining")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                
                elif data == "auto_mining_info":
                    await callback.message.edit_text(
                        self.text_templates.auto_mining_info(),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="auto_mining")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "collections":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                    
                    await callback.message.edit_text(
                        self.text_templates.collections_stats(collectibles_stats),
                        reply_markup=self.keyboard_manager.collections_menu(collectibles_stats),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "collections_stats":
                    collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                    
                    await callback.message.edit_text(
                        self.text_templates.collections_stats(collectibles_stats),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("collectible_type_"):
                    collectible_type_name = data[17:]
                    try:
                        collectible_type = None
                        for ct in CollectibleType:
                            if ct.name == collectible_type_name:
                                collectible_type = ct
                                break
                        
                        if collectible_type:
                            player = data_manager.players.get(callback.from_user.id)
                            
                            if player:
                                count = player.collectibles.get(collectible_type_name, 0)
                                
                                text = f"""
{collectible_type.value}

📊 У вас есть: {count}/3 шт.
🎯 Статус: {'✅ Полная коллекция' if count >= 3 else '🟡 Частично собрано' if count > 0 else '❌ Не собрано'}
💎 Ценность: Коллекционный предмет
💰 Можно продавать

💡 Этот предмет можно получить:
• При обычной добыче (0.8% шанс)
• Из ящиков (0.4-8% шанс)
• В подарок от администратора
• Из специальных донатных наборов ⭐
"""
                                
                                await callback.message.edit_text(
                                    text,
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")]
                                        ]
                                    ),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                    except:
                        await callback.answer("❌ Тип коллекционного предмета не найден")
                
                elif data == "collections_types":
                    collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                    by_type = collectibles_stats.get("by_type", {})
                    
                    text = "🎯 Типы коллекционных предметов:\n\n"
                    
                    for collectible_type in CollectibleType:
                        count = by_type.get(collectible_type.name, 0)
                        text += f"{collectible_type.value}: {count}/3 шт.\n"
                    
                    text += f"\nВсего типов: {len(CollectibleType)}\n"
                    text += f"Ваш прогресс: {collectibles_stats.get('unique_types', 0)}/{len(CollectibleType)}"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "collections_progress":
                    collectibles_stats = data_manager.get_player_collectibles_stats(callback.from_user.id)
                    percentage = collectibles_stats.get("completion_percentage", 0)
                    
                    progress_bar_length = 20
                    filled = int(percentage / 100 * progress_bar_length)
                    progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
                    
                    text = f"""
📊 Прогресс коллекции

{progress_bar} {percentage:.1f}%

🎯 Собрано уникальных типов: {collectibles_stats.get('unique_types', 0)}/24
📈 Всего предметов: {collectibles_stats.get('total', 0)}

🏆 Награды за завершение:
• 100%: 40,000 🪙 + Мифический ящик
• 75%: 20,000 🪙 + Легендарный ящик
• 50%: 8,000 🪙 + Эпический ящик
• 25%: 4,000 🪙 + Редкий ящик
"""
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "gold":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    await callback.message.edit_text(
                        self.text_templates.gold_balance(player),
                        reply_markup=self.keyboard_manager.gold_menu(player.gold_balance),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "gold_balance":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    await callback.message.edit_text(
                        self.text_templates.gold_balance(player),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="gold")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "convert_all_minerals":
                    success, message, gold = data_manager.convert_all_minerals_to_gold(
                        callback.from_user.id
                    )
                    
                    if success:
                        await callback.message.edit_text(
                            f"✅ {message}",
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "upgrades":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    await callback.message.edit_text(
                        "⚡ Улучшения оборудования\n\n"
                        "Улучшайте характеристики за золото:",
                        reply_markup=self.keyboard_manager.upgrades_menu(
                            player.upgrades, player.gold_balance
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "upgrade_effects":
                    await callback.message.edit_text(
                        self.text_templates.upgrade_effects(),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="upgrades")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("buy_upgrade_"):
                    upgrade_name = data[12:]
                    success, message = data_manager.buy_upgrade(
                        callback.from_user.id,
                        upgrade_name
                    )
                    
                    if success:
                        player = data_manager.players[callback.from_user.id]
                        await callback.message.edit_text(
                            f"✅ {message}\n\n"
                            f"Выберите следующее улучшение:",
                            reply_markup=self.keyboard_manager.upgrades_menu(
                                player.upgrades, player.gold_balance
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "cases":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    await callback.message.edit_text(
                        "📦 Ящики с предметами\n\n"
                        "Купите ящики за золото:",
                        reply_markup=self.keyboard_manager.cases_menu(
                            data_manager.cases, player.gold_balance
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("buy_case_"):
                    case_type_name = data[9:]
                    success, message, case_item = data_manager.buy_case(
                        callback.from_user.id,
                        case_type_name
                    )
                    
                    if success:
                        player = data_manager.players[callback.from_user.id]
                        await callback.message.edit_text(
                            f"✅ {message}\n\n"
                            f"Ящик добавлен в инвентарь!",
                            reply_markup=self.keyboard_manager.cases_menu(
                                data_manager.cases, player.gold_balance
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "open_cases":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    cases = []
                    for item_id in player.inventory:
                        item = data_manager.items.get(item_id)
                        if item and item.item_type == ItemType.CASE:
                            cases.append(item)
                    
                    if not cases:
                        await callback.answer("❌ У вас нет ящиков")
                        return
                    
                    case_item = random.choice(cases)
                    success, message, items = data_manager.open_case(
                        callback.from_user.id,
                        case_item.item_id
                    )
                    
                    if success:
                        text = f"✅ {message}\n\n🎁 Получены предметы:\n"
                        for item in items:
                            emoji = "🏆" if item.is_collectible else KeyboardManager.get_rarity_emoji(item.rarity)
                            text += f"{emoji} {item.name} ({item.rarity.value})\n"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data.startswith("open_"):
                    case_item_id = data[5:]
                    success, message, items = data_manager.open_case(
                        callback.from_user.id,
                        case_item_id
                    )
                    
                    if success:
                        text = f"✅ {message}\n\n🎁 Получены предметы:\n"
                        for item in items:
                            emoji = "🏆" if item.is_collectible else KeyboardManager.get_rarity_emoji(item.rarity)
                            text += f"{emoji} {item.name} ({item.rarity.value})\n"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "inventory":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    if not player.inventory:
                        await callback.message.edit_text(
                            "🎒 Ваш инвентарь пуст!\n\nНайдите предметы при добыче или купите их в магазине!",
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.message.edit_text(
                            f"🎒 Инвентарь ({len(player.inventory)} предметов)",
                            reply_markup=self.keyboard_manager.inventory_menu(
                                player, data_manager.items
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                
                elif data.startswith("inv_page_"):
                    page = int(data[9:])
                    player = data_manager.players.get(callback.from_user.id)
                    if player:
                        await callback.message.edit_text(
                            f"🎒 Инвентарь (стр. {page+1})",
                            reply_markup=self.keyboard_manager.inventory_menu(
                                player, data_manager.items, page
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                
                elif data.startswith("item_"):
                    item_id = data[5:]
                    item = data_manager.items.get(item_id)
                    
                    if item:
                        player = data_manager.players.get(callback.from_user.id)
                        is_equipped = item_id in player.equipped_items.values() if player else False
                        
                        await callback.message.edit_text(
                            self.text_templates.item_info(item),
                            reply_markup=self.keyboard_manager.item_menu(item, is_equipped),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer("❌ Предмет не найден")
                
                elif data.startswith("equip_"):
                    item_id = data[6:]
                    success, message = data_manager.equip_item(
                        callback.from_user.id,
                        item_id
                    )
                    
                    if success:
                        await callback.answer(f"✅ {message}")
                        item = data_manager.items.get(item_id)
                        if item:
                            await callback.message.edit_text(
                                self.text_templates.item_info(item),
                                reply_markup=self.keyboard_manager.item_menu(item, True),
                                parse_mode=ParseMode.MARKDOWN
                            )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data.startswith("unequip_"):
                    slot_or_item_id = data[8:]
                    
                    if slot_or_item_id in ["tool", "charm", "chip", "core"]:
                        success, message = data_manager.unequip_item(
                            callback.from_user.id,
                            slot_or_item_id
                        )
                    else:
                        player = data_manager.players.get(callback.from_user.id)
                        slot = None
                        for s, iid in player.equipped_items.items():
                            if iid == slot_or_item_id:
                                slot = s
                                break
                        
                        if slot:
                            success, message = data_manager.unequip_item(
                                callback.from_user.id,
                                slot
                            )
                        else:
                            await callback.answer("❌ Предмет не экипирован")
                            return
                    
                    if success:
                        await callback.answer(f"✅ {message}")
                        player = data_manager.players[callback.from_user.id]
                        await callback.message.edit_text(
                            "🛡️ Экипировка",
                            reply_markup=self.keyboard_manager.equipment_menu(
                                player.equipped_items,
                                data_manager.items
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "equipment":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    await callback.message.edit_text(
                        "🛡️ Экипировка",
                        reply_markup=self.keyboard_manager.equipment_menu(
                            player.equipped_items,
                            data_manager.items
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "equipment_bonuses":
                    player = data_manager.players.get(callback.from_user.id)
                    if not player:
                        await callback.answer("❌ Шахтёр не найден")
                        return
                    
                    bonuses_text = "📊 Бонусы от экипировки:\n\n"
                    total_mining_bonus = 1.0
                    total_luck_bonus = 0.0
                    
                    for slot, item_id in player.equipped_items.items():
                        item = data_manager.items.get(item_id)
                        if item:
                            if item.mining_bonus > 1.0:
                                total_mining_bonus *= item.mining_bonus
                            if item.luck_bonus > 0:
                                total_luck_bonus += item.luck_bonus
                    
                    bonuses_text += f"⚡ Общий бонус добычи: +{(total_mining_bonus-1)*100:.1f}%\n"
                    bonuses_text += f"🍀 Общий бонус удачи: +{total_luck_bonus*100:.1f}%\n"
                    
                    await callback.message.edit_text(
                        bonuses_text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="equipment")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "sell_all_common_items":
                    success, message, sold_count, total_price = data_manager.sell_all_common_items(callback.from_user.id)
                    
                    if success:
                        await callback.message.edit_text(
                            f"✅ {message}\n"
                            f"💰 Получено: {total_price} 🪙",
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data.startswith("sell_"):
                    item_id = data[5:]
                    success, message = data_manager.sell_item(
                        callback.from_user.id,
                        item_id
                    )
                    
                    if success:
                        await callback.message.edit_text(
                            f"✅ {message}",
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data.startswith("market_sell_"):
                    item_id = data[12:]
                    player = data_manager.players.get(callback.from_user.id)
                    
                    if not player or item_id not in player.inventory:
                        await callback.answer("❌ Предмет не найден в инвентаре")
                        return
                    
                    item = data_manager.items.get(item_id)
                    if not item or not item.is_tradable:
                        await callback.answer("❌ Этот предмет нельзя продавать")
                        return
                    
                    self.user_states[callback.from_user.id] = {
                        "action": "create_offer_price",
                        "selected_item": item_id
                    }
                    
                    await callback.message.edit_text(
                        f"Выбран предмет: {item.name}\n\nВведите цену в золоте:",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="❌ Отмена", callback_data=f"item_{item_id}")]
                            ]
                        )
                    )
                
                elif data == "market":
                    await callback.message.edit_text(
                        self.text_templates.market_info(),
                        reply_markup=self.keyboard_manager.market_menu(
                            data_manager.market_offers,
                            data_manager.items
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("market_page_"):
                    page = int(data[12:])
                    await callback.message.edit_text(
                        self.text_templates.market_info(),
                        reply_markup=self.keyboard_manager.market_menu(
                            data_manager.market_offers,
                            data_manager.items,
                            page
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("buy_offer_"):
                    offer_id = data[10:]
                    success, message = data_manager.buy_market_offer(
                        callback.from_user.id,
                        offer_id
                    )
                    
                    if success:
                        await callback.message.edit_text(
                            f"✅ {message}",
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer(f"❌ {message}")
                
                elif data == "my_offers":
                    player = data_manager.players.get(callback.from_user.id)
                    if not player:
                        await callback.answer("❌ Шахтёр не найден")
                        return
                    
                    my_offers = [
                        offer for offer in data_manager.market_offers.values()
                        if offer.seller_id == callback.from_user.id
                    ]
                    
                    if not my_offers:
                        await callback.message.edit_text(
                            "📤 У вас нет активных предложений",
                            reply_markup=self.keyboard_manager.back_button("market"),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    
                    text = "📤 Ваши предложения на рынке:\n\n"
                    for i, offer in enumerate(my_offers, 1):
                        item = data_manager.items.get(offer.item_id)
                        if item:
                            text += f"{i}. {item.name} - {offer.price} 🪙\n"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="❌ Снять все предложения", callback_data="cancel_all_offers")],
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="market")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "create_offer":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    if not player.inventory:
                        await callback.answer("❌ В инвентаре нет предметов")
                        return
                    
                    self.user_states[callback.from_user.id] = {
                        "action": "create_offer",
                        "step": "select_item"
                    }
                    
                    text = "Выберите предмет для продажи:\n\n"
                    for i, item_id in enumerate(player.inventory[:10], 1):
                        item = data_manager.items.get(item_id)
                        if item and item.is_tradable:
                            text += f"{i}. {item.name}\n"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="❌ Отмена", callback_data="market")]
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "cancel_all_offers":
                    player = data_manager.players.get(callback.from_user.id)
                    if not player:
                        await callback.answer("❌ Шахтёр не найден")
                        return
                    
                    offers_to_cancel = [
                        offer_id for offer_id, offer in data_manager.market_offers.items()
                        if offer.seller_id == callback.from_user.id
                    ]
                    
                    for offer_id in offers_to_cancel:
                        del data_manager.market_offers[offer_id]
                    
                    data_manager.save_data()
                    
                    await callback.message.edit_text(
                        f"✅ Снято {len(offers_to_cancel)} предложений",
                        reply_markup=self.keyboard_manager.back_button("market"),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data == "channels":
                    await callback.message.edit_text(
                        "📢 Каналы для подписки\n\nПодпишитесь на каналы и получайте награды в золоте!",
                        reply_markup=self.keyboard_manager.channels_menu(
                            data_manager.channels
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif data.startswith("channel_"):
                    channel_id = data[8:]
                    channel = data_manager.channels.get(channel_id)
                    
                    if channel:
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        
                        is_subscribed = channel_id in player.subscribed_channels
                        status = "✅ Подписан" if is_subscribed else "❌ Не подписан"
                        bot_status = "✅ Бот в канале" if channel.bot_member else "⚠️ Бота нет в канале"
                        
                        text = f"""
📢 {channel.name}

🔗 {channel.url}
🏆 Требуется уровень: {channel.required_level}
💰 Награда: {channel.reward} 🪙
📊 Статус: {status}
🤖 {bot_status}
                        """
                        
                        buttons = [
                            [
                                InlineKeyboardButton(text="🔗 Перейти", url=channel.url),
                                InlineKeyboardButton(text="✅ Проверить", callback_data=f"check_{channel_id}")
                            ]
                        ]
                        
                        if channel.bot_member:
                            buttons.append([InlineKeyboardButton(text="🔄 Проверить статус бота", callback_data=f"refresh_bot_{channel_id}")])
                        
                        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="channels")])
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                            parse_mode=ParseMode.MARKDOWN
                        )
                
                elif data.startswith("check_"):
                    channel_id = data[6:]
                    channel = data_manager.channels.get(channel_id)
                    
                    if channel:
                        player = data_manager.get_or_create_player(
                            callback.from_user.id,
                            callback.from_user.username or "",
                            callback.from_user.first_name or "Шахтёр"
                        )
                        
                        if channel_id not in player.subscribed_channels:
                            if not channel.bot_member:
                                bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                                if bot_in_channel:
                                    channel.bot_member = True
                                    data_manager.save_data()
                                else:
                                    await callback.message.edit_text(
                                        f"⚠️ Бот не добавлен в канал или не является администратором!\n\n"
                                        f"Добавьте бота @CRIPTO_MAINER_GAMEBOT в канал как администратора, "
                                        f"чтобы проверять подписки игроков.",
                                        reply_markup=InlineKeyboardMarkup(
                                            inline_keyboard=[
                                                [InlineKeyboardButton(text="⬅️ Назад", callback_data="channels")]
                                            ]
                                        ),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                    return
                            
                            player.subscribed_channels.append(channel_id)
                            player.gold_balance += channel.reward
                            data_manager.save_data()
                            
                            await callback.message.edit_text(
                                f"✅ Подписка подтверждена!\n"
                                f"🎁 Получено: {channel.reward} 🪙",
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="channels")]
                                    ]
                                ),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            await callback.answer("✅ Вы уже подписаны")
                
                elif data == "check_subscriptions":
                    player = data_manager.get_or_create_player(
                        callback.from_user.id,
                        callback.from_user.username or "",
                        callback.from_user.first_name or "Шахтёр"
                    )
                    
                    new_subs = 0
                    total_reward = 0
                    
                    for channel_id, channel in data_manager.channels.items():
                        if channel_id not in player.subscribed_channels:
                            if not channel.bot_member:
                                bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                                if bot_in_channel:
                                    channel.bot_member = True
                                    data_manager.save_data()
                                else:
                                    continue
                            
                            player.subscribed_channels.append(channel_id)
                            player.gold_balance += channel.reward
                            new_subs += 1
                            total_reward += channel.reward
                    
                    if new_subs > 0:
                        data_manager.save_data()
                        await callback.message.edit_text(
                            f"✅ Проверка завершена!\n\n"
                            f"📊 Новых подписок: {new_subs}\n"
                            f"💰 Получено наград: {total_reward} 🪙",
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await callback.answer("ℹ️ Вы уже подписаны на все доступные каналы")
                
                elif data.startswith("refresh_bot_"):
                    channel_id = data[12:]
                    channel = data_manager.channels.get(channel_id)
                    
                    if channel:
                        bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                        if bot_in_channel:
                            channel.bot_member = True
                            data_manager.save_data()
                            await callback.answer("✅ Бот проверен и добавлен в канал!")
                        else:
                            channel.bot_member = False
                            data_manager.save_data()
                            await callback.answer("⚠️ Бот не найден в канале или не является администратором!")
                
                elif data == "help":
                    await callback.message.edit_text(
                        self.text_templates.help_text(),
                        reply_markup=self.keyboard_manager.main_menu(),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif callback.from_user.id == ADMIN_ID:
                    if data == "admin_stats":
                        total_players = len(data_manager.players)
                        active_today = sum(
                            1 for player in data_manager.players.values()
                            if player.last_mining_time and (datetime.now() - player.last_mining_time).days < 1
                        )
                        total_mined = sum(player.total_mined for player in data_manager.players.values())
                        total_gold = sum(player.gold_balance for player in data_manager.players.values())
                        
                        total_collectibles = 0
                        for player in data_manager.players.values():
                            total_collectibles += sum(player.collectibles.values())
                        
                        stats_text = f"""
📊 Статистика бота v{VERSION}

👥 Игроков всего: {total_players}
🎮 Активных сегодня: {active_today}
⛏️ Всего добыто: {total_mined:.2f} кг
🪙 Золота в системе: {total_gold}
🏆 Коллекционных предметов: {total_collectibles}

🤖 Автодобыча:
  Активных: {sum(1 for p in data_manager.players.values() if p.auto_mining_enabled)}
  Всего автодобыч: {sum(p.stats.get('auto_mines', 0) for p in data_manager.players.values())}

📦 Ящики:
  Всего ящиков в системе: {len(data_manager.cases)}
  Всего предметов в системе: {len(data_manager.items)}

📢 Каналы:
  Всего каналов: {len(data_manager.channels)}
  Каналов с ботом: {sum(1 for c in data_manager.channels.values() if c.bot_member)}

📈 Топ 5 игроков по уровню:
"""
                        
                        sorted_players = sorted(
                            data_manager.players.values(),
                            key=lambda p: p.miner_level,
                            reverse=True
                        )[:5]
                        
                        for i, player in enumerate(sorted_players, 1):
                            collectibles_count = sum(player.collectibles.values())
                            stats_text += f"{i}. @{player.username} ({player.first_name}) - Ур. {player.miner_level} | 🪙{player.gold_balance} | 🏆{collectibles_count}\n"
                        
                        await callback.message.edit_text(
                            stats_text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_donate_stats":
                        stats_text = """
⭐ Статистика донатов

📊 Общая статистика:
• Всего игроков: Загружается...
• Всего донатов: Загружается...
• Общая сумма: Загружается...

🎁 Самые популярные донаты:
• 100 ⭐: 0 раз
• 50 ⭐: 0 раз
• 20 ⭐: 0 раз
• 10 ⭐: 0 раз
• 5 ⭐: 0 раз
• 1 ⭐: 0 раз

👑 Топ донатеров:
1. Нет данных

📈 Для полной статистики нужна интеграция с платежной системой.
"""
                        
                        await callback.message.edit_text(
                            stats_text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_players":
                        text = "👤 Список игроков:\n\n"
                        for i, player in enumerate(list(data_manager.players.values())[:20], 1):
                            collectibles_count = sum(player.collectibles.values())
                            text += f"{i}. @{player.username} ({player.first_name}) - Ур. {player.miner_level} | 🪙{player.gold_balance} | 🏆{collectibles_count}\n"
                        
                        if len(data_manager.players) > 20:
                            text += f"\n... и еще {len(data_manager.players) - 20} игроков"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_find_player":
                        self.user_states[callback.from_user.id] = {
                            "action": "find_player",
                            "step": "enter_query"
                        }
                        
                        await callback.message.edit_text(
                            "🔍 Поиск игрока\n\n"
                            "Введите username или ID игрока:",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_add_channel":
                        self.user_states[callback.from_user.id] = {
                            "action": "add_channel",
                            "step": "enter_name"
                        }
                        
                        await callback.message.edit_text(
                            "➕ Добавление канала\n\n"
                            "Введите название канала:",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_remove_channel":
                        text = "➖ Удаление канала\n\nВыберите канал:\n\n"
                        for i, (channel_id, channel) in enumerate(data_manager.channels.items(), 1):
                            bot_status = "✅" if channel.bot_member else "⚠️"
                            text += f"{i}. {bot_status} {channel.name} (ID: {channel_id})\n"
                        
                        if not data_manager.channels:
                            text += "Каналы отсутствуют"
                        
                        self.user_states[callback.from_user.id] = {
                            "action": "remove_channel",
                            "step": "select_channel"
                        }
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_check_channels":
                        text = "🔧 Проверка статуса бота в каналах:\n\n"
                        
                        updated_channels = 0
                        for channel_id, channel in data_manager.channels.items():
                            bot_in_channel = await data_manager.check_bot_in_channel(channel.url)
                            if bot_in_channel != channel.bot_member:
                                channel.bot_member = bot_in_channel
                                updated_channels += 1
                            
                            status = "✅ Бот в канале" if channel.bot_member else "⚠️ Бота нет"
                            text += f"• {channel.name}: {status}\n"
                        
                        if updated_channels > 0:
                            data_manager.save_data()
                            text += f"\n✅ Обновлено {updated_channels} каналов"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_add_bot":
                        instructions = f"""
🤖 Как добавить бота в канал:

1. Создайте канал в Telegram
2. Добавьте бота @CRIPTO_MAINER_GAMEBOT как администратора
3. Дайте боту права:
   • Отправка сообщений
   • Просмотр участников
   • Добавление участников
4. После добавления используйте кнопку "🔧 Проверить каналы"

⚠️ Важно: Бот должен быть администратором для проверки подписок игроков!

После добавления бота в канал, вы можете добавить канал в игру через "➕ Добавить канал"
"""
                        
                        await callback.message.edit_text(
                            instructions,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_give_gold":
                        self.user_states[callback.from_user.id] = {
                            "action": "give_gold",
                            "step": "enter_username"
                        }
                        
                        await callback.message.edit_text(
                            "🎁 Выдача золота\n\n"
                            "Введите username игрока (без @):",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_give_item":
                        self.user_states[callback.from_user.id] = {
                            "action": "give_item",
                            "step": "enter_username"
                        }
                        
                        await callback.message.edit_text(
                            "🎁 Выдача предмета\n\n"
                            "Введите username игрока (без @):",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_set_level":
                        self.user_states[callback.from_user.id] = {
                            "action": "set_level",
                            "step": "enter_username"
                        }
                        
                        await callback.message.edit_text(
                            "📈 Установка уровня игрока\n\n"
                            "Введите username игрока (без @):",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_set_gold":
                        self.user_states[callback.from_user.id] = {
                            "action": "set_gold",
                            "step": "enter_username"
                        }
                        
                        await callback.message.edit_text(
                            "💰 Установка золота игрока\n\n"
                            "Введите username игрока (без @):",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_set_balance":
                        self.user_states[callback.from_user.id] = {
                            "action": "set_balance",
                            "step": "enter_username"
                        }
                        
                        await callback.message.edit_text(
                            "💱 Установка баланса минералов\n\n"
                            "Введите username игрока (без @):",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_reset_player":
                        self.user_states[callback.from_user.id] = {
                            "action": "reset_player",
                            "step": "enter_username"
                        }
                        
                        await callback.message.edit_text(
                            "🔄 Сброс игрока\n\n"
                            "Введите username игрока (без @):",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_broadcast":
                        self.user_states[callback.from_user.id] = {
                            "action": "broadcast",
                            "step": "enter_message"
                        }
                        
                        await callback.message.edit_text(
                            "📢 Рассылка сообщения\n\n"
                            "Введите сообщение для рассылки:",
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                ]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_items_list":
                        text = "📋 Список всех предметов:\n\n"
                        items_list = list(data_manager.items.values())
                        for i, item in enumerate(items_list[:50], 1):
                            emoji = "🏆" if item.is_collectible else KeyboardManager.get_rarity_emoji(item.rarity)
                            text += f"{i}. {emoji} {item.name} (Сер.№ {item.serial_number})\n"
                        
                        if len(items_list) > 50:
                            text += f"\n... и еще {len(items_list) - 50} предметов"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_minerals_list":
                        text = "💰 Список всех минералов:\n\n"
                        for i, mineral in enumerate(MineralType, 1):
                            text += f"{i}. {mineral.value}\n"
                        
                        text += f"\nВсего минералов: {len(MineralType)}"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_collections":
                        text = "🏆 Коллекции всех игроков:\n\n"
                        
                        for player in data_manager.players.values():
                            collectibles_count = sum(player.collectibles.values())
                            if collectibles_count > 0:
                                unique_types = sum(1 for count in player.collectibles.values() if count > 0)
                                text += f"👤 @{player.username}: {collectibles_count} шт. ({unique_types}/24 типов)\n"
                        
                        total_collectibles = 0
                        for player in data_manager.players.values():
                            total_collectibles += sum(player.collectibles.values())
                        
                        text += f"\nВсего коллекционных предметов: {total_collectibles}"
                        
                        await callback.message.edit_text(
                            text,
                            reply_markup=self.keyboard_manager.admin_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    elif data == "admin_backup":
                        try:
                            data_manager.save_data()
                            await callback.message.edit_text(
                                "✅ Бекап данных создан!",
                                reply_markup=self.keyboard_manager.admin_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except:
                            await callback.answer(f"❌ Ошибка создания бекапа")
                
                else:
                    await callback.answer("ℹ️ Функция не реализована")
            
            except TelegramBadRequest as e:
                if "query is too old" in str(e) or "message is not modified" in str(e):
                    pass
                else:
                    await callback.answer("❌ Произошла ошибка при обработке запроса!")
            except:
                await callback.answer("❌ Произошла ошибка!")
        
        @self.dp.message()
        async def handle_message(message: Message):
            if message.chat.type != "private":
                await message.answer(f"👋 Привет! Я {GAME_NAME}\n\nДля игры со мной напишите мне в личные сообщения: @CRIPTO_MAINER_GAMEBOT")
                return
            
            user_id = message.from_user.id
            
            if user_id in data_manager.active_mining_sessions:
                session = data_manager.active_mining_sessions[user_id]
                
                if datetime.now() >= session.end_time:
                    success, result = data_manager.complete_mining(user_id)
                    
                    if success:
                        await message.answer(
                            self.text_templates.mining_result(result),
                            reply_markup=self.keyboard_manager.main_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
            
            state = self.user_states.get(user_id)
            
            if state:
                action = state.get("action")
                
                if action == "create_offer":
                    player = data_manager.players.get(user_id)
                    if not player:
                        return
                    
                    step = state.get("step")
                    
                    if step == "select_item":
                        try:
                            item_index = int(message.text) - 1
                            if 0 <= item_index < len(player.inventory):
                                item_id = player.inventory[item_index]
                                item = data_manager.items.get(item_id)
                                
                                if item and item.is_tradable:
                                    state["selected_item"] = item_id
                                    state["step"] = "enter_price"
                                    
                                    await message.answer(
                                        f"Выбран предмет: {item.name}\n"
                                        f"Введите цену в золоте:",
                                        reply_markup=InlineKeyboardMarkup(
                                            inline_keyboard=[
                                                [InlineKeyboardButton(text="❌ Отмена", callback_data="market")]
                                            ]
                                        )
                                    )
                                else:
                                    await message.answer(
                                        "❌ Этот предмет нельзя продавать",
                                        reply_markup=self.keyboard_manager.main_menu()
                                    )
                                    del self.user_states[user_id]
                            else:
                                await message.answer(
                                    "❌ Неверный номер предмета",
                                    reply_markup=self.keyboard_manager.main_menu()
                                )
                                del self.user_states[user_id]
                        except ValueError:
                            await message.answer(
                                "❌ Введите номер предмета!",
                                reply_markup=self.keyboard_manager.main_menu()
                            )
                            del self.user_states[user_id]
                    
                    elif step == "enter_price":
                        try:
                            price = int(message.text)
                            item_id = state.get("selected_item")
                            
                            if item_id:
                                success, result = data_manager.create_market_offer(
                                    user_id,
                                    item_id,
                                    price
                                )
                                
                                if success:
                                    await message.answer(
                                        f"✅ {result}",
                                        reply_markup=self.keyboard_manager.main_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                else:
                                    await message.answer(
                                        f"❌ {result}",
                                        reply_markup=self.keyboard_manager.main_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                            
                            del self.user_states[user_id]
                            
                        except ValueError:
                            await message.answer(
                                "❌ Введите корректную цену!",
                                reply_markup=self.keyboard_manager.main_menu()
                            )
                
                elif action == "create_offer_price":
                    try:
                        price = int(message.text)
                        item_id = state.get("selected_item")
                        
                        if item_id:
                            success, result = data_manager.create_market_offer(
                                user_id,
                                item_id,
                                price
                            )
                            
                            if success:
                                await message.answer(
                                    f"✅ {result}",
                                    reply_markup=self.keyboard_manager.main_menu(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await message.answer(
                                    f"❌ {result}",
                                    reply_markup=self.keyboard_manager.main_menu(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        
                        del self.user_states[user_id]
                        
                    except ValueError:
                        await message.answer(
                            "❌ Введите корректную цену!",
                            reply_markup=self.keyboard_manager.main_menu()
                        )
                
                elif user_id == ADMIN_ID:
                    if action == "add_channel":
                        step = state.get("step")
                        
                        if step == "enter_name":
                            state["name"] = message.text
                            state["step"] = "enter_url"
                            
                            await message.answer(
                                "Введите ссылку на канал:",
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                    ]
                                )
                            )
                        
                        elif step == "enter_url":
                            state["url"] = message.text
                            state["step"] = "enter_level"
                            
                            await message.answer(
                                "Введите требуемый уровень:",
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                    ]
                                )
                            )
                        
                        elif step == "enter_level":
                            try:
                                required_level = int(message.text)
                                state["required_level"] = required_level
                                state["step"] = "enter_reward"
                                
                                await message.answer(
                                    "Введите награду в золоте:",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            except ValueError:
                                await message.answer("❌ Введите число!")
                        
                        elif step == "enter_reward":
                            try:
                                reward = int(message.text)
                                name = state.get("name", "")
                                url = state.get("url", "")
                                required_level = state.get("required_level", 1)
                                
                                success, result = await data_manager.add_channel(
                                    name, url, required_level, reward
                                )
                                
                                if success:
                                    await message.answer(
                                        f"✅ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                else:
                                    await message.answer(
                                        f"❌ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                
                                del self.user_states[user_id]
                                
                            except ValueError:
                                await message.answer("❌ Введите число!")
                    
                    elif action == "remove_channel":
                        step = state.get("step")
                        
                        if step == "select_channel":
                            try:
                                channel_index = int(message.text) - 1
                                channel_ids = list(data_manager.channels.keys())
                                
                                if 0 <= channel_index < len(channel_ids):
                                    channel_id = channel_ids[channel_index]
                                    channel = data_manager.channels.get(channel_id)
                                    
                                    if channel:
                                        success, result = data_manager.remove_channel(channel_id)
                                        
                                        if success:
                                            await message.answer(
                                                f"✅ Канал '{channel.name}' удален!",
                                                reply_markup=self.keyboard_manager.admin_menu(),
                                                parse_mode=ParseMode.MARKDOWN
                                            )
                                        else:
                                            await message.answer(
                                                f"❌ {result}",
                                                reply_markup=self.keyboard_manager.admin_menu(),
                                                parse_mode=ParseMode.MARKDOWN
                                            )
                                    else:
                                        await message.answer(
                                            "❌ Канал не найден",
                                            reply_markup=self.keyboard_manager.admin_menu()
                                        )
                                else:
                                    await message.answer(
                                        "❌ Неверный номер канала",
                                        reply_markup=self.keyboard_manager.admin_menu()
                                    )
                            except ValueError:
                                await message.answer(
                                    "❌ Введите номер канала!",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                            
                            del self.user_states[user_id]
                    
                    elif action == "find_player":
                        step = state.get("step")
                        
                        if step == "enter_query":
                            query = message.text
                            player = data_manager.search_player(query)
                            
                            if player:
                                total_collectibles = sum(player.collectibles.values())
                                
                                player_info = f"""
👤 Информация об игроке:

📛 Имя: {player.first_name}
👤 Username: @{player.username}
🆔 ID: {player.user_id}
🏆 Уровень: {player.miner_level}
🪙 Золота: {player.gold_balance}
🏆 Коллекционных: {total_collectibles}
⛽ Топливо: {player.fuel} мин.
📅 Зарегистрирован: {player.created_at.strftime('%d.%m.%Y %H:%M')}
⛏️ Всего добыто: {player.total_mined:.2f} кг
🤖 Автодобыча: {'✅ ВКЛ' if player.auto_mining_enabled else '❌ ВЫКЛ'}
"""
                                await message.answer(
                                    player_info,
                                    reply_markup=self.keyboard_manager.admin_menu(),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                            
                            del self.user_states[user_id]
                    
                    elif action == "give_gold":
                        step = state.get("step")
                        
                        if step == "enter_username":
                            username = message.text
                            
                            target_player = None
                            for player in data_manager.players.values():
                                if player.username == username:
                                    target_player = player
                                    break
                            
                            if target_player:
                                state["target_user_id"] = target_player.user_id
                                state["target_username"] = username
                                state["step"] = "enter_amount"
                                
                                await message.answer(
                                    f"Игрок найден: {target_player.first_name}\n"
                                    f"Введите количество золота:",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                                del self.user_states[user_id]
                        
                        elif step == "enter_amount":
                            try:
                                amount = int(message.text)
                                target_user_id = state.get("target_user_id")
                                
                                if target_user_id:
                                    success, result = data_manager.give_gold(
                                        target_user_id, amount
                                    )
                                    
                                    if success:
                                        await message.answer(
                                            f"✅ {result}",
                                            reply_markup=self.keyboard_manager.admin_menu(),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                    else:
                                        await message.answer(
                                            f"❌ {result}",
                                            reply_markup=self.keyboard_manager.admin_menu(),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                
                                del self.user_states[user_id]
                                
                            except ValueError:
                                await message.answer("❌ Введите число!")
                    
                    elif action == "give_item":
                        step = state.get("step")
                        
                        if step == "enter_username":
                            username = message.text
                            
                            target_player = None
                            for player in data_manager.players.values():
                                if player.username == username:
                                    target_player = player
                                    break
                            
                            if target_player:
                                state["target_user_id"] = target_player.user_id
                                state["target_username"] = username
                                state["step"] = "enter_item_name"
                                
                                await message.answer(
                                    f"Игрок найден: {target_player.first_name}\n"
                                    f"Введите название предмета:",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                                del self.user_states[user_id]
                        
                        elif step == "enter_item_name":
                            item_name = message.text
                            target_user_id = state.get("target_user_id")
                            
                            if target_user_id:
                                success, result = data_manager.give_item(
                                    target_user_id, item_name
                                )
                                
                                if success:
                                    await message.answer(
                                        f"✅ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                else:
                                    await message.answer(
                                        f"❌ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                            
                            del self.user_states[user_id]
                    
                    elif action == "set_level":
                        step = state.get("step")
                        
                        if step == "enter_username":
                            username = message.text
                            
                            target_player = None
                            for player in data_manager.players.values():
                                if player.username == username:
                                    target_player = player
                                    break
                            
                            if target_player:
                                state["target_user_id"] = target_player.user_id
                                state["target_username"] = username
                                state["step"] = "enter_level"
                                
                                await message.answer(
                                    f"Игрок найден: {target_player.first_name}\n"
                                    f"Введите новый уровень (1-80):",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                                del self.user_states[user_id]
                        
                        elif step == "enter_level":
                            try:
                                level = int(message.text)
                                target_user_id = state.get("target_user_id")
                                
                                if target_user_id:
                                    success, result = data_manager.set_player_level(
                                        target_user_id, level
                                    )
                                
                                if success:
                                    await message.answer(
                                        f"✅ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                else:
                                    await message.answer(
                                        f"❌ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                            
                                del self.user_states[user_id]
                            
                            except ValueError:
                                await message.answer("❌ Введите число!")
                    
                    elif action == "set_gold":
                        step = state.get("step")
                        
                        if step == "enter_username":
                            username = message.text
                            
                            target_player = None
                            for player in data_manager.players.values():
                                if player.username == username:
                                    target_player = player
                                    break
                            
                            if target_player:
                                state["target_user_id"] = target_player.user_id
                                state["target_username"] = username
                                state["step"] = "enter_gold"
                                
                                await message.answer(
                                    f"Игрок найден: {target_player.first_name}\n"
                                    f"Введите количество золота:",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                                del self.user_states[user_id]
                        
                        elif step == "enter_gold":
                            try:
                                gold = int(message.text)
                                target_user_id = state.get("target_user_id")
                                
                                if target_user_id:
                                    success, result = data_manager.set_player_gold(
                                        target_user_id, gold
                                    )
                                    
                                    if success:
                                        await message.answer(
                                            f"✅ {result}",
                                            reply_markup=self.keyboard_manager.admin_menu(),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                    else:
                                        await message.answer(
                                            f"❌ {result}",
                                            reply_markup=self.keyboard_manager.admin_menu(),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                
                                del self.user_states[user_id]
                                
                            except ValueError:
                                await message.answer("❌ Введите число!")
                    
                    elif action == "set_balance":
                        step = state.get("step")
                        
                        if step == "enter_username":
                            username = message.text
                            
                            target_player = None
                            for player in data_manager.players.values():
                                if player.username == username:
                                    target_player = player
                                    break
                            
                            if target_player:
                                state["target_user_id"] = target_player.user_id
                                state["target_username"] = username
                                state["step"] = "enter_mineral"
                                
                                await message.answer(
                                    f"Игрок найден: {target_player.first_name}\n"
                                    f"Введите минерал (например, GOLD):",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                                del self.user_states[user_id]
                        
                        elif step == "enter_mineral":
                            mineral_name = message.text
                            
                            mineral = None
                            for m in MineralType:
                                if m.name == mineral_name:
                                    mineral = m
                                    break
                            
                            if mineral:
                                state["mineral"] = mineral_name
                                state["step"] = "enter_amount"
                                
                                await message.answer(
                                    f"Минерал: {mineral.value}\n"
                                    f"Введите количество (кг):",
                                    reply_markup=InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin")]
                                        ]
                                    )
                                )
                            else:
                                await message.answer("❌ Минерал не найден. Попробуйте снова:")
                        
                        elif step == "enter_amount":
                            try:
                                amount = float(message.text)
                                target_user_id = state.get("target_user_id")
                                mineral_name = state.get("mineral")
                                
                                if target_user_id and mineral_name:
                                    success, result = data_manager.set_player_balance(
                                        target_user_id, mineral_name, amount
                                    )
                                    
                                    if success:
                                        await message.answer(
                                            f"✅ {result}",
                                            reply_markup=self.keyboard_manager.admin_menu(),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                    else:
                                        await message.answer(
                                            f"❌ {result}",
                                            reply_markup=self.keyboard_manager.admin_menu(),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                
                                del self.user_states[user_id]
                                
                            except ValueError:
                                await message.answer("❌ Введите число!")
                    
                    elif action == "reset_player":
                        step = state.get("step")
                        
                        if step == "enter_username":
                            username = message.text
                            
                            target_player = None
                            for player in data_manager.players.values():
                                if player.username == username:
                                    target_player = player
                                    break
                            
                            if target_player:
                                success, result = data_manager.reset_player(
                                    target_player.user_id
                                )
                                
                                if success:
                                    await message.answer(
                                        f"✅ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                else:
                                    await message.answer(
                                        f"❌ {result}",
                                        reply_markup=self.keyboard_manager.admin_menu(),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                            else:
                                await message.answer(
                                    "❌ Игрок не найден",
                                    reply_markup=self.keyboard_manager.admin_menu()
                                )
                            
                            del self.user_states[user_id]
                    
                    elif action == "broadcast":
                        step = state.get("step")
                        
                        if step == "enter_message":
                            broadcast_message = message.text
                            
                            results = data_manager.broadcast_message(broadcast_message)
                            sent = len([r for r in results if r[1]])
                            
                            await message.answer(
                                f"✅ Рассылка отправлена {sent} игрокам",
                                reply_markup=self.keyboard_manager.admin_menu(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            
                            del self.user_states[user_id]
            
            else:
                await message.answer(
                    f"⛏️ {GAME_NAME}\n\nГлавное меню",
                    reply_markup=self.keyboard_manager.main_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
    
    async def run(self):
        asyncio.create_task(self.check_mining_sessions())
        asyncio.create_task(self.check_auto_mining())
        await self.dp.start_polling(self.bot)
    
    async def check_mining_sessions(self):
        while True:
            try:
                current_time = datetime.now()
                completed_users = []
                
                for user_id, session in data_manager.active_mining_sessions.items():
                    if session.active and current_time >= session.end_time:
                        completed_users.append(user_id)
                
                for user_id in completed_users:
                    try:
                        success, result = data_manager.complete_mining(user_id)
                        
                        if success:
                            await self.bot.send_message(
                                user_id,
                                self.text_templates.mining_result(result),
                                parse_mode=ParseMode.MARKDOWN
                            )
                    except:
                        pass
                
                await asyncio.sleep(5)
            except:
                await asyncio.sleep(10)
    
    async def check_auto_mining(self):
        while True:
            try:
                current_time = datetime.now()
                
                for user_id, auto_session in list(data_manager.auto_mining_sessions.items()):
                    if auto_session.is_active and auto_session.next_mine_time and current_time >= auto_session.next_mine_time:
                        try:
                            success, result = data_manager.process_auto_mining(user_id)
                            
                            if success and result.get('total_mineral', 0) > 0:
                                await self.bot.send_message(
                                    user_id,
                                    self.text_templates.auto_mining_result(result),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        except:
                            pass
                
                await asyncio.sleep(30)
            except:
                await asyncio.sleep(60)

# ========== ЗАПУСК ==========

async def main():
    bot = MinerichBot(BOT_TOKEN)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
