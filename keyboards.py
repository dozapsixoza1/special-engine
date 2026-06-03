from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎮 Открыть казино", web_app=WebAppInfo(url=webapp_url))
    )
    builder.row(
        InlineKeyboardButton(text="💰 Депозит", callback_data="deposit"),
        InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        InlineKeyboardButton(text="🏆 Топ игроков", callback_data="leaderboard"),
    )
    builder.row(
        InlineKeyboardButton(text="📖 Игры", callback_data="games_list"),
    )
    return builder.as_markup()

def deposit_amounts_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amounts = [1, 5, 10, 25, 50, 100]
    for i in range(0, len(amounts), 3):
        row = amounts[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=f"${a}", callback_data=f"dep_{a}")
            for a in row
        ])
    builder.row(InlineKeyboardButton(text="✏️ Своя сумма", callback_data="dep_custom"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    return builder.as_markup()

def currency_kb(action: str, amount: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    currencies = ["USDT", "TON", "BTC", "ETH", "LTC", "BNB"]
    for i in range(0, len(currencies), 3):
        row = currencies[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=c, callback_data=f"{action}_cur_{c}_{amount}")
            for c in row
        ])
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="deposit" if action == "dep" else "withdraw"))
    return builder.as_markup()

def withdraw_amounts_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amounts = [1, 5, 10, 25, 50, 100]
    for i in range(0, len(amounts), 3):
        row = amounts[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=f"${a}", callback_data=f"wdr_{a}")
            for a in row
        ])
    builder.row(InlineKeyboardButton(text="✏️ Своя сумма", callback_data="wdr_custom"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    return builder.as_markup()

def games_list_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots"),
        InlineKeyboardButton(text="🪙 Монетка", callback_data="game_coin"),
    )
    builder.row(
        InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette"),
        InlineKeyboardButton(text="🚀 Краш", callback_data="game_crash"),
    )
    builder.row(
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="game_blackjack"),
        InlineKeyboardButton(text="🎲 Кости", callback_data="game_dice"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    return builder.as_markup()

def bet_amounts_kb(game: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    bets = [0.5, 1, 2, 5, 10, 25]
    for i in range(0, len(bets), 3):
        row = bets[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=f"${b}", callback_data=f"bet_{game}_{b}")
            for b in row
        ])
    builder.row(InlineKeyboardButton(text="✏️ Своя сумма", callback_data=f"bet_{game}_custom"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="games_list"))
    return builder.as_markup()

def coin_choice_kb(bet: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👑 Орёл", callback_data=f"coin_heads_{bet}"),
        InlineKeyboardButton(text="🪙 Решка", callback_data=f"coin_tails_{bet}"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="game_coin"))
    return builder.as_markup()

def roulette_kb(bet: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔴 Красное", callback_data=f"rul_red_{bet}"),
        InlineKeyboardButton(text="⚫ Чёрное", callback_data=f"rul_black_{bet}"),
        InlineKeyboardButton(text="🟢 Зелёное", callback_data=f"rul_green_{bet}"),
    )
    builder.row(
        InlineKeyboardButton(text="Чётное", callback_data=f"rul_even_{bet}"),
        InlineKeyboardButton(text="Нечётное", callback_data=f"rul_odd_{bet}"),
    )
    builder.row(
        InlineKeyboardButton(text="1-12", callback_data=f"rul_1-12_{bet}"),
        InlineKeyboardButton(text="13-24", callback_data=f"rul_13-24_{bet}"),
        InlineKeyboardButton(text="25-36", callback_data=f"rul_25-36_{bet}"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="game_roulette"))
    return builder.as_markup()

def crash_cashout_kb(bet: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    cashouts = [1.5, 2.0, 3.0, 5.0, 10.0, 20.0]
    for i in range(0, len(cashouts), 3):
        row = cashouts[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=f"x{c}", callback_data=f"crash_{c}_{bet}")
            for c in row
        ])
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="game_crash"))
    return builder.as_markup()

def blackjack_action_kb(state_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👊 Ещё карту", callback_data=f"bj_hit_{state_id}"),
        InlineKeyboardButton(text="✋ Стоп", callback_data=f"bj_stand_{state_id}"),
    )
    return builder.as_markup()

def dice_choice_kb(bet: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Высокое (4-6)", callback_data=f"dice_high_{bet}"),
        InlineKeyboardButton(text="📉 Низкое (1-3)", callback_data=f"dice_low_{bet}"),
    )
    builder.row(*[
        InlineKeyboardButton(text=f"{e}", callback_data=f"dice_{n}_{bet}")
        for n, e in enumerate(["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣"], 1)
    ])
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="game_dice"))
    return builder.as_markup()

def play_again_kb(game: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Играть снова", callback_data=f"game_{game}"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu"),
    )
    return builder.as_markup()

def back_kb(callback: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=callback))
    return builder.as_markup()

def check_deposit_kb(invoice_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_dep_{invoice_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="main_menu"))
    return builder.as_markup()
