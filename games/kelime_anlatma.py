import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import GS, kelimeler
from utils import add_score, load_scores, ctrl_kb, is_valid_answer, flood_ok

router = Router()

async def start_kelime_anlatma(msg, state, caller=None):
    w = random.choice(kelimeler)
    await state.set_state(GS.kelime_anlatma)
    await state.update_data(answer=w["kelime"], game="kelime_anlatma")
    return await msg.answer(
        f"📝 Kelime Anlatma\n\nİpucu: {w['ipucu']}\n\nKelimeyi tahmin et!",
        reply_markup=ctrl_kb()
    )

@router.message(GS.kelime_anlatma)
async def kelime_anlatma_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    if not is_valid_answer(msg.text):
        return
    if not flood_ok(msg.from_user.id):
        return
    
    data = await state.get_data()
    ans = data.get("answer", "")
    name = msg.from_user.first_name
    
    if msg.text.strip().lower() == ans.lower():
        scores = add_score(msg.chat.id, msg.from_user.id, name)
        await msg.reply(f"✅ Doğru cevap! Tebrikler {name}! 🎉\n+1 puan")
        # Yeni oyun başlat
        from games import start_game_by_name
        await start_game_by_name(msg, state, "kelime_anlatma")
    else:
        await msg.reply("❌ Yanlış, tekrar dene!")
