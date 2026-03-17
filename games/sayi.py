import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS
from utils import add_score, ctrl_kb

router = Router()

async def start_sayi(msg, state, caller=None):
    n = random.randint(1, 100)
    await state.set_state(GS.sayi)
    await state.update_data(answer=str(n), game="sayi", attempts=0)
    return await msg.answer(
        "🔢 Sayı Oyunu\n\n1-100 arası bir sayı tuttum.\nTahmin et!",
        reply_markup=ctrl_kb()
    )

@router.message(GS.sayi)
async def sayi_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    if not msg.text:
        return
    if msg.text.startswith('/'):
        return
    
    try:
        guess = int(msg.text.strip())
    except ValueError:
        return
    
    data = await state.get_data()
    ans = int(data["answer"])
    att = data.get("attempts", 0) + 1
    await state.update_data(attempts=att)
    name = msg.from_user.first_name
    
    if guess == ans:
        add_score(msg.chat.id, msg.from_user.id, name, max(1, 11 - att))
        await msg.reply(f"✅ Doğru! {att} denemede bildin! 🎉")
        from games import start_game_by_name
        await start_game_by_name(msg, state, "sayi")
    elif guess < ans:
        await msg.reply("⬆️ Daha büyük!")
    else:
        await msg.reply("⬇️ Daha küçük!")
