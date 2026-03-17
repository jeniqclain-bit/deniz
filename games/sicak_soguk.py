import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS, kelimeler
from utils import add_score, ctrl_kb, is_valid_answer, flood_ok, word_similarity

router = Router()

async def start_sicak_soguk(msg, state, caller=None):
    w = random.choice(kelimeler)
    await state.set_state(GS.sicak_soguk)
    await state.update_data(answer=w["kelime"], game="sicak_soguk", attempts=0)
    return await msg.answer(
        "🌡 Sıcak Soğuk\n\nBir kelime tuttum.\nTahmin et, yakınlığını söyleyeceğim!",
        reply_markup=ctrl_kb()
    )

@router.message(GS.sicak_soguk)
async def sicak_soguk_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    if not is_valid_answer(msg.text):
        return
    if not flood_ok(msg.from_user.id):
        return
    
    data = await state.get_data()
    ans = data["answer"]
    guess = msg.text.strip().lower()
    name = msg.from_user.first_name
    att = data.get("attempts", 0) + 1
    await state.update_data(attempts=att)
    
    if guess == ans.lower():
        add_score(msg.chat.id, msg.from_user.id, name, max(1, 11 - att))
        await msg.reply(f"🔥 Doğru! '{ans}' — {att} denemede bildin! 🎉")
        from games import start_game_by_name
        await start_game_by_name(msg, state, "sicak_soguk")
    else:
        pct = word_similarity(guess, ans)
        await msg.reply(f"Yakınlık: %{pct}")
