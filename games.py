import random
import math
from dataclasses import dataclass
from typing import Optional

@dataclass
class GameResult:
    won: bool
    multiplier: float
    profit: float        # может быть отрицательным (проигрыш = -bet)
    description: str
    emoji: str = "🎰"

# ─────────────────────────── СЛОТЫ ───────────────────────────
SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "🃏", "⭐"]
SLOT_WEIGHTS = [30, 25, 20, 15, 5, 3, 1.5, 0.5]  # редкость символов

SLOT_PAYOUTS = {
    "7️⃣": 50.0,
    "💎": 20.0,
    "⭐": 15.0,
    "🃏": 10.0,
    "🍇": 5.0,
    "🍊": 3.0,
    "🍋": 2.0,
    "🍒": 1.5,
}

def spin_slots(bet: float) -> GameResult:
    reels = random.choices(SLOT_SYMBOLS, weights=SLOT_WEIGHTS, k=3)
    display = " | ".join(reels)

    if reels[0] == reels[1] == reels[2]:  # три одинаковых
        mult = SLOT_PAYOUTS[reels[0]]
        profit = bet * mult - bet
        return GameResult(True, mult, profit, f"🎰 {display}\n🎉 ДЖЕКПОТ x{mult}!", "🎰")

    if reels[0] == reels[1] or reels[1] == reels[2]:  # два одинаковых
        sym = reels[1]
        mult = SLOT_PAYOUTS[sym] * 0.3
        profit = bet * mult - bet
        return GameResult(True, mult, profit, f"🎰 {display}\n✨ Два подряд x{mult:.1f}!", "🎰")

    return GameResult(False, 0, -bet, f"🎰 {display}\n😔 Не повезло...", "🎰")

# ─────────────────────────── МОНЕТКА ─────────────────────────
def flip_coin(bet: float, choice: str) -> GameResult:
    result = random.choice(["heads", "tails"])
    emoji_map = {"heads": "👑", "tails": "🪙"}
    name_map = {"heads": "Орёл", "tails": "Решка"}
    win = result == choice
    profit = bet * 0.95 if win else -bet   # 5% хаус эдж
    desc = f"{emoji_map[result]} {name_map[result]}!\n"
    desc += "🎉 Выиграл!" if win else "😔 Проиграл"
    return GameResult(win, 1.95 if win else 0, profit, desc, emoji_map[result])

# ─────────────────────────── РУЛЕТКА ─────────────────────────
ROULETTE_BETS = {
    "red": {"numbers": [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36], "mult": 2.0},
    "black": {"numbers": [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35], "mult": 2.0},
    "green": {"numbers": [0], "mult": 14.0},
    "even": {"numbers": list(range(2, 37, 2)), "mult": 2.0},
    "odd": {"numbers": list(range(1, 37, 2)), "mult": 2.0},
    "1-12": {"numbers": list(range(1, 13)), "mult": 3.0},
    "13-24": {"numbers": list(range(13, 25)), "mult": 3.0},
    "25-36": {"numbers": list(range(25, 37)), "mult": 3.0},
}

ROULETTE_COLORS = {0: "🟢"}
for n in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
    ROULETTE_COLORS[n] = "🔴"
for n in [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]:
    ROULETTE_COLORS[n] = "⚫"

def spin_roulette(bet: float, bet_type: str) -> GameResult:
    number = random.randint(0, 36)
    color_emoji = ROULETTE_COLORS[number]
    desc_num = f"🎡 Выпало: {color_emoji} {number}\n"

    if bet_type.lstrip("+-").isdigit():  # ставка на конкретное число
        num = int(bet_type)
        if number == num:
            profit = bet * 35
            return GameResult(True, 36, profit, desc_num + f"🎉 Прямое попадание! x36", "🎡")
        return GameResult(False, 0, -bet, desc_num + "😔 Проиграл", "🎡")

    if bet_type not in ROULETTE_BETS:
        return GameResult(False, 0, -bet, "❌ Неверный тип ставки", "🎡")

    info = ROULETTE_BETS[bet_type]
    win = number in info["numbers"]
    mult = info["mult"]
    profit = bet * (mult - 1) if win else -bet
    label = {"red": "Красное", "black": "Чёрное", "green": "Зелёное",
             "even": "Чётное", "odd": "Нечётное",
             "1-12": "1-12", "13-24": "13-24", "25-36": "25-36"}.get(bet_type, bet_type)
    desc = desc_num + (f"🎉 {label} — выиграл! x{mult}" if win else f"😔 {label} — проиграл")
    return GameResult(win, mult if win else 0, profit, desc, "🎡")

# ─────────────────────────── КРАШ ────────────────────────────
def generate_crash_point() -> float:
    """Генерация точки краша с хаус-эджем ~4%"""
    r = random.random()
    if r < 0.04:
        return 1.0
    crash = 0.96 / (1 - r)
    return round(min(crash, 1000.0), 2)

def play_crash(bet: float, cashout: float) -> GameResult:
    crash_point = generate_crash_point()
    won = cashout <= crash_point
    if won:
        profit = bet * cashout - bet
        desc = f"🚀 Краш: x{crash_point}\n✅ Кэшаут на x{cashout} — выиграл!"
    else:
        profit = -bet
        desc = f"💥 Краш: x{crash_point}\n❌ Кэшаут на x{cashout} — слишком жадно!"
    return GameResult(won, cashout if won else 0, profit, desc, "🚀")

# ─────────────────────────── БЛЭКДЖЕК ────────────────────────
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11,
}
CARD_SUITS = ["♠️", "♥️", "♦️", "♣️"]
CARD_RANKS = list(CARD_VALUES.keys())

def new_deck() -> list:
    deck = [f"{r}{s}" for r in CARD_RANKS for s in CARD_SUITS]
    random.shuffle(deck)
    return deck

def card_value(card: str) -> int:
    rank = card[:-2] if len(card) > 2 else card[0]
    return CARD_VALUES.get(rank, 10)

def hand_total(hand: list) -> int:
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def hand_str(hand: list) -> str:
    return " ".join(hand)

@dataclass
class BlackjackState:
    player_hand: list
    dealer_hand: list
    deck: list
    bet: float
    done: bool = False
    result: Optional[GameResult] = None

def start_blackjack(bet: float) -> BlackjackState:
    deck = new_deck()
    ph = [deck.pop(), deck.pop()]
    dh = [deck.pop(), deck.pop()]
    state = BlackjackState(player_hand=ph, dealer_hand=dh, deck=deck, bet=bet)

    # Натуральный блэкджек
    if hand_total(ph) == 21:
        profit = bet * 1.5
        state.done = True
        state.result = GameResult(True, 2.5, profit,
            f"🃏 Блэкджек! {hand_str(ph)}\n🎉 Выиграл x2.5!", "🃏")
    return state

def blackjack_hit(state: BlackjackState) -> BlackjackState:
    state.player_hand.append(state.deck.pop())
    if hand_total(state.player_hand) > 21:
        state.done = True
        state.result = GameResult(False, 0, -state.bet,
            f"🃏 Перебор! {hand_str(state.player_hand)} = {hand_total(state.player_hand)}", "🃏")
    return state

def blackjack_stand(state: BlackjackState) -> BlackjackState:
    # Дилер добирает карты до 17
    while hand_total(state.dealer_hand) < 17:
        state.dealer_hand.append(state.deck.pop())

    pt = hand_total(state.player_hand)
    dt = hand_total(state.dealer_hand)
    state.done = True

    desc = f"🃏 Вы: {hand_str(state.player_hand)} = {pt}\n"
    desc += f"🏦 Дилер: {hand_str(state.dealer_hand)} = {dt}\n"

    if dt > 21 or pt > dt:
        profit = state.bet
        state.result = GameResult(True, 2, profit, desc + "🎉 Победа!")
    elif pt == dt:
        state.result = GameResult(False, 1, 0, desc + "🤝 Ничья — возврат ставки")
        state.result.profit = 0
    else:
        state.result = GameResult(False, 0, -state.bet, desc + "😔 Дилер победил")
    return state

# ─────────────────────────── DICE ────────────────────────────
def play_dice(bet: float, choice: str) -> GameResult:
    """
    Виды ставок: число 1-6, high (4-6), low (1-3), exact (конкретное число x5)
    """
    roll = random.randint(1, 6)
    dice_emojis = ["", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    desc_base = f"🎲 Выпало: {dice_emojis[roll]}\n"

    if choice == "high":
        win = roll >= 4
        profit = bet * 0.9 if win else -bet
        return GameResult(win, 1.9 if win else 0, profit, desc_base + ("🎉 Высокое — победа!" if win else "😔 Проиграл"), "🎲")
    elif choice == "low":
        win = roll <= 3
        profit = bet * 0.9 if win else -bet
        return GameResult(win, 1.9 if win else 0, profit, desc_base + ("🎉 Низкое — победа!" if win else "😔 Проиграл"), "🎲")
    elif choice.isdigit() and 1 <= int(choice) <= 6:
        win = roll == int(choice)
        profit = bet * 4.5 if win else -bet
        return GameResult(win, 5.5 if win else 0, profit, desc_base + (f"🎉 Точное попадание! x5.5" if win else "😔 Проиграл"), "🎲")
    return GameResult(False, 0, -bet, "❌ Неверная ставка", "🎲")
