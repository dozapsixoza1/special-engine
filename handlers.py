import json
import logging
import uuid
from aiogram import Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import Config
from database import (
    get_or_create_user, get_user, update_balance,
    save_game, save_transaction, update_transaction, get_top_players
)
from cryptopay import CryptoPay
from games import (
    spin_slots, flip_coin, spin_roulette, play_crash,
    start_blackjack, blackjack_hit, blackjack_stand, play_dice, BlackjackState
)
from keyboards import *

logger = logging.getLogger(__name__)

# ─── Хранилище состояний блэкджека в памяти ───
bj_states: dict[str, BlackjackState] = {}

class PaymentStates(StatesGroup):
    waiting_custom_deposit = State()
    waiting_custom_withdraw = State()

def register_handlers(dp: Dispatcher, config: Config):
    router = Router()
    crypto = CryptoPay(config.CRYPTO_PAY_TOKEN, config.CRYPTO_PAY_API_URL)

    # ─── СТАРТ ───────────────────────────────────────────────────
    @router.message(CommandStart())
    async def start(msg: Message):
        user = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        await msg.answer(
            f"🎰 <b>Добро пожаловать в Lucky Casino!</b>\n\n"
            f"👋 Привет, {msg.from_user.first_name}!\n"
            f"💰 Баланс: <b>${user['balance']:.2f}</b>\n\n"
            f"Выбери действие ниже 👇",
            parse_mode="HTML",
            reply_markup=main_menu_kb(config.WEBAPP_URL)
        )

    @router.callback_query(F.data == "main_menu")
    async def cb_main_menu(cb: CallbackQuery):
        user = await get_user(cb.from_user.id)
        await cb.message.edit_text(
            f"🎰 <b>Lucky Casino</b>\n\n"
            f"💰 Баланс: <b>${user['balance']:.2f}</b>\n\n"
            f"Выбери действие 👇",
            parse_mode="HTML",
            reply_markup=main_menu_kb(config.WEBAPP_URL)
        )

    # ─── ПРОФИЛЬ ─────────────────────────────────────────────────
    @router.callback_query(F.data == "profile")
    async def cb_profile(cb: CallbackQuery):
        user = await get_user(cb.from_user.id)
        wager = user.get("total_wagered", 0)
        won = user.get("total_won", 0)
        dep = user.get("total_deposited", 0)
        wdr = user.get("total_withdrawn", 0)
        games = user.get("games_played", 0)
        winrate = (won / wager * 100) if wager > 0 else 0

        text = (
            f"👤 <b>Профиль</b>\n\n"
            f"🆔 ID: <code>{cb.from_user.id}</code>\n"
            f"👤 Имя: {cb.from_user.first_name}\n\n"
            f"💰 <b>Баланс:</b> ${user['balance']:.2f}\n"
            f"📥 Депозиты: ${dep:.2f}\n"
            f"📤 Выводы: ${wdr:.2f}\n\n"
            f"🎮 Игр сыграно: {games}\n"
            f"💵 Поставлено всего: ${wager:.2f}\n"
            f"🏆 Выиграно всего: ${won:.2f}\n"
            f"📊 Винрейт: {winrate:.1f}%"
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb())

    # ─── ТОП ИГРОКОВ ──────────────────────────────────────────────
    @router.callback_query(F.data == "leaderboard")
    async def cb_leaderboard(cb: CallbackQuery):
        players = await get_top_players(10)
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines = ["🏆 <b>Топ игроков</b>\n"]
        for i, p in enumerate(players):
            name = p.get("first_name") or p.get("username") or "Аноним"
            lines.append(f"{medals[i]} {name} — ${p['total_won']:.2f} выиграно")
        await cb.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_kb())

    # ─── ДЕПОЗИТ ─────────────────────────────────────────────────
    @router.callback_query(F.data == "deposit")
    async def cb_deposit(cb: CallbackQuery):
        await cb.message.edit_text(
            "💰 <b>Пополнение баланса</b>\n\nВыбери сумму или введи свою:",
            parse_mode="HTML",
            reply_markup=deposit_amounts_kb()
        )

    @router.callback_query(F.data == "dep_custom")
    async def cb_dep_custom(cb: CallbackQuery, state: FSMContext):
        await state.set_state(PaymentStates.waiting_custom_deposit)
        await cb.message.edit_text(
            "✏️ Введи сумму депозита в USDT (минимум $1):",
            reply_markup=back_kb("deposit")
        )

    @router.message(PaymentStates.waiting_custom_deposit)
    async def msg_custom_deposit(msg: Message, state: FSMContext):
        await state.clear()
        try:
            amount = float(msg.text.replace(",", "."))
            if amount < config.MIN_DEPOSIT:
                await msg.answer(f"❌ Минимум ${config.MIN_DEPOSIT}")
                return
            await _show_currency_choice(msg, amount, "dep")
        except ValueError:
            await msg.answer("❌ Неверное число")

    @router.callback_query(F.data.startswith("dep_") & ~F.data.startswith("dep_cur_"))
    async def cb_dep_amount(cb: CallbackQuery):
        amount = float(cb.data.split("_")[1])
        await _show_currency_choice(cb.message, amount, "dep", edit=True)

    async def _show_currency_choice(target, amount, action, edit=False):
        text = f"💱 Выбери валюту для {'пополнения' if action == 'dep' else 'вывода'} ${amount}:"
        kb = currency_kb(action, amount)
        if edit:
            await target.edit_text(text, reply_markup=kb)
        else:
            await target.answer(text, reply_markup=kb)

    @router.callback_query(F.data.startswith("dep_cur_"))
    async def cb_dep_currency(cb: CallbackQuery):
        _, _, currency, amount_str = cb.data.split("_", 3)
        amount = float(amount_str)
        user_id = cb.from_user.id

        try:
            invoice = await crypto.create_invoice(
                asset=currency,
                amount=amount,
                description=f"💰 Casino Deposit #{user_id}",
                payload=str(user_id),
            )
            invoice_id = invoice["invoice_id"]
            pay_url = invoice["bot_invoice_url"]

            tx_id = await save_transaction(user_id, "deposit", amount, str(invoice_id))

            await cb.message.edit_text(
                f"📄 <b>Счёт создан!</b>\n\n"
                f"💰 Сумма: {amount} {currency}\n"
                f"🔢 ID счёта: <code>{invoice_id}</code>\n\n"
                f"👇 Нажми кнопку для оплаты через @CryptoBot\n"
                f"После оплаты нажми «Проверить оплату»",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
                    [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_dep_{invoice_id}_{tx_id}_{amount}")],
                    [InlineKeyboardButton(text="🔙 Отмена", callback_data="main_menu")],
                ])
            )
        except Exception as e:
            logger.error(f"Invoice creation error: {e}")
            await cb.message.edit_text(
                "❌ Ошибка при создании счёта. Проверь токен CryptoBot и попробуй снова.",
                reply_markup=back_kb("deposit")
            )

    @router.callback_query(F.data.startswith("check_dep_"))
    async def cb_check_deposit(cb: CallbackQuery):
        parts = cb.data.split("_")
        invoice_id = int(parts[2])
        tx_id = int(parts[3])
        amount = float(parts[4])

        await cb.answer("⏳ Проверяю...")
        try:
            invoice = await crypto.check_invoice(invoice_id)
            if not invoice:
                await cb.answer("❌ Счёт не найден", show_alert=True)
                return

            if invoice["status"] == "paid":
                await update_balance(cb.from_user.id, amount)
                await update_transaction(tx_id, "completed")
                user = await get_user(cb.from_user.id)
                await cb.message.edit_text(
                    f"✅ <b>Оплата подтверждена!</b>\n\n"
                    f"💰 Зачислено: ${amount:.2f}\n"
                    f"💼 Новый баланс: ${user['balance']:.2f}",
                    parse_mode="HTML",
                    reply_markup=back_kb()
                )
            elif invoice["status"] == "expired":
                await cb.answer("⌛ Счёт истёк. Создай новый.", show_alert=True)
            else:
                await cb.answer("⏳ Оплата ещё не получена. Попробуй через минуту.", show_alert=True)
        except Exception as e:
            logger.error(f"Check deposit error: {e}")
            await cb.answer("❌ Ошибка проверки", show_alert=True)

    # ─── ВЫВОД ───────────────────────────────────────────────────
    @router.callback_query(F.data == "withdraw")
    async def cb_withdraw(cb: CallbackQuery):
        user = await get_user(cb.from_user.id)
        await cb.message.edit_text(
            f"💸 <b>Вывод средств</b>\n\n"
            f"💰 Доступно: ${user['balance']:.2f}\n"
            f"📊 Минимум: ${config.MIN_WITHDRAW}\n\n"
            f"Выбери сумму:",
            parse_mode="HTML",
            reply_markup=withdraw_amounts_kb()
        )

    @router.callback_query(F.data == "wdr_custom")
    async def cb_wdr_custom(cb: CallbackQuery, state: FSMContext):
        await state.set_state(PaymentStates.waiting_custom_withdraw)
        await cb.message.edit_text("✏️ Введи сумму вывода в USDT:", reply_markup=back_kb("withdraw"))

    @router.message(PaymentStates.waiting_custom_withdraw)
    async def msg_custom_withdraw(msg: Message, state: FSMContext):
        await state.clear()
        try:
            amount = float(msg.text.replace(",", "."))
            if amount < config.MIN_WITHDRAW:
                await msg.answer(f"❌ Минимум ${config.MIN_WITHDRAW}")
                return
            await _show_currency_choice(msg, amount, "wdr")
        except ValueError:
            await msg.answer("❌ Неверное число")

    @router.callback_query(F.data.startswith("wdr_") & ~F.data.startswith("wdr_cur_") & ~F.data.startswith("wdr_custom"))
    async def cb_wdr_amount(cb: CallbackQuery):
        amount = float(cb.data.split("_")[1])
        user = await get_user(cb.from_user.id)
        if user["balance"] < amount:
            await cb.answer("❌ Недостаточно средств", show_alert=True)
            return
        await _show_currency_choice(cb.message, amount, "wdr", edit=True)

    @router.callback_query(F.data.startswith("wdr_cur_"))
    async def cb_wdr_currency(cb: CallbackQuery):
        _, _, currency, amount_str = cb.data.split("_", 3)
        amount = float(amount_str)
        user_id = cb.from_user.id

        user = await get_user(user_id)
        if user["balance"] < amount:
            await cb.answer("❌ Недостаточно средств", show_alert=True)
            return

        await update_balance(user_id, -amount)
        tx_id = await save_transaction(user_id, "withdrawal", amount, status="pending")

        try:
            # Метод 1: Прямой перевод (нужно разрешение в боте CryptoPay)
            result = await crypto.transfer(
                user_id=user_id,
                asset=currency,
                amount=amount,
                spend_id=str(tx_id),
                comment=f"🎰 Вывод из Lucky Casino"
            )
            await update_transaction(tx_id, "completed")
            user = await get_user(user_id)
            await cb.message.edit_text(
                f"✅ <b>Вывод выполнен!</b>\n\n"
                f"💸 {amount} {currency} отправлено на твой @CryptoBot\n"
                f"💼 Остаток: ${user['balance']:.2f}",
                parse_mode="HTML",
                reply_markup=back_kb()
            )
        except Exception as e:
            # Метод 2: Создать чек (если нет разрешения на transfer)
            logger.warning(f"Transfer failed, trying check: {e}")
            try:
                check = await crypto.create_check(asset=currency, amount=amount, pin_to_user_id=user_id)
                check_link = check["bot_check_url"]
                await update_transaction(tx_id, "check_created", check.get("check_id", ""))
                user = await get_user(user_id)
                await cb.message.edit_text(
                    f"✅ <b>Чек создан!</b>\n\n"
                    f"💸 Сумма: {amount} {currency}\n"
                    f"👇 Активируй чек в @CryptoBot:\n{check_link}\n\n"
                    f"💼 Остаток: ${user['balance']:.2f}",
                    parse_mode="HTML",
                    reply_markup=back_kb()
                )
            except Exception as e2:
                logger.error(f"Check creation failed: {e2}")
                await update_balance(user_id, amount)  # вернуть деньги
                await update_transaction(tx_id, "failed")
                await cb.message.edit_text(
                    "❌ Ошибка вывода. Деньги возвращены на баланс. Обратитесь в поддержку.",
                    reply_markup=back_kb()
                )

    # ─── СПИСОК ИГР ──────────────────────────────────────────────
    @router.callback_query(F.data == "games_list")
    async def cb_games_list(cb: CallbackQuery):
        await cb.message.edit_text(
            "🎮 <b>Выбери игру:</b>\n\n"
            "🎰 <b>Слоты</b> — до x50 за джекпот\n"
            "🪙 <b>Монетка</b> — x1.95, 50/50\n"
            "🎡 <b>Рулетка</b> — до x36 на число\n"
            "🚀 <b>Краш</b> — сам выбери множитель\n"
            "🃏 <b>Блэкджек</b> — beat the dealer!\n"
            "🎲 <b>Кости</b> — до x5.5 за точное число",
            parse_mode="HTML",
            reply_markup=games_list_kb()
        )

    # ─── СЛОТЫ ───────────────────────────────────────────────────
    @router.callback_query(F.data == "game_slots")
    async def cb_game_slots(cb: CallbackQuery):
        await cb.message.edit_text(
            "🎰 <b>Слоты</b>\n\nВыбери ставку:",
            parse_mode="HTML", reply_markup=bet_amounts_kb("slots")
        )

    @router.callback_query(F.data.startswith("bet_slots_") & ~F.data.endswith("_custom"))
    async def cb_play_slots(cb: CallbackQuery):
        bet = float(cb.data.split("_")[2])
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return

        result = spin_slots(bet)
        new_balance = await update_balance(cb.from_user.id, result.profit - (-bet if not result.won else 0) if result.won else result.profit)
        # Проще: вычитаем ставку, добавляем выигрыш
        await update_balance(cb.from_user.id, -bet)
        if result.won:
            await update_balance(cb.from_user.id, bet + result.profit)
        user = await get_user(cb.from_user.id)

        await save_game(cb.from_user.id, "slots", bet, "win" if result.won else "loss", result.profit if result.won else -bet, user["balance"])

        text = (
            f"🎰 <b>Слоты</b>\n\n"
            f"{result.description}\n\n"
            f"💰 Ставка: ${bet:.2f}\n"
            f"{'💸 Выигрыш' if result.won else '😔 Потеря'}: ${abs(result.profit if result.won else bet):.2f}\n"
            f"💼 Баланс: ${user['balance']:.2f}"
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=play_again_kb("slots"))

    # ─── МОНЕТКА ─────────────────────────────────────────────────
    @router.callback_query(F.data == "game_coin")
    async def cb_game_coin(cb: CallbackQuery):
        await cb.message.edit_text("🪙 <b>Монетка</b>\n\nВыбери ставку:", parse_mode="HTML", reply_markup=bet_amounts_kb("coin"))

    @router.callback_query(F.data.startswith("bet_coin_") & ~F.data.endswith("_custom"))
    async def cb_bet_coin(cb: CallbackQuery):
        bet = float(cb.data.split("_")[2])
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return
        await cb.message.edit_text(
            f"🪙 <b>Монетка</b>\n\nСтавка: ${bet}\nВыбери сторону:",
            parse_mode="HTML", reply_markup=coin_choice_kb(bet)
        )

    @router.callback_query(F.data.startswith("coin_"))
    async def cb_play_coin(cb: CallbackQuery):
        _, choice, bet_str = cb.data.split("_")
        bet = float(bet_str)
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return

        result = flip_coin(bet, choice)
        await update_balance(cb.from_user.id, -bet)
        if result.won:
            await update_balance(cb.from_user.id, bet + result.profit)
        user = await get_user(cb.from_user.id)
        await save_game(cb.from_user.id, "coin", bet, "win" if result.won else "loss", result.profit if result.won else -bet, user["balance"])

        text = (
            f"🪙 <b>Монетка</b>\n\n{result.description}\n\n"
            f"💰 Ставка: ${bet:.2f}\n"
            f"{'💸 Выигрыш' if result.won else '😔 Потеря'}: ${abs(result.profit if result.won else bet):.2f}\n"
            f"💼 Баланс: ${user['balance']:.2f}"
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=play_again_kb("coin"))

    # ─── РУЛЕТКА ─────────────────────────────────────────────────
    @router.callback_query(F.data == "game_roulette")
    async def cb_game_roulette(cb: CallbackQuery):
        await cb.message.edit_text("🎡 <b>Рулетка</b>\n\nВыбери ставку:", parse_mode="HTML", reply_markup=bet_amounts_kb("roulette"))

    @router.callback_query(F.data.startswith("bet_roulette_") & ~F.data.endswith("_custom"))
    async def cb_bet_roulette(cb: CallbackQuery):
        bet = float(cb.data.split("_")[2])
        await cb.message.edit_text(f"🎡 <b>Рулетка</b>\n\nСтавка: ${bet}\nВыбери тип ставки:", parse_mode="HTML", reply_markup=roulette_kb(bet))

    @router.callback_query(F.data.startswith("rul_"))
    async def cb_play_roulette(cb: CallbackQuery):
        parts = cb.data.split("_")
        bet_type = parts[1]
        bet = float(parts[2])
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return

        result = spin_roulette(bet, bet_type)
        await update_balance(cb.from_user.id, -bet)
        if result.won:
            await update_balance(cb.from_user.id, bet + result.profit)
        user = await get_user(cb.from_user.id)
        await save_game(cb.from_user.id, "roulette", bet, "win" if result.won else "loss", result.profit if result.won else -bet, user["balance"])

        text = (
            f"🎡 <b>Рулетка</b>\n\n{result.description}\n\n"
            f"💰 Ставка: ${bet:.2f}\n"
            f"{'💸 Выигрыш' if result.won else '😔 Потеря'}: ${abs(result.profit if result.won else bet):.2f}\n"
            f"💼 Баланс: ${user['balance']:.2f}"
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=play_again_kb("roulette"))

    # ─── КРАШ ────────────────────────────────────────────────────
    @router.callback_query(F.data == "game_crash")
    async def cb_game_crash(cb: CallbackQuery):
        await cb.message.edit_text("🚀 <b>Краш</b>\n\nВыбери ставку:", parse_mode="HTML", reply_markup=bet_amounts_kb("crash"))

    @router.callback_query(F.data.startswith("bet_crash_") & ~F.data.endswith("_custom"))
    async def cb_bet_crash(cb: CallbackQuery):
        bet = float(cb.data.split("_")[2])
        await cb.message.edit_text(
            f"🚀 <b>Краш</b>\n\nСтавка: ${bet}\nВыбери коэффициент кэшаута:",
            parse_mode="HTML", reply_markup=crash_cashout_kb(bet)
        )

    @router.callback_query(F.data.startswith("crash_"))
    async def cb_play_crash(cb: CallbackQuery):
        _, cashout_str, bet_str = cb.data.split("_")
        bet = float(bet_str)
        cashout = float(cashout_str)
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return

        result = play_crash(bet, cashout)
        await update_balance(cb.from_user.id, -bet)
        if result.won:
            await update_balance(cb.from_user.id, bet + result.profit)
        user = await get_user(cb.from_user.id)
        await save_game(cb.from_user.id, "crash", bet, "win" if result.won else "loss", result.profit if result.won else -bet, user["balance"])

        text = (
            f"🚀 <b>Краш</b>\n\n{result.description}\n\n"
            f"💰 Ставка: ${bet:.2f}\n"
            f"{'💸 Выигрыш' if result.won else '😔 Потеря'}: ${abs(result.profit if result.won else bet):.2f}\n"
            f"💼 Баланс: ${user['balance']:.2f}"
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=play_again_kb("crash"))

    # ─── БЛЭКДЖЕК ────────────────────────────────────────────────
    @router.callback_query(F.data == "game_blackjack")
    async def cb_game_blackjack(cb: CallbackQuery):
        await cb.message.edit_text("🃏 <b>Блэкджек</b>\n\nВыбери ставку:", parse_mode="HTML", reply_markup=bet_amounts_kb("blackjack"))

    @router.callback_query(F.data.startswith("bet_blackjack_") & ~F.data.endswith("_custom"))
    async def cb_start_blackjack(cb: CallbackQuery):
        bet = float(cb.data.split("_")[2])
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return

        state = start_blackjack(bet)
        state_id = str(uuid.uuid4())[:8]
        bj_states[state_id] = state

        pt = sum(10 if c.startswith(("10","J","Q","K")) else (11 if c.startswith("A") else int(c[0])) for c in state.player_hand)

        text = _bj_text(state, state_id)
        if state.done:
            await update_balance(cb.from_user.id, -bet)
            if state.result.won:
                await update_balance(cb.from_user.id, bet + state.result.profit)
            user = await get_user(cb.from_user.id)
            await save_game(cb.from_user.id, "blackjack", bet, "win" if state.result.won else "loss", state.result.profit if state.result.won else -bet, user["balance"])
            await cb.message.edit_text(text + f"\n💼 Баланс: ${user['balance']:.2f}", parse_mode="HTML", reply_markup=play_again_kb("blackjack"))
        else:
            await cb.message.edit_text(text, parse_mode="HTML", reply_markup=blackjack_action_kb(state_id))

    @router.callback_query(F.data.startswith("bj_hit_"))
    async def cb_bj_hit(cb: CallbackQuery):
        state_id = cb.data.split("_")[2]
        state = bj_states.get(state_id)
        if not state:
            await cb.answer("❌ Игра не найдена", show_alert=True)
            return

        state = blackjack_hit(state)
        bj_states[state_id] = state
        text = _bj_text(state, state_id)

        if state.done:
            await _finish_blackjack(cb, state, text)
        else:
            await cb.message.edit_text(text, parse_mode="HTML", reply_markup=blackjack_action_kb(state_id))

    @router.callback_query(F.data.startswith("bj_stand_"))
    async def cb_bj_stand(cb: CallbackQuery):
        state_id = cb.data.split("_")[2]
        state = bj_states.get(state_id)
        if not state:
            await cb.answer("❌ Игра не найдена", show_alert=True)
            return

        state = blackjack_stand(state)
        bj_states[state_id] = state
        text = _bj_text(state, state_id)
        await _finish_blackjack(cb, state, text)

    async def _finish_blackjack(cb: CallbackQuery, state: BlackjackState, text: str):
        await update_balance(cb.from_user.id, -state.bet)
        if state.result.won:
            await update_balance(cb.from_user.id, state.bet + state.result.profit)
        elif state.result.multiplier == 1:  # ничья
            await update_balance(cb.from_user.id, state.bet)
        user = await get_user(cb.from_user.id)
        await save_game(cb.from_user.id, "blackjack", state.bet,
            "win" if state.result.won else "loss",
            state.result.profit if state.result.won else -state.bet, user["balance"])
        full_text = text + f"\n\n💼 Баланс: ${user['balance']:.2f}"
        await cb.message.edit_text(full_text, parse_mode="HTML", reply_markup=play_again_kb("blackjack"))

    def _bj_text(state: BlackjackState, state_id: str) -> str:
        from games import hand_total, hand_str
        pt = hand_total(state.player_hand)
        dt = hand_total(state.dealer_hand)
        dealer_show = state.dealer_hand[0] if not state.done else hand_str(state.dealer_hand)
        text = (
            f"🃏 <b>Блэкджек</b>\n\n"
            f"🏦 Дилер: {dealer_show if state.done else state.dealer_hand[0] + ' ❓'}\n"
            f"👤 Вы: {hand_str(state.player_hand)} = {pt}\n\n"
        )
        if state.done and state.result:
            text += state.result.description
        return text

    # ─── КОСТИ ───────────────────────────────────────────────────
    @router.callback_query(F.data == "game_dice")
    async def cb_game_dice(cb: CallbackQuery):
        await cb.message.edit_text("🎲 <b>Кости</b>\n\nВыбери ставку:", parse_mode="HTML", reply_markup=bet_amounts_kb("dice"))

    @router.callback_query(F.data.startswith("bet_dice_") & ~F.data.endswith("_custom"))
    async def cb_bet_dice(cb: CallbackQuery):
        bet = float(cb.data.split("_")[2])
        await cb.message.edit_text(
            f"🎲 <b>Кости</b>\n\nСтавка: ${bet}\nВыбери тип ставки:",
            parse_mode="HTML", reply_markup=dice_choice_kb(bet)
        )

    @router.callback_query(F.data.startswith("dice_"))
    async def cb_play_dice(cb: CallbackQuery):
        parts = cb.data.split("_")
        choice = parts[1]
        bet = float(parts[2])
        user = await get_user(cb.from_user.id)
        if user["balance"] < bet:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return

        result = play_dice(bet, choice)
        await update_balance(cb.from_user.id, -bet)
        if result.won:
            await update_balance(cb.from_user.id, bet + result.profit)
        user = await get_user(cb.from_user.id)
        await save_game(cb.from_user.id, "dice", bet, "win" if result.won else "loss", result.profit if result.won else -bet, user["balance"])

        text = (
            f"🎲 <b>Кости</b>\n\n{result.description}\n\n"
            f"💰 Ставка: ${bet:.2f}\n"
            f"{'💸 Выигрыш' if result.won else '😔 Потеря'}: ${abs(result.profit if result.won else bet):.2f}\n"
            f"💼 Баланс: ${user['balance']:.2f}"
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=play_again_kb("dice"))

    # ─── ADMIN ────────────────────────────────────────────────────
    @router.message(Command("admin"))
    async def cmd_admin(msg: Message):
        if msg.from_user.id not in config.ADMIN_IDS:
            return
        balance_info = await crypto.get_balance()
        lines = ["👑 <b>Admin Panel</b>\n"]
        for b in balance_info:
            lines.append(f"• {b['currency_code']}: {b['available']}")
        await msg.answer("\n".join(lines), parse_mode="HTML")

    @router.message(Command("addbalance"))
    async def cmd_add_balance(msg: Message):
        if msg.from_user.id not in config.ADMIN_IDS:
            return
        try:
            _, uid, amount = msg.text.split()
            await update_balance(int(uid), float(amount))
            await msg.answer(f"✅ Добавлено ${amount} пользователю {uid}")
        except:
            await msg.answer("Формат: /addbalance <user_id> <amount>")

    dp.include_router(router)
