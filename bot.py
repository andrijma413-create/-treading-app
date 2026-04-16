import os
import asyncio
import random
import yfinance as yf
import pandas_ta as ta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo

# --- НАЛАШТУВАННЯ ---
TOKEN = "8708611740:AAFqaQIm-mz_bEuOKMmngxEk7PXaGwzuh-E"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Тікери для Yahoo Finance
TICKERS = {
    "Apple": "AAPL", 
    "Tesla": "TSLA", 
    "Alibaba": "BABA", 
    "McDonald's": "MCD",
    "AUD/NZD": "AUDNZD=X", 
    "AUD/CHF": "AUDCHF=X", 
    "AED/CNY": "AEDCNY=X"
}

# --- ЛОГІКА РЕАЛЬНОГО АНАЛІЗУ ---
def perform_real_analysis(asset):
    ticker_sym = TICKERS.get(asset, "EURUSD=X")
    try:
        # Отримуємо дані за останні 2 дні з інтервалом 15 хв
        df = yf.download(ticker_sym, period="2d", interval="15m", progress=False)
        
        if df.empty:
            return "❌ Дані недоступні", "Не вдалося отримати котирування. Можливо, ринок закритий (вихідні)."

        # Розрахунок технічних індикаторів
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA'] = ta.ema(df['Close'], length=20)
        
        last_rsi = df['RSI'].iloc[-1]
        last_close = df['Close'].iloc[-1]
        last_ema = df['EMA'].iloc[-1]
        
        # Аналіз для видачі сигналу
        if last_rsi < 30:
            direction = "📈 ВГОРУ (CALL)"
            reason = f"RSI низький ({round(last_rsi, 1)}). Актив перепроданий, очікується розворот вгору."
        elif last_rsi > 70:
            direction = "📉 ВНИЗ (PUT)"
            reason = f"RSI високий ({round(last_rsi, 1)}). Актив перекуплений, очікується падіння."
        elif last_close > last_ema:
            direction = "📈 ВГОРУ (CALL)"
            reason = "Ціна вище лінії EMA(20). Тренд висхідний (бичачий)."
        else:
            direction = "📉 ВНИЗ (PUT)"
            reason = "Ціна нижче лінії EMA(20). Тренд низхідний (ведмежий)."
            
        return direction, reason
    except Exception as e:
        return "⚠️ Помилка", f"Сталася помилка при читанні ринку: {e}"

# --- КЛАВІАТУРИ ---
def main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📈 Акції", callback_data="cat_stocks"))
    builder.row(types.InlineKeyboardButton(text="💱 Валюта", callback_data="cat_forex"))
    return builder.as_markup()

def asset_kb(cat):
    builder = InlineKeyboardBuilder()
    if cat == "cat_forex":
        assets = ["AUD/NZD", "AUD/CHF", "AED/CNY"]
    else:
        assets = ["Apple", "Tesla", "Alibaba", "McDonald's"]
    
    for a in assets:
        builder.row(types.InlineKeyboardButton(text=a, callback_data=f"asset_{a}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return builder.as_markup()

def trade_kb(asset):
    builder = InlineKeyboardBuilder()
    # Чистий символ для TradingView (без =X)
    clean_symbol = TICKERS.get(asset, "EURUSD").replace("=X", "")
    builder.row(types.InlineKeyboardButton(
        text="📊 Відкрити LIVE Графік", 
        web_app=WebAppInfo(url=f"https://s.tradingview.com/widgetembed/?symbol={clean_symbol}&interval=1&theme=dark")
    ))
    builder.row(types.InlineKeyboardButton(text="🔍 ПРОВЕСТИ АНАЛІЗ", callback_data=f"calc_{asset}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return builder.as_markup()

# --- ОБРОБНИКИ ПОДІЙ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "💎 **Trading Terminal v3.5**\n\nОберіть актив для аналізу та перегляду графіка:", 
        reply_markup=main_kb(), 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("cat_"))
async def select_cat(callback: types.CallbackQuery):
    await callback.message.edit_text("Оберіть потрібний актив:", reply_markup=asset_kb(callback.data))

@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text("Оберіть категорію:", reply_markup=main_kb())

@dp.callback_query(F.data.startswith("asset_"))
async def select_asset(callback: types.CallbackQuery):
    asset = callback.data.split("_")[1]
    await callback.message.answer(
        f"💹 Актив: **{asset}**\n\nВикористовуйте кнопки нижче:", 
        reply_markup=trade_kb(asset), 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("calc_"))
async def run_analysis(callback: types.CallbackQuery):
    asset = callback.data.split("_")[1]
    await callback.answer("Аналізую ринкові дані...")
    
    direction, reason = perform_real_analysis(asset)
    
    await callback.message.answer(
        f"✅ **СИГНАЛ: {asset}**\n\nПрогноз: **{direction}**\n🧠 **Обґрунтування:** {reason}",
        parse_mode="Markdown"
    )

async def main():
    print("--- БОТ ЗАПУЩЕНИЙ І ГОТОВИЙ ДО РОБОТИ ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
          
