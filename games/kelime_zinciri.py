import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS, kelimeler, kelime_set
from utils import add_score, ctrl_kb, is_valid_answer, flood_ok

router = Router()

async def start_kelime_zinciri(msg, state, caller=None):
    w = random.choice(kelimeler)["kelime"]
    await state.set_state(GS.kelime_zinciri)
    await state.update_data(last_letter=w[-1], last_word=w, game="kelime_zinciri", answer=w[-1])
    return await msg.answer(
        f"🔗 Kelime Zinciri\n\nKelime: {w.upper()}\n\n'{w[-1].upper()}' ile başlayan bir kelime yaz!\n(Sadece veri setindeki kelimeler geçerli)",
        reply_markup=ctrl_kb()
    )

@router.message(GS.kelime_zinciri)
async def kelime_zinciri_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    if not is_valid_answer(msg.text):
        return
    if not flood_ok(msg.from_user.id):
        return
    
    data = await state.get_data()
    ll = data["last_letter"]
    word = msg.text.strip().lower()
    name = msg.from_user.first_name
    
    if not word.startswith(ll):
        await msg.reply(f"❌ Kelime '{ll.upper()}' ile başlamalı!")
        return
    
    if word not in kelime_set:
        await msg.reply("❌ Bu kelime veri setinde yok! Başka dene.")
        return
    
    add_score(msg.chat.id, msg.from_user.id, name)
    nl = word[-1]
    bot_words = [w for w in kelime_set if w.startswith(nl) and w != word]
    
    if bot_words:
        bw = random.choice(list(bot_words))
        bnl = bw[-1]
        await state.update_data(last_letter=bnl, last_word=bw, answer=bnl)
        await msg.reply(
            f"✅ Güzel! +1 puan\n\n"
            f"🤖 Kelimem: {bw.upper()}\n\n"
            f"'{bnl.upper()}' ile başlayan kelime yaz!"
        )
    else:
        await msg.reply(
            f"✅ +1 puan\n\n"
            f"🤖 '{nl.upper()}' ile kelime bulamadım. Kazandın! 🎉"
        )
        add_score(msg.chat.id, msg.from_user.id, name, 2)
        await state.clear()
