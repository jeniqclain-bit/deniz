import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS, eser_data
from utils import add_score, ctrl_kb, is_valid_answer, flood_ok

router = Router()

async def start_eser(msg, state, caller=None):
    e = random.choice(eser_data)
    await state.set_state(GS.eser)
    await state.update_data(answer=e["yazar"], game="eser")
    return await msg.answer(
        f'📚 Eser Yazar\n\n"{e["eser"]}" yazarı kim?',
        reply_markup=ctrl_kb()
    )

@router.message(GS.eser)
async def eser_answer(msg: Message, state: FSMContext):
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
        await start_game_by_name(msg, state, "eser")
    else:
        await msg.reply("❌ Yanlış, tekrar dene!")
