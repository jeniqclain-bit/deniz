import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS
from utils import add_score, ctrl_kb, is_valid_answer, flood_ok

router = Router()

async def start_hizli_mat(msg, state, caller=None):
    ops = [("+", lambda a, b: a+b), ("-", lambda a, b: a-b), ("×", lambda a, b: a*b)]
    op, fn = random.choice(ops)
    a, b = random.randint(1, 50), random.randint(1, 20)
    ans = fn(a, b)
    await state.set_state(GS.hizli_mat)
    await state.update_data(answer=str(ans), game="hizli_mat")
    return await msg.answer(
        f"🔢 Hızlı Matematik\n\n{a} {op} {b} = ?",
        reply_markup=ctrl_kb()
    )

@router.message(GS.hizli_mat)
async def hizli_mat_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    if not is_valid_answer(msg.text):
        return
    if not flood_ok(msg.from_user.id):
        return
    
    data = await state.get_data()
    ans = data.get("answer", "")
    name = msg.from_user.first_name
    
    if msg.text.strip() == str(ans):
        add_score(msg.chat.id, msg.from_user.id, name)
        await msg.reply(f"✅ Doğru cevap! Tebrikler {name}! 🎉\n+1 puan")
        from games import start_game_by_name
        await start_game_by_name(msg, state, "hizli_mat")
    else:
        await msg.reply("❌ Yanlış, tekrar dene!")
