import asyncio, sys
from pathlib import Path
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

# Config ve utils import
from config import bot_username, openai_client, GS, SCORE_FILE
from utils import load_scores, save_scores, get_scores_text, ctrl_kb, games_menu_kb, is_valid_answer

# Games import
from games import game_routers
from games.kelime_anlatma import start_kelime_anlatma
from games.bosluk_doldurma import start_bosluk_doldurma
from games.kelime_sarmali import start_kelime_sarmali
from games.hizli_mat import start_hizli_mat
from games.sayi import start_sayi
from games.bilgi_y import start_bilgi_y
from games.bayrak import start_bayrak
from games.kelime_zinciri import start_kelime_zinciri
from games.baskent import start_baskent
from games.plaka import start_plaka
from games.xo import start_xo
from games.dogru_yanlis import start_dogru_yanlis
from games.bilmece import start_bilmece
from games.emoji import start_emoji
from games.eser import start_eser
from games.sicak_soguk import start_sicak_soguk
from games.duello import start_duello
from games.fark_bulmaca import start_fark_bulmaca
from games.sudoku import start_sudoku

# Commands import
from commands import router as commands_router

# Game mapping
GAME_MAP = {
    "g_ka": ("kelime_anlatma", start_kelime_anlatma),
    "g_bd": ("bosluk_doldurma", start_bosluk_doldurma),
    "g_ks": ("kelime_sarmali", start_kelime_sarmali),
    "g_hm": ("hizli_mat", start_hizli_mat),
    "g_so": ("sayi", start_sayi),
    "g_by": ("bilgi_y", start_bilgi_y),
    "g_bt": ("bayrak", start_bayrak),
    "g_kz": ("kelime_zinciri", start_kelime_zinciri),
    "g_bk": ("baskent", start_baskent),
    "g_pl": ("plaka", start_plaka),
    "g_xo": ("xo", start_xo),
    "g_dy": ("dogru_yanlis", start_dogru_yanlis),
    "g_bi": ("bilmece", start_bilmece),
    "g_em": ("emoji", start_emoji),
    "g_ey": ("eser", start_eser),
    "g_ss": ("sicak_soguk", start_sicak_soguk),
    "g_du": ("duello", start_duello),
    "g_fb": ("fark_bulmaca", start_fark_bulmaca),
    "g_su": ("sudoku", start_sudoku),
}

# Global değişkenler için
import config
import utils

async def is_game_active(state):
    cur = await state.get_state()
    return cur is not None and cur != GS.ai.state

async def start_game(msg, state, game_name, caller=None):
    """Oyun başlatma fonksiyonu"""
    data = await state.get_data()
    old_mid = data.get("bot_msg_id")
    
    if caller is None:
        caller = msg.from_user
    
    await state.clear()
    sent = None
    
    # Game fonksiyonunu bul ve çalıştır
    for key, (name, func) in GAME_MAP.items():
        if name == game_name:
            sent = await func(msg, state, caller)
            break
    
    if sent:
        await state.update_data(bot_msg_id=sent.message_id)
    elif old_mid:
        await state.update_data(bot_msg_id=old_mid)

async def start_game_by_name(msg, state, game_name, caller=None):
    """İsim ile oyun başlatma (diğer dosyalardan erişim için)"""
    await start_game(msg, state, game_name, caller)

# Control callbacks router
ctrl_router = Router()

@ctrl_router.callback_query(F.data == "c_cancel")
async def ctrl_cancel(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    data = await state.get_data()
    ans = data.get("answer", "")
    has_answer = ans and ans != "XO" and ans != "sudoku"
    text = "💥 Oyun başarıyla iptal edildi!"
    if has_answer:
        text += f"\n\n📝 Cevap: {ans}"
    
    await state.clear()
    try:
        await cb.message.edit_text(text)
    except Exception:
        await cb.message.answer(text)
    await cb.answer()

@ctrl_router.callback_query(F.data == "c_scores")
async def ctrl_scores(cb: CallbackQuery):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    scores = load_scores()
    await cb.message.answer(get_scores_text(cb.message.chat.id, scores))
    await cb.answer()

@ctrl_router.callback_query(F.data == "c_new")
async def ctrl_new(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    await state.clear()
    try:
        await cb.message.edit_text("🎮 Bir oyun seç:", reply_markup=games_menu_kb())
    except Exception:
        await cb.message.answer("🎮 Bir oyun seç:", reply_markup=games_menu_kb())
    await cb.answer()

@ctrl_router.callback_query(F.data == "c_skip")
async def ctrl_skip(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    data = await state.get_data()
    game = data.get("game", "")
    ans = data.get("answer", "")
    
    if ans:
        await cb.message.answer(f"⏭ Cevap: {ans}")
    if game:
        await start_game(cb.message, state, game, caller=cb.from_user)
    await cb.answer()

@ctrl_router.callback_query(F.data.in_(set(GAME_MAP.keys())))
async def game_select(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    if await is_game_active(state):
        await cb.answer("⚠️ Aktif oyun var! Önce /iptal yaz.", show_alert=True)
        await cb.message.answer("⚠️ Aktif bir oyun var! Önce /iptal yazarak iptal et.")
        return
    
    game_name, _ = GAME_MAP[cb.data]
    await start_game(cb.message, state, game_name, caller=cb.from_user)
    await cb.answer()

# Export fonksiyonu (diğer dosyalardan erişim için)
import games
games.start_game_by_name = start_game_by_name

async def main():
    global bot_username, openai_client
    
    token = "8285378686:AAFit5acNU2r1UpzgOCzuxfkyp1cjpxkhL8"
    if not token:
        print("Token boş olamaz!")
        sys.exit(1)
    
    api_key = input("🔑 OpenAI API Key girin (boş bırakılabilir): ").strip()
    if api_key and AsyncOpenAI:
        config.openai_client = AsyncOpenAI(api_key=api_key)
        print("✅ OpenAI bağlantısı kuruldu.")
    elif not AsyncOpenAI:
        print("⚠️ openai paketi yüklü değil. pip install openai")
    
    bot = Bot(token=token)
    info = await bot.me()
    config.bot_username = info.username
    
    dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
    
    # Router'ları ekle
    dp.include_router(commands_router)
    dp.include_router(ctrl_router)
    for router in game_routers:
        dp.include_router(router)
    
    print(f"✅ @{config.bot_username} çalışıyor!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
