import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS, plakalar
from utils import add_score, ctrl_kb, is_valid_answer, flood_ok

router = Router()

async def start_plaka(msg, state, caller=None):
    p = random.choice(plakalar)
    await state.set_state(GS.plaka)
    await state.update_data(answer=p["sehir"], game="plaka")
    return await msg.answer(
        f"🚗 Plaka Oyunu\n\n{p['plaka']} = hangi şehir?",
        reply_markup=ctrl_kb()
    )

@router.message(GS.plaka)
async def plaka_answer(msg: Message, state: FSMContext):
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
        add_score(msg.chat.id, msg.from_user.id, name)
        await msg.reply(f"✅ Doğru cevap! Tebrikler {name}! 🎉\n+1 puan")
        from games import start_game_by_name
        await start_game_by_name(msg, state, "plaka")
    else:
        await msg.reply("❌ Yanlış, tekrar dene!")
